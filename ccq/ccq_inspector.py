#!/usr/bin/env python3

import json
import hashlib
from pathlib import Path

QUARANTINE_DIR = Path("ccq_quarantine")

def list_quarantine_artifacts():
    if not QUARANTINE_DIR.exists():
        return []
    return sorted(QUARANTINE_DIR.glob("*.json"))

def load_artifact(artifact_path):
    try:
        with artifact_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

def verify_golden_thread(report):
    gt = report.get("golden_thread", {})
    event_hash = gt.get("event_hash") or gt.get("eventhash")

    if not event_hash:
        return {
            "status": "MISSING",
            "expected": None,
            "actual": None
        }

    unsigned = {k: v for k, v in report.items() if k != "golden_thread"}
    canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = hashlib.sha256(canonical).hexdigest()

    status = "OK" if expected == event_hash else "FAIL"

    return {
        "status": status,
        "expected": expected,
        "actual": event_hash
    }

def inspect_artifact(artifact_path):
    data = load_artifact(artifact_path)
    if not data:
        return None

    data["golden_thread_verification"] = verify_golden_thread(data)
    return data

def print_artifact_report(report):
    traveler = report.get("traveler", "unknown")
    verification = report.get("golden_thread_verification", {})
    
    status_colors = {
        "OK": "\033[32m[PASS]\033[0m",
        "FAIL": "\033[31m[CRITICAL_FAIL]\033[0m",
        "MISSING": "\033[33m[UNSEALED]\033[0m"
    }

    print(f"Artifact: \033[36m{traveler}\033[0m")
    print(f"Golden Thread Status: {status_colors.get(verification['status'], '[UNKNOWN]')}")
    if verification['status'] == "FAIL":
        print(f"  Expected: {verification['expected']}")
        print(f"  Actual:   {verification['actual']}")
    print()
