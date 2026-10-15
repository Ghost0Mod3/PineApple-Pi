PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS access_points (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 ssid TEXT,
 bssid TEXT UNIQUE NOT NULL,
 channel INTEGER,
 frequency_mhz INTEGER,
 signal_percent INTEGER,
 security TEXT,
 first_seen TEXT NOT NULL,
 last_seen TEXT NOT NULL,
 sightings INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_access_points_last_seen ON access_points(last_seen);
CREATE TABLE IF NOT EXISTS scan_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 started_at TEXT NOT NULL,
 interface TEXT NOT NULL,
 result_count INTEGER NOT NULL,
 status TEXT NOT NULL
);
