"""
PitchPulse 360 - Dead Letter Queue (DLQ) Module (CO3 & Lab 10)
Handles corrupted, out-of-order, or schema-violating event payloads.
Safely quarantines malformed records to prevent downstream pipeline crashes.
Provides replay and error diagnostics capabilities.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List

class DeadLetterQueue:
    def __init__(self, dlq_dir: str = "data/dlq"):
        self.dlq_dir = dlq_dir
        os.makedirs(self.dlq_dir, exist_ok=True)
        self.quarantine_file = os.path.join(self.dlq_dir, "quarantined_events.jsonl")

    def route_to_dlq(self, payload: Any, error_reason: str, source: str = "event_streamer") -> Dict[str, Any]:
        """
        Quarantines a malformed payload into the DLQ with full diagnostic metadata.
        """
        dlq_entry = {
            "quarantine_id": f"dlq_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": source,
            "error_reason": error_reason,
            "raw_payload": payload
        }

        with open(self.quarantine_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(dlq_entry) + "\n")

        print(f"[DLQ Alert] Quarantined corrupted event: {error_reason}")
        return dlq_entry

    def get_quarantined_count(self) -> int:
        if not os.path.exists(self.quarantine_file):
            return 0
        with open(self.quarantine_file, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def inspect_quarantine(self, limit: int = 10) -> List[Dict[str, Any]]:
        if not os.path.exists(self.quarantine_file):
            return []
        items = []
        with open(self.quarantine_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items[-limit:]

    def replay_quarantined(self) -> List[Dict[str, Any]]:
        """
        Reads quarantined records for potential recovery/replay after fixing upstream bugs.
        """
        items = self.inspect_quarantine(limit=1000)
        print(f"[DLQ Replay] Loaded {len(items)} quarantined items for inspection.")
        return items

if __name__ == "__main__":
    dlq = DeadLetterQueue()
    dlq.route_to_dlq({"broken": "packet"}, "Missing mandatory 'period' attribute")
    print(f"Total quarantined: {dlq.get_quarantined_count()}")
