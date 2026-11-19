#!/usr/bin/env python3
"""CathedralOS — PantryZork v0.3
Read-only exploration, explicit evidence states, ephemeral session journal.
Automation recommends; humans decide.
"""

import copy
import hashlib
import json
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    from validate_pantry_contract import validate_pantry_data
except ImportError:
    def validate_pantry_data(data):
        """Standalone compatibility validator."""
        if not isinstance(data, dict):
            raise ValueError("Pantry root must be a dictionary.")
        if not data:
            raise ValueError("Pantry cannot be empty.")

        for name, item in data.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Ingredient name must be a non-empty string.")
            if not isinstance(item, dict):
                raise ValueError(f"Item '{name}' must be a dictionary.")
            if "amount" not in item or "unit" not in item:
                raise ValueError(f"Item '{name}' is incomplete.")

            amount = item["amount"]
            unit = item["unit"]

            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                raise ValueError(f"Amount for '{name}' must be numeric (not bool).")
            if isinstance(amount, float):
                import math
                if not math.isfinite(amount):
                    raise ValueError(f"Amount for '{name}' must be finite.")
            if amount < 0:
                raise ValueError(f"Amount for '{name}' cannot be negative.")
            if not isinstance(unit, str) or not unit.strip():
                raise ValueError(f"Unit for '{name}' must be a non-empty string.")


BASE_DIR = Path(__file__).resolve().parent
PANTRY_FILE = BASE_DIR / "pantry.json"
ENSEMBLE_WAV = BASE_DIR / "audio_foundry" / "cathedralos_v6_2_ensemble.wav"
ENSEMBLE_SHA256 = (
    "5a72509e79740ee3af5313a97ce9f47826e6d6a989f0618442e275c50d182316"
)
SEED = 369

MALFUNCTIONS = [
    "Your left tuxedo sleeve folds into a swirling nebula of Electric Chartreuse stardust",
    "An extra-dimensional pocket launches three miniature dumplings and a 159ms echo",
    "Your Mystic Burgundy lapel reveals a 432 Hz tuning fork orbiting a tiny moon",
    "Both cuffs invert into zero-gravity portals and spill cosmic glitter across the floorboards",
]

FALLBACK_RATIONS = {
    "Carole's Mashed Potatoes": {
        "amount": None, "unit": "unverified ration"
    },
    "Peanut Butter Pie": {
        "amount": None, "unit": "unverified ration"
    },
    "Sourdough Starter": {
        "amount": None, "unit": "unverified ration"
    },
}

WELCOME_TOKEN_LINE = "WELCOME TOKEN IS NARRATIVE-ONLY"
INSCRIPTION_LINE = (
    "Hospitality before hostility. Reality has the final vote."
)


class PantryLoadState(Enum):
    MISSING = "missing_file"
    UNREADABLE = "unreadable_file"
    MALFORMED_JSON = "malformed_json"
    INVALID_CONTRACT = "valid_json_invalid_contract"
    VALID_LIVE = "valid_json_valid_contract"


@dataclass(frozen=True)
class PantrySnapshot:
    state: PantryLoadState
    data: dict
    contract_verified: bool
    reason: str = ""
    evidence_note: str = ""


@dataclass(frozen=True)
class SessionObservation:
    pantry_state: str
    origin: str
    note: str


@dataclass
class SessionJournal:
    """Process-local notes. Never writes to disk."""
    observations: list = field(default_factory=list)

    def record(self, snapshot, note):
        normalized = " ".join(note.split())

        if normalized:
            origin = "user_input"
            recorded_note = normalized
        else:
            origin = "fallback_state_note"
            recorded_note = (
                f"Observed pantry state={snapshot.state.value}"
            )

        observation = SessionObservation(
            pantry_state=snapshot.state.value,
            origin=origin,
            note=recorded_note,
        )
        self.observations.append(observation)
        return observation


def load_pantry_snapshot(pantry_path=PANTRY_FILE):
    """Read once and classify the pantry evidence state."""
    pantry_path = Path(pantry_path)

    try:
        raw = pantry_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        print(f"[PANTRY WARNING] Ledger missing: {exc}")
        return PantrySnapshot(
            PantryLoadState.MISSING, {}, False, str(exc)
        )
    except (OSError, UnicodeError) as exc:
        print(f"[PANTRY WARNING] Ledger unreadable: {exc}")
        return PantrySnapshot(
            PantryLoadState.UNREADABLE, {}, False,
            f"{type(exc).__name__}: {exc}",
        )

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[PANTRY WARNING] Malformed pantry JSON: {exc}")
        return PantrySnapshot(
            PantryLoadState.MALFORMED_JSON, {}, False, str(exc)
        )

    try:
        validate_pantry_data(data)
    except (ValueError, TypeError, OverflowError) as exc:
        print(f"[PANTRY WARNING] Pantry contract rejected: {exc}")
        return PantrySnapshot(
            PantryLoadState.INVALID_CONTRACT, {}, False, str(exc)
        )

    return PantrySnapshot(
        PantryLoadState.VALID_LIVE,
        copy.deepcopy(data),
        True,
        "",
        "Contract verified; this does not prove authenticity.",
    )


def view_from_snapshot(snapshot):
    """Derive a display view without modifying the evidence snapshot."""
    if snapshot.state == PantryLoadState.VALID_LIVE:
        return copy.deepcopy(snapshot.data), "live pantry.json"

    return copy.deepcopy(FALLBACK_RATIONS), "fallback rations"


def load_pantry(pantry_path=PANTRY_FILE):
    """Legacy tuple interface retained for existing callers."""
    snapshot = load_pantry_snapshot(pantry_path)
    return view_from_snapshot(snapshot)


def format_item(name, item):
    amount = item["amount"]
    unit = item["unit"]

    if amount is None:
        return f"{name}: quantity unverified"

    if isinstance(amount, int):
        return f"{name}: {amount} {unit}"

    return f"{name}: {amount:g} {unit}"


def describe_audio_bridge(context_label):
    """Verify the artifact and recommend, but never launch, playback."""
    relative_path = "audio_foundry/cathedralos_v6_2_ensemble.wav"

    if not ENSEMBLE_WAV.is_file():
        return (
            f"{context_label}; the ensemble WAV is missing—human decides: "
            "'python3 audio_foundry/render_v6_2_ensemble.py'"
        )

    try:
        actual_hash = hashlib.sha256(
            ENSEMBLE_WAV.read_bytes()
        ).hexdigest()
    except OSError as exc:
        return f"{context_label}; the ensemble WAV could not be read: {exc}"

    if actual_hash != ENSEMBLE_SHA256:
        return (
            f"{context_label}; artifact integrity mismatch "
            f"(SHA-256 {actual_hash})—playback is not recommended"
        )

    return (
        f"{context_label}; verified v6.2 artifact "
        f"(SHA-256 {actual_hash}) is present—human decides: "
        f"'termux-media-player play {relative_path}'"
    )


def render_turn(command, pantry, source, rng):
    """Render the original three-part adventure response."""
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

        sentence_one += f"; {WELCOME_TOKEN_LINE}"

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

            if target == "garlic bread":
                sentence_one = (
                    f"You inspect the narrative welcome token. "
                    f"{WELCOME_TOKEN_LINE}; {INSCRIPTION_LINE}"
                )
            elif match:
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
                    "You inspect the Pantry Ledger; "
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

    elif action == "NORTH" or (action == "GO" and target == "north"):
        sentence_one = describe_audio_bridge(
            "You step through the NORTH archway toward Audio Foundry"
        )

    elif action == "PLAY" and target in {
        "gramophone", "golden gramophone"
    }:
        sentence_one = describe_audio_bridge(
            "You cue the Golden Gramophone needle"
        )

    elif action == "LOOK":
        sentence_one = (
            "You stand inside the Cathedral Pantry, reading "
            f"{len(pantry)} inventory entries from {source}"
        )

    elif action == "HELP":
        sentence_one = (
            "The command tablet recognizes INVENTORY, INSPECT <item>, "
            "GO NORTH, NORTH, PLAY GRAMOPHONE, LOOK, HELP, and QUIT"
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
        warning = (
            ", zero-stock warning detected for " + ", ".join(zero_stock)
        )
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


def render_guild(snapshot):
    """Report known evidence; do not invent subsystem telemetry."""
    return (
        f"Pantry evidence state: {snapshot.state.value}\n"
        f"Contract verified: {snapshot.contract_verified}\n"
        "Detector status unavailable. Evidence: "
        "no detector result supplied."
    )


def render_log(journal):
    if not journal.observations:
        return "No in-memory session notes recorded in this run."

    lines = [
        "SESSION LOG — IN-MEMORY ONLY — NOT PERSISTED"
    ]

    for index, observation in enumerate(journal.observations, 1):
        lines.append(
            f"{index}. state={observation.pantry_state}; "
            f"origin={observation.origin}; note={observation.note}"
        )

    return "\n".join(lines)


def dispatch_command(command, snapshot, journal=None, rng=None):
    """Dispatch one command without persistent side effects."""
    command = command.strip()
    parts = command.split(maxsplit=1)
    action = parts[0].upper() if parts else "LOOK"
    argument = parts[1] if len(parts) > 1 else ""

    if action in {"QUIT", "EXIT"}:
        return "You leave the Cathedral Pantry.", True

    if action == "SENSE":
        if journal is None:
            return "Cannot SENSE: no journal supplied.", False

        observation = journal.record(snapshot, argument)
        return (
            f"recorded pantry state={observation.pantry_state}; "
            f"origin={observation.origin}; note={observation.note}",
            False,
        )

    if action == "LOG":
        if journal is None:
            return "Cannot read session log: no journal supplied.", False
        return render_log(journal), False

    if action == "GUILD":
        return render_guild(snapshot), False

    pantry, source = view_from_snapshot(snapshot)
    return render_turn(command, pantry, source, rng or random.Random(SEED)), False


def main():
    rng = random.Random(SEED)

    # One disk read. All session views derive from this snapshot.
    snapshot = load_pantry_snapshot(PANTRY_FILE)
    pantry, source = view_from_snapshot(snapshot)
    journal = SessionJournal()

    print("=== CATHEDRALOS: PANTRYZORK v0.3 ===")
    print(f"Pantry state={snapshot.state.value}")

    if source == "fallback rations":
        print("[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS]")
    else:
        print(f"Inventory source: {source}")

    print(
        "Type INVENTORY, INSPECT <item>, GO NORTH, PLAY GRAMOPHONE, "
        "SENSE [note], LOG, GUILD, LOOK, HELP, or QUIT"
    )

    while True:
        try:
            command = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nThe pantry doors close quietly.")
            break

        if not command:
            continue

        output, should_quit = dispatch_command(
            command, snapshot, journal, rng
        )

        if should_quit:
            print(output)
            break

        print()
        print(output)


if __name__ == "__main__":
    main()
