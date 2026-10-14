CREATE TABLE IF NOT EXISTS clients
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT,
    vendor TEXT,
    signal INTEGER,
    first_seen TEXT,
    last_seen TEXT
);