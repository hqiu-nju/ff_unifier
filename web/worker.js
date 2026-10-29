import data from "./data.js";
import { createCalculator } from "./calculator.js";

const calculator = createCalculator(data);
self.addEventListener("message", ({ data: message }) => {
  try {
    self.postMessage({ id: message.id, result: calculator.calculateFlight(message.input) });
  } catch {
    self.postMessage({ id: message.id, result: { error: "The comparison could not be completed. Please check your flight details and try again." } });
  }
});
self.postMessage({ type: "ready" });
