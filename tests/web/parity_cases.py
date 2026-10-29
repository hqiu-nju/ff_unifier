"""Reference cases from the original engine for the JavaScript parity test."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from calculator import calculate_flight, calculate_points
from programs import PROGRAMS, _CLASS_BAND
from ui_options import AIRLINE_OPTIONS


cases = []
# Every supported airline, programme, and class. Include exact half ties and
# distance-band edges, both sides of each threshold, and minimum-mile cases.
distances = [0, 1, 100, 250, 250.1, 400, 500, 500.1, 750, 750.1,
             1000, 1000.1, 1500, 1500.1, 2500, 2500.1, 2750, 2750.1,
             3500, 3500.1, 5000, 5000.1, 6500, 6500.1, 7500, 7500.1, 10560]
for program in PROGRAMS:
    for airline, _ in AIRLINE_OPTIONS:
        for booking_class in _CLASS_BAND:
            for distance in distances:
                args = [distance, airline, booking_class, program]
                cases.append({"kind": "points", "args": args, "expected": calculate_points(*args)})

# Geodesic distances, country-dependent Cathay zones and reversed routes.
routes = [("SYD", "LHR"), ("SYD", "MEL"), ("PER", "SIN"), ("HKG", "BKK"),
          ("HKG", "NRT"), ("NRT", "HKG"), ("HKG", "DEL"), ("HKG", "LHR"),
          ("JFK", "LAX"), ("SIN", "LHR"), ("HKG", "JFK")]
for origin, destination in routes:
    for airline, _ in AIRLINE_OPTIONS:
        for booking_class in _CLASS_BAND:
            for offset in range(0, len(PROGRAMS), 3):
                ids = list(PROGRAMS)[offset:offset + 3]
                args = [origin, destination, airline, booking_class, ids]
                cases.append({"kind": "flight", "args": args, "expected": calculate_flight(*args)})

json.dump(cases, sys.stdout, separators=(",", ":"))
