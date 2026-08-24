#!/usr/bin/env python3

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from ledger_rotation import (
    load_current_ledger,
    rotate_ledger,
    should_rotate,
)
from ccq.ccq_ledger_bridge import record_ccq_event
from ccq.ccq_inspector import (
    list_quarantine_artifacts,
    inspect_artifact,
    print_artifact_report,
)


LEDGER_DIR = Path("ledger")
CURRENT = LEDGER_DIR / "ledger-current.json"


def clear_screen():
    os.system("clear")


def banner():
    print("=" * 46)
    print("          CATHEDRALOS STEWARD CONSOLE")
    print("=" * 46)
    print(
        "Time:",
        datetime.now(timezone.utc).isoformat(),
    )
    print()


def show_current_segment():
    print(">> CURRENT LEDGER SEGMENT")

    if not CURRENT.exists():
        print("No ledger-current.json found.")
        return

    try:
        data = load_current_ledger()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as exc:
        print(f"Invalid ledger JSON: {exc}")

    print()


def show_segments():
    print(">> ARCHIVED SEGMENTS")

    if not LEDGER_DIR.exists():
        print("No ledger directory found.")
        return

    segments = sorted(LEDGER_DIR.glob("ledger-*.json"))

    if not segments:
        print("No archived segments found.")
    else:
        for path in segments:
            print(f"- {path.name}")

    print()


def show_status():
    print(">> LEDGER STATUS")

    ledger = load_current_ledger()
    entries = ledger.get("entries", [])

    print(f"Current segment: {ledger.get('segment', 1)}")
    print(f"Entries: {len(entries)}")
    print(f"Rotation threshold reached: {should_rotate()}")
    print("Previous hash:", ledger.get("previous_sha256"))
    print()


def rotate_now():
    print(">> ROTATION REQUESTED")

    digest = rotate_ledger()

    if digest:
        print(f"[ROTATED] Sealed segment -> {digest}")
    else:
        print("[ROTATION] No entries; nothing to rotate.")

    print()


def record_test_event():
    print(">> RECORDING TEST CCQ EVENT")

    event, digest = record_ccq_event({
        "traveler": "test-artifact",
        "decision": "PROMOTED",
        "source": "steward_console",
    })

    print(f"[CCQ] Event hash: {event['event_hash']}")

    if digest:
        print(f"[ROTATED] Segment hash: {digest}")

    print()


def inspect_quarantine():
    print(">> CCQ QUARANTINE ANALYSIS")

    artifacts = list_quarantine_artifacts()

    if not artifacts:
        print("No pending quarantine artifacts.")
        print()
        return

    for path in artifacts:
        report = inspect_artifact(path)
        if report:
            print_artifact_report(report)
        else:
            print(f"Could not load artifact: {path.name}")

    print()


def pause():
    input("Press Enter to return...")


def main_menu():
    while True:
        clear_screen()
        banner()

        print("1. View current ledger segment")
        print("2. View archived segments")
        print("3. View ledger status")
        print("4. Rotate ledger now")
        print("5. Record test CCQ event")
        print("6. Inspect CCQ quarantine")
        print("7. Exit")
        print()

        choice = input("Select option: ").strip()

        if choice == "1":
            clear_screen()
            show_current_segment()
            pause()
        elif choice == "2":
            clear_screen()
            show_segments()
            pause()
        elif choice == "3":
            clear_screen()
            show_status()
            pause()
        elif choice == "4":
            clear_screen()
            rotate_now()
            pause()
        elif choice == "5":
            clear_screen()
            record_test_event()
            pause()
        elif choice == "6":
            clear_screen()
            inspect_quarantine()
            pause()
        elif choice == "7":
            print("Exiting Steward Console.")
            break
        else:
            input("Invalid option. Press Enter to continue...")


if __name__ == "__main__":
    main_menu()
