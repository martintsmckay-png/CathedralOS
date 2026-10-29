import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("cathedral_state.json")
AUDIT_FILE = Path("auditor.log")
MAX_COHERENCE = 1.0


@dataclass(frozen=True)
class Ingredient:
    name: str
    harmonic_value: float
    effect: str


class Steward:
    def __init__(self):
        self.inventory = []

    def pick_up(self, item_name):
        self.inventory.append(item_name)

    def drop(self, item_name):
        if item_name in self.inventory:
            self.inventory.remove(item_name)
            return True
        return False


class Pantry:
    def __init__(self):
        self.ingredients = {
            "Wild Yeast": Ingredient("Wild Yeast", 1.0, "Supports portal breath"),
            "Sea Salt": Ingredient("Sea Salt", 0.5, "Supports bridge stability"),
            "Himalayan Pink": Ingredient("Himalayan Pink", 1.618, "Unlocks the Liminal Larder"),
            "Perfect Fifth": Ingredient("Perfect Fifth", 1.5, "Adds a bounded coherence boost"),
        }
        self.stock = {
            "C": ["Wild Yeast", "Sea Salt"],
            "D": ["Perfect Fifth"],
            "Eb": ["Himalayan Pink"],
        }


class TonalEngine:
    def __init__(self):
        self.steward = Steward()
        self.pantry = Pantry()
        self.rooms = {
            "G": {"name": "Root Directory", "frequency": 196.00, "status": "Memory and configuration"},
            "Bb": {"name": "Sourdough Portal", "frequency": 233.08, "status": "Bridge stable"},
            "C": {"name": "Pantry", "frequency": 261.63, "status": "Resource recycling"},
            "D": {"name": "Auditor Gallery", "frequency": 293.66, "status": "Telemetry active"},
            "Eb": {"name": "Shaman Grove", "frequency": 311.13, "status": "Creative mode"},
            "F": {"name": "Quarantine Ward", "frequency": 349.23, "status": "Inspection mode"},
        }
        self.current_room = "Bb"
        self.coherence = {note: 0.5 for note in self.rooms}
        self.coherence["Bb"] = 0.8
        self.discovered_larder = False
        self.mirror_sharp = False
        self.inventory = self.steward.inventory
        self.load_state()

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with AUDIT_FILE.open("a", encoding="utf-8") as file:
            file.write(f"[{timestamp}] {message}\n")

    def save_state(self):
        state = {
            "current_room": self.current_room,
            "inventory": self.inventory,
            "coherence": self.coherence,
            "stock": self.pantry.stock,
            "discovered_larder": self.discovered_larder,
            "mirror_sharp": self.mirror_sharp,
        }
        temporary = STATE_FILE.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, indent=2), encoding="utf-8")
        temporary.replace(STATE_FILE)

    def load_state(self):
        if not STATE_FILE.exists():
            self.log("New Steward state initialized.")
            self.save_state()
            return
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            room = state.get("current_room", "Bb")
            if room in self.rooms or room == "LL":
                self.current_room = room

            saved_inventory = state.get("inventory", [])
            if isinstance(saved_inventory, list):
                self.inventory[:] = [
                    name for name in saved_inventory
                    if isinstance(name, str) and name in self.pantry.ingredients
                ]

            saved_coherence = state.get("coherence", {})
            if isinstance(saved_coherence, dict):
                for note in self.rooms:
                    value = saved_coherence.get(note, self.coherence[note])
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        self.coherence[note] = max(0.0, min(MAX_COHERENCE, float(value)))

            saved_stock = state.get("stock", {})
            if isinstance(saved_stock, dict):
                for note in self.pantry.stock:
                    names = saved_stock.get(note, self.pantry.stock[note])
                    if isinstance(names, list):
                        self.pantry.stock[note] = [
                            name for name in names
                            if isinstance(name, str) and name in self.pantry.ingredients
                        ]

            self.discovered_larder = bool(state.get("discovered_larder", False))
            self.mirror_sharp = bool(state.get("mirror_sharp", False))
            if self.discovered_larder:
                self.rooms["LL"] = self.liminal_room()
            elif self.current_room == "LL":
                self.current_room = "Bb"
            self.log("Saved Steward state restored.")
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as error:
            self.log(f"State load error: {error}")
            print("Warning: saved state could not be loaded.")
            print("The existing state file was not overwritten.")

    def liminal_room(self):
        return {
            "name": "The Liminal Larder",
            "frequency": self.rooms["Bb"]["frequency"] * 1.618,
            "status": "Golden Crust / discovered",
        }

    @staticmethod
    def canonical_room(note):
        cleaned = note.strip()
        aliases = {
            "A#": "Bb", "BB": "Bb", "B♭": "Bb", "A♯": "Bb",
            "EB": "Eb", "D#": "Eb", "E♭": "Eb", "D♯": "Eb",
            "LL": "LL",
        }
        return aliases.get(cleaned.upper(), cleaned)

    def shift_room(self, note):
        note = self.canonical_room(note)
        if note == "LL" and not self.discovered_larder:
            return "The Liminal Larder is still undiscovered."
        if note not in self.rooms:
            return "Unknown room. The bridge remains stable."
        self.current_room = note
        room = self.rooms[note]
        self.log(f"Room shift -> {note} | {room['name']}")
        self.save_state()
        return f"Moved to {room['name']}."

    def search_room(self):
        note = self.current_room
        if note not in self.pantry.stock:
            return "Nothing collectible is listed in this room."
        available = self.pantry.stock[note]
        if not available:
            return "The room's shelves are empty."
        print(f"\nAvailable in {self.rooms[note]['name']}:")
        for index, name in enumerate(available, start=1):
            item = self.pantry.ingredients[name]
            print(f"  {index}. {item.name} (harmonic value {item.harmonic_value})")
        choice = input("Enter item name to collect, or Enter to cancel: ").strip()
        match = next((name for name in available if name.lower() == choice.lower()), None)
        if not match:
            return "No item collected."
        self.steward.pick_up(match)
        available.remove(match)
        self.log(f"Pickup -> {match} | Room {note}")
        self.save_state()
        return f"Collected {match}. Your inventory persists across room shifts."

    def apply_ingredient(self, item_name):
        match = next(
            (name for name in self.inventory if name.lower() == item_name.strip().lower()),
            None,
        )
        if match is None:
            return "You aren't carrying that ingredient."

        note = self.current_room
        if note not in self.coherence:
            return (
                f"Ingredient application rejected in {self.rooms[note]['name']}.\n"
                "This discovery room has no assigned Hλ score.\n"
                f"{match} remains safely in your inventory."
            )

        item = self.pantry.ingredients[match]
        old = self.coherence[note]
        boost = min(item.harmonic_value * 0.1, 0.2)
        new = min(MAX_COHERENCE, old + boost)
        self.coherence[note] = new
        self.steward.drop(match)
        self.log(f"Applied {match} in {note} | coherence {old:.4f} -> {new:.4f}")
        message = f"Applied {match} in {self.rooms[note]['name']}. Hλ: {old:.2f} -> {new:.2f}."

        if item.harmonic_value == 1.618:
            self.discovered_larder = True
            self.rooms["LL"] = self.liminal_room()
            self.current_room = "LL"
            liminal = self.rooms["LL"]
            self.log(f"DISCOVERY -> The Liminal Larder | {liminal['frequency']:.2f} Hz")
            message += (
                "\nGOLDEN CRUST UNLOCKED!"
                f"\n{liminal['name']} discovered."
                "\nRatio-generated frequency: "
                f"{liminal['frequency']:.2f} Hz"
            )
        self.save_state()
        return message

    def show_inventory(self):
        print("\n--- STEWARD'S INVENTORY ---")
        if not self.inventory:
            print("Your bag is empty.")
        else:
            for name in self.inventory:
                print(f"- {name}: {self.pantry.ingredients[name].effect}")
        print("---------------------------")

    def show_status(self):
        room = self.rooms[self.current_room]
        print(f"Room: {room['name']} ({self.current_room})")
        print(f"Frequency: {room['frequency']:.2f} Hz")
        print(f"Status: {room['status']}")
        if self.current_room in self.coherence:
            print(f"Hλ: {self.coherence[self.current_room]:.2f}")
        else:
            print("Hλ: no score assigned to this discovery room")

    def display(self):
        room = self.rooms[self.current_room]
        print("\n" + "=" * 42)
        print("  CATHEDRALOS // TONAL ENGINE")
        print("=" * 42)
        print(f"  ROOM      : {room['name']}")
        shown_note = "A#" if self.current_room == "Bb" and self.mirror_sharp else self.current_room
        print(f"  NOTE      : {shown_note}")
        print(f"  FREQUENCY : {room['frequency']:.2f} Hz")
        print(f"  STATUS    : {room['status']}")
        if self.current_room in self.coherence:
            print(f"  Hλ        : {self.coherence[self.current_room]:.2f}")
        else:
            print("  Hλ        : discovery room; score not assigned")
        print("-" * 42)
        for note in ("G", "Bb", "C", "D", "Eb", "F"):
            print(f"  {note:<3} {self.rooms[note]['name']}")
        if self.discovered_larder:
            print("  LL  The Liminal Larder [UNLOCKED]")
        print("  GO <room>      Move to a room (or enter its note)")
        print("  STATUS         Show current room details")
        print("  MIRROR         Toggle B♭ / A♯ spelling at the portal")
        print("  S              Search current room")
        print("  I              Show inventory")
        print("  USE <item>     Apply an ingredient")
        print("  L              View Auditor ledger")
        print("  Q              Save and quit")
        print("=" * 42)

    def show_log(self):
        if AUDIT_FILE.exists():
            print("\n--- AUDITOR LEDGER (latest 4000 characters) ---")
            print(AUDIT_FILE.read_text(encoding="utf-8")[-4000:])
        else:
            print("No ledger entries yet.")
        input("Press Enter to return...")

    def toggle_mirror(self):
        if self.current_room != "Bb":
            return "Mirror toggle is available at the B-flat portal."
        self.mirror_sharp = not self.mirror_sharp
        spelling = "A#" if self.mirror_sharp else "Bb"
        self.log(f"Mirror spelling -> {spelling} (canonical room remains Bb)")
        self.save_state()
        return (
            f"Mirror spelling now displays {spelling}.\n"
            "Same portal, same 233.08 Hz; canonical room remains Bb."
        )

    def run(self):
        self.log("Tonal Engine started.")
        print("\n[BOOT] CathedralOS Tonal Engine v2.1")
        print("[OK] Pantry loaded")
        print("[OK] Steward inventory loaded")
        print("[OK] Persistent state enabled")
        print("[OK] Auditor ledger enabled")
        print("[OK] B-flat bridge ready")
        print("[OK] Safe discovery-room handling enabled")
        while True:
            self.display()
            command = input("\nSteward@CathedralOS > ").strip()
            if not command:
                continue
            upper = command.upper()
            if upper == "Q":
                self.save_state()
                self.log("Tonal Engine shut down; state saved.")
                print("Inventory saved. Bank the coals!")
                break
            elif upper in {"S", "SEARCH"}:
                print(self.search_room())
                input("Press Enter to continue...")
            elif upper in {"I", "INVENTORY"}:
                self.show_inventory()
                input("Press Enter to continue...")
            elif upper in {"L", "LOG", "LEDGER"}:
                self.show_log()
            elif upper == "STATUS":
                self.show_status()
                input("Press Enter to continue...")
            elif upper == "MIRROR":
                print(self.toggle_mirror())
                input("Press Enter to continue...")
            elif upper.startswith("USE "):
                print(self.apply_ingredient(command[4:]))
                input("Press Enter to continue...")
            elif upper.startswith("GO "):
                print(self.shift_room(command[3:].strip()))
                input("Press Enter to continue...")
            else:
                print(self.shift_room(command))
                input("Press Enter to continue...")


if __name__ == "__main__":
    TonalEngine().run()
