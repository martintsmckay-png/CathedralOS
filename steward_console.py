#!/usr/bin/env python3

import json
import os
import shutil
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
QUARANTINE_DIR = Path("ccq_quarantine")
DECISION_DIR = Path("ccq_decisions")


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


def archive_artifact(artifact_path, decision):
    DECISION_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = (
        DECISION_DIR / f"{timestamp}-{decision.lower()}-{artifact_path.name}"
    )

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    return Path(shutil.move(str(artifact_path), str(destination)))


def artifact_actions_menu(artifact_path):
    print(f">> CCQ ARTIFACT ACTIONS - {artifact_path.name}")

    report = inspect_artifact(artifact_path)

    if not report:
        print("Could not load artifact.")
        print()
        return

    print_artifact_report(report)
    print()

    while True:
        print("Actions:")
        print("1. Approve artifact")
        print("2. Reject artifact")
        print("3. Promote artifact")
        print("4. Return")
        print()

        action = input("Select action: ").strip()

        decisions = {
            "1": "APPROVED",
            "2": "REJECTED",
            "3": "PROMOTED",
        }

        if action == "4":
            return

        decision = decisions.get(action)

        if decision is None:
            input("Invalid option. Press Enter to continue...")
            continue

        event = {
            "traveler": report.get("traveler"),
            "decision": decision,
            "source": "steward_console",
            "artifact": artifact_path.name,
            "passport": report.get("passport", {}),
            "xray": report.get("xray", {}),
            "hospitality_packet": report.get("hospitality_packet", {}),
            "golden_thread": report.get("golden_thread", {}),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            recorded_event, digest = record_ccq_event(event)
            archived_path = archive_artifact(artifact_path, decision)
        except Exception as exc:
            print(f"[FAILED] Action was not completed: {exc}")
            input("Press Enter to continue...")
            continue

        print(f"[CCQ] {decision}: {recorded_event['event_hash']}")
        print(f"[ARCHIVED] {archived_path}")

        if digest:
            print(f"[ROTATED] Segment hash: {digest}")

        print()
        return


def select_quarantine_artifact():
    print(">> CCQ QUARANTINE - SELECT ARTIFACT")

    artifacts = list_quarantine_artifacts()

    if not artifacts:
        print("No pending quarantine artifacts.")
        print()
        return

    for index, artifact_path in enumerate(artifacts, start=1):
        print(f"{index}. {artifact_path.name}")

    print()
    choice = input("Select artifact number (or press Enter to cancel): ").strip()

    if not choice:
        print("Cancelled.")
        print()
        return

    if not choice.isdigit():
        print("Invalid selection.")
        print()
        return

    index = int(choice)

    if index < 1 or index > len(artifacts):
        print("Selection out of range.")
        print()
        return

    artifact_path = artifacts[index - 1]
    artifact_actions_menu(artifact_path)


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
            while True:
                clear_screen()
                banner()

                print(">> CCQ QUARANTINE MENU")
                print("1. View all artifact reports")
                print("2. Select a single artifact")
                print("3. Return to main menu")
                print()

                sub_choice = input("Select option: ").strip()

                if sub_choice == "1":
                    clear_screen()
                    inspect_quarantine()
                    pause()
                elif sub_choice == "2":
                    clear_screen()
                    select_quarantine_artifact()
                    pause()
                elif sub_choice == "3":
                    break
                else:
                    input("Invalid option. Press Enter to continue...")

        elif choice == "7":
            print("Exiting Steward Console.")
            break
        else:
            input("Invalid option. Press Enter to continue...")


if __name__ == "__main__":
    main_menu()
