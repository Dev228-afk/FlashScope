"""
High-throughput synthetic telemetry generator for the 2.3M-record benchmark.
Generates streams of realistic normal operations and injected fault events in memory-efficient batches.
"""

import datetime
from typing import Iterator, List
from flashscope.normalize.schema import Event


def generate_synthetic_event_stream(
    total_records: int = 2300000,
    batch_size: int = 50000,
    fault_frequency: int = 25000
) -> Iterator[List[Event]]:
    """
    Generates batches of synthetic storage telemetry events.
    Injects realistic failure signatures periodically amidst normal fio/SMART/dmesg noise.
    """
    base_time = datetime.datetime(2026, 10, 10, 0, 0, 0, tzinfo=datetime.timezone.utc)
    records_generated = 0

    fault_signatures = [
        ("smart_media_errors", "CRITICAL", "MEDIA_ERROR", "Uncorrectable ECC block read error on NAND page 0x4B210"),
        ("kernel_signature", "CRITICAL", "CONTROLLER_RESET", "nvme0: controller reset triggered by fatal timeout"),
        ("kernel_signature", "ERROR", "IO_TIMEOUT", "nvme0: I/O command 0x1A abort request timed out"),
        ("metric_temperature", "WARN", "THERMAL_THROTTLE", "SMART composite temperature reached 78C throttle limit"),
        ("metric_latency", "WARN", "LATENCY_REGRESSION", "p99 latency spiked to 68.4 ms under heavy load"),
        ("kernel_signature", "CRITICAL", "PCIE_LINK_DOWNGRADE", "PCIe AER reported correctable error, link retrained x2")
    ]

    while records_generated < total_records:
        current_batch_size = min(batch_size, total_records - records_generated)
        batch: List[Event] = []

        for i in range(current_batch_size):
            idx = records_generated + i
            cur_time = (base_time + datetime.timedelta(milliseconds=idx * 10)).isoformat()
            case_id = f"tc_bs4k_qd32_rm70_j1_rand_t{idx // 1000}"

            # Check for periodic injected fault
            if idx > 0 and (idx % fault_frequency == 0):
                sig_tuple = fault_signatures[(idx // fault_frequency) % len(fault_signatures)]
                ev_type, sev, sig_id, msg = sig_tuple
                batch.append(Event(
                    event_id=f"ev_fault_{idx}",
                    run_id="bench_run_2300k",
                    case_id=case_id,
                    timestamp=cur_time,
                    source="dmesg" if "kernel" in ev_type else ("smart" if "smart" in ev_type else "fio"),
                    device_id="nvme0",
                    firmware="REV_1.0_PROD",
                    severity=sev,
                    event_type=ev_type,
                    metric_name="media_errors_count" if "smart" in ev_type else None,
                    metric_value=1.0 if "smart" in ev_type else None,
                    message=msg,
                    signature_id=sig_id
                ))
            else:
                # Normal operational background noise (fio, smart, dmesg)
                mod = idx % 3
                if mod == 0:
                    batch.append(Event(
                        event_id=f"ev_fio_{idx}",
                        run_id="bench_run_2300k",
                        case_id=case_id,
                        timestamp=cur_time,
                        source="fio",
                        device_id="nvme0",
                        firmware="REV_1.0_PROD",
                        severity="INFO",
                        event_type="metric_iops",
                        metric_name="total_iops",
                        metric_value=24500.0 + (idx % 500),
                        unit="IOPS",
                        message=f"Steady state I/O sample #{idx}"
                    ))
                elif mod == 1:
                    batch.append(Event(
                        event_id=f"ev_smart_{idx}",
                        run_id="bench_run_2300k",
                        case_id=case_id,
                        timestamp=cur_time,
                        source="smart",
                        device_id="nvme0",
                        firmware="REV_1.0_PROD",
                        severity="INFO",
                        event_type="metric_temperature",
                        metric_name="temperature_c",
                        metric_value=42.0 + (idx % 5),
                        unit="C",
                        message="Routine SMART telemetry poll"
                    ))
                else:
                    batch.append(Event(
                        event_id=f"ev_dmesg_{idx}",
                        run_id="bench_run_2300k",
                        case_id=case_id,
                        timestamp=cur_time,
                        source="dmesg",
                        device_id="nvme0",
                        firmware="REV_1.0_PROD",
                        severity="INFO",
                        event_type="kernel_log",
                        message=f"nvme0: queue {idx % 8} I/O completion nominal"
                    ))

        records_generated += current_batch_size
        yield batch
