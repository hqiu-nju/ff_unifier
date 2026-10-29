"""Read-only flight search adapters. Provider credentials stay on the host.

API contracts: https://duffel.com/docs/api/offer-requests/create-offer-request
and https://developers.seats.aero/reference/live-search
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
import os
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler


AWARD_SOURCES = {
    "qantas": "Qantas Frequent Flyer", "velocity": "Virgin Australia Velocity",
    "singapore": "Singapore KrisFlyer", "united": "United MileagePlus",
    "american": "American AAdvantage", "flyingblue": "Air France/KLM Flying Blue",
    "aeroplan": "Air Canada Aeroplan", "alaska": "Alaska Mileage Plan",
    "qatar": "Qatar Privilege Club", "emirates": "Emirates Skywards",
    "etihad": "Etihad Guest", "virginatlantic": "Virgin Atlantic Flying Club",
}
CABINS = {"economy", "premium_economy", "business", "first"}


class SearchError(Exception):
    def __init__(self, message, status=400, code="invalid_search"):
        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class SearchSettings:
    duffel_token: str = ""
    seats_token: str = ""
    seats_live_approved: bool = False

    @classmethod
    def from_env(cls):
        return cls(
            duffel_token=os.getenv("DUFFEL_ACCESS_TOKEN", ""),
            seats_token=os.getenv("SEATS_AERO_API_KEY", ""),
            # Explicit operator opt-in: live API access for this public product
            # must be approved by Seats.aero. A personal Pro key is insufficient.
            seats_live_approved=os.getenv("FF_SEATS_LIVE_APPROVED", "") == "true",
        )


def validate_search(value):
    if not isinstance(value, dict):
        raise SearchError("Please enter flight search details.")
    origin = str(value.get("origin", "")).strip().upper()
    destination = str(value.get("destination", "")).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", origin) or not re.fullmatch(r"[A-Z]{3}", destination):
        raise SearchError("Enter three-letter origin and destination airport codes.")
    if origin == destination:
        raise SearchError("Origin and destination must be different airports.")
    raw_date = value.get("departure_date", "")
    if not isinstance(raw_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date):
        raise SearchError("Choose a valid departure date.")
    try:
        departure = date.fromisoformat(raw_date)
    except ValueError:
        raise SearchError("Choose a valid departure date.") from None
    today = datetime.now(timezone.utc).date()
    if not today <= departure <= today + timedelta(days=365):
        raise SearchError("Choose a departure date within the next 365 days.")
    adults = value.get("adults", 1)
    if type(adults) is not int or not 1 <= adults <= 9:
        raise SearchError("Search for between 1 and 9 adults.")
    kind = value.get("kind", "cash")
    if not isinstance(kind, str) or kind not in {"cash", "award"}:
        raise SearchError("Choose cash fares or award seats.")
    cabin = value.get("cabin", "economy")
    if not isinstance(cabin, str) or cabin not in CABINS:
        raise SearchError("Choose a supported cabin.")
    source = value.get("source", "qantas")
    if not isinstance(source, str) or source not in AWARD_SOURCES:
        raise SearchError("Choose a supported award programme.")
    return dict(origin=origin, destination=destination, departure_date=raw_date,
                adults=adults, kind=kind, cabin=cabin, source=source)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Do not forward credentials if a provider redirects to another host.
        return None


def fetch_json(method, url, headers, body):
    request = Request(url, method=method, headers={"Accept": "application/json", **headers},
                      data=json.dumps(body).encode("utf-8"))
    try:
        with build_opener(_NoRedirect()).open(request, timeout=35) as response:
            content = response.read(5_000_001)
            if len(content) > 5_000_000:
                raise SearchError("The provider returned too much data. Try a narrower search.", 502, "provider_response")
            return json.loads(content)
    except HTTPError as error:
        if error.code == 429:
            raise SearchError("The data provider's search limit has been reached. Try again later.", 429, "provider_limit") from None
        if error.code in {401, 403}:
            raise SearchError("The flight data connection needs attention. Please try again later.", 503, "provider_access") from None
        raise SearchError("The data provider could not complete this search. Try again later.", 502, "provider_error") from None
    except (TimeoutError, socket.timeout):
        raise SearchError("The flight data provider timed out. Please try again.", 504, "provider_timeout") from None
    except (URLError, OSError, ValueError):
        raise SearchError("The flight data provider could not be reached or returned an invalid response.", 502, "provider_error") from None


def _amount(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
        return str(amount) if amount.is_finite() and amount >= 0 else None
    except InvalidOperation:
        return None


def _currency(value):
    return value if isinstance(value, str) and re.fullmatch(r"[A-Z]{3}", value) else None


def _text(value):
    return str(value)[:200] if value is not None else ""


def _positive_int(value):
    return value if type(value) is int and value > 0 else None


def _schema_error():
    raise SearchError("The data provider returned an unexpected response. Please try again later.", 502, "provider_response")


class FlightSearchService:
    def __init__(self, settings=None, transport=fetch_json):
        self.settings = settings or SearchSettings.from_env()
        self.transport = transport

    def capabilities(self):
        return {
            "cash": bool(self.settings.duffel_token),
            "cash_mode": "test" if self.settings.duffel_token.startswith("duffel_test_") else "live",
            "award": bool(self.settings.seats_token and self.settings.seats_live_approved),
            "award_sources": AWARD_SOURCES,
        }

    def search(self, query):
        caps = self.capabilities()
        if not caps[query["kind"]]:
            raise SearchError("This search option is not available on this site yet.", 503, "not_configured")
        try:
            if query["kind"] == "cash":
                result = self._cash(query)
            else:
                result = self._award(query)
        except (AttributeError, KeyError, TypeError, IndexError):
            _schema_error()
        result["fetched_at"] = datetime.now(timezone.utc).isoformat()
        result["query"] = query
        return result

    def _cash(self, query):
        payload = self.transport("POST", "https://api.duffel.com/air/offer_requests?return_offers=true&supplier_timeout=20000", {
            "Authorization": f"Bearer {self.settings.duffel_token}",
            "Duffel-Version": "v2", "Content-Type": "application/json",
        }, {"data": {
            "slices": [{key: query[key] for key in ("origin", "destination", "departure_date")}],
            "passengers": [{"type": "adult"} for _ in range(query["adults"])],
            "cabin_class": query["cabin"],
        }})
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or type(data.get("live_mode")) is not bool or not isinstance(data.get("offers"), list):
            _schema_error()
        offers = []
        for offer in data["offers"][:100]:
            slices = offer.get("slices")
            if not isinstance(slices, list) or len(slices) != 1 or not slices[0].get("segments"):
                _schema_error()
            amount, currency = _amount(offer.get("total_amount")), _currency(offer.get("total_currency"))
            if amount is None or currency is None:
                _schema_error()
            segments = []
            for segment in slices[0]["segments"]:
                operating = segment.get("operating_carrier") or {}
                marketing = segment.get("marketing_carrier") or {}
                segments.append({
                    "origin": _text(segment.get("origin", {}).get("iata_code")),
                    "destination": _text(segment.get("destination", {}).get("iata_code")),
                    "departure": _text(segment.get("departing_at")),
                    "arrival": _text(segment.get("arriving_at")),
                    "operating_airline": _text(operating.get("iata_code")),
                    "flight_number": _text(marketing.get("iata_code")) + _text(segment.get("marketing_carrier_flight_number")),
                    # A cabin or fare-basis first letter is not a reliable RBD.
                    "booking_class": None,
                })
            offers.append({"id": _text(offer.get("id")), "amount": amount, "currency": currency,
                           "expires_at": _text(offer.get("expires_at")), "segments": segments,
                           "stops": len(segments) - 1 + sum(len(s.get("stops") or []) for s in slices[0]["segments"])})
        return {"provider": "Duffel", "mode": "live" if data["live_mode"] else "test", "offers": offers,
                "truncated": len(data["offers"]) > 100}

    def _award(self, query):
        payload = self.transport("POST", "https://seats.aero/partnerapi/live", {
            "Partner-Authorization": self.settings.seats_token, "Content-Type": "application/json",
        }, {"origin_airport": query["origin"], "destination_airport": query["destination"],
            "departure_date": query["departure_date"], "source": query["source"],
            "seat_count": query["adults"], "smart_cache": False})
        # Live search has trip objects, never route/date summary availability.
        trips = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(trips, list):
            _schema_error()
        offers = []
        for trip in trips[:100]:
            if not isinstance(trip, dict):
                _schema_error()
            cabin = trip.get("Cabin")
            if cabin == "premium":
                cabin = "premium_economy"
            if cabin != query["cabin"]:
                continue
            seats = _positive_int(trip.get("RemainingSeats"))
            if seats is not None and seats < query["adults"]:
                continue
            miles = _amount(trip.get("MileageCost"))
            if miles is None:
                _schema_error()
            segments = [{
                "origin": _text(segment.get("OriginAirport")), "destination": _text(segment.get("DestinationAirport")),
                "departure": _text(segment.get("DepartsAt")), "arrival": _text(segment.get("ArrivesAt")),
                "flight_number": _text(segment.get("FlightNumber")), "booking_class": None,
            } for segment in trip.get("AvailabilitySegments", [])]
            offers.append({"id": _text(trip.get("ID")), "miles": miles,
                           "source": query["source"], "seats": seats, "segments": segments,
                           "stops": trip.get("Stops") if type(trip.get("Stops")) is int and trip["Stops"] >= 0 else None,
                           # Taxes are deliberately unreported until currency
                           # and minor-unit scaling are confirmed per provider.
                           "taxes": None, "updated_at": _text(trip.get("UpdatedAt"))})
        return {"provider": "Seats.aero", "mode": "cached" if isinstance(payload, dict) and payload.get("cached") else "live", "offers": offers,
                "truncated": len(trips) > 100}
