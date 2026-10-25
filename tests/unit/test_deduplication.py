import pytest
from flashscope.normalize.schema import Event
from flashscope.grouping.deduplicate import IncidentDeduplicator


def test_deduplicator_groups_same_signature():
    dedup = IncidentDeduplicator()
    events = [
        Event(
            event_id="ev_1",
            run_id="run_alpha",
            case_id="case_seq_read",
            timestamp="2026-10-10T12:00:00Z",
            source="dmesg",
            severity="CRITICAL",
            signature_id="CONTROLLER_RESET",
            message="Kernel detected NVMe reset"
        ),
        Event(
            event_id="ev_2",
            run_id="run_alpha",
            case_id="case_seq_read",
            timestamp="2026-10-10T12:00:05Z",
            source="dmesg",
            severity="CRITICAL",
            signature_id="CONTROLLER_RESET",
            message="Watchdog timeout triggered reset"
        ),
    ]

    incidents = dedup.group_events_into_incidents(events)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.run_id == "run_alpha"
    assert inc.case_id == "case_seq_read"
    assert inc.signature_id == "CONTROLLER_RESET"
    assert inc.occurrence_count == 2
    assert inc.first_timestamp == "2026-10-10T12:00:00Z"
    assert inc.last_timestamp == "2026-10-10T12:00:05Z"
    assert inc.evidence_event_ids == ["ev_1", "ev_2"]
    assert inc.confidence == 0.90  # Single source (dmesg)


def test_deduplicator_multi_source_confidence():
    dedup = IncidentDeduplicator()
    events = [
        Event(
            event_id="ev_10",
            run_id="run_beta",
            case_id="case_rnd_write",
            timestamp="2026-10-10T14:10:00Z",
            source="smart",
            severity="CRITICAL",
            signature_id="MEDIA_ERROR",
            message="SMART media error count increased"
        ),
        Event(
            event_id="ev_11",
            run_id="run_beta",
            case_id="case_rnd_write",
            timestamp="2026-10-10T14:10:02Z",
            source="dmesg",
            severity="CRITICAL",
            signature_id="MEDIA_ERROR",
            message="Kernel I/O error on sector 4096"
        ),
    ]

    incidents = dedup.group_events_into_incidents(events)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.occurrence_count == 2
    assert inc.confidence == 1.0  # Multi-source corroborated (smart + dmesg)
    assert set(inc.evidence_event_ids) == {"ev_10", "ev_11"}


def test_deduplicator_ignores_events_without_signature():
    dedup = IncidentDeduplicator()
    events = [
        Event(
            event_id="ev_normal_1",
            run_id="run_gamma",
            case_id="case_normal",
            source="fio",
            signature_id=None,
            message="Workload completed normally"
        ),
        Event(
            event_id="ev_normal_2",
            run_id="run_gamma",
            case_id="case_normal",
            source="smart",
            signature_id=None,
            message="Temperature 45 C"
        ),
    ]

    incidents = dedup.group_events_into_incidents(events)
    assert len(incidents) == 0


def test_deduplicator_separates_distinct_signatures_and_cases():
    dedup = IncidentDeduplicator()
    events = [
        Event(
            event_id="ev_a",
            run_id="run_1",
            case_id="case_1",
            signature_id="MEDIA_ERROR",
            source="smart"
        ),
        Event(
            event_id="ev_b",
            run_id="run_1",
            case_id="case_1",
            signature_id="THERMAL_THROTTLE",
            source="smart"
        ),
        Event(
            event_id="ev_c",
            run_id="run_1",
            case_id="case_2",
            signature_id="MEDIA_ERROR",
            source="smart"
        ),
    ]

    incidents = dedup.group_events_into_incidents(events)
    assert len(incidents) == 3
    sig_case_pairs = {(inc.case_id, inc.signature_id) for inc in incidents}
    assert sig_case_pairs == {
        ("case_1", "MEDIA_ERROR"),
        ("case_1", "THERMAL_THROTTLE"),
        ("case_2", "MEDIA_ERROR"),
    }
