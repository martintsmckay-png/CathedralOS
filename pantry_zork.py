#!/usr/bin/env python3
"""CathedralOS — PantryZork v0.1
Read-only inventory adventure. Automation recommends; human decides.
"""

import json
import random
from pathlib import Path

PANTRY_FILE = Path(__file__).resolve().parent / "pantry.json"
SEED = 369

MALFUNCTIONS = [
    "Your left tuxedo sleeve folds into a swirling nebula of Electric Chartreuse stardust",
    "An extra-dimensional pocket launches three miniature dumplings and a 159ms echo",
    "Your Mystic Burgundy lapel reveals a 432 Hz tuning fork orbiting a tiny moon",
    "Both cuffs invert into zero-gravity portals and spill cosmic glitter across the floorboards",
]

FALLBACK_RATIONS = {
    "Carole's Mashed Potatoes": {"amount": None, "unit": "unverified ration"},
    "Peanut Butter Pie": {"amount": None, "unit": "unverified ration"},
    "Sourdough Starter": {"amount": None, "unit": "unverified ration"},
}


def load_pantry():
    """Load and validate inventory without modifying the ledger."""
    if not PANTRY_FILE.exists():
        return FALLBACK_RATIONS.copy(), "fallback rations"

    try:
        data = json.loads(PANTRY_FILE.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            raise ValueError("Pantry root must be an object")

        for name, item in data.items():
            if not isinstance(name, str) or not isinstance(item, dict):
                raise ValueError("Invalid inventory entry")
            if "amount" not in item or "unit" not in item:
                raise ValueError(f"Incomplete inventory entry: {name}")
            amount = item["amount"]
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                raise ValueError(f"Invalid amount for {name}")
            if amount < 0:
                raise ValueError(f"Negative amount for {name}")
            if not isinstance(item["unit"], str):
                raise ValueError(f"Invalid unit for {name}")

        return data, "live pantry.json"

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[PANTRY WARNING] Ledger unavailable: {exc}")
        return FALLBACK_RATIONS.copy(), "fallback rations"


def format_item(name, item):
    amount = item["amount"]
    unit = item["unit"]

    if amount is None:
        return f"{name}: quantity unverified"

    return f"{name}: {amount:g} {unit}"


def render_turn(command, pantry, source, rng):
    """Render exactly three sentences from the current inventory snapshot."""
    command = command.strip()
    parts = command.split(maxsplit=1)
    action = parts[0].upper() if parts else "LOOK"
    target = parts[1].strip().lower() if len(parts) > 1 else ""

    zero_stock = [
        name for name, item in pantry.items()
        if item["amount"] == 0
    ]

    if action == "INVENTORY":
        details = "; ".join(
            format_item(name, item)
            for name, item in pantry.items()
        )
        if source == "fallback rations":
            sentence_one = (
                "[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS] "
                f"The ledger reveals {details}"
            )
        else:
            sentence_one = f"The ledger reveals {details}"

    elif action == "INSPECT":
        if not target:
            sentence_one = (
                "The parser awaits an object; try INSPECT peanut butter "
                "or INSPECT tuning fork"
            )
        else:
            match = next(
                (name for name in pantry if name.lower() == target),
                None,
            )

            if match:
                sentence_one = (
                    f"You inspect {format_item(match, pantry[match])}"
                )
            elif target in {"tuning fork", "432 hz tuning fork"}:
                sentence_one = (
                    "You inspect the orbiting tuning fork; "
                    "its reference is A4 at 432 Hz"
                )
            elif target in {"golden gramophone", "gramophone"}:
                sentence_one = (
                    "You inspect the Golden Gramophone; "
                    "its Audio Foundry bridge awaits a human command"
                )
            elif target in {"pantry ledger", "ledger"}:
                sentence_one = (
                    f"You inspect the Pantry Ledger; "
                    f"{len(pantry)} ingredient entries are recorded"
                )
            elif target in {"pie tin", "tin"}:
                sentence_one = (
                    "You inspect the empty Pie Tin; "
                    "its contents must be verified against the ledger"
                )
            else:
                sentence_one = (
                    f"Your search for '{target}' "
                    "finds no matching pantry or room object"
                )

    elif action == "LOOK":
        sentence_one = (
            f"You stand inside the Cathedral Pantry, reading "
            f"{len(pantry)} inventory entries from {source}"
        )

    elif action == "HELP":
        sentence_one = (
            "The command tablet recognizes INVENTORY, INSPECT <item>, "
            "LOOK, HELP, and QUIT"
        )

    else:
        sentence_one = (
            f"The parser cannot interpret '{command}', but the pantry "
            "ledger remains untouched"
        )

    sentence_two = rng.choice(MALFUNCTIONS)

    objects = "Pantry Ledger, Golden Gramophone, Pie Tin"
    exits = "NORTH to Audio Foundry, EAST to Open-Air Granite Staircase"

    if zero_stock:
        warning = ", zero-stock warning detected for " + ", ".join(zero_stock)
        audio = "; optional Audio Foundry cue: 432 Hz reference with 369 Hz glitch"
    else:
        warning = ""
        audio = "; Audio Foundry bridge available on request"

    sentence_three = (
        f"Interactables: {objects}; exits: {exits}{warning}{audio}"
    )

    return (
        f"{sentence_one}. "
        f"{sentence_two}. "
        f"{sentence_three}."
    )


def main():
    rng = random.Random(SEED)
    pantry, source = load_pantry()

    print("=== CATHEDRALOS: PANTRYZORK v0.1 ===")
    if source == "fallback rations":
        print("[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS]")
    else:
        print(f"Inventory source: {source}")
    print("Type INVENTORY, INSPECT <item>, LOOK, HELP, or QUIT")

    while True:
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThe pantry doors close quietly.")
            break

        if command.lower() in {"quit", "exit"}:
            print("You leave the Cathedral Pantry.")
            break

        if not command:
            continue

        print()
        print(render_turn(command, pantry, source, rng))


if __name__ == "__main__":
    main()
