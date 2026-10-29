"""Host the static interface and a bounded, read-only flight-search gateway."""

from collections import Counter
from datetime import datetime, timezone
import os
import re
from pathlib import Path
import threading
import time
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from flight_search import FlightSearchService, SearchError, validate_search

ROOT = Path(__file__).resolve().parent


def allowed_origins(raw):
    origins = set()
    for value in raw.split(","):
        value = value.strip().rstrip("/")
        parts = urlsplit(value)
        local = parts.hostname in {"localhost", "127.0.0.1"}
        if not re.fullmatch(r"https?://[A-Za-z0-9.-]+(?::\d{1,5})?", value) or (parts.scheme != "https" and not (local and parts.scheme == "http")) or not parts.netloc or parts.path or parts.query or parts.fragment or parts.username or parts.password:
            raise ValueError("FF_ALLOWED_ORIGINS must contain exact HTTPS origins (HTTP is allowed for loopback development).")
        origins.add(value)
    return origins


class SearchBudget:
    """Atomic single-process budgets; deploy with one process or shared limits."""
    def __init__(self, daily=250, per_minute=20, per_ip=5):
        self.daily_limit, self.minute_limit, self.ip_limit = daily, per_minute, per_ip
        self.lock = threading.Lock()
        self.day = None
        self.minute = None
        self.daily_count = 0
        self.ips = Counter()

    def consume(self, address):
        with self.lock:
            day = datetime.now(timezone.utc).date()
            minute = int(time.monotonic() // 60)
            if day != self.day:
                self.day, self.daily_count = day, 0
            if minute != self.minute:
                self.minute, self.ips = minute, Counter()
            if self.daily_count >= self.daily_limit or sum(self.ips.values()) >= self.minute_limit or self.ips[address] >= self.ip_limit:
                raise SearchError("The site's search limit has been reached. Please try again later.", 429, "site_limit")
            self.daily_count += 1
            self.ips[address] += 1


def create_app(service=None, origins=None, budget=None):
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 4096
    service = service or FlightSearchService()
    origins = origins if origins is not None else allowed_origins(os.getenv("FF_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://127.0.0.1:5001,http://localhost:5001"))
    budget = budget or SearchBudget(daily=int(os.getenv("FF_DAILY_SEARCH_LIMIT", "250")))
    slots = threading.BoundedSemaphore(2)

    @app.before_request
    def protect_api():
        if not request.path.startswith("/api/"):
            return None
        origin = request.headers.get("Origin")
        if origin is not None and origin not in origins:
            raise SearchError("This site is not allowed to use this search connection.", 403, "origin_denied")
        if request.method == "OPTIONS":
            return "", 204
        if request.method == "POST" and (origin not in origins or not request.is_json):
            raise SearchError("Please search from the FF Unifier web interface.", 403, "origin_denied")

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Vary"] = "Origin"
            if request.headers.get("Origin") in origins:
                response.headers["Access-Control-Allow-Origin"] = request.headers["Origin"]
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            if response.status_code == 429:
                response.headers["Retry-After"] = "60"
        return response

    @app.errorhandler(SearchError)
    def search_error(error):
        return jsonify(error=str(error), code=error.code), error.status

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error="The request could not be accepted.", code="invalid_request"), error.code

    @app.get("/api/capabilities")
    def capabilities():
        return jsonify(service.capabilities())

    @app.post("/api/search")
    def search():
        query = validate_search(request.get_json())
        if not service.capabilities()[query["kind"]]:
            raise SearchError("This search option is not available on this site yet.", 503, "not_configured")
        if not slots.acquire(blocking=False):
            raise SearchError("Search is busy. Please try again shortly.", 429, "site_busy")
        try:
            # Ignore untrusted forwarded-IP headers. A shared proxy may cause
            # conservative throttling; configure trusted edge limits to scale.
            budget.consume(request.remote_addr)
            return jsonify(service.search(query))
        finally:
            slots.release()

    @app.get("/")
    def index():
        if not (ROOT / "dist" / "index.html").is_file():
            return "Build the website first: python3 scripts/build_web.py", 503
        return send_from_directory(ROOT / "dist", "index.html")

    @app.get("/<path:asset>")
    def static_asset(asset):
        if asset.startswith("api/"):
            return jsonify(error="Unknown endpoint."), 404
        return send_from_directory(ROOT / "dist", asset)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
