"""
Normalizer for fio execution outputs into FlashScope Event records.
"""

import json
from typing import List, Dict, Any, Optional
from flashscope.normalize.schema import Event


def normalize_fio_events(
    fio_data: Dict[str, Any],
    run_id: str,
    case_id: str,
    device_id: str = "nvme0",
    firmware: str = "REV_1.0",
    timestamp: str = "",
    raw_artifact_path: Optional[str] = None
) -> List[Event]:
    """Extracts normalized metric and state events from fio parsed results."""
    events: List[Event] = []

    # Total IOPS
    iops = float(fio_data.get("total_iops", 0.0))
    events.append(Event(
        run_id=run_id,
        case_id=case_id,
        timestamp=timestamp,
        source="fio",
        device_id=device_id,
        firmware=firmware,
        event_type="metric_iops",
        metric_name="total_iops",
        metric_value=iops,
        unit="IOPS",
        message=f"Observed IOPS: {iops:,.0f}",
        raw_artifact=raw_artifact_path
    ))

    # Total Bandwidth (MB/s)
    bw = float(fio_data.get("total_bw_mb", 0.0))
    events.append(Event(
        run_id=run_id,
        case_id=case_id,
        timestamp=timestamp,
        source="fio",
        device_id=device_id,
        firmware=firmware,
        event_type="metric_bandwidth",
        metric_name="total_bw_mb",
        metric_value=bw,
        unit="MiB/s",
        message=f"Observed throughput: {bw:.2f} MiB/s",
        raw_artifact=raw_artifact_path
    ))

    # Latencies
    p99_us = float(fio_data.get("lat_p99_us", 0.0))
    p99_ms = round(p99_us / 1000.0, 3)
    events.append(Event(
        run_id=run_id,
        case_id=case_id,
        timestamp=timestamp,
        source="fio",
        device_id=device_id,
        firmware=firmware,
        severity="WARN" if p99_ms > 50.0 else "INFO",
        event_type="metric_latency",
        metric_name="latency_p99_ms",
        metric_value=p99_ms,
        unit="ms",
        message=f"Observed p99 tail latency: {p99_ms} ms",
        raw_artifact=raw_artifact_path
    ))

    # Errors
    err_cnt = int(fio_data.get("total_errors", 0))
    if err_cnt > 0:
        events.append(Event(
            run_id=run_id,
            case_id=case_id,
            timestamp=timestamp,
            source="fio",
            device_id=device_id,
            firmware=firmware,
            severity="ERROR",
            event_type="fio_io_error",
            metric_name="fio_errors",
            metric_value=float(err_cnt),
            unit="count",
            message=f"fio reported {err_cnt} I/O completion errors",
            raw_artifact=raw_artifact_path
        ))

    return events
