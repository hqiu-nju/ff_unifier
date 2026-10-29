"""Contract fixtures and gateway checks. These never query a real provider."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from urllib.error import HTTPError

import pytest

import flight_search
from flight_search import FlightSearchService, SearchError, SearchSettings, validate_search
from gateway import SearchBudget, allowed_origins, create_app

ORIGIN = "https://flights.example.com"


@pytest.fixture
def query():
    return {"origin": "SYD", "destination": "SIN", "departure_date": (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat(),
            "adults": 2, "kind": "cash", "cabin": "business", "source": "qantas"}


@pytest.fixture
def cash_payload():
    # Contract-shaped fixture, not real inventory. The live_mode flag is false.
    return {"data": {"live_mode": False, "client_key": "DO-NOT-EXPOSE", "offers": [{
        "id": "fixture-cash", "total_amount": "1800.50", "total_currency": "AUD", "expires_at": "2030-01-01T00:00:00Z",
        "slices": [{"segments": [{"origin": {"iata_code": "SYD"}, "destination": {"iata_code": "SIN"},
            "departing_at": "2030-01-01T12:00:00", "arriving_at": "2030-01-01T18:00:00",
            "operating_carrier": {"iata_code": "SQ"}, "marketing_carrier": {"iata_code": "QF"},
            "marketing_carrier_flight_number": "123", "stops": [],
            "passengers": [{"fare_basis_code": "JFAKE", "cabin_class": "business"}]}]}]}]}}


@pytest.fixture
def award_payload():
    return {"data": [{"ID": "fixture-award", "Cabin": "business", "MileageCost": 70000, "RemainingSeats": 0,
        "TotalTaxes": 1290, "TaxesCurrency": "", "Source": "qantas", "Stops": 0,
        "UpdatedAt": "2030-01-01T00:00:00Z", "AvailabilitySegments": [{"OriginAirport": "SYD", "DestinationAirport": "SIN",
            "FlightNumber": "QF81", "FareClass": "U", "DepartsAt": "2030-01-01T12:00:00Z", "ArrivesAt": "2030-01-01T18:00:00Z"}]}]}


def test_duffel_contract_keeps_tokens_private_and_does_not_invent_booking_class(query, cash_payload):
    calls = []
    def transport(*args):
        calls.append(args)
        return cash_payload
    result = FlightSearchService(SearchSettings(duffel_token="duffel_test_SECRET"), transport).search(query)
    method, url, headers, body = calls[0]
    assert method == "POST" and url.startswith("https://api.duffel.com/air/offer_requests?")
    assert headers["Authorization"] == "Bearer duffel_test_SECRET"
    assert body["data"]["passengers"] == [{"type": "adult"}, {"type": "adult"}]
    assert body["data"]["slices"][0]["origin"] == "SYD"
    assert result["mode"] == "test"
    offer = result["offers"][0]
    assert offer["amount"] == "1800.50" and offer["currency"] == "AUD"
    assert offer["stops"] == 0
    assert offer["segments"][0]["operating_airline"] == "SQ"
    assert offer["segments"][0]["flight_number"] == "QF123"
    assert offer["segments"][0]["booking_class"] is None
    assert "SECRET" not in json.dumps(result) and "DO-NOT-EXPOSE" not in json.dumps(result)


def test_provider_live_mode_is_authoritative(query, cash_payload):
    cash_payload["data"]["live_mode"] = True
    result = FlightSearchService(SearchSettings(duffel_token="configured"), lambda *args: cash_payload).search(query)
    assert result["mode"] == "live"


def test_disabled_provider_is_never_called(query):
    def must_not_call(*args):
        pytest.fail("Disabled provider was contacted")
    for settings, kind in [(SearchSettings(), "cash"), (SearchSettings(seats_token="personal-key"), "award")]:
        with pytest.raises(SearchError) as caught:
            FlightSearchService(settings, must_not_call).search({**query, "kind": kind})
        assert caught.value.code == "not_configured"


def test_award_contract_preserves_unknown_seat_count_and_taxes(query, award_payload):
    calls = []
    def transport(*args):
        calls.append(args)
        return award_payload
    result = FlightSearchService(SearchSettings(seats_token="approved-key", seats_live_approved=True), transport).search({**query, "kind": "award"})
    assert calls[0][1] == "https://seats.aero/partnerapi/live"
    assert calls[0][3]["seat_count"] == 2 and calls[0][3]["smart_cache"] is False
    assert result["mode"] == "live"
    assert result["offers"][0]["miles"] == "70000"
    assert result["offers"][0]["seats"] is None
    assert result["offers"][0]["taxes"] is None
    assert "approved-key" not in json.dumps(result)


def test_award_cabins_seat_counts_and_cached_response_are_not_mislabelled(query, award_payload):
    low_seats = deepcopy(award_payload["data"][0])
    low_seats["RemainingSeats"] = 1
    other_cabin = deepcopy(award_payload["data"][0])
    other_cabin["Cabin"] = "economy"
    award_payload["data"] += [low_seats, other_cabin]
    award_payload["cached"] = True
    service = FlightSearchService(SearchSettings(seats_token="approved", seats_live_approved=True), lambda *args: award_payload)
    result = service.search({**query, "kind": "award"})
    assert len(result["offers"]) == 1
    assert result["mode"] == "cached"
    award_payload["data"][0]["Cabin"] = "premium"
    result = service.search({**query, "kind": "award", "cabin": "premium_economy"})
    assert len(result["offers"]) == 1


@pytest.mark.parametrize("payload", [{}, {"data": {}}, {"data": {"live_mode": False, "offers": [None]}},
    {"data": {"live_mode": False, "offers": [{"slices": [], "total_amount": "NaN"}]}}])
def test_bad_provider_schema_is_an_error_not_an_empty_search(query, payload):
    with pytest.raises(SearchError) as caught:
        FlightSearchService(SearchSettings(duffel_token="configured"), lambda *args: payload).search(query)
    assert caught.value.status == 502


@pytest.mark.parametrize("patch", [{"origin": "https://evil.example"}, {"destination": "SYD"}, {"departure_date": "2026-02-30"},
    {"departure_date": "1999-01-01"}, {"adults": True}, {"adults": 1.5}, {"adults": 10}, {"cabin": {}}, {"kind": []}, {"source": "../../orders"}])
def test_search_input_validation(query, patch):
    with pytest.raises(SearchError):
        validate_search({**query, **patch})


def test_gateway_capabilities_cors_and_readonly_surface(query, cash_payload):
    service = FlightSearchService(SearchSettings(duffel_token="duffel_test_SECRET"), lambda *args: cash_payload)
    client = create_app(service=service, origins={ORIGIN}).test_client()
    capabilities = client.get("/api/capabilities", headers={"Origin": ORIGIN})
    assert capabilities.json["cash"] is True and capabilities.json["cash_mode"] == "test"
    assert "SECRET" not in capabilities.text
    assert capabilities.headers["Access-Control-Allow-Origin"] == ORIGIN
    assert client.options("/api/search", headers={"Origin": ORIGIN}).status_code == 204
    response = client.post("/api/search", headers={"Origin": ORIGIN}, json=query)
    assert response.status_code == 200 and response.json["mode"] == "test"
    assert response.headers["Cache-Control"] == "no-store"
    for origin in [None, "https://evil.example", "null"]:
        response = client.post("/api/search", headers={"Origin": origin} if origin else {}, json=query)
        assert response.status_code == 403
        assert "Access-Control-Allow-Origin" not in response.headers
    assert client.post("/api/orders", headers={"Origin": ORIGIN}, json=query).status_code in {404, 405}
    assert client.get("/../flight_search.py").status_code == 404


def test_gateway_budget_bounds_provider_usage(query, cash_payload):
    calls = []
    def transport(*args):
        calls.append(args)
        return cash_payload
    service = FlightSearchService(SearchSettings(duffel_token="configured"), transport)
    budget = SearchBudget(daily=1)
    client = create_app(service=service, origins={ORIGIN}, budget=budget).test_client()
    assert client.post("/api/search", headers={"Origin": ORIGIN}, json=query).status_code == 200
    blocked = client.post("/api/search", headers={"Origin": ORIGIN}, json=query)
    assert blocked.status_code == 429 and blocked.headers["Retry-After"] == "60"
    assert len(calls) == 1


def test_gateway_rejects_bad_bodies_and_unconfigured_search(query):
    client = create_app(service=FlightSearchService(SearchSettings()), origins={ORIGIN}).test_client()
    assert client.post("/api/search", headers={"Origin": ORIGIN}, json=query).status_code == 503
    assert client.post("/api/search", headers={"Origin": ORIGIN}, json=[]).status_code == 400
    assert client.post("/api/search", headers={"Origin": ORIGIN}, data="x" * 5000, content_type="application/json").status_code == 413


@pytest.mark.parametrize("origin", ["*", "https://*.example.com", "http://public.example.com", "https://example.com/path", "https://user:secret@example.com"])
def test_origins_must_be_exact_and_secure(origin):
    with pytest.raises(ValueError):
        allowed_origins(origin)


@pytest.mark.parametrize("code,status", [(401, 503), (403, 503), (429, 429), (500, 502)])
def test_provider_errors_are_sanitized(monkeypatch, code, status):
    class BrokenOpener:
        def open(self, *args, **kwargs):
            raise HTTPError("https://provider.invalid", code, "SECRET-provider-detail", {}, None)
    monkeypatch.setattr(flight_search, "build_opener", lambda *args: BrokenOpener())
    with pytest.raises(SearchError) as caught:
        flight_search.fetch_json("POST", "https://provider.invalid/search", {}, {})
    assert caught.value.status == status
    assert "SECRET" not in str(caught.value)
