"""
Loyalty program definitions and earning rate tables.

Earning rates are represented as:
  (miles_pct, status_rate)

Where:
  miles_pct   – award miles earned as a percentage of flown miles
                (e.g. 150 → earn 150 % of the flown distance as award miles)
  status_rate – status points / credits earned per 1 000 flown miles
                (programme-specific unit: SC, Elite Miles, PQP, LP, TP, XP)

Booking-class groups used as keys in each airline entry:
  'F'  – First (full/flex)
  'J'  – Business (full/flex)
  'W'  – Premium Economy
  'Y'  – Economy full-fare
  'H'  – Economy mid-fare
  'K'  – Economy discount
  'Q'  – Economy deep-discount / promo
  'O'  – Non-earning / award ticket
"""

# ---------------------------------------------------------------------------
# Canonical cabin classes
# ---------------------------------------------------------------------------
CABIN_CLASSES = {
    "F": "First",
    "A": "First",
    "J": "Business",
    "C": "Business",
    "D": "Business",
    "I": "Business",
    "W": "Premium Economy",
    "R": "Premium Economy",
    "P": "Premium Economy",
    "E": "Premium Economy",
    "Y": "Economy",
    "B": "Economy",
    "H": "Economy",
    "K": "Economy",
    "M": "Economy",
    "L": "Economy",
    "V": "Economy",
    "S": "Economy",
    "N": "Economy",
    "Q": "Economy",
    "T": "Economy",
    "G": "Economy",
    "U": "Economy",
    "X": "Economy",
    "O": "Economy",
    "Z": "Business",
}

# Map each booking class to a simplified rate band
_CLASS_BAND = {
    "F": "F", "A": "F",
    "J": "J", "C": "J", "D": "J", "I": "J", "Z": "J",
    "W": "W", "R": "W", "P": "W", "E": "W",
    "Y": "Y", "B": "Y",
    "H": "H", "K": "H", "M": "H",
    "L": "K", "V": "K", "S": "K",
    "N": "Q", "Q": "Q", "T": "Q", "G": "Q", "U": "Q", "X": "Q",
    "O": "O",
}


def get_band(booking_class: str) -> str:
    """Return the simplified rate band for a booking class code."""
    return _CLASS_BAND.get(booking_class.upper(), "Q")


# ---------------------------------------------------------------------------
# Alliance memberships (used to select default partner earn rates)
# ---------------------------------------------------------------------------
ALLIANCES = {
    "QF": "oneworld",
    "AA": "oneworld",
    "BA": "oneworld",
    "IB": "oneworld",
    "CX": "oneworld",
    "AY": "oneworld",
    "JL": "oneworld",
    "MH": "oneworld",
    "QR": "oneworld",
    "RJ": "oneworld",
    "S7": "oneworld",
    "UL": "oneworld",
    "UA": "star",
    "LH": "star",
    "SQ": "star",
    "NH": "star",
    "AC": "star",
    "NZ": "star",
    "OS": "star",
    "SK": "star",
    "TG": "star",
    "TK": "star",
    "ET": "star",
    "SN": "star",
    "LO": "star",
    "OZ": "star",
    "CA": "star",
    "AI": "star",
    "MS": "star",
    "BR": "star",
    "OU": "star",
    "ZH": "star",
    "SA": "star",
    "AF": "skyteam",
    "KL": "skyteam",
    "DL": "skyteam",
    "KE": "skyteam",
    "AM": "skyteam",
    "AZ": "skyteam",
    "MU": "skyteam",
    "CZ": "skyteam",
    "GA": "skyteam",
    "RO": "skyteam",
    "SU": "skyteam",
    "VN": "skyteam",
    "XF": "skyteam",
    "EK": "none",
    "EY": "none",
    "WY": "none",
    "GF": "none",
    "VS": "none",
}

# ---------------------------------------------------------------------------
# Loyalty programme definitions
# ---------------------------------------------------------------------------
# Each programme entry:
#   name         – display name
#   points_unit  – name of the award currency
#   status_unit  – name of the status currency
#   min_miles    – minimum award miles credited per flight regardless of distance
#   airlines     – dict keyed by IATA airline code with band→(miles_pct, status_rate)
#   default_*    – fallback earn rates by alliance / generic
#
# status_rate is per 1 000 flown miles; callers multiply by (distance/1000).
# ---------------------------------------------------------------------------

PROGRAMS = {
    # -----------------------------------------------------------------------
    # 1. Qantas Frequent Flyer
    # -----------------------------------------------------------------------
    "QFF": {
        "name": "Qantas Frequent Flyer",
        "points_unit": "Qantas Points",
        "status_unit": "Status Credits",
        "min_miles": 500,
        "airlines": {
            "QF": {
                "F": (200, 20), "J": (150, 12), "W": (100, 8),
                "Y": (100, 8),  "H": (75, 6),   "K": (50, 4),
                "Q": (25, 2),   "O": (0, 0),
            },
            "JQ": {  # Jetstar – domestic
                "F": (0, 0),  "J": (75, 4), "W": (0, 0),
                "Y": (25, 2), "H": (25, 2), "K": (0, 0),
                "Q": (0, 0),  "O": (0, 0),
            },
            # Oneworld partners
            "AA": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            "BA": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            "CX": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            "JL": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            "QR": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            "IB": {
                "F": (150, 12), "J": (100, 8), "W": (75, 5),
                "Y": (75, 5),   "H": (50, 3),  "K": (25, 2),
                "Q": (0, 0),    "O": (0, 0),
            },
            # Emirates (non-alliance partner)
            "EK": {
                "F": (125, 10), "J": (75, 6),  "W": (50, 3),
                "Y": (50, 3),   "H": (25, 2),  "K": (0, 0),
                "Q": (0, 0),    "O": (0, 0),
            },
        },
        "default_oneworld": {
            "F": (125, 10), "J": (75, 6), "W": (50, 3),
            "Y": (50, 3),   "H": (25, 2), "K": (0, 0),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 5), "J": (50, 3), "W": (25, 2),
            "Y": (25, 2), "H": (0, 0),  "K": (0, 0),
            "Q": (0, 0),  "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },

    # -----------------------------------------------------------------------
    # 2. Singapore Airlines KrisFlyer
    # -----------------------------------------------------------------------
    "KRISFLYER": {
        "name": "Singapore Airlines KrisFlyer",
        "points_unit": "KrisFlyer Miles",
        "status_unit": "Elite Miles",
        "min_miles": 500,
        "airlines": {
            "SQ": {
                "F": (150, 20), "J": (125, 15), "W": (100, 10),
                "Y": (100, 8),  "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            # Star Alliance partners
            "UA": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
            "LH": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
            "NH": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
            "AC": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
            "NZ": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
            "TK": {
                "F": (150, 15), "J": (125, 12), "W": (100, 8),
                "Y": (100, 6),  "H": (75, 4),   "K": (50, 2),
                "Q": (25, 0),   "O": (0, 0),
            },
        },
        "default_star": {
            "F": (125, 12), "J": (100, 10), "W": (75, 6),
            "Y": (75, 4),   "H": (50, 2),   "K": (25, 0),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 5), "J": (50, 4), "W": (25, 2),
            "Y": (25, 2), "H": (0, 0),  "K": (0, 0),
            "Q": (0, 0),  "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },

    # -----------------------------------------------------------------------
    # 3. United MileagePlus
    # -----------------------------------------------------------------------
    "MILEAGEPLUS": {
        "name": "United MileagePlus",
        "points_unit": "Award Miles",
        "status_unit": "PQP (est.)",
        "min_miles": 500,
        "airlines": {
            "UA": {
                "F": (200, 75), "J": (175, 60), "W": (125, 40),
                "Y": (100, 20), "H": (100, 15), "K": (75, 10),
                "Q": (50, 5),   "O": (0, 0),
            },
            # Star Alliance partners
            "LH": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "SQ": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "NH": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "AC": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "TK": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "NZ": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
        },
        "default_star": {
            "F": (125, 25), "J": (100, 20), "W": (75, 12),
            "Y": (75, 8),   "H": (50, 5),   "K": (25, 2),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 10), "J": (50, 8), "W": (25, 4),
            "Y": (25, 3),  "H": (0, 0),  "K": (0, 0),
            "Q": (0, 0),   "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },

    # -----------------------------------------------------------------------
    # 4. American Airlines AAdvantage
    # -----------------------------------------------------------------------
    "AADVANTAGE": {
        "name": "American Airlines AAdvantage",
        "points_unit": "AAdvantage Miles",
        "status_unit": "Loyalty Points (est.)",
        "min_miles": 500,
        "airlines": {
            "AA": {
                "F": (200, 75), "J": (175, 60), "W": (100, 30),
                "Y": (100, 20), "H": (75, 15),  "K": (50, 10),
                "Q": (0, 0),    "O": (0, 0),
            },
            # Oneworld partners
            "BA": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "QF": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "CX": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "JL": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "QR": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
            "IB": {
                "F": (150, 40), "J": (125, 30), "W": (100, 20),
                "Y": (100, 12), "H": (75, 8),   "K": (50, 4),
                "Q": (25, 0),   "O": (0, 0),
            },
        },
        "default_oneworld": {
            "F": (125, 25), "J": (100, 20), "W": (75, 12),
            "Y": (75, 8),   "H": (50, 5),   "K": (25, 2),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 10), "J": (50, 8), "W": (25, 4),
            "Y": (25, 3),  "H": (0, 0),  "K": (0, 0),
            "Q": (0, 0),   "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },

    # -----------------------------------------------------------------------
    # 5. British Airways Executive Club
    # -----------------------------------------------------------------------
    "BAEC": {
        "name": "British Airways Executive Club",
        "points_unit": "Avios",
        "status_unit": "Tier Points",
        "min_miles": 500,
        "airlines": {
            "BA": {
                "F": (200, 120), "J": (150, 80), "W": (125, 40),
                "Y": (100, 20),  "H": (75, 10),  "K": (50, 5),
                "Q": (25, 0),    "O": (0, 0),
            },
            # Oneworld partners
            "AA": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "QF": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "IB": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "CX": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "JL": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "QR": {
                "F": (150, 60), "J": (125, 40), "W": (100, 20),
                "Y": (100, 10), "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
        },
        "default_oneworld": {
            "F": (125, 40), "J": (100, 30), "W": (75, 15),
            "Y": (75, 8),   "H": (50, 4),   "K": (25, 2),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 15), "J": (50, 10), "W": (25, 5),
            "Y": (25, 3),  "H": (0, 0),   "K": (0, 0),
            "Q": (0, 0),   "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },

    # -----------------------------------------------------------------------
    # 6. Air France / KLM Flying Blue
    # -----------------------------------------------------------------------
    "FLYINGBLUE": {
        "name": "Air France / KLM Flying Blue",
        "points_unit": "Flying Blue Miles",
        "status_unit": "XP (Experience Points)",
        "min_miles": 500,
        "airlines": {
            "AF": {
                "F": (200, 40), "J": (150, 30), "W": (100, 20),
                "Y": (100, 10), "H": (75, 7),   "K": (50, 5),
                "Q": (25, 2),   "O": (0, 0),
            },
            "KL": {
                "F": (200, 40), "J": (150, 30), "W": (100, 20),
                "Y": (100, 10), "H": (75, 7),   "K": (50, 5),
                "Q": (25, 2),   "O": (0, 0),
            },
            # SkyTeam partners
            "DL": {
                "F": (150, 25), "J": (125, 20), "W": (100, 12),
                "Y": (100, 8),  "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
            "KE": {
                "F": (150, 25), "J": (125, 20), "W": (100, 12),
                "Y": (100, 8),  "H": (75, 5),   "K": (50, 3),
                "Q": (25, 0),   "O": (0, 0),
            },
        },
        "default_skyteam": {
            "F": (125, 20), "J": (100, 15), "W": (75, 8),
            "Y": (75, 5),   "H": (50, 3),   "K": (25, 2),
            "Q": (0, 0),    "O": (0, 0),
        },
        "default_partner": {
            "F": (75, 8), "J": (50, 6), "W": (25, 3),
            "Y": (25, 2), "H": (0, 0),  "K": (0, 0),
            "Q": (0, 0),  "O": (0, 0),
        },
        "default_none": {
            "F": (0, 0), "J": (0, 0), "W": (0, 0),
            "Y": (0, 0), "H": (0, 0), "K": (0, 0),
            "Q": (0, 0), "O": (0, 0),
        },
    },
}

# Ordered list for the UI
PROGRAM_LIST = [
    ("QFF",        "Qantas Frequent Flyer"),
    ("KRISFLYER",  "Singapore Airlines KrisFlyer"),
    ("MILEAGEPLUS","United MileagePlus"),
    ("AADVANTAGE", "American Airlines AAdvantage"),
    ("BAEC",       "British Airways Executive Club"),
    ("FLYINGBLUE", "Air France/KLM Flying Blue"),
]
