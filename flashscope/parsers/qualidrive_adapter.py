"""
Adapter importing QualiDrive run results and artifacts directly into FlashScope.
"""

import json
import os
import glob
from typing import Dict, Any, List
from flashscope.normalize.schema import Event
from flashscope.parsers.fio_parser import normalize_fio_events
from flashscope.parsers.smart_parser import normalize_smart_events
from flashscope.parsers.dmesg_parser import normalize_dmesg_events
from flashscope.storage.sqlite_store import SqliteStore


def import_qualidrive_run(qualidrive_dir: str, store: SqliteStore) -> Dict[str, Any]:
    """Imports a QualiDrive qualification run directory into FlashScope SQLite storage."""
    summary_files = glob.glob(os.path.join(qualidrive_dir, "*_summary.json"))
    if not summary_files:
        raise FileNotFoundError(f"No summary.json found in QualiDrive run directory: {qualidrive_dir}")

    summary_path = summary_files[0]
    with open(summary_path, "r", encoding="utf-8") as f:
        run_data = json.load(f)

    run_id = run_data.get("run_id", "qual_import")
    results = run_data.get("results", [])

    # Extract device information from first case
    first_case = results[0] if results else {}
    dev_info = first_case.get("device", {})
    device_id = dev_info.get("controller_id", "nvme0")
    model = dev_info.get("model", "Unknown Model")
    serial = dev_info.get("serial", "Unknown Serial")
    firmware = dev_info.get("firmware_rev", "REV_1.0")

    pcie = dev_info.get("pcie_link", {})
    pcie_speed = pcie.get("speed", "8.0 GT/s")
    pcie_width = pcie.get("width", "x4")

    # Insert device and run
    store.insert_device(
        device_id=device_id,
        model=model,
        serial=serial,
        firmware_rev=firmware,
        pcie_link_speed=pcie_speed,
        pcie_link_width=pcie_width
    )

    store.insert_run(
        run_id=run_id,
        run_name="QualiDrive Qualification Run",
        start_time=first_case.get("pre_health", {}).get("timestamp", ""),
        end_time=results[-1].get("post_health", {}).get("timestamp", "") if results else "",
        device_id=device_id,
        firmware=firmware,
        metadata_json=json.dumps(run_data.get("thresholds", {}))
    )

    all_events: List[Event] = []

    for r in results:
        case_id = r["case_id"]
        pre_h = r.get("pre_health", {})
        post_h = r.get("post_health", {})
        fio = r.get("fio", {})
        deltas = r.get("deltas", {})
        ts = post_h.get("timestamp") or pre_h.get("timestamp") or ""

        # Raw artifacts
        raw_art = r.get("artifacts", [None])[0] if r.get("artifacts") else None

        # Fio events
        if fio:
            all_events.extend(normalize_fio_events(
                fio_data=fio,
                run_id=run_id,
                case_id=case_id,
                device_id=device_id,
                firmware=firmware,
                timestamp=ts,
                raw_artifact_path=raw_art
            ))

        # SMART events
        if post_h:
            all_events.extend(normalize_smart_events(
                smart_data=post_h,
                run_id=run_id,
                case_id=case_id,
                device_id=device_id,
                firmware=firmware,
                timestamp=ts,
                raw_artifact_path=raw_art
            ))

        # Kernel fault signatures from deltas
        signatures = deltas.get("detected_kernel_signatures", [])
        for sig in signatures:
            all_events.append(Event(
                run_id=run_id,
                case_id=case_id,
                timestamp=ts,
                source="dmesg",
                device_id=device_id,
                firmware=firmware,
                severity="CRITICAL",
                event_type="kernel_signature",
                signature_id=sig,
                message=f"QualiDrive detected kernel signature: {sig}",
                raw_artifact=raw_art
            ))

    # Bulk insert
    store.insert_events_batch(all_events)

    return {
        "run_id": run_id,
        "device_id": device_id,
        "cases_imported": len(results),
        "events_created": len(all_events)
    }
