import data from "./data.js";
import "./search.js";

const $ = (selector) => document.querySelector(selector);
const form = $("#flight-form");
const button = $("#calculate");
const error = $("#form-error");
const status = $("#calculation-status");
const results = $("#results");
const number = new Intl.NumberFormat("en");
let worker;
let requestId = 0;
let busy = false;
let ready = false;
let timeout;

function failStartup() {
  clearTimeout(timeout);
  ready = false;
  busy = false;
  worker?.terminate();
  $("#flight-fields").disabled = true;
  $("#program-fields").disabled = true;
  $("#example").disabled = true;
  button.disabled = true;
  button.textContent = "Calculator unavailable";
  results.setAttribute("aria-busy", "false");
  const message = "The local calculator could not load. Reload the page to try again. Use a current browser with JavaScript and Web Workers enabled.";
  $("#startup-error").textContent = message;
  $("#startup-error").hidden = false;
  status.textContent = message;
}

function updateSelection() {
  const boxes = [...document.querySelectorAll('input[name="programs"]')];
  const count = boxes.filter((box) => box.checked).length;
  for (const box of boxes) box.disabled = count === 3 && !box.checked;
  $("#program-count").textContent = `${count} of 3 selected${count === 3 ? " · Deselect a programme to choose another." : ""}`;
}

function populateForm() {
  for (const [code, [name, city]] of Object.entries(data.airports).sort(([a], [b]) => a.localeCompare(b))) {
    const option = document.createElement("option");
    option.value = code;
    option.label = `${city} · ${name}`;
    $("#airports").append(option);
  }
  for (const [code, label] of data.airlines) $("#airline").add(new Option(label, code));
  for (const [cabin, classes] of data.booking_classes) {
    const group = document.createElement("optgroup");
    group.label = cabin;
    for (const [code, label] of classes) group.append(new Option(label, code));
    $("#booking_class").append(group);
  }
  for (const [id, name] of data.program_list) {
    const label = document.createElement("label");
    label.className = "program-option";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.name = "programs";
    checkbox.value = id;
    checkbox.checked = id === "QFF";
    checkbox.setAttribute("aria-describedby", "program-help");
    const text = document.createElement("span");
    text.textContent = name;
    label.append(checkbox, text);
    $("#programs").append(label);
  }
  updateSelection();
}

function invalidate() {
  $("#import-flight-info").hidden = true;
  requestId += 1;
  busy = false;
  results.hidden = true;
  results.setAttribute("aria-busy", "false");
  error.hidden = true;
  button.disabled = !ready;
  button.textContent = ready ? "Compare earnings →" : "Loading calculator…";
  status.textContent = ready ? "Flight details changed. Compare again for updated estimates." : "Loading calculator.";
}

document.addEventListener("ff:estimate-segment", ({ detail: segment }) => {
  if (!ready) return;
  invalidate();
  $("#origin").value = segment.origin;
  $("#destination").value = segment.destination;
  $("#airline").value = segment.operating_airline;
  $("#booking_class").value = "";
  $("#import-flight-info").textContent = "Flight details copied. Enter the booking-class letter on your ticket to estimate earnings. The cabin alone is not enough.";
  $("#import-flight-info").hidden = false;
  form.scrollIntoView({ behavior: "instant", block: "start" });
  $("#booking_class").focus({ preventScroll: true });
});

function showResult(result) {
  if (result.error) {
    error.textContent = result.error;
    error.hidden = false;
    results.hidden = true;
    status.textContent = "Check your flight details.";
    return;
  }
  $("#route-summary").textContent = `${result.origin_name} (${result.origin}) → ${result.destination_name} (${result.destination}) · ${result.airline} · Class ${result.booking_class} · ${number.format(Math.round(result.distance_miles))} mi`;
  const cards = $("#result-cards");
  cards.replaceChildren();
  for (const [index, item] of result.results.entries()) {
    const card = $("#result-template").content.cloneNode(true);
    card.querySelector(".result-index").textContent = `PROGRAMME 0${index + 1}`;
    card.querySelector("h3").textContent = item.program_name;
    card.querySelector(".result-currency").textContent = item.points_unit;
    card.querySelector(".result-miles").textContent = number.format(item.award_miles);
    card.querySelector(".result-status-unit").textContent = item.status_unit;
    card.querySelector(".result-status").textContent = number.format(item.status_points);
    card.querySelector(".result-rate").textContent = item.earns ? `${item.earn_pct}% distance earning rate` : "No award miles in the bundled model";
    cards.append(card);
  }
  results.hidden = false;
  status.textContent = `Comparison ready for ${result.results.length} programmes. Results are indicative estimates.`;
  $("#results-title").focus({ preventScroll: true });
  results.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
}

$("#swap").addEventListener("click", () => {
  [$("#origin").value, $("#destination").value] = [$("#destination").value, $("#origin").value];
  invalidate();
});
form.addEventListener("input", invalidate);
form.addEventListener("change", () => { updateSelection(); invalidate(); });
$("#example").addEventListener("click", () => {
  $("#origin").value = "SYD";
  $("#destination").value = "LHR";
  $("#airline").value = "QF";
  $("#booking_class").value = "J";
  for (const box of document.querySelectorAll('input[name="programs"]')) {
    box.checked = ["QFF", "AADVANTAGE", "BAEC"].includes(box.value);
  }
  updateSelection();
  invalidate();
  form.requestSubmit();
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!ready || busy) return;
  error.hidden = true;
  const selected = [...document.querySelectorAll('input[name="programs"]:checked')].map((box) => box.value);
  if (!selected.length) {
    showResult({ error: "Please select at least one loyalty programme." });
    document.querySelector('input[name="programs"]').focus();
    return;
  }
  busy = true;
  button.disabled = true;
  button.textContent = "Calculating on your device…";
  results.hidden = true;
  results.setAttribute("aria-busy", "true");
  status.textContent = "Calculating on your device.";
  const input = {
    origin: $("#origin").value,
    destination: $("#destination").value,
    airline: $("#airline").value,
    booking_class: $("#booking_class").value,
    program_ids: selected,
  };
  worker.postMessage({ id: ++requestId, input });
});

try {
  populateForm();
  timeout = setTimeout(failStartup, 15000);
  worker = new Worker(new URL("./worker.js", import.meta.url), { type: "module" });
  worker.addEventListener("error", (event) => { event.preventDefault(); failStartup(); });
  worker.addEventListener("messageerror", failStartup);
  worker.addEventListener("message", ({ data: message }) => {
    if (message.type === "ready") {
      clearTimeout(timeout);
      ready = true;
      $("#flight-fields").disabled = false;
      $("#program-fields").disabled = false;
      $("#example").disabled = false;
      button.disabled = false;
      button.textContent = "Compare earnings →";
      status.textContent = "Calculator ready. Your flight details stay in this browser.";
      return;
    }
    if (message.id !== requestId) return;
    busy = false;
    button.disabled = false;
    button.textContent = "Compare earnings →";
    results.setAttribute("aria-busy", "false");
    showResult(message.result);
  });
} catch {
  failStartup();
}
