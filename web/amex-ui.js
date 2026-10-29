import { amexProfiles, amexReviewDate, amexSources, convertAmex } from "./amex.js";

const form = document.querySelector("#amex-form");
const profile = document.querySelector("#amex-profile");
const balance = document.querySelector("#amex-balance");
const results = document.querySelector("#amex-results");
const error = document.querySelector("#amex-error");
const status = document.querySelector("#amex-status");
const number = new Intl.NumberFormat("en-AU");

for (const item of amexProfiles) profile.add(new Option(item.name, item.id));
document.querySelector("#amex-reviewed").textContent = `Reference rates reviewed ${amexReviewDate}.`;
for (const link of document.querySelectorAll("[data-amex-source]")) {
  link.href = amexSources[link.dataset.amexSource];
}

function invalidate() {
  results.hidden = true;
  error.hidden = true;
  status.textContent = "Amex details changed. Convert again for updated estimates.";
}

function showConversions() {
  const conversion = convertAmex(balance.value, profile.value);
  error.hidden = !conversion.error;
  results.hidden = Boolean(conversion.error);
  if (conversion.error) {
    error.textContent = conversion.error;
    status.textContent = "Check your Amex points balance and programme.";
    return;
  }

  const rows = document.querySelector("#amex-rows");
  rows.replaceChildren();
  for (const item of conversion.results) {
    const row = document.createElement("tr");
    const name = document.createElement("th");
    name.scope = "row";
    name.textContent = item.name;
    const ratio = document.createElement("td");
    ratio.textContent = `${item.mr}:${item.points}`;
    const amount = document.createElement("td");
    const notes = document.createElement("td");
    if (!item.eligible) {
      amount.textContent = "Unavailable";
      notes.textContent = "Requires an eligible Ascent Premium account.";
    } else if (item.belowMinimum) {
      amount.textContent = "Below minimum";
      notes.textContent = `Published minimum: ${number.format(item.minimum)} MR points.`;
    } else {
      amount.textContent = `${number.format(item.partnerPoints)} ${item.unit}`;
      notes.textContent = item.minimum === null ? "Check your transfer minimum with Amex." : `Minimum: ${number.format(item.minimum)} MR points.`;
      if (item.remainder) notes.textContent += ` ${number.format(item.remainder)} MR ${item.remainder === 1 ? "point" : "points"} left after whole-point conversion.`;
    }
    row.append(name, ratio, amount, notes);
    rows.append(row);
  }
  document.querySelector("#amex-summary").textContent = `${number.format(conversion.balance)} Membership Rewards points · ${profile.selectedOptions[0].textContent}`;
  status.textContent = "Amex conversion estimates ready for 10 airline partners. Each row is a separate alternative for the same balance.";
}

form.addEventListener("input", invalidate);
form.addEventListener("change", invalidate);
form.addEventListener("submit", (event) => {
  event.preventDefault();
  showConversions();
});
showConversions();
