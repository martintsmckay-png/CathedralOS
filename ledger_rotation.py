#!/usr/bin/env python3

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


LEDGER_DIR = Path("ledger")
CURRENT_LEDGER = LEDGER_DIR / "ledger-current.json"


def canonical_bytes(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


def load_current_ledger():
    if not CURRENT_LEDGER.exists():
        return {
            "segment": 1,
            "entries": [],
            "previous_sha256": None,
        }

    return json.loads(
        CURRENT_LEDGER.read_text(encoding="utf-8")
    )


def save_current_ledger(data):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    content = f"{json.dumps(data, indent=2, ensure_ascii=False)}\n"
    CURRENT_LEDGER.write_text(content, encoding="utf-8")


def append_entry(entry):
    ledger = load_current_ledger()
    ledger.setdefault("entries", []).append(entry)
    save_current_ledger(ledger)


def rotate_ledger(max_entries=512):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    ledger = load_current_ledger()
    entries = ledger.get("entries", [])

    if not entries:
        return ""

    digest = sha256_hex(canonical_bytes(ledger))
    segment_id = int(ledger.get("segment", 1))

    archive_path = LEDGER_DIR / f"ledger-{segment_id:05d}.json"

    if archive_path.exists():
        raise FileExistsError(
            f"Archive already exists: {archive_path}"
        )

    archive_payload = {
        "segment": segment_id,
        "entries": entries,
        "previous_sha256": ledger.get("previous_sha256"),
        "sha256": digest,
        "segment_closed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    archive_content = f"{json.dumps(archive_payload, indent=2, ensure_ascii=False)}\n"
    archive_path.write_text(archive_content, encoding="utf-8")

    save_current_ledger({
        "segment": segment_id + 1,
        "entries": [],
        "previous_sha256": digest,
    })

    return digest


def should_rotate(max_entries=512):
    ledger = load_current_ledger()
    return len(ledger.get("entries", [])) >= max_entries


if __name__ == "__main__":
    if should_rotate():
        digest = rotate_ledger()
        print(f"[ROTATED] Sealed segment -> {digest}")
    else:
        print("[LEDGER] Rotation not required; below threshold.")
