"""
Firmware regression analytics comparing candidate vs baseline builds across matched workloads.
"""

from typing import List, Dict, Any
from flashscope.storage.sqlite_store import SqliteStore


def compare_firmware_releases(
    store: SqliteStore,
    baseline_fw: str,
    candidate_fw: str,
    iops_threshold_pct: float = -10.0,
    p99_threshold_pct: float = 15.0
) -> Dict[str, Any]:
    """Compares baseline and candidate firmware metrics across all matched test cases in the store."""
    cursor = store.conn.cursor()

    query = """
    SELECT
        case_id,
        firmware,
        metric_name,
        AVG(metric_value) as avg_val
    FROM events
    WHERE firmware IN (?, ?) AND metric_name IS NOT NULL
    GROUP BY case_id, firmware, metric_name
    """
    rows = cursor.execute(query, (baseline_fw, candidate_fw)).fetchall()

    data: Dict[str, Dict[str, Dict[str, float]]] = {}
    for r in rows:
        cid, fw, m_name, val = r["case_id"], r["firmware"], r["metric_name"], r["avg_val"]
        if cid not in data:
            data[cid] = {baseline_fw: {}, candidate_fw: {}}
        data[cid][fw][m_name] = val

    comparisons = []
    regressions = 0

    for cid, fw_map in data.items():
        base_m = fw_map.get(baseline_fw, {})
        cand_m = fw_map.get(candidate_fw, {})

        if not base_m or not cand_m:
            continue

        base_iops = base_m.get("total_iops", 0.0)
        cand_iops = cand_m.get("total_iops", 0.0)
        iops_delta_pct = round(((cand_iops - base_iops) / base_iops * 100.0) if base_iops > 0 else 0.0, 2)

        base_p99 = base_m.get("latency_p99_ms", 0.0)
        cand_p99 = cand_m.get("latency_p99_ms", 0.0)
        p99_delta_pct = round(((cand_p99 - base_p99) / base_p99 * 100.0) if base_p99 > 0 else 0.0, 2)

        is_reg = False
        reasons = []

        if iops_delta_pct < iops_threshold_pct:
            is_reg = True
            reasons.append(f"IOPS dropped {iops_delta_pct}%")
        if p99_delta_pct > p99_threshold_pct:
            is_reg = True
            reasons.append(f"p99 latency increased {p99_delta_pct}%")

        if is_reg:
            regressions += 1

        comparisons.append({
            "case_id": cid,
            "baseline_fw": baseline_fw,
            "candidate_fw": candidate_fw,
            "baseline_iops": base_iops,
            "candidate_iops": cand_iops,
            "iops_delta_pct": iops_delta_pct,
            "baseline_p99_ms": base_p99,
            "candidate_p99_ms": cand_p99,
            "p99_delta_pct": p99_delta_pct,
            "regressed": is_reg,
            "notes": "; ".join(reasons) if reasons else "Nominal"
        })

    return {
        "baseline_firmware": baseline_fw,
        "candidate_firmware": candidate_fw,
        "workloads_compared": len(comparisons),
        "regressions_detected": regressions,
        "comparisons": comparisons
    }
