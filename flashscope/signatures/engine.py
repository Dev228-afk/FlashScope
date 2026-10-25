"""
Signature evaluation engine scanning normalized events against failure patterns.
"""

from typing import List, Optional
from flashscope.normalize.schema import Event
from flashscope.signatures.rules import SignatureRule, get_default_signature_rules


class SignatureEngine:
    def __init__(self, rules: Optional[List[SignatureRule]] = None):
        self.rules = rules or get_default_signature_rules()

    def evaluate_event(self, event: Event) -> Optional[str]:
        """Evaluates an event against rules and returns the matched signature_id if any."""
        for r in self.rules:
            if r.matcher(event):
                event.signature_id = r.signature_id
                event.severity = r.severity
                return r.signature_id
        return None

    def evaluate_events_batch(self, events: List[Event]) -> int:
        """Evaluates a batch of events in-place, returning count of matched signatures."""
        matches = 0
        for ev in events:
            if self.evaluate_event(ev):
                matches += 1
        return matches
