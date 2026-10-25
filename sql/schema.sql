-- FlashScope SQLite Relational Storage Schema

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    run_name TEXT NOT NULL,
    start_time TEXT,
    end_time TEXT,
    device_id TEXT,
    firmware TEXT,
    status TEXT DEFAULT 'COMPLETED',
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    model TEXT,
    serial TEXT,
    firmware_rev TEXT,
    pcie_link_speed TEXT,
    pcie_link_width TEXT,
    sector_size INTEGER DEFAULT 512,
    capacity_bytes INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS workloads (
    workload_id TEXT PRIMARY KEY,
    run_id TEXT,
    case_id TEXT,
    block_size TEXT,
    queue_depth INTEGER,
    read_percent INTEGER,
    access TEXT,
    jobs INTEGER DEFAULT 1,
    runtime_seconds INTEGER DEFAULT 10
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT,
    timestamp TEXT NOT NULL,
    source TEXT NOT NULL,         -- 'fio', 'smart', 'error_log', 'dmesg', 'pcie'
    device_id TEXT,
    controller_id TEXT,
    namespace_id TEXT,
    firmware TEXT,
    workload_id TEXT,
    test_phase TEXT DEFAULT 'RUN',
    severity TEXT DEFAULT 'INFO', -- 'INFO', 'WARN', 'ERROR', 'CRITICAL'
    event_type TEXT NOT NULL,
    metric_name TEXT,
    metric_value REAL,
    unit TEXT,
    message TEXT,
    signature_id TEXT,
    raw_artifact TEXT,
    raw_offset INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    case_id TEXT,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT,
    signature_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    occurrence_count INTEGER DEFAULT 1,
    first_timestamp TEXT NOT NULL,
    last_timestamp TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT DEFAULT 'OPEN'
);

CREATE TABLE IF NOT EXISTS incident_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    relation_type TEXT DEFAULT 'CORRELATED'
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT,
    file_path TEXT NOT NULL,
    artifact_type TEXT,
    file_size_bytes INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS firmware_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_fw TEXT NOT NULL,
    candidate_fw TEXT NOT NULL,
    workload_fingerprint TEXT NOT NULL,
    iops_delta_pct REAL,
    latency_p99_delta_pct REAL,
    regressions_detected INTEGER DEFAULT 0,
    notes TEXT
);

-- Analytical Indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_run_case ON events(run_id, case_id);
CREATE INDEX IF NOT EXISTS idx_events_device_fw ON events(device_id, firmware);
CREATE INDEX IF NOT EXISTS idx_events_sig ON events(signature_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_incidents_run ON incidents(run_id);
CREATE INDEX IF NOT EXISTS idx_metrics_run_case ON metrics(run_id, case_id, metric_name);
