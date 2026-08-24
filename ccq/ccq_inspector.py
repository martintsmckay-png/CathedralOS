#!/usr/bin/env python3

import json
from pathlib import Path

QUARANTINE_DIR = Path("ccq_quarantine")


def list_quarantine_artifacts():
    if not QUARANTINE_DIR.exists():
        return []
    return sorted(QUARANTINE_DIR.glob("*.json"))


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def inspect_artifact(path):
    path = Path(path)
    data = load_json(path)

    if data is None or not isinstance(data, dict):
        return None

    return {
        "filename": path.name,
        "traveler": data.get("traveler"),
        "decision": data.get("decision"),
        "passport": data.get("passport", {}),
        "xray": data.get("xray", {}),
        "hospitality_packet": data.get(
            "hospitality_packet", data.get("hospitalitypacket", {})
        ),
        "golden_thread": data.get(
            "golden_thread", data.get("goldenthread", {})
        ),
    }


def print_artifact_report(report):
    print(f"\n=== CCQ Artifact Report: {report['filename']} ===")
    print(f"Traveler: {report.get('traveler')}")
    print(f"Decision: {report.get('decision')}\n")

    print("Passport:")
    print(json.dumps(report.get("passport", {}), indent=2, ensure_ascii=False))

    print("\nX-Ray Findings:")
    print(json.dumps(report.get("xray", {}), indent=2, ensure_ascii=False))

    print("\nHospitality Packet:")
    print(
        json.dumps(
            report.get("hospitality_packet", {}), indent=2, ensure_ascii=False
        )
    )

    print("\nGolden Thread:")
    print(
        json.dumps(
            report.get("golden_thread", {}), indent=2, ensure_ascii=False
        )
    )
    print("============================================\n")


def main():
    artifacts = list_quarantine_artifacts()
    print(f"[CCQ INSPECTOR] Pending artifacts in quarantine: {len(artifacts)}")

    if not artifacts:
        return

    for artifact in artifacts:
        print(f" - {artifact.name}")


if __name__ == "__main__":
    main()
