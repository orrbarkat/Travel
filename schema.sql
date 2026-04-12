-- ============================================================
-- Flight Stopover Optimization Engine — DuckDB Schema
-- ============================================================

-- AIRPORTS: Master airport reference data
CREATE TABLE IF NOT EXISTS airports (
    iata_code    VARCHAR(3)   PRIMARY KEY,
    icao_code    VARCHAR(4),
    name         VARCHAR(200) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    country      VARCHAR(100) NOT NULL,
    country_code VARCHAR(2)   NOT NULL,
    latitude     DOUBLE       NOT NULL,
    longitude    DOUBLE       NOT NULL,
    timezone     VARCHAR(50)  NOT NULL,
    region       VARCHAR(50)  -- 'Western Europe', 'Eastern Europe', 'Middle East', etc.
);

-- AIRLINES: Carrier reference data
CREATE TABLE IF NOT EXISTS airlines (
    airline_code VARCHAR(3)   PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    country      VARCHAR(100),
    is_lowcost   BOOLEAN      DEFAULT FALSE
);

-- ROUTES: Which airline flies which city pair (schedule skeleton)
CREATE TABLE IF NOT EXISTS routes (
    route_id             INTEGER PRIMARY KEY,
    origin_iata          VARCHAR(3)  NOT NULL REFERENCES airports(iata_code),
    dest_iata            VARCHAR(3)  NOT NULL REFERENCES airports(iata_code),
    airline_code         VARCHAR(3)  NOT NULL REFERENCES airlines(airline_code),
    flight_number        VARCHAR(10),
    aircraft_type        VARCHAR(50),
    typical_duration_min INTEGER,
    is_direct            BOOLEAN     DEFAULT TRUE,
    frequency            VARCHAR(20) DEFAULT 'daily'
);

CREATE INDEX IF NOT EXISTS idx_routes_origin ON routes(origin_iata);
CREATE INDEX IF NOT EXISTS idx_routes_dest   ON routes(dest_iata);
CREATE INDEX IF NOT EXISTS idx_routes_pair   ON routes(origin_iata, dest_iata);

-- FLIGHT PRICES: Individual priced flight offers (the big table)
CREATE TABLE IF NOT EXISTS flight_prices (
    id              INTEGER       PRIMARY KEY,
    flight_date     DATE          NOT NULL,
    origin          VARCHAR(3)    NOT NULL,
    destination     VARCHAR(3)    NOT NULL,
    airline_code    VARCHAR(3)    NOT NULL,
    flight_number   VARCHAR(10),
    departure_time  TIMESTAMP     NOT NULL,
    arrival_time    TIMESTAMP     NOT NULL,
    duration_min    INTEGER       NOT NULL,
    price_usd       DECIMAL(10,2) NOT NULL,
    price_ils       DECIMAL(10,2) NOT NULL,
    stops           INTEGER       DEFAULT 0,
    cabin_class     VARCHAR(20)   DEFAULT 'economy',
    booking_class   VARCHAR(5),
    seats_remaining INTEGER,
    data_source     VARCHAR(50)   DEFAULT 'generated'
);

CREATE INDEX IF NOT EXISTS idx_fp_origin_dest      ON flight_prices(origin, destination);
CREATE INDEX IF NOT EXISTS idx_fp_date             ON flight_prices(flight_date);
CREATE INDEX IF NOT EXISTS idx_fp_origin_dest_date ON flight_prices(origin, destination, flight_date);
CREATE INDEX IF NOT EXISTS idx_fp_price            ON flight_prices(price_usd);

-- CURRENCY RATES: Simple lookup table
CREATE TABLE IF NOT EXISTS currency_rates (
    from_currency VARCHAR(3),
    to_currency   VARCHAR(3),
    rate          DECIMAL(10,4),
    as_of_date    DATE,
    PRIMARY KEY (from_currency, to_currency)
);

-- ============================================================
-- VIEWS
-- ============================================================

-- Cheapest direct flight per route per date
CREATE VIEW IF NOT EXISTS v_cheapest_direct AS
SELECT
    origin,
    destination,
    flight_date,
    MIN(price_usd)  AS min_price_usd,
    MIN(price_ils)  AS min_price_ils,
    COUNT(*)         AS num_options,
    MIN(duration_min) AS min_duration
FROM flight_prices
WHERE stops = 0
GROUP BY origin, destination, flight_date;

-- Route-level aggregate statistics
CREATE VIEW IF NOT EXISTS v_route_stats AS
SELECT
    origin,
    destination,
    COUNT(*)                    AS total_flights,
    COUNT(DISTINCT airline_code) AS num_airlines,
    ROUND(AVG(price_usd), 2)   AS avg_price_usd,
    MIN(price_usd)              AS min_price_usd,
    MAX(price_usd)              AS max_price_usd,
    ROUND(STDDEV(price_usd), 2) AS stddev_price_usd,
    ROUND(AVG(duration_min), 0) AS avg_duration
FROM flight_prices
WHERE stops = 0
GROUP BY origin, destination;
