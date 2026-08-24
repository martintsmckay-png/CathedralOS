#!/usr/bin/env python3

import json
from pathlib import Path

QUARANTINE_DIR = Path("ccq/quarantine")


def list_quarantine_artifacts():
    if not QUARANTINE_DIR.exists():
        return []
    return sorted(QUARANTINE_DIR.glob("*.json"))


def inspect_artifact(filepath):
    path = Path(filepath)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    artifacts = list_quarantine_artifacts()
    print(f"[CCQ INSPECTOR] Pending artifacts in quarantine: {len(artifacts)}")
    for a in artifacts:
        print(f" - {a.name}")
