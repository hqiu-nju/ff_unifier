/** Browser equivalent of calculator.py. Tables come from the Python build. */
export function createCalculator(data) {
  const has = (object, key) => Object.hasOwn(object, key);
  const normalize = (value) => typeof value === "string" ? value.trim().toUpperCase() : "";
  const bandFor = (bookingClass) => data.class_bands[bookingClass] ?? "Q";
  const allianceKey = (airline) => ["oneworld", "star", "skyteam"].includes(data.alliances[airline])
    ? `default_${data.alliances[airline]}` : undefined;

  // Python rounds ties to the nearest even integer; Math.round uses a different rule.
  function roundEven(value, digits = 0) {
    const scale = 10 ** digits;
    const scaled = value * scale;
    const floor = Math.floor(scaled);
    const fraction = scaled - floor;
    return (fraction === 0.5 ? floor + (floor % 2) : Math.round(scaled)) / scale;
  }

  function getDistance(origin, destination) {
    const a = data.airports[normalize(origin)];
    const b = data.airports[normalize(destination)];
    if (!a || !b) return null;
    const rad = (n) => n * Math.PI / 180;
    const h = Math.sin(rad(b[2] - a[2]) / 2) ** 2
      + Math.cos(rad(a[2])) * Math.cos(rad(b[2])) * Math.sin(rad(b[3] - a[3]) / 2) ** 2;
    return 3958.8 * 2 * Math.asin(Math.sqrt(Math.min(1, h)));
  }

  function getEarnRates(programId, airline, bookingClass) {
    if (!has(data.programs, programId)) return [0, 0];
    const program = data.programs[programId];
    const band = bandFor(normalize(bookingClass));
    const code = normalize(airline);
    return program.airlines?.[code]?.[band]
      ?? program[allianceKey(code)]?.[band]
      ?? program.default_partner?.[band]
      ?? [0, 0];
  }

  function calculateStatus(distance, airline, bookingClass, programId, rate, origin, destination) {
    const program = data.programs[programId];
    const band = bandFor(bookingClass);
    if (programId === "KRISFLYER" && airline === "SQ") {
      const pct = program.status_pct_by_class?.SQ?.[bookingClass];
      if (pct !== undefined) return roundEven(distance * pct / 100);
    }
    if (programId === "CATHAY" && airline === "CX") {
      const values = data.cathay_status_by_class[bookingClass] ?? data.cathay_status_by_class[band];
      const other = origin === "HKG" ? destination : origin;
      const shortType2 = (origin === "HKG" || destination === "HKG")
        && data.cathay_short_type2_airports.includes(other);
      const zone = distance <= 750 ? "ultra_short"
        : distance <= 2750 ? (shortType2 ? "short_type2" : "short_type1")
        : distance <= 5000 ? "medium" : distance <= 7500 ? "long" : "ultra_long";
      return values[zone];
    }
    if (programId === "VELOCITY" && airline === "VA") {
      const bucket = data.velocity_business_classes.includes(bookingClass) ? "business"
        : data.velocity_flex_classes.includes(bookingClass) ? "flex"
        : data.velocity_choice_classes.includes(bookingClass) ? "choice" : "lite";
      return data.velocity_status_bands.find(([limit]) => limit === null || distance <= limit)[1][bucket];
    }
    const tables = program.status_bands;
    // An explicit null prevents Qantas/Jetstar using the alliance fallback.
    const table = tables && (has(tables, airline)
      ? tables[airline] : tables[allianceKey(airline)]);
    if (table) {
      const entry = table.find(([limit]) => limit === null || distance <= limit);
      return entry?.[1]?.[band] ?? 0;
    }
    return roundEven(distance / 1000 * rate);
  }

  function calculatePoints(distance, airline, bookingClass, programId, origin, destination) {
    const code = normalize(airline);
    const cls = normalize(bookingClass);
    const program = data.programs[programId];
    const [pct, rate] = getEarnRates(programId, code, cls);
    return {
      program_id: programId,
      program_name: program.name,
      points_unit: program.points_unit,
      status_unit: program.status_unit,
      award_miles: pct === 0 ? 0 : Math.max(roundEven(distance * pct / 100), program.min_miles ?? 0),
      status_points: calculateStatus(distance, code, cls, programId, rate, normalize(origin), normalize(destination)),
      earn_pct: pct,
      earns: pct > 0,
    };
  }

  function calculateFlight(input = {}) {
    const origin = normalize(input.origin);
    const destination = normalize(input.destination);
    const airline = normalize(input.airline);
    const bookingClass = normalize(input.booking_class);
    if (!has(data.airports, origin)) return { error: `Unknown origin airport: ${origin}` };
    if (!has(data.airports, destination)) return { error: `Unknown destination airport: ${destination}` };
    if (origin === destination) return { error: "Origin and destination must be different airports." };
    if (!data.airlines.some(([code]) => code === airline)) return { error: "Please select a supported operating airline." };
    if (!has(data.class_bands, bookingClass)) return { error: "Please select a valid booking class." };
    const ids = input.program_ids;
    if (!Array.isArray(ids) || ids.length === 0) return { error: "Please select at least one loyalty programme." };
    if (ids.length > 3) return { error: "Please select no more than 3 loyalty programmes." };
    if (ids.some((id) => typeof id !== "string" || !has(data.programs, id))) {
      return { error: "Unknown loyalty programme selected." };
    }
    if (new Set(ids).size !== ids.length) return { error: "Please select each programme only once." };
    const distance = getDistance(origin, destination);
    return {
      origin, destination, airline, booking_class: bookingClass,
      origin_name: data.airports[origin][0],
      destination_name: data.airports[destination][0],
      distance_miles: roundEven(distance, 1),
      results: ids.map((id) => calculatePoints(distance, airline, bookingClass, id, origin, destination)),
    };
  }

  return { getDistance, getEarnRates, calculatePoints, calculateFlight };
}
