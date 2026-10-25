"""
Normalizer for NVMe SMART/health logs into FlashScope Event records.
"""

from typing import List, Dict, Any, Optional
from flashscope.normalize.schema import Event


def normalize_smart_events(
    smart_data: Dict[str, Any],
    run_id: str,
    case_id: str,
    device_id: str = "nvme0",
    firmware: str = "REV_1.0",
    timestamp: str = "",
    test_phase: str = "POST",
    raw_artifact_path: Optional[str] = None
) -> List[Event]:
    """Extracts normalized temperature, media errors, and wear events from SMART data."""
    events: List[Event] = []

    # Temperature
    temp_c = int(smart_data.get("temperature_c", 0))
    if temp_c > 0:
        events.append(Event(
            run_id=run_id,
            case_id=case_id,
            timestamp=timestamp,
            source="smart",
            device_id=device_id,
            firmware=firmware,
            test_phase=test_phase,
            severity="WARN" if temp_c >= 75 else "INFO",
            event_type="metric_temperature",
            metric_name="temperature_c",
            metric_value=float(temp_c),
            unit="C",
            message=f"SMART composite temperature: {temp_c}°C",
            raw_artifact=raw_artifact_path
        ))

    # Media and Data Integrity Errors
    media_errs = int(smart_data.get("media_errors", 0))
    events.append(Event(
        run_id=run_id,
        case_id=case_id,
        timestamp=timestamp,
        source="smart",
        device_id=device_id,
        firmware=firmware,
        test_phase=test_phase,
        severity="CRITICAL" if media_errs > 0 else "INFO",
        event_type="smart_media_errors",
        metric_name="media_errors_count",
        metric_value=float(media_errs),
        unit="count",
        message=f"SMART media errors lifetime count: {media_errs}",
        raw_artifact=raw_artifact_path
    ))

    # Unsafe Shutdowns
    unsafe_sh = int(smart_data.get("unsafe_shutdowns", 0))
    events.append(Event(
        run_id=run_id,
        case_id=case_id,
        timestamp=timestamp,
        source="smart",
        device_id=device_id,
        firmware=firmware,
        test_phase=test_phase,
        severity="INFO",
        event_type="smart_unsafe_shutdowns",
        metric_name="unsafe_shutdowns_count",
        metric_value=float(unsafe_sh),
        unit="count",
        message=f"SMART unsafe shutdowns lifetime count: {unsafe_sh}",
        raw_artifact=raw_artifact_path
    ))

    return events
