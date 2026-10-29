# FF Unifier

Calculate and compare **frequent flyer points** and **status credits** across up to **3 loyalty programmes** for any flight.

## Features

- Enter a flight route (origin → destination), operating airline and booking class
- Instantly see award miles/points and status credits for up to 3 programmes side by side
- Supports 100+ airports worldwide and 35+ airlines
- Convert Australian Amex Membership Rewards balances into estimated airline
  points/miles across ten partners in the static and integrated interfaces
- Loyalty programmes supported:
  - **Qantas Frequent Flyer** (Status Credits + Qantas Points)
  - **Cathay Membership** (Status Points + Asia Miles)
  - **Singapore Airlines KrisFlyer** (Elite Miles + KrisFlyer Miles)
  - **Virgin Australia Velocity** (Status Credits + Velocity Points)
  - **United MileagePlus** (PQP + Award Miles)
  - **American Airlines AAdvantage** (Loyalty Points + AAdvantage Miles)
  - **British Airways Executive Club** (Tier Points + Avios)
  - **Air France / KLM Flying Blue** (XP + Flying Blue Miles)

## Public website with browser-side compute

The static version runs the calculator on the visitor's device in a Web Worker.
The host only serves HTML, CSS, JavaScript, and bundled tables. Earnings inputs
are sent to the local worker, never to a calculation API. Flight and award searches
send route, departure date, cabin, and adult count to a separate provider gateway.
No Python installation or browser extension is needed for visitors.

This version includes one-way cash-flight and award-seat search through an
optional hosted gateway. Search requires operator-configured provider access; it
is disabled when access is missing. The browser sorts and filters returned offers
locally and can copy a supported paid flight leg into the earnings calculator.
A booking-class letter must still be entered: cabin alone is insufficient.
Never put secret API keys in the static bundle.

### Build and preview

Maintainers need Python 3.10+ to build. The build uses only the standard library;
Flask is not required for the static website.

```bash
python3 scripts/build_web.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open <http://127.0.0.1:8000>. Serve over HTTP or HTTPS; opening `index.html`
directly with `file://` does not support the module worker. Use a current Chrome,
Firefox, Edge, or Safari with JavaScript and Web Workers enabled.

If Node.js 22+ is installed, `npm run build` and `npm run preview` provide the
same commands. There are no npm packages to install.

### Publish on GitHub Pages

The repository includes `.github/workflows/pages.yml`. In the repository's
**Settings → Pages → Build and deployment**, select **GitHub Actions** as the
source. Once these changes are on `main`, the workflow tests, builds, and deploys
`dist/`. You can also start it manually from **Actions → Static website**.
Pull requests run the checks without deploying.

With the default Pages domain for this repository, the expected address is
<https://hqiu-nju.github.io/ff_unifier/> after the first successful deployment.
This address is a deployment target, not a claim that the site is already live.
All asset and worker paths are relative, so the repository subpath is supported.
Any static HTTPS host can serve the contents of `dist/` instead.

See [GitHub's custom workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
for the one-time Pages setup.

### Australian Amex points conversion

The **Convert Amex points** panel compares a Membership Rewards balance across
ten airline partners. Select **Ascent** or **Ascent Premium** as shown in your
Amex account. Qantas is available only for an eligible Ascent Premium account.
The converter runs locally and works without a search gateway or provider keys.
It is included in the static/integrated site; the original Flask interface
continues to provide flight earnings only.

Reference rates were reviewed on **29 October 2026**: Qantas and Velocity use
2 MR points per partner point, KrisFlyer, Cathay, British Airways, Qatar,
Malaysia Airlines and Virgin Atlantic use 3:1, Emirates uses 4:1, and Air New
Zealand uses 200:1 for Airpoints Dollars. Each result is an alternative using the
same balance, not a combined allocation. Award currencies remain separate from
flight earnings and status credits.

Sources and limits:

- [Amex Australia's transfer catalogue](https://www.americanexpress.com/en-au/rewards/membership-rewards/travel/all/1000)
  says displayed Ascent rates may differ by card. Its public page did not expose
  a usable rate table during this review; signed-in card-specific rates were
  **not** verified.
- [Amex consumer terms, effective 15 December 2025](https://www.americanexpress.com/content/dam/amex/en-au/company/terms-and-conditions/AME12313_MRTCsDoc-Consumer_FA.pdf),
  clauses 1.6, 5.2–5.4 and 10.5, require checking redemption options, minimums and
  conversion rates in the account or at redemption time.
- [Velocity's Amex partner page](https://estore.velocityfrequentflyer.com/partners-offers/credit-cards-banking-insurance/american-express)
  confirms the Ascent/Ascent Premium 2:1 rate and 2,000 MR minimum. It lists a
  different Business Ascent rate, so Business Ascent is deliberately unsupported.
- [Point Hacks' Australian Membership Rewards reference table](https://www.pointhacks.com.au/american-express/)
  supplies the remaining reference rates, published minimums and Qantas tier
  restriction. This secondary source is labelled in the interface. British
  Airways' minimum is unverified and shown as needing confirmation.

The converter floors arithmetic to whole partner points and shows leftover MR
points. **It does not model partner transfer increments**: actual transfers may
leave more points unused. Balances below a published minimum do not show a
transferable estimate. No promotional bonuses, cash valuation, onward transfers
or availability are included. Gateway, Business Ascent, other countries and
direct-earn Qantas/Velocity cards are outside this converter's supported scope.
Confirm your account's current rules before transferring.

Edit `web/amex.js` for the reference data and pure conversion logic, and
`web/amex-ui.js` for presentation. Keep source provenance and the review date in
sync with this documentation, and run `npm test` after changes.

### Data and correctness

Edit airport and programme definitions in `airports.py`, `programs.py`, and
`calculator.py`, then rebuild. `ui_options.py` supplies shared form choices for
both interfaces. The build generates `dist/data.js`; do not edit it by hand.

The browser engine preserves the Python engine's existing tables, fallback
behaviour, distance bands, minimum miles, and rounding. Matching the Python
engine does **not** verify the accuracy or freshness of the airline rules.
Some existing partner fallbacks, fare categories, revenue-based currencies,
and non-earning status rules are simplified and need a separate rules audit
before relying on results to choose a booking. The interface labels all
results as indicative estimates.

## Live flight and award search (no visitor installation)

The public page needs a hosted gateway because provider credentials must stay
on the host. Visitors use the browser only. This means **earnings calculations,
sorting, and filtering run locally**, while inventory requests go through the
host to the provider; inventory retrieval is not entirely browser-only.

Two adapters are included:

- **Duffel**: one-way cash fare search for 1–9 adults. Test-mode responses are
  explicitly labelled as test data. Live mode requires an activated Duffel account.
- **Seats.aero Live Search**: one route/date/programme per request. Requires
  provider approval for this public product and live API access; a personal Pro
  API key alone does not grant Live Search access. No automatic cached fallback
  is requested. A provider response marked cached is displayed as cached.

No provider account, credentials, or real inventory validation is included in
this checkout. Provider tests use clearly marked offline contract fixtures.
Unknown seat counts and taxes are shown as unreported. The app never creates
orders, books tickets, or accepts payment. Search results do not cover all airlines.

Provider references: [Duffel search](https://duffel.com/docs/api/offer-requests/create-offer-request),
[Duffel frontend restriction](https://help.duffel.com/hc/en-gb/articles/4504698704530-Can-I-use-the-Duffel-API-directly-from-my-frontend-application-or-mobile-app),
[Seats.aero Live Search](https://developers.seats.aero/reference/live-search),
[Seats.aero access rules](https://docs.seats.aero/article/68-seatsaero-pro-api-access-limits-and-usage).

### Run the integrated site locally (maintainer)

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-gateway.txt
python3 scripts/build_web.py
.venv/bin/python gateway.py
```

Open <http://127.0.0.1:5001>. Without provider credentials, the search panel explains
that search is unavailable and the local earnings calculator continues to work.
Set secrets using your hosting platform's secret settings or environment, not
tracked files or browser form fields:

| Environment setting | Purpose |
| --- | --- |
| `DUFFEL_ACCESS_TOKEN` | Operator's Duffel access token; test and live modes are distinguished in results. |
| `SEATS_AERO_API_KEY` | Operator's approved Seats.aero key. |
| `FF_SEATS_LIVE_APPROVED=true` | Operator opt-in after obtaining provider approval for this public product and live endpoint. Defaults off. |
| `FF_ALLOWED_ORIGINS` | Comma-separated exact website origins, e.g. `https://hqiu-nju.github.io`. No paths or wildcards. |
| `FF_DAILY_SEARCH_LIMIT` | Maximum provider calls per process per UTC day; default 250. |

Only configure the provider(s) you plan to offer. Keys are read by the gateway,
never included in `dist/`, capabilities responses, or search results. Do not
paste secrets into chat. The `FF_SEATS_LIVE_APPROVED` setting is an operator
assertion, not a grant of access from Seats.aero.

### Hosting

The simplest setup serves the built site and gateway from one HTTPS origin.
Use a Python host with TLS and a production WSGI server, for example:

```bash
python3 scripts/build_web.py
gunicorn --workers 1 --threads 4 --timeout 45 --bind 0.0.0.0:8000 gateway:app
```

Set `FF_ALLOWED_ORIGINS` to the public site's exact HTTPS origin. The built-in
Flask development server is only for local development.

For **GitHub Pages plus a separately hosted gateway**, set the repository's
Actions variable `FF_GATEWAY_URL` to the gateway's HTTPS origin, then run the
Static website workflow. The build adds that origin to the browser connection
policy. The gateway must allow the **page's** origin in `FF_ALLOWED_ORIGINS`.
For this repository's default Pages URL the origin is `https://hqiu-nju.github.io`,
without `/ff_unifier/`. To build manually:

```bash
python3 scripts/build_web.py --gateway-url https://search.example.com
```

The gateway exposes only `GET /api/capabilities` and `POST /api/search`, with
fixed provider URLs. It accepts no booking or arbitrary proxy requests, sends
no provider credentials to redirects, and returns sanitized provider errors.
Searches are limited to two concurrent calls, 20 per minute across the site,
5 per minute per direct client IP, and the configured daily budget.

These are **in-memory, single-process limits** and reset on restart. Keep one
worker as shown; use shared edge rate limits and provider spending limits before
scaling or adding replicas. Origin checks alone do not authenticate non-browser
clients. Behind an unconfigured reverse proxy, clients may share the same
conservative IP limit; forwarded IP headers are deliberately not trusted.

## Original Flask interface

```bash
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Running Tests

```bash
pytest tests/
npm test
```

The Python tests need `requirements.txt`. The browser tests need Node.js 22+
and Python, with no additional packages. They compare more than 230,000 cases
against the Python engine, covering all supported airlines, programmes, booking
classes, distance-band boundaries, and sample routes. They also verify input
validation and the built worker's message handling.

## Project Structure

```
ff_unifier/
├── app.py            # Original Flask calculator
├── gateway.py        # Public site + restricted provider gateway
├── flight_search.py  # Duffel / Seats.aero adapters
├── calculator.py     # Core calculation engine (distance + earning rates)
├── airports.py       # Airport data (IATA codes, coordinates)
├── programs.py       # Loyalty programme definitions and earning rate tables
├── ui_options.py     # Shared flight form options
├── web/              # Search UI, local result filtering, calculator and worker
│   ├── amex.js       # Australian Amex reference data and conversion logic
│   └── amex-ui.js    # Local Amex conversion form and results
├── scripts/
│   └── build_web.py  # Export Python data and build dist/ without dependencies
├── .github/workflows/pages.yml  # Test and deploy the static website
├── templates/
│   └── index.html    # Bootstrap 5 web UI
├── tests/
│   ├── test_calculator.py
│   └── web/          # Browser engine parity, validation and worker tests
├── requirements-gateway.txt  # Production gateway dependencies
└── requirements.txt
```

> **Disclaimer:** Earning rates shown are indicative estimates based on publicly available information.
> Always verify with the official loyalty programme before booking.
