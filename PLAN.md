# Flight Stopover Optimization Engine - Implementation Plan

## Context

Replicate the flight-optimization engine from @mluggy's viral X post: SQL-powered system that finds stopover deals (e.g., 2-3 days in Madrid en route to Portugal, saving 40-60% vs direct). Uses DuckDB + Python + Streamlit.

## Architecture

- **Database**: DuckDB (embedded, zero-config, analytical SQL on millions of rows)
- **Backend**: Python functions wrapping parameterized SQL queries
- **Frontend**: Streamlit web dashboard + Rich CLI
- **Claude integration**: System prompt generator for Claude-as-travel-agent mode

## File Structure

```
Travel/
├── .gitignore                # DuckDB files, __pycache__, .env
├── requirements.txt          # duckdb, pandas, streamlit, plotly, rich, click, pyarrow
├── schema.sql                # DuckDB DDL (5 tables, 4 indexes, 2 views)
├── load_data.py              # Sample data generator + CSV/Parquet/API loaders
├── engine.py                 # Core SQL query functions
├── app.py                    # Streamlit web dashboard
├── cli.py                    # CLI interface (click + rich)
├── claude_prompt.py          # System prompt generator for Claude-as-travel-agent
└── README.md                 # Setup instructions + example queries
```

## PR-Level Breakdown

Each PR below is independently shippable and testable. They must be merged in order.

---

### PR 1: Project scaffolding (DONE)
**Branch**: `claude/flight-optimization-engine-7i3P2`
**Files**: `.gitignore`, `requirements.txt`, `schema.sql`, `PLAN.md`

Already merged. Contains:
- DuckDB schema with 5 tables (airports, airlines, routes, flight_prices, currency_rates)
- 4 indexes on flight_prices for fast lookups
- 2 analytical views (v_cheapest_direct, v_route_stats)
- Python dependencies

---

### PR 2: Data layer (`load_data.py`)
**Depends on**: PR 1

**Tasks**:
- [ ] Define `AIRPORTS` constant (~90 airports: TLV, Turkey, Greece, Cyprus, Eastern/Western Europe, Middle East, long-haul) with IATA, ICAO, name, city, country, lat/lon, timezone, region
- [ ] Define `AIRLINES` constant (~15 carriers: LY, W6, FR, U2, TK, BA, AF, LH, KL, IB, TP, AZ, OS, SK, RO)
- [ ] Define `ROUTE_PATTERNS` (hub connectivity: TLV→60 destinations, IST→40, European hubs)
- [ ] Define `REGION_PRICE_TIERS` mapping (origin_region, dest_region) → (min_usd, max_usd)
- [ ] Write `load_airports()`, `load_airlines()`, `load_routes()` — bulk insert from constants
- [ ] Write `generate_price()` with modifiers: day-of-week (weekend 1.2x, Tue/Wed 0.85x), airline type (low-cost 0.6x), time-of-day (red-eye 0.8x), Gaussian noise (σ=0.08)
- [ ] Write `generate_flight_prices()` targeting 20k+ rows for July 2026
- [ ] Write utilities: `load_currency_rates()`, `load_from_csv()`/`load_from_parquet()`, `fetch_flight_data()` API placeholder, `verify_data()`, `__main__`

**Acceptance criteria**:
```bash
python load_data.py
# All checks pass: airports ≥80, routes ≥200, prices ≥10k, stopover savings exist
```

**Key pricing tiers that guarantee stopover savings emerge**:
| Route Category | Price Range (USD one-way) |
|---|---|
| TLV → Eastern Europe | $55–$160 |
| TLV → Western Europe (direct) | $170–$480 |
| Eastern Europe → Western Europe | $25–$110 |

Result: TLV→BUD($70) + BUD→LIS($50) = $120 vs TLV→LIS direct $300+ → 40-60% savings

---

### PR 3: Query engine (`engine.py`)
**Depends on**: PR 2

**Tasks**:
- [ ] `get_connection(db_path)` — read-only DuckDB connection
- [ ] `find_cheapest_direct(origin, dest, date_from, date_to)` — filtered sort WHERE stops=0
- [ ] `find_stopover_deals(origin, final_dest, date_from, date_to, min_layover, max_layover)` — THE CORE: self-join with CTE baseline + savings_pct
- [ ] `compare_airlines(origin, dest, date_from, date_to)` — GROUP BY airline stats
- [ ] `rank_stopovers_by_savings(origin, final_dest, date_from, date_to)` — aggregate by city
- [ ] `generate_comparison_table(origin, final_dest, date_from, date_to)` — viral post format
- [ ] `find_multi_city(origin, cities, start_date, min_days, max_days)` — permutation optimizer
- [ ] `execute_raw_sql(sql)` — read-only arbitrary SQL
- [ ] `get_schema_info()` — introspect tables/columns/counts
- [ ] `refresh_stopover_combinations()` — materialized table refresh
- [ ] `get_airports_list()`, `get_destinations_from(origin)` — UI helpers

**Acceptance criteria**:
```python
from engine import find_stopover_deals
df = find_stopover_deals('TLV', 'LIS', '2026-07-01', '2026-07-31')
assert len(df) > 0 and df['savings_pct'].max() > 10
```

**Core SQL pattern (stopover self-join)**:
```sql
WITH direct_baseline AS (
    SELECT MIN(price_usd) AS direct_min_price
    FROM flight_prices WHERE origin = ? AND destination = ? AND stops = 0
)
SELECT leg1.destination AS stopover_city,
       (leg1.price_usd + leg2.price_usd) AS total_price,
       ROUND(100.0*(1-(leg1.price_usd+leg2.price_usd)/d.direct_min_price),1) AS savings_pct
FROM flight_prices leg1
JOIN flight_prices leg2 ON leg1.destination = leg2.origin
    AND leg2.flight_date >= leg1.flight_date + ?
    AND leg2.flight_date <= leg1.flight_date + ?
JOIN airports a ON leg1.destination = a.iata_code
CROSS JOIN direct_baseline d
WHERE leg1.origin = ? AND leg2.destination = ?
  AND leg1.stops = 0 AND leg2.stops = 0
  AND (leg1.price_usd + leg2.price_usd) < d.direct_min_price
ORDER BY savings_pct DESC
```

---

### PR 4: Claude integration (`claude_prompt.py`)
**Depends on**: PR 3

**Tasks**:
- [ ] `generate_system_prompt(db_path)` — builds system prompt with: role definition, full schema DDL, row counts, date range, airport list, 5 example SQL queries, output format specs, read-only constraints
- [ ] `__main__` to print the prompt

**Acceptance criteria**:
```bash
python claude_prompt.py | head -50
# Prints system prompt with schema and example queries
```

---

### PR 5: CLI interface (`cli.py`)
**Depends on**: PR 3

**Tasks**:
- [ ] Click group with subcommands: `direct`, `stopover`, `compare`, `rank`, `multicity`, `sql`, `chat`
- [ ] Rich table formatting for all output
- [ ] `chat` subcommand: interactive REPL with regex pattern matching to detect intent + extract IATA codes

**Acceptance criteria**:
```bash
python cli.py stopover TLV LIS
# Formatted table with stopover deals and savings %

python cli.py stopover TLV OPO
# Madrid appears as a stopover city (the viral post deal)
```

---

### PR 6: Streamlit dashboard (`app.py`)
**Depends on**: PR 3

**Tasks**:
- [ ] Page config, sidebar with origin/dest selectors, date range picker, layover slider
- [ ] `@st.cache_resource` DB connection, `@st.cache_data` query results
- [ ] Tab 1 — Stopover Deals: metric cards + comparison table + route map
- [ ] Tab 2 — Direct Flights: sorted table + price calendar heatmap
- [ ] Tab 3 — Airline Comparison: bar chart + stats table
- [ ] Tab 4 — Route Map: Plotly Scattergeo with great-circle arcs
- [ ] Tab 5 — Multi-City Planner: multi-select cities + itinerary
- [ ] Tab 6 — SQL Lab: text area + Run button + example queries

**Acceptance criteria**:
```bash
streamlit run app.py
# Dashboard loads, all 6 tabs functional, map renders routes
```

---

### PR 7: Documentation (`README.md`) + final polish
**Depends on**: All above

**Tasks**:
- [ ] Project description referencing the viral post
- [ ] Quickstart: `pip install` → `python load_data.py` → `streamlit run app.py`
- [ ] CLI usage examples for each subcommand
- [ ] Example reproducing the Madrid-to-Portugal deal
- [ ] How to use real data (Amadeus API placeholder)
- [ ] Caveats: separate bookings, connection risk, simulated prices
- [ ] End-to-end test all components

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| DuckDB over SQLite/Postgres | Embedded, zero-config, optimized for analytical queries |
| Pricing tiers by region pair | Guarantees stopover savings emerge naturally |
| Both `price_usd` and `price_ils` stored | Avoids runtime currency joins |
| Plotly over Folium | Native `st.plotly_chart()`, great-circle arcs built-in |
| Read-only connections except in loader | Prevents DuckDB write contention |
| Self-join as core pattern | `leg1 JOIN leg2 ON leg1.dest = leg2.origin` with date window = stopover detection |
