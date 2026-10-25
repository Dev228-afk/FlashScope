"""
Timeline builder reconstructing chronological event progressions around failure events.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from flashscope.normalize.schema import Event


@dataclass
class TimelineEntry:
    timestamp: str
    relative_seconds: float
    source: str
    severity: str
    event_type: str
    signature_id: Optional[str]
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_first_failure_timeline(events: List[Event], target_case_id: Optional[str] = None) -> List[TimelineEntry]:
    """Constructs an ordered timeline of events leading up to and following the initial fault onset."""
    filtered = [e for e in events if not target_case_id or e.case_id == target_case_id]
    if not filtered:
        return []

    # Sort chronologically
    filtered.sort(key=lambda x: x.timestamp or "")

    # Locate first critical/error signature event as T0
    t0_idx = -1
    for i, e in enumerate(filtered):
        if e.signature_id or e.severity in ("ERROR", "CRITICAL"):
            t0_idx = i
            break

    if t0_idx == -1:
        t0_idx = 0

    timeline: List[TimelineEntry] = []
    # Relative timing offset simulation (in seconds)
    for idx, e in enumerate(filtered):
        rel_sec = float((idx - t0_idx) * 2)  # 2 second intervals if timestamps identical
        timeline.append(TimelineEntry(
            timestamp=e.timestamp or f"T+{rel_sec:.0f}s",
            relative_seconds=rel_sec,
            source=e.source,
            severity=e.severity,
            event_type=e.event_type,
            signature_id=e.signature_id,
            description=e.message
        ))

    return timeline
