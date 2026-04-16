"""Flight Stopover Optimization Engine — Data Generation & Loading.

Generates synthetic flight data and loads it into DuckDB.
Uses the airportsdata package for accurate airport metadata.

Usage:
    python load_data.py
"""

import math
import random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import airportsdata
import duckdb
import pandas as pd

DB_PATH = "flights.duckdb"
USD_ILS_RATE = 3.65

# ---------------------------------------------------------------------------
# Airport IATA codes — all verified to exist in airportsdata
# ---------------------------------------------------------------------------
IATA_CODES = [
    # Israel (1)
    "TLV",
    # Turkey (4)
    "IST", "SAW", "AYT", "ADB",
    # Greece (5)
    "ATH", "SKG", "HER", "RHO", "CFU",
    # Cyprus (2)
    "LCA", "PFO",
    # Eastern Europe (18)
    "BUD", "PRG", "WAW", "KRK", "OTP", "SOF", "BEG", "ZAG",
    "LJU", "BTS", "VNO", "RIX", "TLL", "RMO", "CLJ", "GDN",
    "WRO", "POZ",
    # Western Europe (29)
    "LHR", "LGW", "STN", "EDI", "CDG", "AMS", "FRA", "MUC",
    "BCN", "MAD", "PMI", "FCO", "MXP", "LIS", "OPO", "DUB",
    "BRU", "ZRH", "VIE", "CPH", "OSL", "ARN", "HEL", "GVA",
    "NCE", "MRS", "BER", "HAM", "DUS",
    # Middle East (9)
    "AMM", "CAI", "SSH", "RUH", "DXB", "DOH", "BAH", "KWI", "TBS",
    # Caucasus (1)
    "EVN",
    # Long-haul (16)
    "JFK", "EWR", "BOS", "LAX", "ORD", "YYZ",
    "BKK", "SIN", "HKG", "NRT", "DEL", "BOM",
    "JNB", "GRU", "BOG", "MEX",
]

COUNTRY_NAMES = {
    "IL": "Israel", "TR": "Turkey", "GR": "Greece", "CY": "Cyprus",
    "HU": "Hungary", "CZ": "Czech Republic", "PL": "Poland", "RO": "Romania",
    "BG": "Bulgaria", "RS": "Serbia", "HR": "Croatia", "SI": "Slovenia",
    "SK": "Slovakia", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
    "MD": "Moldova",
    "GB": "United Kingdom", "FR": "France", "NL": "Netherlands", "DE": "Germany",
    "ES": "Spain", "IT": "Italy", "PT": "Portugal", "IE": "Ireland",
    "BE": "Belgium", "CH": "Switzerland", "AT": "Austria", "DK": "Denmark",
    "NO": "Norway", "SE": "Sweden", "FI": "Finland",
    "JO": "Jordan", "EG": "Egypt", "SA": "Saudi Arabia", "AE": "United Arab Emirates",
    "QA": "Qatar", "BH": "Bahrain", "KW": "Kuwait", "GE": "Georgia", "AM": "Armenia",
    "US": "United States", "CA": "Canada", "TH": "Thailand", "SG": "Singapore",
    "HK": "Hong Kong", "JP": "Japan", "IN": "India", "ZA": "South Africa",
    "BR": "Brazil", "CO": "Colombia", "MX": "Mexico",
}

REGION_MAP = {
    "IL": "Israel", "TR": "Turkey",
    "GR": "Eastern Europe", "CY": "Eastern Europe",
    "HU": "Eastern Europe", "CZ": "Eastern Europe", "PL": "Eastern Europe",
    "RO": "Eastern Europe", "BG": "Eastern Europe", "RS": "Eastern Europe",
    "HR": "Eastern Europe", "SI": "Eastern Europe", "SK": "Eastern Europe",
    "LT": "Eastern Europe", "LV": "Eastern Europe", "EE": "Eastern Europe",
    "MD": "Eastern Europe",
    "GB": "Western Europe", "FR": "Western Europe", "NL": "Western Europe",
    "DE": "Western Europe", "ES": "Western Europe", "IT": "Western Europe",
    "PT": "Western Europe", "IE": "Western Europe", "BE": "Western Europe",
    "CH": "Western Europe", "AT": "Western Europe", "DK": "Western Europe",
    "NO": "Western Europe", "SE": "Western Europe", "FI": "Western Europe",
    "JO": "Middle East", "EG": "Middle East", "SA": "Middle East",
    "AE": "Middle East", "QA": "Middle East", "BH": "Middle East",
    "KW": "Middle East", "GE": "Middle East", "AM": "Middle East",
    "US": "North America", "CA": "North America",
    "TH": "Asia", "SG": "Asia", "HK": "Asia", "JP": "Asia", "IN": "Asia",
    "ZA": "Africa",
    "BR": "South America", "CO": "South America", "MX": "South America",
}

AIRLINES = [
    {"airline_code": "LY", "airline_name": "El Al", "country": "Israel", "is_lowcost": False},
    {"airline_code": "W6", "airline_name": "Wizz Air", "country": "Hungary", "is_lowcost": True},
    {"airline_code": "FR", "airline_name": "Ryanair", "country": "Ireland", "is_lowcost": True},
    {"airline_code": "U2", "airline_name": "easyJet", "country": "United Kingdom", "is_lowcost": True},
    {"airline_code": "TK", "airline_name": "Turkish Airlines", "country": "Turkey", "is_lowcost": False},
    {"airline_code": "BA", "airline_name": "British Airways", "country": "United Kingdom", "is_lowcost": False},
    {"airline_code": "AF", "airline_name": "Air France", "country": "France", "is_lowcost": False},
    {"airline_code": "LH", "airline_name": "Lufthansa", "country": "Germany", "is_lowcost": False},
    {"airline_code": "KL", "airline_name": "KLM", "country": "Netherlands", "is_lowcost": False},
    {"airline_code": "IB", "airline_name": "Iberia", "country": "Spain", "is_lowcost": False},
    {"airline_code": "TP", "airline_name": "TAP Portugal", "country": "Portugal", "is_lowcost": False},
    {"airline_code": "AZ", "airline_name": "ITA Airways", "country": "Italy", "is_lowcost": False},
    {"airline_code": "OS", "airline_name": "Austrian", "country": "Austria", "is_lowcost": False},
    {"airline_code": "SK", "airline_name": "SAS", "country": "Denmark", "is_lowcost": False},
    {"airline_code": "RO", "airline_name": "TAROM", "country": "Romania", "is_lowcost": False},
]

AIRLINE_REGIONS = {
    "LY": ["Israel", "Turkey", "Eastern Europe", "Western Europe", "Middle East", "North America"],
    "W6": ["Israel", "Eastern Europe", "Western Europe", "Turkey"],
    "FR": ["Eastern Europe", "Western Europe"],
    "U2": ["Eastern Europe", "Western Europe", "Israel"],
    "TK": ["Israel", "Turkey", "Eastern Europe", "Western Europe", "Middle East", "Asia", "Africa", "North America"],
    "BA": ["Western Europe", "Middle East", "North America", "Asia", "Africa", "Israel"],
    "AF": ["Western Europe", "Eastern Europe", "Middle East", "North America", "Africa", "Israel"],
    "LH": ["Western Europe", "Eastern Europe", "Middle East", "North America", "Asia", "Israel"],
    "KL": ["Western Europe", "Eastern Europe", "Middle East", "North America", "Asia", "Israel"],
    "IB": ["Western Europe", "South America", "Middle East"],
    "TP": ["Western Europe", "South America", "Africa"],
    "AZ": ["Western Europe", "Eastern Europe", "Middle East", "Israel"],
    "OS": ["Western Europe", "Eastern Europe", "Middle East", "Israel"],
    "SK": ["Western Europe", "Eastern Europe"],
    "RO": ["Eastern Europe", "Western Europe", "Middle East", "Israel"],
}

REGION_PRICE_TIERS = {
    ("Israel", "Eastern Europe"): (55, 160),
    ("Israel", "Turkey"): (60, 150),
    ("Israel", "Western Europe"): (170, 480),
    ("Israel", "Middle East"): (80, 200),
    ("Israel", "North America"): (450, 900),
    ("Israel", "Asia"): (400, 850),
    ("Israel", "Africa"): (350, 700),
    ("Israel", "South America"): (500, 950),
    ("Turkey", "Eastern Europe"): (40, 130),
    ("Turkey", "Western Europe"): (80, 250),
    ("Turkey", "Middle East"): (70, 180),
    ("Turkey", "Israel"): (60, 150),
    ("Turkey", "North America"): (400, 850),
    ("Turkey", "Asia"): (350, 750),
    ("Eastern Europe", "Western Europe"): (25, 110),
    ("Eastern Europe", "Eastern Europe"): (20, 80),
    ("Eastern Europe", "Israel"): (55, 160),
    ("Eastern Europe", "Turkey"): (40, 130),
    ("Eastern Europe", "Middle East"): (100, 280),
    ("Western Europe", "Western Europe"): (30, 150),
    ("Western Europe", "Eastern Europe"): (25, 110),
    ("Western Europe", "Israel"): (170, 480),
    ("Western Europe", "Turkey"): (80, 250),
    ("Western Europe", "Middle East"): (150, 400),
    ("Western Europe", "North America"): (250, 600),
    ("Western Europe", "Asia"): (350, 800),
    ("Western Europe", "South America"): (400, 850),
    ("Western Europe", "Africa"): (300, 650),
    ("Middle East", "Israel"): (80, 200),
    ("Middle East", "Western Europe"): (150, 400),
    ("Middle East", "Eastern Europe"): (100, 280),
    ("Middle East", "Asia"): (200, 500),
    ("Middle East", "Africa"): (200, 450),
    ("Middle East", "Middle East"): (50, 150),
    ("North America", "Western Europe"): (250, 600),
    ("North America", "Israel"): (450, 900),
    ("Asia", "Western Europe"): (350, 800),
    ("Asia", "Israel"): (400, 850),
}

NARROWBODIES = ["B737", "B738", "A320", "A321", "A319"]
WIDEBODIES = ["B787", "A330", "B777", "A350"]
VALID_TABLES = {"airports", "airlines", "routes", "flight_prices", "currency_rates"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _flight_duration_min(dist_km):
    """Estimate flight duration: ~800 km/h cruise + 30 min overhead."""
    return int(dist_km / 800 * 60 + 30)


def generate_price(base_price, flight_date, airline_is_lowcost, departure_hour):
    """Apply realistic pricing modifiers to a base price.

    Modifiers: weekend ×1.2, Tue/Wed ×0.85, low-cost ×0.6,
    red-eye (0-5h) ×0.8, Gaussian noise σ=0.08. Floor $15.
    """
    price = base_price
    dow = flight_date.weekday()
    if dow in (5, 6):
        price *= 1.20
    elif dow in (1, 2):
        price *= 0.85
    if airline_is_lowcost:
        price *= 0.60
    if 0 <= departure_hour < 6:
        price *= 0.80
    price *= 1 + random.gauss(0, 0.08)
    return max(15.0, round(price, 2))


# ---------------------------------------------------------------------------
# Route pattern builder
# ---------------------------------------------------------------------------

def _build_route_patterns():
    """Build realistic route connectivity based on hub tiers.

    Returns a list of (origin, dest) IATA tuples. Both directions included.
    Every airport is reachable from TLV in ≤2 hops.
    """
    ap_data = airportsdata.load("IATA")

    # Group airports by region
    region_airports = defaultdict(list)
    airport_region = {}
    for iata in IATA_CODES:
        cc = ap_data[iata]["country"]
        region = REGION_MAP.get(cc, "Other")
        region_airports[region].append(iata)
        airport_region[iata] = region

    mega_hubs = {"TLV", "IST"}
    major_hubs = {"LHR", "CDG", "FRA", "AMS", "MUC", "DXB", "DOH"}
    medium_hubs = {"BCN", "MAD", "FCO", "MXP", "VIE", "ZRH", "ATH",
                   "BUD", "PRG", "WAW", "CPH", "OSL", "ARN"}
    all_hubs = mega_hubs | major_hubs | medium_hubs

    pairs = set()

    def add_pair(a, b):
        if a != b:
            pairs.add((a, b))
            pairs.add((b, a))

    # TLV mega-hub: connect to all EE, Turkey, most WE, all ME, some long-haul
    for region in ["Eastern Europe", "Turkey", "Western Europe", "Middle East"]:
        for dest in region_airports[region]:
            add_pair("TLV", dest)
    long_haul = [c for c in IATA_CODES
                 if airport_region[c] in ("North America", "Asia", "Africa", "South America")]
    for dest in long_haul[:10]:
        add_pair("TLV", dest)

    # IST mega-hub: all Turkey, most EE, major WE, all ME, some long-haul
    for dest in region_airports["Turkey"]:
        add_pair("IST", dest)
    for dest in region_airports["Eastern Europe"]:
        add_pair("IST", dest)
    for dest in region_airports["Middle East"]:
        add_pair("IST", dest)
    for dest in (list(major_hubs) + list(medium_hubs)):
        add_pair("IST", dest)
    for dest in long_haul[:6]:
        add_pair("IST", dest)

    # Major European hubs: connect to all other hubs + TLV + IST + some regional
    for hub in major_hubs:
        for other in all_hubs:
            add_pair(hub, other)
        add_pair(hub, "TLV")
        hub_region = airport_region[hub]
        for dest in region_airports.get(hub_region, []):
            add_pair(hub, dest)
        for dest in long_haul[:4]:
            add_pair(hub, dest)

    # Medium hubs: connect to TLV, IST, all major hubs, some medium peers
    for hub in medium_hubs:
        add_pair(hub, "TLV")
        add_pair(hub, "IST")
        for mj in major_hubs:
            add_pair(hub, mj)
        hub_region = airport_region[hub]
        for dest in region_airports.get(hub_region, []):
            add_pair(hub, dest)

    # Small airports: connect to TLV + nearest 3 hubs by distance
    small = [c for c in IATA_CODES if c not in all_hubs]
    hub_list = sorted(all_hubs)
    for ap in small:
        add_pair(ap, "TLV")
        info = ap_data[ap]
        dists = []
        for h in hub_list:
            if h == ap:
                continue
            hi = ap_data[h]
            d = _haversine(info["lat"], info["lon"], hi["lat"], hi["lon"])
            dists.append((d, h))
        dists.sort()
        for _, h in dists[:3]:
            add_pair(ap, h)

    return list(pairs)


# ---------------------------------------------------------------------------
# Loader functions
# ---------------------------------------------------------------------------

def load_airports(con):
    """Load airports from airportsdata into the airports table."""
    ap_data = airportsdata.load("IATA")
    rows = []
    for iata in IATA_CODES:
        info = ap_data[iata]
        cc = info["country"]
        rows.append((
            iata, info["icao"], info["name"], info["city"],
            COUNTRY_NAMES.get(cc, cc), cc,
            info["lat"], info["lon"], info["tz"],
            REGION_MAP.get(cc, "Other"),
        ))
    con.executemany("INSERT INTO airports VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def load_airlines(con):
    """Insert airline reference data."""
    rows = [(a["airline_code"], a["airline_name"], a["country"], a["is_lowcost"])
            for a in AIRLINES]
    con.executemany("INSERT INTO airlines VALUES (?,?,?,?)", rows)
    return len(rows)


def load_routes(con):
    """Generate routes from hub patterns and assign airlines."""
    ap_data = airportsdata.load("IATA")
    city_pairs = _build_route_patterns()
    airport_region = {}
    for iata in IATA_CODES:
        cc = ap_data[iata]["country"]
        airport_region[iata] = REGION_MAP.get(cc, "Other")

    rows = []
    route_id = 0
    for origin, dest in sorted(city_pairs):
        o_reg = airport_region.get(origin, "Other")
        d_reg = airport_region.get(dest, "Other")
        # Find airlines serving both regions
        candidates = [code for code, regions in AIRLINE_REGIONS.items()
                      if o_reg in regions and d_reg in regions]
        if not candidates:
            candidates = ["TK"]
        # 1-2 airlines per pair
        for airline_code in candidates[:2]:
            route_id += 1
            fnum = (sum(ord(c) for c in origin + dest + airline_code) % 9000) + 100
            flight_number = f"{airline_code}{fnum}"
            oi, di = ap_data[origin], ap_data[dest]
            dist = _haversine(oi["lat"], oi["lon"], di["lat"], di["lon"])
            dur = _flight_duration_min(dist)
            aircraft = random.choice(NARROWBODIES if dur < 300 else WIDEBODIES)
            rows.append((
                route_id, origin, dest, airline_code, flight_number,
                aircraft, dur, True, "daily",
            ))
    con.executemany("INSERT INTO routes VALUES (?,?,?,?,?,?,?,?,?)", rows)
    return len(rows)


def generate_flight_prices(con):
    """Generate flight price offers for each route across July 2026."""
    random.seed(42)
    ap_data = airportsdata.load("IATA")

    airport_region = {}
    for iata in IATA_CODES:
        airport_region[iata] = REGION_MAP.get(ap_data[iata]["country"], "Other")
    lowcost = {a["airline_code"] for a in AIRLINES if a["is_lowcost"]}

    routes = con.execute(
        "SELECT route_id, origin_iata, dest_iata, airline_code, "
        "flight_number, typical_duration_min FROM routes"
    ).fetchall()

    rows = []
    pid = 0
    for _, origin, dest, acode, fnum, dur in routes:
        o_reg = airport_region.get(origin, "Other")
        d_reg = airport_region.get(dest, "Other")
        tier = REGION_PRICE_TIERS.get((o_reg, d_reg))
        if tier is None:
            tier = REGION_PRICE_TIERS.get((d_reg, o_reg))
        if tier is None:
            oi, di = ap_data[origin], ap_data[dest]
            dist = _haversine(oi["lat"], oi["lon"], di["lat"], di["lon"])
            mid = max(50, dist * 0.06)
            tier = (mid * 0.6, mid * 1.4)
        base_price = random.uniform(*tier)
        is_lc = acode in lowcost

        for day in range(1, 32):
            flight_date = date(2026, 7, day)
            n_flights = random.choice([1, 2, 2, 3])
            if n_flights == 1:
                hours = [random.randint(6, 20)]
            elif n_flights == 2:
                hours = [random.randint(6, 11), random.randint(15, 21)]
            else:
                hours = [random.randint(5, 9), random.randint(11, 15), random.randint(17, 22)]
            if random.random() < 0.15:
                hours[0] = random.randint(0, 5)

            for hour in hours:
                pid += 1
                minute = random.choice([0, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
                dep = datetime(2026, 7, day, hour, minute)
                arr = dep + timedelta(minutes=dur)
                price_usd = generate_price(base_price, flight_date, is_lc, hour)
                price_ils = round(price_usd * USD_ILS_RATE, 2)
                bclass = random.choice(["Y", "B", "H", "K", "M", "L", "V", "S"])
                seats = random.randint(1, 9)
                rows.append((
                    pid, flight_date, origin, dest, acode, fnum,
                    dep, arr, dur, price_usd, price_ils,
                    0, "economy", bclass, seats, "generated",
                ))

    # Bulk insert via pandas DataFrame (DuckDB vectorized scan, much faster
    # than executemany which does row-by-row parameter binding)
    df = pd.DataFrame(rows, columns=[
        "id", "flight_date", "origin", "destination", "airline_code",
        "flight_number", "departure_time", "arrival_time", "duration_min",
        "price_usd", "price_ils", "stops", "cabin_class", "booking_class",
        "seats_remaining", "data_source",
    ])
    con.execute("INSERT INTO flight_prices SELECT * FROM df")
    return len(df)


def load_currency_rates(con):
    """Insert currency exchange rates."""
    rates = [
        ("USD", "ILS", 3.65, date(2026, 7, 1)),
        ("EUR", "ILS", 3.98, date(2026, 7, 1)),
        ("GBP", "ILS", 4.62, date(2026, 7, 1)),
    ]
    con.executemany("INSERT INTO currency_rates VALUES (?,?,?,?)", rates)
    return len(rates)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def load_from_csv(con, table, path):
    """Load data from a CSV file into a table."""
    if table not in VALID_TABLES:
        raise ValueError(f"Unknown table: {table}")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {p}")
    con.execute(f"COPY {table} FROM '{p}' (FORMAT CSV, HEADER)")
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def load_from_parquet(con, table, path):
    """Load data from a Parquet file into a table."""
    if table not in VALID_TABLES:
        raise ValueError(f"Unknown table: {table}")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Parquet file not found: {p}")
    con.execute(f"INSERT INTO {table} SELECT * FROM read_parquet('{p}')")
    return con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def fetch_flight_data(api_key=None):
    """Placeholder for real flight data API integration."""
    raise NotImplementedError("API integration not yet implemented. Use generated data.")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_data(con):
    """Verify data integrity and that stopover savings exist."""
    checks = []

    n_airports = con.execute("SELECT count(*) FROM airports").fetchone()[0]
    checks.append(("airports >= 80", n_airports >= 80, n_airports))

    n_routes = con.execute("SELECT count(*) FROM routes").fetchone()[0]
    checks.append(("routes >= 200", n_routes >= 200, n_routes))

    n_prices = con.execute("SELECT count(*) FROM flight_prices").fetchone()[0]
    checks.append(("prices >= 10000", n_prices >= 10000, n_prices))

    n_deals = con.execute("""
        WITH direct AS (
            SELECT destination, MIN(price_usd) AS dp
            FROM flight_prices WHERE origin = 'TLV' AND stops = 0
            GROUP BY destination
        ),
        stopover AS (
            SELECT leg2.destination AS final_dest,
                   MIN(leg1.price_usd + leg2.price_usd) AS sp
            FROM flight_prices leg1
            JOIN flight_prices leg2
              ON leg1.destination = leg2.origin
             AND leg2.flight_date BETWEEN leg1.flight_date
                 AND leg1.flight_date + INTERVAL '7' DAY
            WHERE leg1.origin = 'TLV' AND leg1.stops = 0 AND leg2.stops = 0
            GROUP BY leg2.destination
        )
        SELECT COUNT(*) FROM stopover s
        JOIN direct d ON s.final_dest = d.destination
        WHERE s.sp < d.dp
    """).fetchone()[0]
    checks.append(("stopover savings exist", n_deals > 0, n_deals))

    all_pass = True
    for label, passed, value in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {label} (actual: {value})")
        if not passed:
            all_pass = False

    if not all_pass:
        raise AssertionError("Data verification failed")
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(db_path=DB_PATH):
    """Create database, load schema, generate all data, and verify."""
    db = Path(db_path)
    backup = db.with_suffix(".duckdb.bak")

    # Move existing DB aside (restore on failure)
    if db.exists():
        db.rename(backup)

    try:
        con = duckdb.connect(str(db))
        con.execute(Path("schema.sql").read_text())

        print("Loading data...")
        n = load_airports(con)
        print(f"  Airports:   {n}")
        n = load_airlines(con)
        print(f"  Airlines:   {n}")
        n = load_routes(con)
        print(f"  Routes:     {n}")
        n = generate_flight_prices(con)
        print(f"  Prices:     {n}")
        n = load_currency_rates(con)
        print(f"  Currencies: {n}")

        print("\nVerification:")
        verify_data(con)
        con.close()

        # Success — remove backup
        if backup.exists():
            backup.unlink()
        print(f"\nDone. Database: {db} ({db.stat().st_size / 1024 / 1024:.1f} MB)")

    except Exception:
        # Restore backup on failure
        if db.exists():
            db.unlink()
        if backup.exists():
            backup.rename(db)
        raise


if __name__ == "__main__":
    main()
