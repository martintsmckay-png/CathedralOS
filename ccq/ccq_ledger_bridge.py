#!/usr/bin/env python3

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ledger_rotation import append_entry, rotate_ledger, should_rotate


def canonical_bytes(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def event_hash(event):
    unsigned = dict(event)
    unsigned.pop("event_hash", None)
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def record_ccq_event(event, max_entries=512):
    recorded = dict(event)
    recorded.setdefault(
        "timestamp",
        datetime.now(timezone.utc).isoformat(),
    )
    recorded["event_hash"] = event_hash(recorded)

    append_entry(recorded)

    digest = ""
    if should_rotate(max_entries):
        digest = rotate_ledger(max_entries)

    print(f"[CCQ] Recorded event: {recorded['event_hash']}")
    if digest:
        print(f"[ROTATED] Sealed segment -> {digest}")

    return recorded, digest


if __name__ == "__main__":
    record_ccq_event({
        "traveler": "test-artifact",
        "decision": "PROMOTED",
        "source": "ccq",
    })
