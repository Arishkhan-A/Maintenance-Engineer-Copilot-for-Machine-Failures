-- SQLite Database Schema for Maintenance Engineer Copilot (Production Edition)

CREATE TABLE IF NOT EXISTS machines (
    machine_id TEXT PRIMARY KEY,
    machine_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Normal',
    installed_date TEXT,
    location TEXT,
    operating_mode TEXT DEFAULT 'normal'
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    machine_id TEXT NOT NULL,
    temperature REAL NOT NULL,
    vibration REAL NOT NULL,
    pressure REAL NOT NULL,
    current REAL NOT NULL,
    rpm REAL NOT NULL,
    ambient_temp REAL DEFAULT 25.0,
    operating_mode TEXT DEFAULT 'normal',
    hours_since_maintenance REAL DEFAULT 0.0,
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
);

CREATE INDEX IF NOT EXISTS idx_sensor_machine_time ON sensor_readings(machine_id, timestamp);

CREATE TABLE IF NOT EXISTS maintenance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    date TEXT NOT NULL,
    action TEXT NOT NULL,
    component TEXT NOT NULL,
    technician TEXT,
    cost REAL DEFAULT 0.0,
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS failure_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    failure_type TEXT NOT NULL,
    root_cause TEXT,
    downtime_hours REAL,
    estimated_cost REAL DEFAULT 0.0,
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    risk TEXT NOT NULL,
    probability REAL NOT NULL,
    rul_hours REAL,
    is_anomaly INTEGER DEFAULT 0,
    anomaly_score REAL DEFAULT 0.0,
    model_version TEXT NOT NULL,
    top_contributing_feature TEXT,
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    machine_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT DEFAULT 'Open',
    FOREIGN KEY(machine_id) REFERENCES machines(machine_id)
);

CREATE TABLE IF NOT EXISTS spare_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL UNIQUE,
    part_number TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    min_threshold INTEGER NOT NULL DEFAULT 2,
    location TEXT
);

CREATE TABLE IF NOT EXISTS uploaded_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT UNIQUE NOT NULL,
    original_filename TEXT NOT NULL,
    file_format TEXT NOT NULL,
    original_size_bytes INTEGER NOT NULL,
    converted_csv_filename TEXT NOT NULL,
    converted_csv_path TEXT NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    column_count INTEGER NOT NULL DEFAULT 0,
    columns_json TEXT,
    upload_timestamp TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed'
);
