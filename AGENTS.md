# AGENTS.md

Repository guidance for Codex working on FF Unifier. This file travels with the
synced project and applies throughout this repository.

## Context and continuity

- This checkout is in a synced folder on the user's portable Mac. Keep commands
  and project configuration portable across machines; derive paths from the
  repository instead of hard-coding a username, home directory, or device path.
- Start by reading `README.md`, checking `git status --short`, and reviewing recent
  commits and the files relevant to the task. Existing modified and untracked
  files may contain substantial development that has not been committed.
- Preserve existing work. Do not reset, clean, overwrite, or discard changes
  unrelated to the task. Prefer small edits in the current checkout.
- Earlier development includes the Flask calculator and airline-specific rules
  for Qantas, Cathay, Velocity, and KrisFlyer, followed by the static browser
  calculator and optional flight-search gateway. Inspect current code as well as
  Git history; history alone may omit the newer work.
- Codex chats and machine settings may be unavailable on another Mac. Use the
  repository's documentation, code, and tests as durable context; say when a
  requested earlier conversation cannot be accessed.
- Record lasting setup or architecture changes in `README.md`. Update this file
  when working conventions change. Do not record credentials or transient chat
  transcripts here.

## Working in the synced folder

- Avoid simultaneous edits or Git mutations from multiple devices. If sync
  conflicts, unexpected concurrent changes, or a Git lock appear, preserve the
  files and resolve the cause before continuing affected operations. Do not
  delete lock files or conflict copies speculatively.
- Prefer the existing checkout. Git worktrees and their absolute metadata paths
  are machine-specific; do not assume a worktree made on another Mac is usable.
- Treat virtual environments, caches, and generated output as disposable local
  artifacts. Create or recreate the Python environment on the current device;
  do not rely on a virtual environment copied from another Mac.
- Keep `.venv/`, `__pycache__/`, `.pytest_cache/`, `dist/`, build output, and secret
  files out of Git, consistent with `.gitignore`. Git ignore rules do not control
  the folder-sync service or exclude these files from syncing.
- Use loopback addresses for local previews. Treat this Mac as a development
  machine; persistent hosting, launch agents, tunnels, deployment, and changes to
  another machine require a user request that includes that work.

## Architecture and sources of truth

- `calculator.py`, `programs.py`, and `airports.py` contain the Python calculation
  rules and data. `ui_options.py` supplies shared form choices.
- `app.py` and `templates/index.html` provide the original Flask interface.
- `web/` contains the static interface, browser calculation engine, Web Worker,
  and local search filtering. Earnings calculations run on the visitor's device.
- `scripts/build_web.py` exports Python data and copies browser assets into
  `dist/`. Edit source files and rebuild; do not hand-edit generated files such
  as `dist/data.js` or `dist/config.js`.
- `gateway.py` serves the integrated site and restricted search endpoints;
  `flight_search.py` implements the Duffel and Seats.aero adapters. Inventory
  requests use the gateway because provider secrets must stay on the server.
- The static build uses the Python standard library. Browser code uses native
  JavaScript modules with no npm dependencies. Retain this simple setup unless
  the requested feature calls for a dependency or tooling change.
- `.github/workflows/pages.yml` runs checks and builds the static site. A push to
  `main` can deploy GitHub Pages; consider that effect before pushing.

## Setup and commands

Run from the repository root. The static build needs Python 3.10+; browser tests
need Node.js 22+. CI uses Python 3.12 and Node.js 22.

```sh
# Create a device-local Python environment when needed.
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Python tests, including calculator, build, and offline provider contracts.
python -m pytest tests/

# Rebuild the static site and run the browser tests; no npm install is needed.
npm test

# Build and preview without Flask or Node.js.
python3 scripts/build_web.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

- Static preview: `http://127.0.0.1:8000`. Serve over HTTP rather than opening
  `index.html` directly, because the browser uses a module worker.
- Original interface: `python app.py`, then `http://127.0.0.1:5000`.
- Integrated interface: install `requirements-gateway.txt` into the local
  environment, build the static site, run `python gateway.py`, then open
  `http://127.0.0.1:5001`. Missing provider access must leave the calculator usable.
- For Python changes, run the relevant pytest checks. For browser changes, run
  `npm test`. For shared rules, exported data, or interface contracts, run both.
  Documentation-only edits need a content and diff review rather than app tests.
- Add regression coverage for changed calculation or search behavior. Preserve
  Python/browser parity, rounding, minimum miles, and distance-band boundaries.
  State which checks passed and which could not run.

## Calculation and search requirements

- Keep award points/miles distinct from status currencies. A cabin name alone
  does not establish a booking-class letter or eligibility to earn.
- Browser parity verifies agreement with the Python engine, not whether airline
  rules are current. For rule changes, verify official programme sources and
  document the source and applicable date. Keep results labelled as estimates.
- Preserve the calculator's independence from provider availability. Do not turn
  local earnings calculations into server requests without a requested change.
- Keep provider credentials in server environment or hosting secret settings.
  Never place them in browser code, generated assets, responses, logs, or chat.
- Preserve fixed provider destinations, input validation, sanitized errors,
  origin checks, timeouts, and search budgets. Do not turn the gateway into an
  arbitrary proxy or add order, booking, or payment actions incidentally.
- Seats.aero Live Search requires provider approval and the explicit
  `FF_SEATS_LIVE_APPROVED` operator setting. Do not enable it or substitute cached
  inventory merely because a key exists.
- Keep test, cached, and live search results accurately labelled. Do not invent
  seat counts, taxes, availability, or claims that real inventory was verified.
- Use offline fixtures for routine tests. Live provider calls consume external
  quota and require a task that authorizes live validation.
- Gateway limits are currently in memory per process. Preserve the documented
  single-worker deployment unless shared limits are implemented.
