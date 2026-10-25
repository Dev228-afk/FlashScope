import pytest
from flashscope.parsers.fio_parser import normalize_fio_events
from flashscope.parsers.smart_parser import normalize_smart_events
from flashscope.parsers.dmesg_parser import normalize_dmesg_events


def test_normalize_fio_events():
    fio_data = {
        "total_iops": 52000.0,
        "total_bw_mb": 203.12,
        "lat_p99_us": 12500.0,  # 12.5 ms
        "total_errors": 0
    }
    events = normalize_fio_events(fio_data, run_id="r1", case_id="c1")
    assert len(events) == 3
    iops_ev = next(e for e in events if e.metric_name == "total_iops")
    assert iops_ev.metric_value == 52000.0
    lat_ev = next(e for e in events if e.metric_name == "latency_p99_ms")
    assert lat_ev.metric_value == 12.5


def test_normalize_smart_events():
    smart_data = {
        "temperature_c": 79,
        "media_errors": 2,
        "unsafe_shutdowns": 5
    }
    events = normalize_smart_events(smart_data, run_id="r1", case_id="c1")
    assert len(events) == 3
    temp_ev = next(e for e in events if e.metric_name == "temperature_c")
    assert temp_ev.metric_value == 79.0
    assert temp_ev.severity == "WARN"  # >= 75C triggers WARN
    media_ev = next(e for e in events if e.metric_name == "media_errors_count")
    assert media_ev.metric_value == 2.0
    assert media_ev.severity == "CRITICAL"


def test_normalize_dmesg_events():
    dmesg_sample = """
        [  10.123] nvme nvme0: pci function 0000:01:00.0
        [  15.456] nvme nvme0: controller reset triggered by watchdog
        [  18.789] nvme nvme0: 4/0/0 queues ready
    """
    events = normalize_dmesg_events(dmesg_sample, run_id="r1", case_id="c1")
    assert len(events) == 3
    reset_ev = next(e for e in events if e.signature_id == "NVME_CONTROLLER_RESET")
    assert reset_ev.severity == "CRITICAL"
    assert "controller reset" in reset_ev.message.lower()
