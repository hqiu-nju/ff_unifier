# FF Unifier

Calculate and compare **frequent flyer points** and **status credits** across up to **3 loyalty programmes** for any flight.

## Features

- Enter a flight route (origin → destination), operating airline and booking class
- Instantly see award miles/points and status credits for up to 3 programmes side by side
- Supports 100+ airports worldwide and 35+ airlines
- Loyalty programmes supported:
  - **Qantas Frequent Flyer** (Status Credits + Qantas Points)
  - **Cathay Membership** (Status Points + Asia Miles)
  - **Singapore Airlines KrisFlyer** (Elite Miles + KrisFlyer Miles)
  - **Virgin Australia Velocity** (Status Credits + Velocity Points)
  - **United MileagePlus** (PQP + Award Miles)
  - **American Airlines AAdvantage** (Loyalty Points + AAdvantage Miles)
  - **British Airways Executive Club** (Tier Points + Avios)
  - **Air France / KLM Flying Blue** (XP + Flying Blue Miles)

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Running Tests

```bash
pytest tests/
```

## Project Structure

```
ff_unifier/
├── app.py            # Flask web application
├── calculator.py     # Core calculation engine (distance + earning rates)
├── airports.py       # Airport data (IATA codes, coordinates)
├── programs.py       # Loyalty programme definitions and earning rate tables
├── templates/
│   └── index.html    # Bootstrap 5 web UI
├── tests/
│   └── test_calculator.py
└── requirements.txt
```

> **Disclaimer:** Earning rates shown are indicative estimates based on publicly available information.
> Always verify with the official loyalty programme before booking.
