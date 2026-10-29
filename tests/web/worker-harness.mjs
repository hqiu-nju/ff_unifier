// Adapt Node's worker transport to the browser worker's message interface.
import { parentPort } from "node:worker_threads";
globalThis.self = {
  addEventListener: (type, handler) => parentPort.on(type, (data) => handler({ data })),
  postMessage: (message) => parentPort.postMessage(message),
};
await import("../../dist/worker.js");
