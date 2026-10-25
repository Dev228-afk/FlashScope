import pytest
from flashscope.normalize.schema import Event
from flashscope.signatures.engine import SignatureEngine


def test_signature_media_error_detection():
    engine = SignatureEngine()
    ev = Event(
        source="smart",
        event_type="smart_media_errors",
        metric_name="media_errors_count",
        metric_value=4.0
    )
    sig = engine.evaluate_event(ev)
    assert sig == "MEDIA_ERROR"
    assert ev.severity == "CRITICAL"


def test_signature_controller_reset_detection():
    engine = SignatureEngine()
    ev = Event(
        source="dmesg",
        event_type="kernel_log",
        message="nvme0: resetting controller after timeout"
    )
    sig = engine.evaluate_event(ev)
    assert sig == "CONTROLLER_RESET"
    assert ev.severity == "CRITICAL"


def test_signature_thermal_throttle_detection():
    engine = SignatureEngine()
    ev = Event(
        source="smart",
        event_type="metric_temperature",
        metric_value=78.0
    )
    sig = engine.evaluate_event(ev)
    assert sig == "THERMAL_THROTTLE"
    assert ev.severity == "WARN"


def test_signature_latency_regression_detection():
    engine = SignatureEngine()
    ev = Event(
        source="fio",
        event_type="metric_latency",
        metric_name="latency_p99_ms",
        metric_value=65.2
    )
    sig = engine.evaluate_event(ev)
    assert sig == "LATENCY_REGRESSION"
    assert ev.severity == "WARN"
