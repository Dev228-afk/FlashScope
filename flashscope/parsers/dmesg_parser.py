"""
Normalizer for kernel ring buffer (dmesg) and journalctl logs into FlashScope Event records.
"""

import re
from typing import List, Optional
from flashscope.normalize.schema import Event


def normalize_dmesg_events(
    dmesg_text: str,
    run_id: str,
    case_id: str,
    device_id: str = "nvme0",
    firmware: str = "REV_1.0",
    timestamp: str = "",
    raw_artifact_path: Optional[str] = None
) -> List[Event]:
    """Parses dmesg lines and creates Event records with severity and detected signatures."""
    events: List[Event] = []
    if not dmesg_text.strip():
        return events

    patterns = [
        (r"nvme\d+:.*(?:reset|controller reset)", "CRITICAL", "NVME_CONTROLLER_RESET", "Kernel detected NVMe controller reset"),
        (r"nvme\d+:.*(?:timeout|I/O timeout|abort)", "ERROR", "NVME_IO_TIMEOUT", "Kernel reported NVMe command timeout/abort"),
        (r"I/O error.*dev nvme", "CRITICAL", "NVME_KERNEL_IO_ERROR", "Kernel block layer reported NVMe I/O error"),
        (r"Controller Fatal Status", "CRITICAL", "NVME_CONTROLLER_FATAL_STATUS", "NVMe Controller Fatal Status bit set"),
        (r"PCIe link down|aer_status", "CRITICAL", "PCIE_LINK_DOWN_OR_AER", "PCIe link down or Advanced Error Reporting fault")
    ]

    for offset, line in enumerate(dmesg_text.splitlines()):
        line_clean = line.strip()
        if not line_clean:
            continue

        matched_sig = None
        severity = "INFO"
        desc = line_clean

        for pat, sev, sig, msg in patterns:
            if re.search(pat, line_clean, re.IGNORECASE):
                matched_sig = sig
                severity = sev
                desc = f"{msg}: {line_clean}"
                break

        events.append(Event(
            run_id=run_id,
            case_id=case_id,
            timestamp=timestamp,
            source="dmesg",
            device_id=device_id,
            firmware=firmware,
            severity=severity,
            event_type="kernel_log",
            signature_id=matched_sig,
            message=desc,
            raw_artifact=raw_artifact_path,
            raw_offset=offset
        ))

    return events
