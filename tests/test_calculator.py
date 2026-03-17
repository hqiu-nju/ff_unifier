"""Tests for the FF Unifier calculator."""

import math
import pytest

from calculator import (
    haversine_distance,
    get_distance,
    get_earn_rates,
    calculate_points,
    calculate_flight,
)
from programs import get_band, PROGRAMS


# ---------------------------------------------------------------------------
# haversine_distance
# ---------------------------------------------------------------------------

class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(0, 0, 0, 0) == 0.0

    def test_sydney_to_london_approximate(self):
        # SYD (-33.9461, 151.1772) → LHR (51.4775, -0.4614) ≈ 10,558 mi
        dist = haversine_distance(-33.9461, 151.1772, 51.4775, -0.4614)
        assert 10_400 < dist < 10_750

    def test_jfk_to_lax_approximate(self):
        # JFK (40.6413, -73.7781) → LAX (33.9425, -118.4081) ≈ 2,475 mi
        dist = haversine_distance(40.6413, -73.7781, 33.9425, -118.4081)
        assert 2_300 < dist < 2_600

    def test_symmetry(self):
        d1 = haversine_distance(10, 20, 30, 40)
        d2 = haversine_distance(30, 40, 10, 20)
        assert math.isclose(d1, d2, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# get_distance
# ---------------------------------------------------------------------------

class TestGetDistance:
    def test_known_airports(self):
        dist = get_distance("SYD", "LHR")
        assert dist is not None
        assert 10_400 < dist < 10_750

    def test_unknown_origin_returns_none(self):
        assert get_distance("ZZZ", "LHR") is None

    def test_unknown_destination_returns_none(self):
        assert get_distance("SYD", "ZZZ") is None

    def test_case_insensitive(self):
        assert get_distance("syd", "lhr") == get_distance("SYD", "LHR")

    def test_syd_mel_short_hop(self):
        dist = get_distance("SYD", "MEL")
        # About 450 mi
        assert 400 < dist < 550


# ---------------------------------------------------------------------------
# get_band
# ---------------------------------------------------------------------------

class TestGetBand:
    def test_first_class_codes(self):
        assert get_band("F") == "F"
        assert get_band("A") == "F"

    def test_business_class_codes(self):
        for code in ("J", "C", "D", "I", "Z"):
            assert get_band(code) == "J", f"Expected J band for {code}"

    def test_premium_economy_codes(self):
        for code in ("W", "R", "P", "E"):
            assert get_band(code) == "W", f"Expected W band for {code}"

    def test_economy_full_fare(self):
        for code in ("Y", "B"):
            assert get_band(code) == "Y", f"Expected Y band for {code}"

    def test_economy_mid(self):
        for code in ("H", "K", "M"):
            assert get_band(code) == "H", f"Expected H band for {code}"

    def test_economy_discount(self):
        for code in ("L", "V", "S"):
            assert get_band(code) == "K", f"Expected K band for {code}"

    def test_economy_deep_discount(self):
        for code in ("N", "Q", "T", "G", "U", "X"):
            assert get_band(code) == "Q", f"Expected Q band for {code}"

    def test_non_earning(self):
        assert get_band("O") == "O"

    def test_unknown_falls_back_to_q(self):
        assert get_band("9") == "Q"

    def test_lowercase_input(self):
        assert get_band("f") == "F"
        assert get_band("j") == "J"


# ---------------------------------------------------------------------------
# get_earn_rates
# ---------------------------------------------------------------------------

class TestGetEarnRates:
    def test_qff_on_qantas_first(self):
        miles_pct, status = get_earn_rates("QFF", "QF", "F")
        assert miles_pct == 200
        assert status > 0

    def test_qff_on_qantas_economy_full(self):
        miles_pct, status = get_earn_rates("QFF", "QF", "Y")
        assert miles_pct == 100
        assert status > 0

    def test_qff_on_qantas_non_earning(self):
        miles_pct, status = get_earn_rates("QFF", "QF", "O")
        assert miles_pct == 0
        assert status == 0

    def test_qff_on_oneworld_partner_ba(self):
        miles_pct, status = get_earn_rates("QFF", "BA", "J")
        assert miles_pct > 0

    def test_krisflyer_on_sq_business(self):
        miles_pct, status = get_earn_rates("KRISFLYER", "SQ", "J")
        assert miles_pct == 125
        assert status > 0

    def test_mileageplus_on_ua_first(self):
        miles_pct, status = get_earn_rates("MILEAGEPLUS", "UA", "F")
        assert miles_pct == 200

    def test_baec_on_ba_first(self):
        miles_pct, status = get_earn_rates("BAEC", "BA", "F")
        assert miles_pct == 200
        assert status == 120  # 120 TP per 1000 miles

    def test_flyingblue_on_af_business(self):
        miles_pct, status = get_earn_rates("FLYINGBLUE", "AF", "J")
        assert miles_pct == 150

    def test_unknown_programme_returns_zero(self):
        assert get_earn_rates("UNKNOWN", "QF", "Y") == (0, 0)

    def test_star_alliance_fallback(self):
        # LH is Star Alliance; KrisFlyer should use star alliance defaults
        miles_pct_explicit, _ = get_earn_rates("KRISFLYER", "LH", "Y")
        # LH is in the explicit list for KrisFlyer, so should earn
        assert miles_pct_explicit > 0

    def test_no_alliance_fallback_earns_zero_for_qff(self):
        # EK has its own entry in QFF, but some random non-alliance airline should earn 0
        miles_pct, _ = get_earn_rates("QFF", "XY", "O")
        assert miles_pct == 0


# ---------------------------------------------------------------------------
# calculate_points
# ---------------------------------------------------------------------------

class TestCalculatePoints:
    def test_qf_first_class_long_haul(self):
        # SYD-LHR ≈ 10,560 mi, QF, F-class
        result = calculate_points(10_560, "QF", "F", "QFF")
        assert result["award_miles"] == max(int(round(10_560 * 2.0)), 500)
        assert result["status_points"] > 0
        assert result["earns"] is True
        assert result["earn_pct"] == 200

    def test_non_earning_class(self):
        result = calculate_points(5_000, "QF", "O", "QFF")
        assert result["award_miles"] == 0
        assert result["status_points"] == 0
        assert result["earns"] is False

    def test_minimum_miles_applied(self):
        # Very short distance; minimum 500 miles should apply
        result = calculate_points(100, "QF", "Y", "QFF")
        assert result["award_miles"] == 500

    def test_result_keys_present(self):
        result = calculate_points(5_000, "QF", "Y", "QFF")
        for key in ("program_id", "program_name", "points_unit",
                    "status_unit", "award_miles", "status_points",
                    "earn_pct", "earns"):
            assert key in result, f"Missing key: {key}"

    def test_programme_metadata(self):
        result = calculate_points(5_000, "QF", "Y", "QFF")
        assert result["program_id"] == "QFF"
        assert result["program_name"] == "Qantas Frequent Flyer"
        assert result["points_unit"] == "Qantas Points"

    def test_status_points_scale_with_distance(self):
        r_short = calculate_points(1_000, "QF", "J", "QFF")
        r_long  = calculate_points(10_000, "QF", "J", "QFF")
        assert r_long["status_points"] > r_short["status_points"]

    def test_qff_oneworld_uses_distance_band_table(self):
        # BA (oneworld) in Y band: 751-1500 mi should award 30 SC.
        result = calculate_points(1_000, "BA", "Y", "QFF")
        assert result["status_points"] == 30

    def test_qff_oneworld_status_band_boundary(self):
        # BA (oneworld) in J band:
        # - up to 750 mi => 40 SC
        # - from 751 mi  => 60 SC
        at_boundary = calculate_points(750, "BA", "J", "QFF")
        just_over = calculate_points(751, "BA", "J", "QFF")
        assert at_boundary["status_points"] == 40
        assert just_over["status_points"] == 60

    def test_qff_qantas_stays_on_legacy_status_rate(self):
        # QF should keep its own status-rate table (not oneworld partner table).
        result = calculate_points(1_000, "QF", "J", "QFF")
        assert result["status_points"] == 12

    def test_qff_cathay_uses_oneworld_status_table(self):
        # CX is oneworld; 1,000 miles in Y should use partner status table (30 SC).
        result = calculate_points(1_000, "CX", "Y", "QFF")
        assert result["status_points"] == 30

    def test_qff_singapore_airlines_not_earnable(self):
        result = calculate_points(1_000, "SQ", "Y", "QFF")
        assert result["award_miles"] == 0
        assert result["status_points"] == 0
        assert result["earns"] is False

    def test_qff_virgin_australia_not_earnable(self):
        result = calculate_points(1_000, "VA", "Y", "QFF")
        assert result["award_miles"] == 0
        assert result["status_points"] == 0
        assert result["earns"] is False

    def test_krisflyer_sq_status_uses_official_percent_table(self):
        # SQ F class earns 200% Elite miles.
        result = calculate_points(1_000, "SQ", "F", "KRISFLYER")
        assert result["status_points"] == 2_000

    def test_krisflyer_sq_discount_status_percent(self):
        # SQ K class earns 50% Elite miles.
        result = calculate_points(1_000, "SQ", "K", "KRISFLYER")
        assert result["status_points"] == 500

    def test_cathay_short_type1_status_points(self):
        # HKG-BKK (short type 1) in J should earn 40 Status Points.
        result = calculate_flight("HKG", "BKK", "CX", "J", ["CATHAY"])
        assert "error" not in result
        assert result["results"][0]["status_points"] == 40

    def test_cathay_short_type2_status_points(self):
        # HKG-NRT (short type 2) in J should earn 50 Status Points.
        result = calculate_flight("HKG", "NRT", "CX", "J", ["CATHAY"])
        assert "error" not in result
        assert result["results"][0]["status_points"] == 50

    def test_velocity_business_status_points(self):
        # 251-500 miles in Business bucket => 20 Status Credits.
        result = calculate_points(400, "VA", "J", "VELOCITY")
        assert result["status_points"] == 20

    def test_velocity_lite_status_points(self):
        # 251-500 miles in Lite bucket => 5 Status Credits.
        result = calculate_points(400, "VA", "K", "VELOCITY")
        assert result["status_points"] == 5


# ---------------------------------------------------------------------------
# calculate_flight
# ---------------------------------------------------------------------------

class TestCalculateFlight:
    def test_basic_syd_lhr_qf_business_qff(self):
        result = calculate_flight("SYD", "LHR", "QF", "J", ["QFF"])
        assert "error" not in result
        assert result["origin"] == "SYD"
        assert result["destination"] == "LHR"
        assert result["airline"] == "QF"
        assert result["booking_class"] == "J"
        assert result["distance_miles"] > 10_000
        assert len(result["results"]) == 1

    def test_three_programmes(self):
        result = calculate_flight("JFK", "LHR", "BA", "J",
                                  ["BAEC", "AADVANTAGE", "FLYINGBLUE"])
        assert "error" not in result
        assert len(result["results"]) == 3

    def test_unknown_origin_returns_error(self):
        result = calculate_flight("ZZZ", "LHR", "QF", "Y", ["QFF"])
        assert "error" in result

    def test_unknown_destination_returns_error(self):
        result = calculate_flight("SYD", "ZZZ", "QF", "Y", ["QFF"])
        assert "error" in result

    def test_same_origin_destination_error(self):
        result = calculate_flight("SYD", "SYD", "QF", "Y", ["QFF"])
        assert "error" in result

    def test_unknown_programme_returns_error(self):
        result = calculate_flight("SYD", "LHR", "QF", "Y", ["UNKNOWN"])
        assert "error" in result

    def test_no_programmes_returns_error(self):
        result = calculate_flight("SYD", "LHR", "QF", "Y", [])
        assert "error" in result

    def test_case_insensitive_inputs(self):
        r1 = calculate_flight("syd", "lhr", "qf", "j", ["QFF"])
        r2 = calculate_flight("SYD", "LHR", "QF", "J", ["QFF"])
        assert r1["distance_miles"] == r2["distance_miles"]
        assert r1["results"][0]["award_miles"] == r2["results"][0]["award_miles"]

    def test_airport_names_in_result(self):
        result = calculate_flight("SYD", "LHR", "QF", "J", ["QFF"])
        assert "Sydney" in result["origin_name"]
        assert "London" in result["destination_name"]

    def test_distance_is_positive(self):
        result = calculate_flight("SYD", "MEL", "QF", "Y", ["QFF"])
        assert result["distance_miles"] > 0

    def test_singapore_to_london_krisflyer(self):
        result = calculate_flight("SIN", "LHR", "SQ", "J", ["KRISFLYER"])
        assert "error" not in result
        r = result["results"][0]
        assert r["earn_pct"] == 125
        assert r["award_miles"] > 0
        assert r["status_points"] > 0
