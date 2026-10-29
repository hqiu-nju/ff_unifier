// Australian consumer Membership Rewards reference rates, reviewed 29 October 2026.
// See README.md for sources and verification limits. Card-specific rates take precedence.
export const amexReviewDate = "29 October 2026";
export const amexSources = {
  amex: "https://www.americanexpress.com/en-au/rewards/membership-rewards/travel/all/1000",
  rates: "https://www.pointhacks.com.au/american-express/",
  terms: "https://www.americanexpress.com/content/dam/amex/en-au/company/terms-and-conditions/AME12313_MRTCsDoc-Consumer_FA.pdf",
};

export const amexProfiles = [
  { id: "ascent", name: "Ascent" },
  { id: "ascent_premium", name: "Ascent Premium" },
];

// Ratios are MR points : partner points. Minimums are expressed in MR points.
// These are arithmetic estimates, not a model of each partner's transfer increments.
export const amexPartners = [
  { id: "VELOCITY", name: "Velocity Frequent Flyer", unit: "Velocity Points", mr: 2, points: 1, minimum: 2000 },
  { id: "QFF", name: "Qantas Frequent Flyer", unit: "Qantas Points", mr: 2, points: 1, minimum: 2000, premiumOnly: true },
  { id: "KRISFLYER", name: "Singapore Airlines KrisFlyer", unit: "KrisFlyer miles", mr: 3, points: 1, minimum: 7500 },
  { id: "CATHAY", name: "Cathay", unit: "Asia Miles", mr: 3, points: 1, minimum: 7500 },
  { id: "BAEC", name: "British Airways Club", unit: "Avios", mr: 3, points: 1, minimum: null },
  { id: "QATAR", name: "Qatar Airways Privilege Club", unit: "Avios", mr: 3, points: 1, minimum: 750 },
  { id: "EMIRATES", name: "Emirates Skywards", unit: "Skywards miles", mr: 4, points: 1, minimum: 4000 },
  { id: "ENRICH", name: "Malaysia Airlines Enrich", unit: "Enrich points", mr: 3, points: 1, minimum: 1500 },
  { id: "VIRGIN_ATLANTIC", name: "Virgin Atlantic Flying Club", unit: "Virgin Points", mr: 3, points: 1, minimum: 3000 },
  { id: "AIR_NEW_ZEALAND", name: "Air New Zealand Airpoints", unit: "Airpoints Dollars", mr: 200, points: 1, minimum: 2000 },
];

export function convertAmex(balance, profile = "ascent") {
  if (!amexProfiles.some(({ id }) => id === profile)) {
    return { error: "Choose a supported Australian Membership Rewards programme." };
  }
  // Reject empty, exponential, fractional, coerced and unsafe inputs consistently.
  const raw = typeof balance === "string" ? balance.trim() : balance;
  if ((typeof raw !== "number" && (typeof raw !== "string" || !/^\d+$/.test(raw)))
      || !Number.isSafeInteger(Number(raw)) || Number(raw) < 1 || Number(raw) > 1_000_000_000_000) {
    return { error: "Enter a whole number of Amex points between 1 and 1,000,000,000,000." };
  }
  const amount = Number(raw);
  return {
    balance: amount,
    profile,
    results: amexPartners.map((partner) => {
      const eligible = !partner.premiumOnly || profile === "ascent_premium";
      const belowMinimum = partner.minimum !== null && amount < partner.minimum;
      const wholeUnits = Math.floor(amount / partner.mr);
      return {
        ...partner,
        eligible,
        belowMinimum,
        // An unavailable partner or insufficient balance must not suggest a usable transfer.
        partnerPoints: eligible && !belowMinimum ? wholeUnits * partner.points : null,
        remainder: eligible && !belowMinimum ? amount - wholeUnits * partner.mr : null,
      };
    }),
  };
}
