"""
SQLite persistence and query engine for FlashScope normalized telemetry and incidents.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from flashscope.normalize.schema import Event, Incident


class SqliteStore:
    def __init__(self, db_path: str = "flashscope.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._enable_wal_mode()
        self.init_schema()

    def _enable_wal_mode(self):
        """Enables SQLite Write-Ahead Logging (WAL) and synchronous normal for high throughput."""
        cursor = self.conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.execute("PRAGMA cache_size = -64000;")  # 64 MB cache
        self.conn.commit()

    def init_schema(self):
        schema_path = os.path.join(os.path.dirname(__file__), "../../sql/schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                self.conn.executescript(f.read())
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def insert_run(
        self,
        run_id: str,
        run_name: str,
        start_time: str,
        end_time: str,
        device_id: str,
        firmware: str,
        status: str = "COMPLETED",
        metadata_json: str = "{}"
    ):
        sql = """
        INSERT OR REPLACE INTO runs (run_id, run_name, start_time, end_time, device_id, firmware, status, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(sql, (run_id, run_name, start_time, end_time, device_id, firmware, status, metadata_json))
        self.conn.commit()

    def insert_device(
        self,
        device_id: str,
        model: str,
        serial: str,
        firmware_rev: str,
        pcie_link_speed: str,
        pcie_link_width: str,
        sector_size: int = 512,
        capacity_bytes: int = 0
    ):
        sql = """
        INSERT OR REPLACE INTO devices (device_id, model, serial, firmware_rev, pcie_link_speed, pcie_link_width, sector_size, capacity_bytes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(sql, (device_id, model, serial, firmware_rev, pcie_link_speed, pcie_link_width, sector_size, capacity_bytes))
        self.conn.commit()

    def insert_events_batch(self, events: List[Event], chunk_size: int = 50000):
        """Batch inserts events in transactions for maximum throughput."""
        sql = """
        INSERT INTO events (
            event_id, run_id, case_id, timestamp, source, device_id, controller_id,
            namespace_id, firmware, workload_id, test_phase, severity, event_type,
            metric_name, metric_value, unit, message, signature_id, raw_artifact, raw_offset
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        for i in range(0, len(events), chunk_size):
            chunk = events[i : i + chunk_size]
            data = [e.to_db_tuple() for e in chunk]
            with self.conn:
                self.conn.executemany(sql, data)

    def insert_incidents(self, incidents: List[Incident]):
        sql_inc = """
        INSERT OR REPLACE INTO incidents (
            incident_id, run_id, case_id, signature_id, severity, confidence,
            occurrence_count, first_timestamp, last_timestamp, summary, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        sql_ev = """
        INSERT INTO incident_evidence (incident_id, event_id, relation_type)
        VALUES (?, ?, ?)
        """
        with self.conn:
            for inc in incidents:
                self.conn.execute(sql_inc, inc.to_db_tuple())
                for ev_id in inc.evidence_event_ids:
                    self.conn.execute(sql_ev, (inc.incident_id, ev_id, "TRIGGER"))

    def query_events(
        self,
        run_id: Optional[str] = None,
        case_id: Optional[str] = None,
        source: Optional[str] = None,
        signature_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        if run_id:
            query += " AND run_id = ?"
            params.append(run_id)
        if case_id:
            query += " AND case_id = ?"
            params.append(case_id)
        if source:
            query += " AND source = ?"
            params.append(source)
        if signature_id:
            query += " AND signature_id = ?"
            params.append(signature_id)
        query += f" ORDER BY timestamp ASC LIMIT {limit}"

        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def query_incidents(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM incidents"
        params = []
        if run_id:
            query += " WHERE run_id = ?"
            params.append(run_id)
        query += " ORDER BY first_timestamp ASC"
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        cur = self.conn.cursor()
        total_runs = cur.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        total_events = cur.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        total_incidents = cur.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        return {
            "total_runs": total_runs,
            "total_events": total_events,
            "total_incidents": total_incidents,
            "database_size_bytes": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2)
        }
