import { gatewayUrl } from "./config.js";
import data from "./data.js";
import { selectOffers } from "./search-model.js";

const $ = (selector) => document.querySelector(selector);
const form = $("#search-form");
const button = $("#search-submit");
const error = $("#search-error");
const availability = $("#search-availability");
const resultPanel = $("#search-results");
const apiUrl = (name) => gatewayUrl ? `${gatewayUrl}/api/${name}` : new URL(`./api/${name}`, location.href).href;
let capabilities = { cash: false, award: false, award_sources: {} };
let current = null;
let controller;
let requestId = 0;
let busy = false;
let connectionLabel = "Checking search availability…";

const today = new Date().toISOString().slice(0, 10);
$("#departure-date").min = today;
$("#departure-date").max = new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10);

function updateMode() {
  const kind = $("#search-kind").value;
  $("#award-source-field").hidden = kind !== "award";
  button.disabled = busy || !capabilities[kind];
  button.textContent = busy ? "Searching…" : kind === "award" ? "Search award seats →" : "Search flights →";
  $("#search-description").textContent = kind === "award" ? "Points prices are per passenger. Taxes may be extra." : "Fares show the total for all selected adults.";
}

function invalidate() {
  requestId += 1;
  controller?.abort();
  busy = false;
  current = null;
  error.hidden = true;
  resultPanel.hidden = true;
  resultPanel.setAttribute("aria-busy", "false");
  availability.textContent = connectionLabel;
  updateMode();
}

function text(tag, className, value) {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = value;
  return element;
}

function renderOffers() {
  if (!current) return;
  const offers = selectOffers(current.offers, { nonstop: $("#nonstop-only").checked, sort: $("#search-sort").value });
  const container = $("#flight-offers");
  container.replaceChildren();
  for (const offer of offers) {
    const card = text("article", "flight-offer", "");
    const heading = text("div", "offer-heading", "");
    const title = offer.segments?.length
      ? offer.segments.map((segment) => segment.flight_number || `${segment.origin}–${segment.destination}`).join(" · ")
      : `${current.query.origin} → ${current.query.destination}`;
    heading.append(text("h3", "", title));
    const price = offer.miles !== undefined
      ? `${Number(offer.miles).toLocaleString("en")} points / passenger`
      : new Intl.NumberFormat("en", { style: "currency", currency: offer.currency, currencyDisplay: "code" }).format(Number(offer.amount));
    heading.append(text("strong", "offer-price", price));
    card.append(heading);
    if (current.query.kind === "cash") card.append(text("p", "field-help", `Total for ${current.query.adults} adult${current.query.adults === 1 ? "" : "s"}`));
    const stops = offer.stops === null || offer.stops === undefined ? "Stops not reported" : offer.stops === 0 ? "Nonstop" : `${offer.stops} stop${offer.stops === 1 ? "" : "s"}`;
    card.append(text("p", "field-help", `${stops}${offer.seats ? ` · ${offer.seats} seats reported` : offer.miles !== undefined ? " · Seat count not reported; confirm with programme" : ""}`));
    if (offer.miles !== undefined) {
      card.append(text("p", "field-help", `Book with ${capabilities.award_sources[offer.source] ?? offer.source} · Taxes and surcharges not reported`));
    }
    for (const segment of offer.segments ?? []) {
      const row = text("div", "offer-segment", "");
      const description = `${segment.origin} → ${segment.destination} · ${segment.departure || "Time not reported"}${segment.arrival ? ` → ${segment.arrival}` : ""}${segment.operating_airline ? ` · Operated by ${segment.operating_airline}` : ""}`;
      row.append(text("p", "field-help", description));
      if (current.query.kind === "cash") {
        const action = text("button", "text-button", "Estimate earnings for this leg ↗");
        action.type = "button";
        const supported = Object.hasOwn(data.airports, segment.origin) && Object.hasOwn(data.airports, segment.destination)
          && data.airlines.some(([code]) => code === segment.operating_airline);
        action.disabled = !supported;
        if (!supported) action.textContent = "Earnings estimate unavailable for this leg";
        action.addEventListener("click", () => document.dispatchEvent(new CustomEvent("ff:estimate-segment", { detail: segment })));
        row.append(action);
      }
      card.append(row);
    }
    if (offer.expires_at) card.append(text("p", "field-help", `Quote expires: ${offer.expires_at}`));
    if (offer.updated_at) card.append(text("p", "field-help", `Provider updated: ${offer.updated_at}`));
    container.append(card);
  }
  $("#search-result-count").textContent = offers.length ? `${offers.length} of ${current.offers.length} returned options shown. Provider coverage may be incomplete.`
    : current.offers.length ? "No returned options match this filter." : "The provider returned no matching options. Other flights or award seats may still exist.";
}

form.addEventListener("input", invalidate);
form.addEventListener("change", invalidate);
$("#search-sort").addEventListener("change", renderOffers);
$("#nonstop-only").addEventListener("change", renderOffers);
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const kind = $("#search-kind").value;
  if (busy || !capabilities[kind]) return;
  const input = {
    origin: $("#search-origin").value.trim().toUpperCase(),
    destination: $("#search-destination").value.trim().toUpperCase(),
    departure_date: $("#departure-date").value,
    cabin: $("#search-cabin").value,
    adults: Number($("#search-adults").value),
    kind, source: $("#award-source").value || "qantas",
  };
  busy = true;
  error.hidden = true;
  resultPanel.hidden = true;
  resultPanel.setAttribute("aria-busy", "true");
  updateMode();
  availability.textContent = "Searching the connected travel provider. This may take up to 35 seconds…";
  controller = new AbortController();
  const activeController = controller;
  const id = ++requestId;
  const timeout = setTimeout(() => activeController.abort(), 40000);
  try {
    const response = await fetch(apiUrl("search"), { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(input), signal: activeController.signal, credentials: "omit", cache: "no-store" });
    const result = await response.json().catch(() => { throw new Error("Search is temporarily unavailable. Please try again later."); });
    if (id !== requestId) return;
    if (!response.ok) throw new Error(result.error || "Search could not be completed. Please try again later.");
    if (!Array.isArray(result.offers) || !["live", "test", "cached"].includes(result.mode)) throw new Error("The search returned an unexpected response.");
    current = result;
    $("#nonstop-only").checked = false;
    $("#search-data-mode").textContent = result.mode === "test" ? "Test data · no live inventory" : result.mode === "cached" ? "Cached availability" : "Live provider search";
    $("#search-results-title").textContent = input.kind === "award" ? "Award seat options" : "Flight options";
    $("#search-result-summary").textContent = `${input.origin} → ${input.destination} · ${input.departure_date} · ${input.adults} adult${input.adults === 1 ? "" : "s"} · ${result.provider} · Retrieved ${result.fetched_at}`;
    $("#search-result-notice").textContent = result.mode === "test" ? "These are provider sandbox results, not real flight availability or bookable fares."
      : result.mode === "cached" ? "These are previously collected results, not a fresh inventory check. Confirm availability with the airline or programme."
      : "Prices and seats can change. Confirm with the airline or programme before booking. Times are local to each airport. Currencies are grouped separately when sorting by price.";
    if (result.truncated) $("#search-result-notice").textContent += " Results are limited to the first 100 provider options.";
    renderOffers();
    resultPanel.hidden = false;
    $("#search-results-title").focus({ preventScroll: true });
    resultPanel.scrollIntoView({ behavior: "instant", block: "start" });
  } catch (failure) {
    if (id !== requestId) return;
    error.textContent = failure.name === "AbortError" ? "The search took too long. Please try again."
      : failure.name === "TypeError" ? "The search connection could not be reached. Please try again later." : failure.message;
    error.hidden = false;
  } finally {
    clearTimeout(timeout);
    if (id === requestId) {
      busy = false;
      resultPanel.setAttribute("aria-busy", "false");
      availability.textContent = error.hidden ? "Search complete. You can sort and filter the returned options on your device." : "Search could not be completed.";
      updateMode();
    }
  }
});

async function connect() {
  try {
    const response = await fetch(apiUrl("capabilities"), { cache: "no-store", credentials: "omit", signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error("unavailable");
    capabilities = await response.json();
    for (const [source, name] of Object.entries(capabilities.award_sources ?? {})) $("#award-source").add(new Option(name, source));
    for (const option of $("#search-kind").options) option.disabled = !capabilities[option.value];
    if (!capabilities.cash && capabilities.award) $("#search-kind").value = "award";
    connectionLabel = capabilities.cash || capabilities.award
      ? `${capabilities.cash ? capabilities.cash_mode === "test" ? "Cash search uses test data." : "Live cash fares connected." : "Cash search unavailable."} ${capabilities.award ? "Live award search connected." : "Award search unavailable."}`
      : "Flight and award search has not been enabled on this site yet. You can still compare earnings below.";
  } catch {
    connectionLabel = "Flight and award search is unavailable on this site. You can still compare earnings below.";
  }
  availability.textContent = connectionLabel;
  updateMode();
}
void connect();
updateMode();
