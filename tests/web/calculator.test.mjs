import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { Worker } from "node:worker_threads";
import { once } from "node:events";
import { createCalculator } from "../../dist/calculator.js";
import data from "../../dist/data.js";

const calculator = createCalculator(data);
const valid = { origin: "SYD", destination: "LHR", airline: "QF", booking_class: "J", program_ids: ["QFF"] };

test("browser calculations match the Python engine across supported data and boundaries", () => {
  const result = spawnSync(process.env.PYTHON ?? "python3", ["tests/web/parity_cases.py"], { encoding: "utf8", maxBuffer: 200 * 1024 * 1024 });
  assert.equal(result.status, 0, result.stderr);
  const cases = JSON.parse(result.stdout);
  for (const { kind, args, expected } of cases) {
    const [origin, destination, airline, booking_class, program_ids] = args;
    const actual = kind === "points" ? calculator.calculatePoints(...args)
      : calculator.calculateFlight({ origin, destination, airline, booking_class, program_ids });
    assert.deepEqual(actual, expected, JSON.stringify({ kind, args }));
  }
  console.log(`Verified ${cases.length.toLocaleString()} comparisons with the Python engine.`);
});

test("normalizes typed inputs and rejects invalid flight details", () => {
  assert.deepEqual(calculator.calculateFlight({ ...valid, origin: " syd ", destination: "lhr", airline: "qf", booking_class: "j" }), calculator.calculateFlight(valid));
  for (const patch of [
    { origin: "ZZZ" }, { destination: "SYD" }, { destination: "" },
    { airline: "XY" }, { booking_class: "9" }, { program_ids: [] },
    { program_ids: ["QFF", "QFF"] }, { program_ids: ["unknown"] },
    { program_ids: ["QFF", "CATHAY", "BAEC", "KRISFLYER"] },
    { program_ids: ["__proto__"] }, { origin: "__proto__" },
    { program_ids: null }, { program_ids: [null] },
  ]) {
    assert.ok(calculator.calculateFlight({ ...valid, ...patch }).error, JSON.stringify(patch));
  }
});

test("the built worker starts, calculates, and reports validation errors", { timeout: 5000 }, async (t) => {
  const worker = new Worker(new URL("./worker-harness.mjs", import.meta.url));
  t.after(() => worker.terminate());
  assert.deepEqual((await once(worker, "message"))[0], { type: "ready" });
  const success = once(worker, "message");
  worker.postMessage({ id: 1, input: valid });
  assert.deepEqual((await success)[0], { id: 1, result: calculator.calculateFlight(valid) });
  const failure = once(worker, "message");
  worker.postMessage({ id: 2, input: { ...valid, destination: "SYD" } });
  const response = (await failure)[0];
  assert.equal(response.id, 2);
  assert.match(response.result.error, /different airports/);
  const malformed = once(worker, "message");
  worker.postMessage({ id: 3, input: null });
  assert.ok((await malformed)[0].result.error);
});
