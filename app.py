"""Flask web application for FF Unifier."""

from flask import Flask, render_template, request

from airports import AIRPORTS
from calculator import calculate_flight
from programs import PROGRAM_LIST, PROGRAMS
from ui_options import AIRLINE_OPTIONS, BOOKING_CLASS_OPTIONS

app = Flask(__name__)

# Sorted airport list for the UI dropdown
AIRPORT_OPTIONS = sorted(
    [(code, f"{code} – {data[0]} ({data[1]})") for code, data in AIRPORTS.items()],
    key=lambda x: x[0],
)

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
