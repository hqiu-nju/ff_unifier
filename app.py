"""Flask web application for FF Unifier."""

from flask import Flask, render_template, request

from airports import AIRPORTS
from calculator import calculate_flight
from programs import PROGRAM_LIST, PROGRAMS

app = Flask(__name__)

# Sorted airport list for the UI dropdown
AIRPORT_OPTIONS = sorted(
    [(code, f"{code} – {data[0]} ({data[1]})") for code, data in AIRPORTS.items()],
    key=lambda x: x[0],
)

# Common airline codes for the UI
AIRLINE_OPTIONS = [
    ("QF", "QF – Qantas"),
    ("AA", "AA – American Airlines"),
    ("BA", "BA – British Airways"),
    ("CX", "CX – Cathay Pacific"),
    ("JL", "JL – Japan Airlines"),
    ("QR", "QR – Qatar Airways"),
    ("IB", "IB – Iberia"),
    ("MH", "MH – Malaysia Airlines"),
    ("AY", "AY – Finnair"),
    ("RJ", "RJ – Royal Jordanian"),
    ("SQ", "SQ – Singapore Airlines"),
    ("UA", "UA – United Airlines"),
    ("LH", "LH – Lufthansa"),
    ("NH", "NH – ANA"),
    ("AC", "AC – Air Canada"),
    ("NZ", "NZ – Air New Zealand"),
    ("OS", "OS – Austrian Airlines"),
    ("SK", "SK – SAS"),
    ("TG", "TG – Thai Airways"),
    ("TK", "TK – Turkish Airlines"),
    ("ET", "ET – Ethiopian Airlines"),
    ("OZ", "OZ – Asiana Airlines"),
    ("CA", "CA – Air China"),
    ("AI", "AI – Air India"),
    ("SA", "SA – South African Airways"),
    ("AF", "AF – Air France"),
    ("KL", "KL – KLM"),
    ("DL", "DL – Delta Air Lines"),
    ("KE", "KE – Korean Air"),
    ("AM", "AM – Aeromexico"),
    ("AZ", "AZ – ITA Airways"),
    ("EK", "EK – Emirates"),
    ("EY", "EY – Etihad Airways"),
    ("VS", "VS – Virgin Atlantic"),
    ("JQ", "JQ – Jetstar"),
]

# Booking class options grouped by cabin
BOOKING_CLASS_OPTIONS = [
    ("First", [("F", "F – First (full fare)"), ("A", "A – First (discounted)")]),
    ("Business", [
        ("J", "J – Business (full fare)"),
        ("C", "C – Business (flex)"),
        ("D", "D – Business (flex)"),
        ("I", "I – Business (discounted)"),
        ("Z", "Z – Business (discounted)"),
    ]),
    ("Premium Economy", [
        ("W", "W – Premium Economy (full fare)"),
        ("P", "P – Premium Economy"),
        ("R", "R – Premium Economy (discounted)"),
        ("E", "E – Premium Economy (discounted)"),
    ]),
    ("Economy", [
        ("Y", "Y – Economy (full fare)"),
        ("B", "B – Economy"),
        ("H", "H – Economy"),
        ("K", "K – Economy (discount)"),
        ("M", "M – Economy (discount)"),
        ("L", "L – Economy (deep discount)"),
        ("V", "V – Economy (deep discount)"),
        ("S", "S – Economy (deep discount)"),
        ("N", "N – Economy (promo)"),
        ("Q", "Q – Economy (promo)"),
        ("T", "T – Economy (promo)"),
        ("G", "G – Economy (promo)"),
        ("O", "O – Award / non-earning"),
    ]),
]


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        airports=AIRPORT_OPTIONS,
        airlines=AIRLINE_OPTIONS,
        booking_classes=BOOKING_CLASS_OPTIONS,
        programs=PROGRAM_LIST,
        result=None,
        form_data={},
        error=None,
    )


@app.route("/calculate", methods=["POST"])
def calculate():
    form = request.form
    origin = form.get("origin", "").strip().upper()
    destination = form.get("destination", "").strip().upper()
    airline = form.get("airline", "").strip().upper()
    booking_class = form.get("booking_class", "").strip().upper()
    selected_programs = form.getlist("programs")

    form_data = {
        "origin": origin,
        "destination": destination,
        "airline": airline,
        "booking_class": booking_class,
        "programs": selected_programs,
    }

    # Basic input validation
    if not origin or not destination or not airline or not booking_class:
        return render_template(
            "index.html",
            airports=AIRPORT_OPTIONS,
            airlines=AIRLINE_OPTIONS,
            booking_classes=BOOKING_CLASS_OPTIONS,
            programs=PROGRAM_LIST,
            result=None,
            form_data=form_data,
            error="Please fill in all flight details.",
        )

    if len(selected_programs) == 0:
        return render_template(
            "index.html",
            airports=AIRPORT_OPTIONS,
            airlines=AIRLINE_OPTIONS,
            booking_classes=BOOKING_CLASS_OPTIONS,
            programs=PROGRAM_LIST,
            result=None,
            form_data=form_data,
            error="Please select between 1 and 3 loyalty programmes.",
        )

    if len(selected_programs) > 3:
        return render_template(
            "index.html",
            airports=AIRPORT_OPTIONS,
            airlines=AIRLINE_OPTIONS,
            booking_classes=BOOKING_CLASS_OPTIONS,
            programs=PROGRAM_LIST,
            result=None,
            form_data=form_data,
            error="Please select no more than 3 loyalty programs.",
        )

    result = calculate_flight(origin, destination, airline, booking_class, selected_programs)

    error = result.get("error")
    if error:
        return render_template(
            "index.html",
            airports=AIRPORT_OPTIONS,
            airlines=AIRLINE_OPTIONS,
            booking_classes=BOOKING_CLASS_OPTIONS,
            programs=PROGRAM_LIST,
            result=None,
            form_data=form_data,
            error=error,
        )

    return render_template(
        "index.html",
        airports=AIRPORT_OPTIONS,
        airlines=AIRLINE_OPTIONS,
        booking_classes=BOOKING_CLASS_OPTIONS,
        programs=PROGRAM_LIST,
        result=result,
        form_data=form_data,
        error=None,
    )


if __name__ == "__main__":
    import os
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
