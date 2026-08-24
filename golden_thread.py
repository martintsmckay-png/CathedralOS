import hashlib
import json
from pathlib import Path


def canonical_bytes(data):
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def seal_ledger_file(path):
    ledger_path = Path(path)
    data = json.loads(ledger_path.read_text(encoding="utf-8"))

    golden_thread = data.setdefault("golden_thread", {})
    golden_thread["event_hash"] = ""

    digest = hashlib.sha256(canonical_bytes(data)).hexdigest()
    golden_thread["event_hash"] = digest

    ledger_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\
",
        encoding="utf-8",
    )

    return digest
