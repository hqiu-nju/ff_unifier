import { test } from "node:test";
import assert from "node:assert/strict";
import { amexPartners, convertAmex } from "../../dist/amex.js";

const partner = (balance, id, profile = "ascent") => convertAmex(balance, profile).results.find((item) => item.id === id);

test("Australian Amex reference rates distinguish award currencies and Qantas eligibility", () => {
  assert.equal(amexPartners.length, 10);
  assert.equal(partner("100000", "VELOCITY").partnerPoints, 50000);
  assert.equal(partner(100000, "QFF").partnerPoints, null);
  assert.equal(partner(100000, "QFF").eligible, false);
  assert.equal(partner(100000, "QFF", "ascent_premium").partnerPoints, 50000);
  assert.equal(partner(100000, "KRISFLYER").partnerPoints, 33333);
  assert.equal(partner(100000, "CATHAY").partnerPoints, 33333);
  assert.equal(partner(100000, "BAEC").partnerPoints, 33333);
  assert.equal(partner(100000, "EMIRATES").partnerPoints, 25000);
  assert.equal(partner(100000, "AIR_NEW_ZEALAND").partnerPoints, 500);
  assert.equal(partner(100000, "AIR_NEW_ZEALAND").unit, "Airpoints Dollars");
});

test("minimum balances and whole-point remainders never overstate the mathematical conversion", () => {
  for (const item of amexPartners) {
    if (item.minimum !== null) {
      const below = partner(item.minimum - 1, item.id, "ascent_premium");
      assert.equal(below.belowMinimum, true, item.id);
      assert.equal(below.partnerPoints, null, item.id);
      const at = partner(item.minimum, item.id, "ascent_premium");
      assert.equal(at.belowMinimum, false, item.id);
      assert.ok(at.partnerPoints > 0, item.id);
    }
    for (const balance of [100001, 999999, 1_000_000_000_000]) {
      const result = partner(balance, item.id, "ascent_premium");
      assert.equal(result.partnerPoints / item.points * item.mr + result.remainder, balance);
      assert.ok(result.remainder >= 0 && result.remainder < item.mr);
      assert.ok(Number.isSafeInteger(result.partnerPoints));
    }
  }
  assert.equal(partner(100000, "KRISFLYER").remainder, 1);
  assert.equal(partner(100001, "VELOCITY").remainder, 1);
  assert.equal(partner(100000, "BAEC").minimum, null);
});

test("conversion rejects malformed balances and unsupported country or programme inputs", () => {
  for (const balance of ["", " ", "1,000", "1e5", "0x100", "2.5", "NaN", "Infinity", "-1", 0, -1,
    1.5, NaN, Infinity, 1_000_000_000_001, Number.MAX_SAFE_INTEGER + 1, null, undefined, true, [], {}]) {
    assert.ok(convertAmex(balance).error, String(balance));
  }
  for (const profile of ["us", "gateway", "business_ascent", "__proto__", null]) {
    assert.ok(convertAmex(100000, profile).error);
  }
  assert.equal(convertAmex(" 100000 ").balance, 100000);
});
