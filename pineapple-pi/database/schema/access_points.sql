CREATE TABLE IF NOT EXISTS access_points
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ssid TEXT,
    bssid TEXT,
    channel INTEGER,
    signal INTEGER,
    first_seen TEXT,
    last_seen TEXT
);