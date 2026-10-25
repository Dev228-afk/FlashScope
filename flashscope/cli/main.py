"""
Command Line Interface (CLI) for FlashScope SSD Telemetry & Failure-Triage Pipeline.
"""

import argparse
import json
import os
import sys
from flashscope.parsers.qualidrive_adapter import import_qualidrive_run
from flashscope.signatures.engine import SignatureEngine
from flashscope.grouping.deduplicate import IncidentDeduplicator
from flashscope.storage.sqlite_store import SqliteStore
from flashscope.timeline.timeline_builder import build_first_failure_timeline
from flashscope.regression.comparator import compare_firmware_releases
from flashscope.normalize.schema import Event


def cmd_import_qualidrive(args):
    db_path = args.db or "flashscope.db"
    store = SqliteStore(db_path=db_path)
    res = import_qualidrive_run(args.run_dir, store)
    print("\n" + "=" * 65)
    print(f" QUALIDRIVE RUN IMPORTED INTO FLASHSCOPE")
    print(f" Run ID:          {res['run_id']}")
    print(f" Device ID:       {res['device_id']}")
    print(f" Cases Imported:  {res['cases_imported']}")
    print(f" Events Created:  {res['events_created']}")
    print(f" SQLite Target:   {db_path}")
    print("=" * 65 + "\n")
    store.close()


def cmd_triage(args):
    db_path = args.db or "flashscope.db"
    store = SqliteStore(db_path=db_path)
    raw_events = store.query_events(run_id=args.run_id, limit=50000)

    events: list[Event] = []
    for r in raw_events:
        events.append(Event(
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
        ))

    engine = SignatureEngine()
    engine.evaluate_events_batch(events)

    dedup = IncidentDeduplicator()
    incidents = dedup.group_events_into_incidents(events)
    store.insert_incidents(incidents)

    print("\n" + "=" * 75)
    print(f" FLASHSCOPE AUTOMATED TRIAGE REPORT")
    print("=" * 75)
    print(f"Total Events Evaluated:  {len(events)}")
    print(f"Consolidated Incidents:  {len(incidents)}")
    print("-" * 75)
    print(f"{'Incident ID':<22} | {'Severity':<8} | {'Signature ID':<20} | {'Count':<5} | Summary")
    print("-" * 75)
    for inc in incidents:
        print(f"{inc.incident_id:<22} | {inc.severity:<8} | {inc.signature_id:<20} | {inc.occurrence_count:<5} | {inc.summary[:30]}")
    print("=" * 75 + "\n")
    store.close()


def cmd_timeline(args):
    db_path = args.db or "flashscope.db"
    store = SqliteStore(db_path=db_path)
    raw_events = store.query_events(case_id=args.case_id, limit=100)

    events = [Event(
        event_id=r["event_id"],
        run_id=r["run_id"],
        case_id=r["case_id"],
        timestamp=r["timestamp"],
        source=r["source"],
        device_id=r["device_id"],
        severity=r["severity"],
        event_type=r["event_type"],
        message=r["message"],
        signature_id=r["signature_id"]
    ) for r in raw_events]

    timeline = build_first_failure_timeline(events, target_case_id=args.case_id)

    print("\n" + "=" * 75)
    print(f" FIRST-FAILURE CHRONOLOGICAL TIMELINE: {args.case_id}")
    print("=" * 75)
    for t in timeline:
        sig_str = f"[{t.signature_id}]" if t.signature_id else ""
        print(f"{t.relative_seconds:>+6.1f}s | {t.source:<6} | {t.severity:<8} | {sig_str:<22} {t.description}")
    print("=" * 75 + "\n")
    store.close()


def cmd_compare(args):
    db_path = args.db or "flashscope.db"
    store = SqliteStore(db_path=db_path)
    res = compare_firmware_releases(store, args.baseline_fw, args.candidate_fw)

    print("\n" + "=" * 75)
    print(f" FLASHSCOPE FIRMWARE REGRESSION COMPARISON")
    print(f" Baseline: {args.baseline_fw} vs Candidate: {args.candidate_fw}")
    print("=" * 75)
    print(f"Workloads Compared:    {res['workloads_compared']}")
    print(f"Regressions Flagged:   {res['regressions_detected']}")
    print("-" * 75)
    for c in res["comparisons"][:10]:
        reg = "YES" if c["regressed"] else "NO"
        print(f"{c['case_id']:<30} | IOPS Δ: {c['iops_delta_pct']:>6.1f}% | p99 Δ: {c['p99_delta_pct']:>6.1f}% | Regressed: {reg} | {c['notes']}")
    print("=" * 75 + "\n")
    store.close()


def main():
    parser = argparse.ArgumentParser(description="FlashScope: SSD Telemetry Normalization & Triage Pipeline")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # import-qualidrive
    p_imp = subparsers.add_parser("import-qualidrive", help="Import a QualiDrive qualification run")
    p_imp.add_argument("run_dir", help="Path to QualiDrive run directory")
    p_imp.add_argument("--db", default="flashscope.db", help="Target SQLite database")
    p_imp.set_defaults(func=cmd_import_qualidrive)

    # triage
    p_tri = subparsers.add_parser("triage", help="Run automated failure triage and group incidents")
    p_tri.add_argument("--db", default="flashscope.db", help="Target SQLite database")
    p_tri.add_argument("--run-id", help="Filter by specific run ID")
    p_tri.set_defaults(func=cmd_triage)

    # timeline
    p_time = subparsers.add_parser("timeline", help="Build first-failure timeline for a test case")
    p_time.add_argument("case_id", help="Test case ID")
    p_time.add_argument("--db", default="flashscope.db", help="Target SQLite database")
    p_time.set_defaults(func=cmd_timeline)

    # compare
    p_comp = subparsers.add_parser("compare", help="Compare baseline vs candidate firmware")
    p_comp.add_argument("baseline_fw", help="Baseline firmware version")
    p_comp.add_argument("candidate_fw", help="Candidate firmware version")
    p_comp.add_argument("--db", default="flashscope.db", help="Target SQLite database")
    p_comp.set_defaults(func=cmd_compare)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
