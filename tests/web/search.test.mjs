import { test } from "node:test";
import assert from "node:assert/strict";
import { selectOffers } from "../../dist/search-model.js";

test("flight filtering runs locally and treats unreported stops as unknown", () => {
  const offers = [{ id: "connection", stops: 1, amount: "50", currency: "AUD" },
    { id: "direct", stops: 0, amount: "90", currency: "AUD" }, { id: "unknown", stops: null, amount: "20", currency: "AUD" }];
  assert.deepEqual(selectOffers(offers, { nonstop: true }).map((offer) => offer.id), ["direct"]);
  assert.equal(offers.length, 3);
});

test("sorting keeps different currencies separate and compares numeric amounts", () => {
  const offers = [{ id: "usd", currency: "USD", amount: "10" }, { id: "aud-high", currency: "AUD", amount: "100" }, { id: "aud-low", currency: "AUD", amount: "20" }];
  assert.deepEqual(selectOffers(offers).map((offer) => offer.id), ["aud-low", "aud-high", "usd"]);
  assert.deepEqual(offers.map((offer) => offer.id), ["usd", "aud-high", "aud-low"]);
});

test("award points and airport-local departure times sort without currency conversion", () => {
  const offers = [{ id: "later", miles: "100000", segments: [{ departure: "2030-01-01T14:00:00" }] },
    { id: "earlier", miles: "9000", segments: [{ departure: "2030-01-01T09:00:00" }] },
    { id: "unknown", miles: "5000", segments: [] }];
  assert.deepEqual(selectOffers(offers).map((offer) => offer.id), ["unknown", "earlier", "later"]);
  assert.deepEqual(selectOffers(offers, { sort: "departure" }).map((offer) => offer.id), ["earlier", "later", "unknown"]);
});
