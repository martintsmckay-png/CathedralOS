from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class RoomNote:
    pitch: str
    frequency: float
    room: str
    status: str

class CathedralOS:
    def __init__(self):
        self.rooms = {
            "G": RoomNote(
                "G", 196.00,
                "Root Directory",
                "Memory and configuration"
            ),
            "Bb": RoomNote(
                "Bb", 233.08,
                "Sourdough Portal",
                "Bridge stable"
            ),
            "C": RoomNote(
                "C", 261.63,
                "Pantry",
                "Resource recycling"
            ),
            "D": RoomNote(
                "D", 293.66,
                "Auditor Gallery",
                "Telemetry active"
            ),
            "Eb": RoomNote(
                "Eb", 311.13,
                "Shaman Grove",
                "Creative mode"
            ),
            "F": RoomNote(
                "F", 349.23,
                "Quarantine Ward",
                "Inspection mode"
            ),
        }
        self.active = "Bb"

    def log(self, message):
        with open("auditor.log", "a") as file:
            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            file.write(f"[{timestamp}] {message}\n")

    def display(self):
        room = self.rooms[self.active]
        print("\n" + "=" * 36)
        print("  CATHEDRALOS // MUSICAL ENGINE")
        print("=" * 36)
        print(f"  ACTIVE NOTE : {room.pitch}")
        print(f"  FREQUENCY   : {room.frequency:.2f} Hz")
        print(f"  ROOM        : {room.room}")
        print(f"  STATUS      : {room.status}")
        print("-" * 36)
        print("  G  Root Directory")
        print("  Bb Sourdough Portal")
        print("  C  Pantry")
        print("  D  Auditor Gallery")
        print("  Eb Shaman Grove")
        print("  F  Quarantine Ward")
        print("  L  View Auditor Log")
        print("  Q  Exit")
        print("=" * 36)


    def strike(self, note):
        note = note.strip().lower()

        if note == "mirror":
            if self.active not in ("Bb", "A#"):
                print("Mirror bridge is available from Bb or A# only.")
                return

            previous = self.active

            if previous == "Bb":
                original = self.rooms["Bb"]
                self.rooms["A#"] = RoomNote(
                    "A#",
                    original.frequency,
                    original.room,
                    "Mirror spelling active"
                )
                self.active = "A#"
            else:
                self.active = "Bb"

            message = (
                f"Mirror -> {previous} -> {self.active} | "
                "Same frequency and room; symbolic spelling changed"
            )
            print("[A#/Bb BRIDGE] " + message)
            self.log(message)
            return

        aliases = {
            "bb": "Bb",
            "a#": "Bb",
            "eb": "Eb",
            "d#": "Eb",
        }
        note = aliases.get(note, note.upper())

        if note not in self.rooms:
            print("Unknown note. The bridge remains stable.")
            return

        self.active = note
        room = self.rooms[note]

        message = (
            f"Transition -> {room.pitch} | "
            f"{room.room} | {room.status}"
        )

        print("[Bb BRIDGE] Domain transition recorded.")
        print(message)
        self.log(message)

    def run(self):
        self.log("Musical OS booted.")
        print("[BOOT] CathedralOS Musical Engine v1.0")
        print("[OK] Musical matrix loaded")
        print("[OK] Auditor logging enabled")
        print("[OK] B-flat bridge ready")

        while True:
            self.display()
            print("  mirror  Toggle Bb / A# portal spelling")
            choice = input("Steward@CathedralOS > ").strip()

            if choice.lower() == "q":
                self.log("Musical OS shut down.")
                print("Bank the coals. See you at the hearth!")
                break

            elif choice.lower() == "l":
                try:
                    with open("auditor.log") as file:
                        print("--- AUDITOR LEDGER ---")
                        print(file.read()[-3000:])
                except FileNotFoundError:
                    print("No ledger entries yet.")

                input("Press Enter to return...")

            else:
                self.strike(choice)
                input("Press Enter to continue...")


if __name__ == "__main__":
    CathedralOS().run()
