CREATE TABLE zones (
    zone_id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL,
    is_return_zone BOOLEAN DEFAULT FALSE
);

CREATE TABLE gateways (
    gateway_id SERIAL PRIMARY KEY,
    gateway_name VARCHAR(100) NOT NULL,
    zone_id INTEGER REFERENCES zones(zone_id)
);


CREATE TABLE assets (
    asset_id VARCHAR(50) PRIMARY KEY,
    asset_type VARCHAR(50),

    current_zone_id INTEGER REFERENCES zones(zone_id),

    status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',

    last_seen_at TIMESTAMP,
    last_in_return_zone_at TIMESTAMP
);


CREATE TABLE zone_events (
    event_id SERIAL PRIMARY KEY,

    asset_id VARCHAR(50) REFERENCES assets(asset_id),

    zone_id INTEGER REFERENCES zones(zone_id),

    gateway_id INTEGER REFERENCES gateways(gateway_id),

    observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



CREATE INDEX idx_zone_events_asset
ON zone_events(asset_id);

CREATE INDEX idx_zone_events_time
ON zone_events(observed_at);