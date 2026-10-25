"""
Normalized event, incident, and metric schema for storage telemetry.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import uuid


@dataclass
class Event:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = "run_default"
    case_id: str = "case_default"
    timestamp: str = ""
    source: str = "unknown"             # 'fio', 'smart', 'error_log', 'dmesg', 'pcie'
    device_id: str = "nvme0"
    controller_id: str = "nvme0"
    namespace_id: str = "1"
    firmware: str = "REV_1.0"
    workload_id: str = ""
    test_phase: str = "RUN"             # 'PRE', 'RUN', 'POST'
    severity: str = "INFO"              # 'INFO', 'WARN', 'ERROR', 'CRITICAL'
    event_type: str = "generic"
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    unit: Optional[str] = None
    message: str = ""
    signature_id: Optional[str] = None
    raw_artifact: Optional[str] = None
    raw_offset: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_db_tuple(self) -> tuple:
        return (
            self.event_id,
            self.run_id,
            self.case_id,
            self.timestamp,
            self.source,
            self.device_id,
            self.controller_id,
            self.namespace_id,
            self.firmware,
            self.workload_id,
            self.test_phase,
            self.severity,
            self.event_type,
            self.metric_name,
            self.metric_value,
            self.unit,
            self.message,
            self.signature_id,
            self.raw_artifact,
            self.raw_offset
        )


@dataclass
class Incident:
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str = ""
    case_id: str = ""
    signature_id: str = ""
    severity: str = "ERROR"
    confidence: float = 1.0
    occurrence_count: int = 1
    first_timestamp: str = ""
    last_timestamp: str = ""
    summary: str = ""
    status: str = "OPEN"
    evidence_event_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_db_tuple(self) -> tuple:
        return (
            self.incident_id,
            self.run_id,
            self.case_id,
            self.signature_id,
            self.severity,
            self.confidence,
            self.occurrence_count,
            self.first_timestamp,
            self.last_timestamp,
            self.summary,
            self.status
        )
