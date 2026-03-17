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
# Current website-derived status tables
# ---------------------------------------------------------------------------

# Cathay short type-2 routes (751-2750 miles) include these countries.
# We map the airports currently available in airports.py for those markets.
_CATHAY_SHORT_TYPE2_AIRPORTS = {
    "NRT", "HND",      # Japan
    "CGK",             # Indonesia
    "CMB",             # Sri Lanka
    "KTM",             # Nepal
    "DAC",             # Bangladesh
    "DEL", "BOM", "MAA", "HYD", "BLR",  # India
}

# Cathay Status Points table (Cathay-operated flights), effective Aug 20, 2025.
# Table source:
# https://www.cathaypacific.com/content/dam/focal-point/cx/inspiration/2025/rise-and-shine/cathay-membership/table%20overview%20beforeafter%20eng%20(1).pdf
_CATHAY_STATUS_POINTS_BY_CLASS = {
    "F": {"ultra_short": 35, "short_type1": 45, "short_type2": 60, "medium": 110, "long": 160, "ultra_long": 180},
    "A": {"ultra_short": 35, "short_type1": 45, "short_type2": 60, "medium": 110, "long": 160, "ultra_long": 180},
    "J": {"ultra_short": 30, "short_type1": 40, "short_type2": 50, "medium": 90,  "long": 130, "ultra_long": 150},
    "C": {"ultra_short": 30, "short_type1": 40, "short_type2": 50, "medium": 90,  "long": 130, "ultra_long": 150},
    "Z": {"ultra_short": 30, "short_type1": 40, "short_type2": 50, "medium": 90,  "long": 130, "ultra_long": 150},
    "D": {"ultra_short": 25, "short_type1": 35, "short_type2": 45, "medium": 75,  "long": 100, "ultra_long": 120},
    "I": {"ultra_short": 25, "short_type1": 35, "short_type2": 45, "medium": 75,  "long": 100, "ultra_long": 120},
    "P": {"ultra_short": 25, "short_type1": 35, "short_type2": 45, "medium": 75,  "long": 100, "ultra_long": 120},
    "W": {"ultra_short": 25, "short_type1": 30, "short_type2": 35, "medium": 60,  "long": 80,  "ultra_long": 100},
    "R": {"ultra_short": 25, "short_type1": 30, "short_type2": 35, "medium": 60,  "long": 80,  "ultra_long": 100},
    "E": {"ultra_short": 15, "short_type1": 20, "short_type2": 25, "medium": 45,  "long": 65,  "ultra_long": 85},
    "Y": {"ultra_short": 25, "short_type1": 30, "short_type2": 35, "medium": 48,  "long": 70,  "ultra_long": 90},
    "B": {"ultra_short": 25, "short_type1": 30, "short_type2": 35, "medium": 48,  "long": 70,  "ultra_long": 90},
    "H": {"ultra_short": 15, "short_type1": 20, "short_type2": 25, "medium": 38,  "long": 60,  "ultra_long": 70},
    "K": {"ultra_short": 10, "short_type1": 15, "short_type2": 18, "medium": 30,  "long": 40,  "ultra_long": 50},
    "M": {"ultra_short": 20, "short_type1": 25, "short_type2": 30, "medium": 42,  "long": 60,  "ultra_long": 80},
    "L": {"ultra_short": 10, "short_type1": 15, "short_type2": 20, "medium": 32,  "long": 50,  "ultra_long": 60},
    "V": {"ultra_short": 6,  "short_type1": 10, "short_type2": 12, "medium": 22,  "long": 32,  "ultra_long": 40},
    "S": {"ultra_short": 15, "short_type1": 20, "short_type2": 25, "medium": 32,  "long": 38,  "ultra_long": 45},
    "N": {"ultra_short": 5,  "short_type1": 10, "short_type2": 15, "medium": 22,  "long": 28,  "ultra_long": 35},
    "Q": {"ultra_short": 3,  "short_type1": 6,  "short_type2": 8,  "medium": 15,  "long": 18,  "ultra_long": 25},
    "T": {"ultra_short": 3,  "short_type1": 6,  "short_type2": 8,  "medium": 15,  "long": 18,  "ultra_long": 25},
    "G": {"ultra_short": 3,  "short_type1": 6,  "short_type2": 8,  "medium": 15,  "long": 18,  "ultra_long": 25},
    "U": {"ultra_short": 3,  "short_type1": 6,  "short_type2": 8,  "medium": 15,  "long": 18,  "ultra_long": 25},
    "X": {"ultra_short": 3,  "short_type1": 6,  "short_type2": 8,  "medium": 15,  "long": 18,  "ultra_long": 25},
    # In this app, O is treated as award/non-earning.
    "O": {"ultra_short": 0,  "short_type1": 0,  "short_type2": 0,  "medium": 0,   "long": 0,   "ultra_long": 0},
}

# Singapore Airlines Elite Miles by booking class (% of flown miles).
_KRISFLYER_SQ_STATUS_PCT_BY_CLASS = PROGRAMS["KRISFLYER"].get("status_pct_by_class", {}).get("SQ", {})

# Velocity one-way mileage table (Status Credits).
# Source:
# https://www.velocityfrequentflyer.com/member-support/tiers/changes-to-status
_VELOCITY_STATUS_BANDS = [
    (250,  {"lite": 5,  "choice": 8,  "flex": 10, "business": 15}),
    (500,  {"lite": 5,  "choice": 10, "flex": 15, "business": 20}),
    (1000, {"lite": 10, "choice": 15, "flex": 20, "business": 30}),
    (1500, {"lite": 15, "choice": 20, "flex": 30, "business": 40}),
    (2500, {"lite": 20, "choice": 30, "flex": 40, "business": 55}),
    (3500, {"lite": 25, "choice": 35, "flex": 50, "business": 65}),
    (5000, {"lite": 35, "choice": 45, "flex": 60, "business": 75}),
    (6500, {"lite": 45, "choice": 55, "flex": 70, "business": 85}),
    (None, {"lite": 55, "choice": 65, "flex": 80, "business": 95}),
]

_VELOCITY_BUSINESS_CLASSES = {"F", "A", "J", "C", "D", "I", "Z"}
_VELOCITY_FLEX_CLASSES = {"W", "R", "P", "E", "Y", "B"}
_VELOCITY_CHOICE_CLASSES = {"H", "M"}


def _is_cathay_short_type2_route(origin: Optional[str], destination: Optional[str]) -> bool:
    """Return True when a CX route matches Cathay's short type-2 market set."""
    if not origin or not destination:
        return False
    origin = origin.upper()
    destination = destination.upper()
    if "HKG" not in {origin, destination}:
        return False
    other = destination if origin == "HKG" else origin
    return other in _CATHAY_SHORT_TYPE2_AIRPORTS


def _calculate_cathay_status_points(
    distance_miles: float,
    booking_class: str,
    origin: Optional[str],
    destination: Optional[str],
) -> int:
    """Cathay Membership Status Points for CX-operated flights."""
    cls = booking_class.upper()
    values = _CATHAY_STATUS_POINTS_BY_CLASS.get(cls)
    if values is None:
        # Fallback to simplified class band if an uncommon booking class is used.
        fallback = {
            "F": "F",
            "J": "J",
            "W": "W",
            "Y": "Y",
            "H": "H",
            "K": "K",
            "Q": "Q",
            "O": "O",
        }.get(get_band(cls), "Q")
        values = _CATHAY_STATUS_POINTS_BY_CLASS[fallback]

    if distance_miles <= 750:
        return values["ultra_short"]
    if distance_miles <= 2750:
        if _is_cathay_short_type2_route(origin, destination):
            return values["short_type2"]
        return values["short_type1"]
    if distance_miles <= 5000:
        return values["medium"]
    if distance_miles <= 7500:
        return values["long"]
    return values["ultra_long"]


def _calculate_velocity_status_points(distance_miles: float, booking_class: str) -> int:
    """Velocity Status Credits from one-way mileage table + inferred fare bucket."""
    cls = booking_class.upper()
    if cls in _VELOCITY_BUSINESS_CLASSES:
        bucket = "business"
    elif cls in _VELOCITY_FLEX_CLASSES:
        bucket = "flex"
    elif cls in _VELOCITY_CHOICE_CLASSES:
        bucket = "choice"
    else:
        bucket = "lite"

    for max_distance, band_values in _VELOCITY_STATUS_BANDS:
        if max_distance is None or distance_miles <= max_distance:
            return int(band_values[bucket])

    return 0


def _calculate_special_status_points(
    distance_miles: float,
    airline: str,
    booking_class: str,
    program_id: str,
    origin: Optional[str],
    destination: Optional[str],
) -> Optional[int]:
    """Return a programme-specific status value when a current-table rule applies."""
    airline = airline.upper()
    booking_class = booking_class.upper()

    if program_id == "KRISFLYER" and airline == "SQ":
        pct = _KRISFLYER_SQ_STATUS_PCT_BY_CLASS.get(booking_class)
        if pct is not None:
            return int(round(distance_miles * pct / 100))

    if program_id == "CATHAY" and airline == "CX":
        return _calculate_cathay_status_points(distance_miles, booking_class, origin, destination)

    if program_id == "VELOCITY" and airline == "VA":
        return _calculate_velocity_status_points(distance_miles, booking_class)

    return None


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
# Status-points lookup
# ---------------------------------------------------------------------------

def _get_status_band_table(prog: dict, airline: str) -> Optional[list[tuple[Optional[int], dict[str, int]]]]:
    """
    Return an optional distance-band status table for this programme/airline.

    Resolution order matches earn-rate lookup:
      1. Explicit airline key in status_bands (e.g. "BA")
      2. Alliance fallback key in status_bands (e.g. "default_oneworld")
    """
    status_bands = prog.get("status_bands")
    if not status_bands:
        return None

    if airline in status_bands:
        return status_bands[airline]

    alliance = ALLIANCES.get(airline, "none")
    alliance_key = {
        "oneworld": "default_oneworld",
        "star": "default_star",
        "skyteam": "default_skyteam",
    }.get(alliance)
    if alliance_key:
        return status_bands.get(alliance_key)

    return None


def calculate_status_points(
    distance_miles: float,
    airline: str,
    booking_class: str,
    program_id: str,
    status_rate: int,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
) -> int:
    """
    Calculate status points using either:
      - a per-flight distance-band table (if configured), or
      - legacy per-1,000-mile status_rate approximation.
    """
    special_status = _calculate_special_status_points(
        distance_miles=distance_miles,
        airline=airline,
        booking_class=booking_class,
        program_id=program_id,
        origin=origin,
        destination=destination,
    )
    if special_status is not None:
        return special_status

    prog = PROGRAMS[program_id]
    airline = airline.upper()
    band = get_band(booking_class)

    band_table = _get_status_band_table(prog, airline)
    if band_table is not None:
        for max_distance, values in band_table:
            if max_distance is None or distance_miles <= max_distance:
                return int(values.get(band, 0))
        return 0

    return int(round(distance_miles / 1000 * status_rate))


# ---------------------------------------------------------------------------
# Points calculation
# ---------------------------------------------------------------------------

def calculate_points(
    distance_miles: float,
    airline: str,
    booking_class: str,
    program_id: str,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
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

    status_points = calculate_status_points(
        distance_miles=distance_miles,
        airline=airline,
        booking_class=booking_class,
        program_id=program_id,
        status_rate=status_rate,
        origin=origin,
        destination=destination,
    )

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
        calculate_points(
            distance_miles=distance,
            airline=airline,
            booking_class=booking_class,
            program_id=pid,
            origin=origin,
            destination=destination,
        )
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
