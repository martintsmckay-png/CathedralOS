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


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"

    @staticmethod
    def wrap(text, color):
        return f"{color}{text}{Color.RESET}"


def clear_screen():
    os.system("clear")


def banner():
    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap("          CATHEDRALOS STEWARD CONSOLE", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))
    print(
        "Time:",
        datetime.now(timezone.utc).isoformat(),
    )
    print()


def show_current_segment():
    print(Color.wrap(">> CURRENT LEDGER SEGMENT", Color.CYAN))

    if not CURRENT.exists():
        print(Color.wrap("No ledger-current.json found.", Color.YELLOW))
        return

    try:
        data = load_current_ledger()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError as exc:
        print(Color.wrap(f"Invalid ledger JSON: {exc}", Color.RED))

    print()


def show_segments():
    print(Color.wrap(">> ARCHIVED SEGMENTS", Color.CYAN))

    if not LEDGER_DIR.exists():
        print(Color.wrap("No ledger directory found.", Color.YELLOW))
        return

    segments = sorted(LEDGER_DIR.glob("ledger-*.json"))

    if not segments:
        print(Color.wrap("No archived segments found.", Color.YELLOW))
    else:
        for path in segments:
            print(f"- {path.name}")

    print()


def show_status():
    print(Color.wrap(">> LEDGER STATUS", Color.CYAN))

    ledger = load_current_ledger()
    entries = ledger.get("entries", [])

    print(f"Current segment: {ledger.get('segment', 1)}")
    print(f"Entries: {len(entries)}")
    print(f"Rotation threshold reached: {should_rotate()}")
    print("Previous hash:", ledger.get("previous_sha256"))
    print()


def rotate_now():
    print(Color.wrap(">> ROTATION REQUESTED", Color.CYAN))

    digest = rotate_ledger()

    if digest:
        print(Color.wrap(f"[ROTATED] Sealed segment -> {digest}", Color.CYAN))
    else:
        print(Color.wrap("[ROTATION] No entries; nothing to rotate.", Color.YELLOW))

    print()


def record_test_event():
    print(Color.wrap(">> RECORDING TEST CCQ EVENT", Color.CYAN))

    event, digest = record_ccq_event({
        "traveler": "test-artifact",
        "decision": "PROMOTED",
        "source": "steward_console",
    })

    print(Color.wrap(f"[CCQ] Event hash: {event['event_hash']}", Color.BLUE))

    if digest:
        print(Color.wrap(f"[ROTATED] Segment hash: {digest}", Color.CYAN))

    print()


def render_passport_panel(report):
    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap("              ARTIFACT PASSPORT", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))

    traveler = report.get("traveler", "unknown")
    passport = report.get("passport", {})
    xray = report.get("xray", {})
    hospitality_packet = report.get("hospitality_packet", {})
    golden_thread = report.get("golden_thread", {})

    print(f"Traveler: {Color.wrap(traveler, Color.YELLOW)}")
    print()

    print(Color.wrap("PASSPORT:", Color.BLUE))
    if passport:
        for key, value in passport.items():
            print(f"  - {key}: {value}")
    else:
        print("  (none)")
    print()

    print(Color.wrap("X-RAY:", Color.BLUE))
    if xray:
        for key, value in xray.items():
            print(f"  - {key}: {value}")
    else:
        print("  (none)")
    print()

    print(Color.wrap("HOSPITALITY PACKET:", Color.BLUE))
    if hospitality_packet:
        for key, value in hospitality_packet.items():
            print(f"  - {key}: {value}")
    else:
        print("  (none)")
    print()

    print(Color.wrap("GOLDEN THREAD:", Color.BLUE))
    if golden_thread:
        for key, value in golden_thread.items():
            print(f"  - {key}: {value}")
    else:
        print("  (none)")
    print()

    print(Color.wrap("=" * 46, Color.CYAN))
    print()


def inspect_quarantine():
    print(Color.wrap(">> CCQ QUARANTINE ANALYSIS", Color.CYAN))

    artifacts = list_quarantine_artifacts()

    if not artifacts:
        print(Color.wrap("No pending quarantine artifacts.", Color.YELLOW))
        print()
        return

    for path in artifacts:
        report = inspect_artifact(path)
        if report:
            print_artifact_report(report)
            render_passport_panel(report)
        else:
            print(Color.wrap(f"Could not load artifact: {path.name}", Color.RED))

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
    print(Color.wrap(f">> CCQ ARTIFACT ACTIONS - {artifact_path.name}", Color.CYAN))

    report = inspect_artifact(artifact_path)

    if not report:
        print(Color.wrap("Could not load artifact.", Color.RED))
        print()
        return

    print_artifact_report(report)
    render_passport_panel(report)
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
            input(Color.wrap("Invalid option. Press Enter to continue...", Color.YELLOW))
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
            print(Color.wrap(f"[FAILED] Action was not completed: {exc}", Color.RED))
            input("Press Enter to continue...")
            continue

        decision_color = {
            "APPROVED": Color.GREEN,
            "REJECTED": Color.RED,
            "PROMOTED": Color.BLUE,
        }.get(decision, Color.CYAN)

        print(Color.wrap(f"[CCQ] {decision}: {recorded_event['event_hash']}", decision_color))
        print(Color.wrap(f"[ARCHIVED] {archived_path}", Color.MAGENTA))

        if digest:
            print(Color.wrap(f"[ROTATED] Segment hash: {digest}", Color.CYAN))

        print()
        return


def select_quarantine_artifact():
    print(Color.wrap(">> CCQ QUARANTINE - SELECT ARTIFACT", Color.CYAN))

    artifacts = list_quarantine_artifacts()

    if not artifacts:
        print(Color.wrap("No pending quarantine artifacts.", Color.YELLOW))
        print()
        return

    for index, artifact_path in enumerate(artifacts, start=1):
        print(f"{index}. {Color.wrap(artifact_path.name, Color.YELLOW)}")

    print()
    choice = input("Select artifact number (or press Enter to cancel): ").strip()

    if not choice:
        print("Cancelled.")
        print()
        return

    if not choice.isdigit():
        print(Color.wrap("Invalid selection.", Color.YELLOW))
        print()
        return

    index = int(choice)

    if index < 1 or index > len(artifacts):
        print(Color.wrap("Selection out of range.", Color.YELLOW))
        print()
        return

    artifact_path = artifacts[index - 1]
    artifact_actions_menu(artifact_path)


def explore_segments():
    print(Color.wrap(">> LEDGER SEGMENT EXPLORER", Color.CYAN))
    print()

    segments = sorted(LEDGER_DIR.glob("ledger-*.json"))
    if not segments:
        print(Color.wrap("No archived ledger segments found.", Color.YELLOW))
        print()
        return

    for idx, seg_path in enumerate(segments, start=1):
        print(f"{idx}. {Color.wrap(seg_path.name, Color.YELLOW)}")

    print()
    choice = input("Select segment number (or press Enter to cancel): ").strip()

    if not choice:
        print(Color.wrap("Cancelled.", Color.YELLOW))
        print()
        return

    if not choice.isdigit():
        print(Color.wrap("Invalid selection.", Color.RED))
        print()
        return

    index = int(choice)
    if index < 1 or index > len(segments):
        print(Color.wrap("Selection out of range.", Color.YELLOW))
        print()
        return

    seg_path = segments[index - 1]

    try:
        with seg_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(Color.wrap(f"Could not load segment: {exc}", Color.RED))
        print()
        return

    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap(f"        SEGMENT {data.get('segment')}", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))
    print(f"Previous hash: {data.get('previous_sha256')}")
    print(f"Entries: {len(data.get('entries', []))}")
    print()

    for idx, entry in enumerate(data.get("entries", []), start=1):
        print(Color.wrap(f"Entry {idx}", Color.BLUE))
        print(f"  Traveler: {entry.get('traveler')}")
        print(f"  Decision: {Color.wrap(entry.get('decision'), Color.YELLOW)}")
        print(f"  Event Hash: {Color.wrap(entry.get('event_hash'), Color.MAGENTA)}")
        print(f"  Timestamp: {entry.get('timestamp')}")
        print()

    print(Color.wrap("=" * 46, Color.CYAN))
    print()


def trace_golden_thread():
    print(Color.wrap(">> GOLDEN THREAD TRACE", Color.CYAN))
    print()

    event_hash = input("Enter event hash to trace: ").strip()

    if not event_hash:
        print(Color.wrap("Cancelled.", Color.YELLOW))
        print()
        return

    segments = sorted(LEDGER_DIR.glob("ledger-*.json"))
    if CURRENT.exists():
        segments.append(CURRENT)

    trace_results = []

    for seg_path in segments:
        try:
            with seg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue

        for entry in data.get("entries", []):
            if entry.get("event_hash") == event_hash:
                trace_results.append({
                    "segment": data.get("segment"),
                    "timestamp": entry.get("timestamp"),
                    "decision": entry.get("decision"),
                    "traveler": entry.get("traveler"),
                    "path": seg_path.name,
                })

    if not trace_results:
        print(Color.wrap("No matching event found in any ledger segment.", Color.RED))
        print()
        return

    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap("           GOLDEN THREAD TRACE", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))

    for item in trace_results:
        print(Color.wrap(f"Segment: {item['segment']}", Color.BLUE))
        print(f"  Path: {item['path']}")
        print(f"  Traveler: {item['traveler']}")
        print(f"  Decision: {Color.wrap(item['decision'], Color.YELLOW)}")
        print(f"  Timestamp: {item['timestamp']}")
        print()

    print(Color.wrap("=" * 46, Color.CYAN))
    print()


def explore_decision_history():
    print(Color.wrap(">> CCQ DECISION HISTORY", Color.CYAN))
    print()

    if not DECISION_DIR.exists():
        print(Color.wrap("No decision archive directory found.", Color.YELLOW))
        print()
        return

    decisions = sorted(DECISION_DIR.glob("*.json"))
    if not decisions:
        print(Color.wrap("No archived decisions found.", Color.YELLOW))
        print()
        return

    for idx, path in enumerate(decisions, start=1):
        print(f"{idx}. {Color.wrap(path.name, Color.YELLOW)}")

    print()
    choice = input("Select decision file (or press Enter to cancel): ").strip()

    if not choice:
        print(Color.wrap("Cancelled.", Color.YELLOW))
        print()
        return

    if not choice.isdigit():
        print(Color.wrap("Invalid selection.", Color.RED))
        print()
        return

    index = int(choice)
    if index < 1 or index > len(decisions):
        print(Color.wrap("Selection out of range.", Color.YELLOW))
        print()
        return

    decision_path = decisions[index - 1]

    try:
        with decision_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(Color.wrap(f"Could not load decision file: {exc}", Color.RED))
        print()
        return

    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap("           DECISION RECORD", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))

    print(f"File: {decision_path.name}")
    print(f"Traveler: {data.get('traveler')}")
    print(f"Decision: {Color.wrap(data.get('decision'), Color.YELLOW)}")
    print(f"Timestamp: {data.get('timestamp')}")
    print(f"Source: {data.get('source')}")
    print(
        f"Event Hash: "
        f"{Color.wrap(data.get('event_hash', '(none)'), Color.MAGENTA)}"
    )
    print()

    render_passport_panel(data)

    print(Color.wrap("=" * 46, Color.CYAN))
    print()


def diff_segments():
    print(Color.wrap(">> LEDGER SEGMENT DIFF", Color.CYAN))
    print()

    segments = sorted(LEDGER_DIR.glob("ledger-*.json"))
    if len(segments) < 2:
        print(Color.wrap("Need at least two segments to diff.", Color.YELLOW))
        print()
        return

    for idx, seg_path in enumerate(segments, start=1):
        print(f"{idx}. {Color.wrap(seg_path.name, Color.YELLOW)}")

    print()
    first = input("Select FIRST segment: ").strip()
    second = input("Select SECOND segment: ").strip()

    if not first or not second:
        print(Color.wrap("Cancelled.", Color.YELLOW))
        print()
        return

    if not first.isdigit() or not second.isdigit():
        print(Color.wrap("Invalid selection.", Color.RED))
        print()
        return

    i1, i2 = int(first), int(second)
    if i1 < 1 or i1 > len(segments) or i2 < 1 or i2 > len(segments):
        print(Color.wrap("Selection out of range.", Color.YELLOW))
        print()
        return

    seg1 = segments[i1 - 1]
    seg2 = segments[i2 - 1]

    try:
        with seg1.open("r", encoding="utf-8") as f:
            data1 = json.load(f)
        with seg2.open("r", encoding="utf-8") as f:
            data2 = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(Color.wrap(f"Could not load segments: {exc}", Color.RED))
        print()
        return

    entries1 = {
        e.get("event_hash"): e
        for e in data1.get("entries", [])
        if e.get("event_hash")
    }
    entries2 = {
        e.get("event_hash"): e
        for e in data2.get("entries", [])
        if e.get("event_hash")
    }

    added = [entries2[h] for h in entries2.keys() - entries1.keys()]
    removed = [entries1[h] for h in entries1.keys() - entries2.keys()]
    modified = [
        (entries1[h], entries2[h])
        for h in entries1.keys() & entries2.keys()
        if entries1[h] != entries2[h]
    ]

    print(Color.wrap("=" * 46, Color.CYAN))
    print(Color.wrap("           SEGMENT DIFF RESULTS", Color.BOLD))
    print(Color.wrap("=" * 46, Color.CYAN))
    print(f"Comparing: {seg1.name}  <->  {seg2.name}")
    print()

    print(Color.wrap("ADDED ENTRIES:", Color.GREEN))
    if added:
        for e in added:
            print(f"  + {Color.wrap(e.get('event_hash'), Color.MAGENTA)}")
            print(f"    Traveler: {e.get('traveler')}")
            print(f"    Decision: {Color.wrap(e.get('decision'), Color.YELLOW)}")
            print(f"    Timestamp: {e.get('timestamp')}")
            print()
    else:
        print("  (none)")
        print()

    print(Color.wrap("REMOVED ENTRIES:", Color.RED))
    if removed:
        for e in removed:
            print(f"  - {Color.wrap(e.get('event_hash'), Color.MAGENTA)}")
            print(f"    Traveler: {e.get('traveler')}")
            print(f"    Decision: {Color.wrap(e.get('decision'), Color.YELLOW)}")
            print(f"    Timestamp: {e.get('timestamp')}")
            print()
    else:
        print("  (none)")
        print()

    print(Color.wrap("MODIFIED ENTRIES:", Color.BLUE))
    if modified:
        for old, new in modified:
            print(f"  * {Color.wrap(old.get('event_hash'), Color.MAGENTA)}")
            print(f"    Old decision: {Color.wrap(old.get('decision'), Color.RED)}")
            print(f"    New decision: {Color.wrap(new.get('decision'), Color.GREEN)}")
            print()
    else:
        print("  (none)")
        print()

    print(Color.wrap("=" * 46, Color.CYAN))
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
        print("7. Explore Ledger Segments")
        print("8. Trace Golden Thread")
        print("9. View Decision History")
        print("10. Diff Ledger Segments")
        print("11. Exit")
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

                print(Color.wrap(">> CCQ QUARANTINE MENU", Color.CYAN))
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
                    input(Color.wrap("Invalid option. Press Enter to continue...", Color.YELLOW))

        elif choice == "7":
            clear_screen()
            explore_segments()
            pause()
        elif choice == "8":
            clear_screen()
            trace_golden_thread()
            pause()
        elif choice == "9":
            clear_screen()
            explore_decision_history()
            pause()
        elif choice == "10":
            clear_screen()
            diff_segments()
            pause()
        elif choice == "11":
            print("Exiting Steward Console.")
            break
        else:
            input(Color.wrap("Invalid option. Press Enter to continue...", Color.YELLOW))


if __name__ == "__main__":
    main_menu()
