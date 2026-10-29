/** Sorting and filtering returned options require no additional provider calls. */
export function selectOffers(offers, { nonstop = false, sort = "price" } = {}) {
  return offers.filter((offer) => !nonstop || offer.stops === 0).toSorted((a, b) => {
    if (sort === "departure") {
      const ad = a.segments?.[0]?.departure;
      const bd = b.segments?.[0]?.departure;
      if (!ad || !bd) return ad ? -1 : bd ? 1 : 0;
      return ad.localeCompare(bd);
    }
    // Keep currencies separate: AUD 100 and USD 100 aren't comparable prices.
    return (a.currency ?? "").localeCompare(b.currency ?? "")
      || Number(a.amount ?? a.miles) - Number(b.amount ?? b.miles);
  });
}
