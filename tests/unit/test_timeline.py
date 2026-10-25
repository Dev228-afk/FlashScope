import pytest
from flashscope.normalize.schema import Event
from flashscope.timeline.timeline_builder import build_first_failure_timeline, TimelineEntry


def test_timeline_empty():
    assert build_first_failure_timeline([]) == []
    assert build_first_failure_timeline([], target_case_id="missing_case") == []


def test_timeline_filters_by_case_id():
    events = [
        Event(case_id="case_1", timestamp="2026-10-10T10:00:00Z", message="Case 1 message"),
        Event(case_id="case_2", timestamp="2026-10-10T10:00:01Z", message="Case 2 message"),
    ]
    tl = build_first_failure_timeline(events, target_case_id="case_1")
    assert len(tl) == 1
    assert tl[0].description == "Case 1 message"


def test_timeline_identifies_t0_fault_onset():
    events = [
        Event(
            case_id="c1",
            timestamp="2026-10-10T10:00:00Z",
            severity="INFO",
            event_type="fio_metric",
            source="fio",
            message="Fio baseline I/O running"
        ),
        Event(
            case_id="c1",
            timestamp="2026-10-10T10:00:02Z",
            severity="INFO",
            event_type="smart_sample",
            source="smart",
            message="Temperature 45 C"
        ),
        Event(
            case_id="c1",
            timestamp="2026-10-10T10:00:04Z",
            severity="CRITICAL",
            event_type="kernel_log",
            signature_id="CONTROLLER_RESET",
            source="dmesg",
            message="Kernel detected NVMe controller reset"
        ),
        Event(
            case_id="c1",
            timestamp="2026-10-10T10:00:06Z",
            severity="WARN",
            event_type="fio_metric",
            signature_id="LATENCY_REGRESSION",
            source="fio",
            message="High p99 latency spike observed"
        ),
    ]

    tl = build_first_failure_timeline(events)
    assert len(tl) == 4

    # Index 2 is the first critical event (T0)
    # So relative seconds:
    # index 0: (0 - 2) * 2 = -4.0s
    # index 1: (1 - 2) * 2 = -2.0s
    # index 2: (2 - 2) * 2 = 0.0s
    # index 3: (3 - 2) * 2 = +2.0s
    assert tl[0].relative_seconds == -4.0
    assert tl[1].relative_seconds == -2.0
    assert tl[2].relative_seconds == 0.0
    assert tl[2].signature_id == "CONTROLLER_RESET"
    assert tl[3].relative_seconds == 2.0

    entry_dict = tl[2].to_dict()
    assert entry_dict["signature_id"] == "CONTROLLER_RESET"
    assert entry_dict["severity"] == "CRITICAL"
    assert entry_dict["relative_seconds"] == 0.0
