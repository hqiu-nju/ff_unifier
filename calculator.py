"""
Core calculation engine for FF Unifier.

Provides:
  - haversine_distance  : great-circle distance between two lat/lon points
  - get_distance        : distance between two IATA airport codes
  - get_earn_rates      : look up (miles_pct, status_rate) for a given programme /
                          airline / booking-class combination
  - calculate_points    : full points calculation for one flight + one programme
  - calculate_flight    : convenience wrapper for one flight across multiple programmes
"""

import math
from typing import Optional

from airports import AIRPORTS
from programs import PROGRAMS, ALLIANCES, get_band


# ---------------------------------------------------------------------------
# Distance helpers
# ---------------------------------------------------------------------------

def haversine_distance(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> float:
    """Return the great-circle distance in miles between two points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def get_distance(origin: str, destination: str) -> Optional[float]:
    """
    Return the great-circle distance in miles between *origin* and *destination*
    IATA codes, or ``None`` if either airport is unknown.
    """
    o = AIRPORTS.get(origin.upper())
    d = AIRPORTS.get(destination.upper())
    if o is None or d is None:
        return None
    return haversine_distance(o[2], o[3], d[2], d[3])


# ---------------------------------------------------------------------------
# Earning-rate lookup
# ---------------------------------------------------------------------------

def get_earn_rates(program_id: str, airline: str,
                   booking_class: str) -> tuple[int, int]:
    """
    Return ``(miles_pct, status_rate)`` for the given programme / airline /
    booking-class combination.

    Falls back through:
      1. Explicit airline entry in programme
      2. Alliance-specific default (default_oneworld / default_star / default_skyteam)
      3. Generic partner default (default_partner)
      4. (0, 0)
    """
    prog = PROGRAMS.get(program_id)
    if prog is None:
        return (0, 0)

    band = get_band(booking_class)
    airline = airline.upper()

    # 1. Explicit airline entry
    airline_table = prog.get("airlines", {}).get(airline)
    if airline_table:
        rates = airline_table.get(band)
        if rates:
            return rates

    # 2. Alliance-specific default
    alliance = ALLIANCES.get(airline, "none")
    alliance_key = {
        "oneworld": "default_oneworld",
        "star":     "default_star",
        "skyteam":  "default_skyteam",
    }.get(alliance)
    if alliance_key:
        alliance_table = prog.get(alliance_key)
        if alliance_table:
            rates = alliance_table.get(band)
            if rates:
                return rates

    # 3. Generic partner fallback
    partner_table = prog.get("default_partner")
    if partner_table:
        rates = partner_table.get(band)
        if rates:
            return rates

    return (0, 0)


# ---------------------------------------------------------------------------
# Points calculation
# ---------------------------------------------------------------------------

def calculate_points(
    distance_miles: float,
    airline: str,
    booking_class: str,
    program_id: str,
) -> dict:
    """
    Calculate award miles and status points for one programme.

    Returns a dict with:
      program_id    – e.g. "QFF"
      program_name  – display name
      points_unit   – display name of the award currency
      status_unit   – display name of the status currency
      award_miles   – award miles / points credited (int)
      status_points – status credits / points earned (int, may be 0)
      earn_pct      – miles earn percentage applied
      earns         – True if this programme earns anything on this flight
    """
    prog = PROGRAMS[program_id]
    miles_pct, status_rate = get_earn_rates(program_id, airline, booking_class)
    min_miles = prog.get("min_miles", 0)

    if miles_pct == 0:
        award_miles = 0
    else:
        raw_miles = distance_miles * miles_pct / 100
        award_miles = max(int(round(raw_miles)), min_miles)

    status_points = int(round(distance_miles / 1000 * status_rate))

    return {
        "program_id":    program_id,
        "program_name":  prog["name"],
        "points_unit":   prog["points_unit"],
        "status_unit":   prog["status_unit"],
        "award_miles":   award_miles,
        "status_points": status_points,
        "earn_pct":      miles_pct,
        "earns":         miles_pct > 0,
    }


def calculate_flight(
    origin: str,
    destination: str,
    airline: str,
    booking_class: str,
    program_ids: list[str],
) -> dict:
    """
    Top-level convenience function.  Given a route + operating airline +
    booking class, return earnings for each requested loyalty programme.

    Returns a dict:
      origin        – IATA code (uppercased)
      destination   – IATA code (uppercased)
      airline       – IATA code (uppercased)
      booking_class – uppercased
      distance_miles – float or None if airports unknown
      error         – error string (only present when something went wrong)
      results       – list of per-programme result dicts (from calculate_points)
    """
    origin = origin.upper()
    destination = destination.upper()
    airline = airline.upper()
    booking_class = booking_class.upper()

    # Validate airports
    if origin not in AIRPORTS:
        return {"error": f"Unknown origin airport: {origin}"}
    if destination not in AIRPORTS:
        return {"error": f"Unknown destination airport: {destination}"}
    if origin == destination:
        return {"error": "Origin and destination must be different airports."}

    distance = get_distance(origin, destination)

    # Validate programmes
    unknown_progs = [p for p in program_ids if p not in PROGRAMS]
    if unknown_progs:
        return {"error": f"Unknown programme(s): {', '.join(unknown_progs)}"}
    if not program_ids:
        return {"error": "Please select at least one loyalty programme."}

    results = [
        calculate_points(distance, airline, booking_class, pid)
        for pid in program_ids
    ]

    return {
        "origin":         origin,
        "destination":    destination,
        "origin_name":    AIRPORTS[origin][0],
        "destination_name": AIRPORTS[destination][0],
        "airline":        airline,
        "booking_class":  booking_class,
        "distance_miles": round(distance, 1),
        "results":        results,
    }
