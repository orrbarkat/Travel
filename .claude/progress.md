# Progress: PR 2 — Data Layer (`load_data.py`)

## Branch
`claude/implement-plan-task-airport-G0Q9h`

## What's Done
- **requirements.txt** updated: added `airportsdata` dependency (already committed? NO — uncommitted change)
- **Plan file** written at `/root/.claude/plans/happy-herding-deer.md` with full design
- **Research complete**: all design decisions are made, no open questions

## What Still Needs to Be Done
- [ ] Create `/home/user/Travel/load_data.py` (the entire file — does NOT exist yet)
- [ ] Test with `python load_data.py`
- [ ] Commit and push both `requirements.txt` and `load_data.py`

## Key Design Decisions (implement exactly as described)

### Airport Data: Use `airportsdata` package (NOT hardcoded)
- `airportsdata` is installed (v20260315, 7,883 airports)
- Load via `airportsdata.load('IATA')` — returns dict keyed by IATA code
- Each entry has: `icao`, `iata`, `name`, `city`, `country` (2-letter), `lat`, `lon`, `tz`
- We only define a list of 85 IATA codes + small mappings for country names and regions
- The package does NOT provide: full country name, region — we map those ourselves

### 85 IATA Codes (all verified to exist in airportsdata)
```python
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
```
- KIV doesn't exist in airportsdata — use **RMO** for Chisinau
- TXL (Tegel) closed — use **BER** (Brandenburg)

### Regions (used for pricing tiers)
Israel, Turkey, Eastern Europe (includes Greece & Cyprus), Western Europe, Middle East (includes Georgia & Armenia), North America, South America, Asia, Africa

### COUNTRY_NAMES mapping (~35 entries)
```python
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
```

### REGION_MAP (country code → region)
```python
REGION_MAP = {
    "IL": "Israel", "TR": "Turkey",
    "GR": "Eastern Europe", "CY": "Eastern Europe",  # grouped with EE for pricing
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
```

### Airlines (15 carriers)
LY (El Al, not lowcost), W6 (Wizz Air, lowcost), FR (Ryanair, lowcost), U2 (easyJet, lowcost), TK (Turkish, not), BA (British Airways, not), AF (Air France, not), LH (Lufthansa, not), KL (KLM, not), IB (Iberia, not), TP (TAP Portugal, not), AZ (ITA Airways, not), OS (Austrian, not), SK (SAS, not), RO (TAROM, not)

### AIRLINE_REGIONS (which airlines serve which regions)
```python
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
```

### REGION_PRICE_TIERS — (origin_region, dest_region) → (min_usd, max_usd)
Critical pricing that guarantees stopover savings:
- `("Israel", "Eastern Europe"): (55, 160)` 
- `("Israel", "Western Europe"): (170, 480)` ← expensive direct
- `("Eastern Europe", "Western Europe"): (25, 110)` ← cheap second leg
- So TLV→BUD($70) + BUD→LIS($50) = $120 vs TLV→LIS($300+) = 40-60% savings

Full tier table:
```python
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
```
Fallback for missing pairs: use `max(50, distance_km * 0.06)` clamped to (30, 900).

### Schema Column Order (must match exactly for INSERT)
- airports: iata_code, icao_code, name, city, country, country_code, latitude, longitude, timezone, region
- airlines: airline_code, airline_name, country, is_lowcost
- routes: route_id, origin_iata, dest_iata, airline_code, flight_number, aircraft_type, typical_duration_min, is_direct, frequency
- flight_prices: id, flight_date, origin, destination, airline_code, flight_number, departure_time, arrival_time, duration_min, price_usd, price_ils, stops, cabin_class, booking_class, seats_remaining, data_source
- currency_rates: from_currency, to_currency, rate, as_of_date

### Function Signatures

```python
DB_PATH = "flights.duckdb"
USD_ILS_RATE = 3.65

def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two lat/lon points."""

def _flight_duration_min(dist_km) -> int:
    """Estimate: dist_km / 800 * 60 + 30 min overhead."""

def generate_price(base_price, flight_date, airline_is_lowcost, departure_hour) -> float:
    """Apply modifiers: weekend ×1.2, Tue/Wed ×0.85, lowcost ×0.6, red-eye(0-5) ×0.8, gauss σ=0.08. Floor $15."""

def _build_route_patterns() -> list[tuple[str, str]]:
    """Returns list of (origin, dest) city-pairs based on hub tiers.
    Hub tiers:
    - Mega (TLV, IST): connect to almost all
    - Major (LHR, CDG, FRA, AMS, MUC, DXB, DOH): ~25-30 dests
    - Medium (BCN, MAD, FCO, MXP, VIE, ZRH, ATH, BUD, PRG, WAW, CPH, OSL, ARN): ~15-20
    - Small: connect to TLV + 2-3 nearest major hubs
    All routes bidirectional. Every airport reachable from TLV in ≤2 hops.
    """

def load_airports(con) -> int:
    """Use airportsdata.load('IATA'), look up each IATA_CODES entry, map country/region, executemany INSERT."""

def load_airlines(con) -> int:
    """Bulk insert from AIRLINES constant."""

def load_routes(con) -> int:
    """Call _build_route_patterns(), assign 1-2 airlines per pair from AIRLINE_REGIONS, 
    generate flight numbers, compute duration via haversine. Target ≥200 routes."""

def generate_flight_prices(con) -> int:
    """For each route × each day July 2026 × 1-3 flights/day. random.seed(42).
    Look up base from REGION_PRICE_TIERS, apply generate_price(). price_ils = price_usd × 3.65.
    Target ≥20k rows. Departure windows: morning/midday/evening spread. 15% chance red-eye."""

def load_currency_rates(con) -> int:
    """3 rows: USD→ILS 3.65, EUR→ILS 3.98, GBP→ILS 4.62. as_of_date = 2026-07-01."""

def load_from_csv(con, table, path) -> int:
    """DuckDB COPY FROM CSV. Validate table name against allowlist."""

def load_from_parquet(con, table, path) -> int:
    """DuckDB read_parquet(). Validate table name against allowlist."""

def fetch_flight_data(api_key=None):
    """Placeholder. Raises NotImplementedError."""

def verify_data(con) -> bool:
    """Assert: airports ≥ 80, routes ≥ 200, prices ≥ 10k, stopover savings exist
    (run two-leg join on TLV routes checking total < direct price)."""

def main(db_path=DB_PATH):
    """Delete old DB → connect → execute schema.sql → all loaders → verify → summary."""
```

### Price Generation Algorithm Detail
```
1. random.seed(42) at start of generate_flight_prices
2. For each route, pick base_price = random.uniform(min_usd, max_usd) from tier (once per route)
3. For each day in July 2026 (31 days):
   - n_flights = random.choice([1, 2, 2, 3])  # weighted toward 2
   - For each flight, pick departure hour from time windows:
     - 1 flight: [6-20]
     - 2 flights: [6-11], [15-21]
     - 3 flights: [5-9], [11-15], [17-22]
   - 15% chance replace first flight with red-eye (hour 0-5)
   - Apply generate_price() with all modifiers
   - price_ils = round(price_usd * 3.65, 2)
   - arrival_time = departure_time + timedelta(minutes=duration)
   - stops=0, cabin_class="economy"
   - booking_class = random.choice(["Y","B","H","K","M","L","V","S"])
   - seats_remaining = random.randint(1, 9)
```

### Row Count Estimates
- airports: 85
- airlines: 15
- routes: ~300-500 (city-pairs × 1-2 airlines)
- flight_prices: ~20k (routes × 31 days × ~2 flights/day)
- currency_rates: 3

### Acceptance Criteria (from PLAN.md)
```bash
python load_data.py
# All checks pass: airports ≥80, routes ≥200, prices ≥10k, stopover savings exist
```

### Important Notes
- `random.seed(42)` for reproducibility
- Use `executemany` for bulk inserts (no pandas needed)
- `hash()` is NOT deterministic across Python sessions — use `sum(ord(c) for c in s) % N` or random-based approach for flight numbers
- Read schema.sql with `Path("schema.sql").read_text()` and execute it
- Delete old DB file before creating new one: `Path(db_path).unlink(missing_ok=True)`
- AIRCRAFT_TYPES: narrowbody (B737, B738, A320, A321, A319) for <300min, widebody (B787, A330, B777, A350) for longer
