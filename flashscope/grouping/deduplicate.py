"""
Incident deduplication and grouping engine consolidating cascaded failure events.
"""

from collections import defaultdict
from typing import List, Dict
import uuid
from flashscope.normalize.schema import Event, Incident


class IncidentDeduplicator:
    def group_events_into_incidents(self, events: List[Event]) -> List[Incident]:
        """
        Groups signature-matched events by (run_id, case_id, signature_id) into consolidated incidents.
        Preserves occurrence counts and links all raw evidence events.
        """
        grouped: Dict[tuple, List[Event]] = defaultdict(list)

        for e in events:
            if e.signature_id:
                key = (e.run_id, e.case_id, e.signature_id)
                grouped[key].append(e)

        incidents: List[Incident] = []

        for (run_id, case_id, sig_id), ev_list in grouped.items():
            ev_list.sort(key=lambda x: x.timestamp or "")
            first_ts = ev_list[0].timestamp or "unknown"
            last_ts = ev_list[-1].timestamp or first_ts

            # Multi-source corroboration increases confidence
            sources = {e.source for e in ev_list}
            confidence = 1.0 if len(sources) > 1 else 0.90

            severity = ev_list[0].severity
            summary = f"{sig_id}: {len(ev_list)} events observed across sources ({', '.join(sorted(sources))})"

            inc = Incident(
                incident_id=f"inc_{sig_id.lower()}_{uuid.uuid4().hex[:8]}",
                run_id=run_id,
                case_id=case_id,
                signature_id=sig_id,
                severity=severity,
                confidence=confidence,
                occurrence_count=len(ev_list),
                first_timestamp=first_ts,
                last_timestamp=last_ts,
                summary=summary,
                status="OPEN",
                evidence_event_ids=[e.event_id for e in ev_list]
            )
            incidents.append(inc)

        return incidents
