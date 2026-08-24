import hashlib
import json
import time
from pathlib import Path


LEDGER_DIR = Path("ledger")
CURRENT_LEDGER = LEDGER_DIR / "ledger-current.json"
ENTRY_LIMIT = 50
GENESIS_HASH = "0" * 64


def canonical_bytes(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def segment_hash(data):
    unsigned = dict(data)
    unsigned.pop("sha256", None)
    return hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def init_ledger():
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    if not CURRENT_LEDGER.exists():
        initial_state = {
            "segment": 1,
            "previous_sha256": GENESIS_HASH,
            "created_at": time.time(),
            "entries": [],
        }
        CURRENT_LEDGER.write_text(
            json.dumps(initial_state, indent=2, ensure_ascii=False) + "
",
            encoding="utf-8",
        )


def rotate_ledger(force=False):
    init_ledger()

    data = json.loads(CURRENT_LEDGER.read_text(encoding="utf-8"))
    entries = data.get("entries", [])

    if not entries and not force:
        print("[ROTATION] No entries to rotate.")
        return None

    segment_id = int(data.get("segment", 1))
    digest = segment_hash(data)

    sealed = dict(data)
    sealed["sha256"] = digest

    archive_path = LEDGER_DIR / f"ledger-{segment_id:05d}.json"

    if archive_path.exists():
        raise FileExistsError(f"Archive already exists: {archive_path}")

    archive_path.write_text(
        json.dumps(sealed, indent=2, ensure_ascii=False) + "
",
        encoding="utf-8",
    )

    new_segment = {
        "segment": segment_id + 1,
        "previous_sha256": digest,
        "created_at": time.time(),
        "entries": [],
    }

    CURRENT_LEDGER.write_text(
        json.dumps(new_segment, indent=2, ensure_ascii=False) + "
",
        encoding="utf-8",
    )

    print(f"[ROTATED] Sealed segment {segment_id} -> {archive_path}")
    print(f"[SHA256] {digest}")
    return digest


def append_entry(entry):
    init_ledger()

    data = json.loads(CURRENT_LEDGER.read_text(encoding="utf-8"))
    data.setdefault("entries", []).append(entry)

    CURRENT_LEDGER.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "
",
        encoding="utf-8",
    )

    if len(data["entries"]) >= ENTRY_LIMIT:
        return rotate_ledger()

    return None


if __name__ == "__main__":
    rotate_ledger()
