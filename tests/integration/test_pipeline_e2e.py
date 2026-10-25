import os
import pytest
from pathlib import Path
from flashscope.storage.sqlite_store import SqliteStore
from flashscope.parsers.qualidrive_adapter import import_qualidrive_run
from flashscope.signatures.engine import SignatureEngine
from flashscope.grouping.deduplicate import IncidentDeduplicator
from flashscope.timeline.timeline_builder import build_first_failure_timeline
from flashscope.regression.comparator import compare_firmware_releases
from flashscope.normalize.schema import Event


def test_qualidrive_import_and_triage_e2e(tmp_path):
    # Locate QualiDrive smoke_run
    base_dir = Path(__file__).resolve().parents[3]
    qualidrive_smoke_dir = base_dir / "QualiDrive" / "reports" / "smoke_run"

    assert qualidrive_smoke_dir.exists(), f"QualiDrive smoke run directory not found: {qualidrive_smoke_dir}"

    db_file = tmp_path / "test_e2e.db"
    store = SqliteStore(str(db_file))

    # 1. Import QualiDrive run
    result = import_qualidrive_run(str(qualidrive_smoke_dir), store)
    assert result["cases_imported"] > 0
    assert result["events_created"] > 0

    # 2. Check stats in SQLite
    stats = store.get_stats()
    assert stats["total_runs"] == 1
    assert stats["total_events"] == result["events_created"]

    # 3. Query events
    raw_events = store.query_events(run_id=result["run_id"], limit=1000)
    assert len(raw_events) > 0

    events = [
        Event(
            event_id=r["event_id"],
            run_id=r["run_id"],
            case_id=r["case_id"],
            timestamp=r["timestamp"],
            source=r["source"],
            device_id=r["device_id"],
            firmware=r["firmware"],
            event_type=r["event_type"],
            metric_name=r["metric_name"],
            metric_value=r["metric_value"],
            unit=r["unit"],
            message=r["message"],
            signature_id=r["signature_id"]
        )
        for r in raw_events
    ]

    # 4. Run automated triage & signature engine
    engine = SignatureEngine()
    engine.evaluate_events_batch(events)

    dedup = IncidentDeduplicator()
    incidents = dedup.group_events_into_incidents(events)

    # Insert incidents into SQLite
    store.insert_incidents(incidents)

    queried_incidents = store.query_incidents(run_id=result["run_id"])
    assert len(queried_incidents) == len(incidents)

    # 5. Build first-failure timeline
    sample_case_id = raw_events[0]["case_id"]
    timeline = build_first_failure_timeline(events, target_case_id=sample_case_id)
    assert isinstance(timeline, list)
    if timeline:
        assert all(t.description is not None for t in timeline)

    # 6. Test firmware regression comparison with synthetic baseline/candidate
    # Add a candidate event with degraded IOPS
    candidate_event = Event(
        run_id="run_cand",
        case_id=sample_case_id,
        source="fio",
        firmware="FW_CANDIDATE_2.0",
        event_type="metric_iops",
        metric_name="total_iops",
        metric_value=1000.0,  # severely reduced IOPS
        severity="WARN"
    )
    baseline_event = Event(
        run_id="run_base",
        case_id=sample_case_id,
        source="fio",
        firmware="FW_BASELINE_1.0",
        event_type="metric_iops",
        metric_name="total_iops",
        metric_value=50000.0,
        severity="INFO"
    )
    store.insert_events_batch([baseline_event, candidate_event])

    comp = compare_firmware_releases(store, "FW_BASELINE_1.0", "FW_CANDIDATE_2.0")
    assert comp["workloads_compared"] == 1
    assert comp["regressions_detected"] == 1
    assert comp["comparisons"][0]["regressed"] is True
    assert comp["comparisons"][0]["iops_delta_pct"] < -10.0

    store.close()
