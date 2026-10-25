"""
Failure signature rule definitions for storage fault triage.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from flashscope.normalize.schema import Event


@dataclass
class SignatureRule:
    signature_id: str
    name: str
    severity: str                       # 'WARN', 'ERROR', 'CRITICAL'
    description: str
    matcher: Callable[[Event], bool]


def get_default_signature_rules() -> List[SignatureRule]:
    """Returns the standard production suite of failure signature rules."""
    rules = [
        SignatureRule(
            signature_id="MEDIA_ERROR",
            name="NAND Media / Data Integrity Error",
            severity="CRITICAL",
            description="Hardware media read/write corruption or uncorrectable ECC error detected in SMART or host I/O",
            matcher=lambda e: (
                (e.event_type == "smart_media_errors" and (e.metric_value or 0) > 0)
                or e.event_type == "fio_io_error"
                or e.signature_id == "NVME_KERNEL_IO_ERROR"
            )
        ),
        SignatureRule(
            signature_id="CONTROLLER_RESET",
            name="NVMe Controller Reset / Fatal Status",
            severity="CRITICAL",
            description="Controller firmware crashed or PCIe reset triggered due to fatal status register CFS=1",
            matcher=lambda e: (
                e.signature_id in ("NVME_CONTROLLER_RESET", "NVME_CONTROLLER_FATAL_STATUS")
                or "reset controller" in e.message.lower()
                or "controller reset" in e.message.lower()
                or "resetting controller" in e.message.lower()
                or ("reset" in e.message.lower() and "controller" in e.message.lower())
            )
        ),
        SignatureRule(
            signature_id="IO_TIMEOUT",
            name="Host NVMe Command Watchdog Timeout",
            severity="ERROR",
            description="Command was submitted to hardware queue but completion interrupt was not received within timeout limit",
            matcher=lambda e: (
                e.signature_id == "NVME_IO_TIMEOUT"
                or "timeout" in e.message.lower() and "nvme" in e.message.lower()
            )
        ),
        SignatureRule(
            signature_id="THERMAL_THROTTLE",
            name="Thermal Throttling Condition",
            severity="WARN",
            description="Operating temperature exceeded critical thermal management limit (TMT1/TMT2 >= 75°C)",
            matcher=lambda e: (
                e.event_type == "metric_temperature" and (e.metric_value or 0) >= 75.0
            )
        ),
        SignatureRule(
            signature_id="LATENCY_REGRESSION",
            name="Tail Latency SLA Violation",
            severity="WARN",
            description="Observed p99 completion latency exceeded qualification threshold limit of 50.0 ms",
            matcher=lambda e: (
                e.event_type == "metric_latency" and e.metric_name == "latency_p99_ms" and (e.metric_value or 0) > 50.0
            )
        ),
        SignatureRule(
            signature_id="PCIE_LINK_DOWNGRADE",
            name="PCIe Link Speed/Width Downgrade",
            severity="CRITICAL",
            description="PCIe link retrained to lower width or speed due to electrical signal integrity issues",
            matcher=lambda e: (
                e.signature_id == "PCIE_LINK_DOWN_OR_AER"
                or "pcie link down" in e.message.lower()
            )
        )
    ]
    return rules
