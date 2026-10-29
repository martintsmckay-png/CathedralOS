import json
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / "GastronomicOS" / "kitchen_audit.jsonl"
TARGET_ROOM = Path.home() / "GastronomicOS"
PANTRY_FILE = TARGET_ROOM / "pantry.json"
DEPLOY_LOG = TARGET_ROOM / "deployment_log.jsonl"

RECIPE = {
    "graham crackers": {"required": 200.0, "unit": "g"},
    "butter": {"required": 100.0, "unit": "g"},
    "peanut butter": {"required": 500.0, "unit": "g"},
    "cream cheese": {"required": 250.0, "unit": "g"},
    "whipping cream": {"required": 500.0, "unit": "ml"},
    "powdered sugar": {"required": 120.0, "unit": "g"},
}

class AcousticAltar:
    @staticmethod
    def scan_room():
        if not TARGET_ROOM.exists():
            return {"file_count": 0, "total_bytes": 0, "note": "G3", "frequency": 196.0}
        files = [f for f in TARGET_ROOM.glob("**/*") if f.is_file()]
        file_count = len(files)
        total_bytes = sum(f.stat().st_size for f in files if f.exists())
        scale = ["G3", "Bb3", "C4", "D4", "Eb4", "F4", "G4"]
        freq_map = {
            "G3": 196.00, "Bb3": 233.08, "C4": 261.63,
            "D4": 293.66, "Eb4": 311.13, "F4": 349.23, "G4": 392.00
        }
        note = scale[file_count % len(scale)]
        frequency = freq_map.get(note, 196.00)
        return {"file_count": file_count, "total_bytes": total_bytes, "note": note, "frequency": frequency}

class SessionManager:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now(timezone.utc)
        altar_profile = AcousticAltar.scan_room()
        self.log_event("SESSION_START", {"version": "3.6_LiveRestock"})
        self.log_event("HARMONIC_ALIGNMENT", {
            "chord": altar_profile["note"],
            "frequency_hz": altar_profile["frequency"],
            "payload_bytes": altar_profile["total_bytes"]
        })

    def log_event(self, event_type, metadata=None):
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "event": event_type,
            "metadata": metadata or {}
        }
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def close_session(self, reason="normal_exit"):
        self.log_event("SESSION_CLOSE", {"reason": reason})

class SovereigntyWatchdog:
    def __init__(self, session_manager):
        self.session = session_manager

    def evaluate_state(self, state_str):
        state_upper = state_str.upper()
        current_profile = AcousticAltar.scan_room()

        if "SAG" in state_upper or "SINK" in state_upper:
            print("\n🚨 WATCHDOG ALERT: Structural instability detected!")
            print("🎵 HARMONIC OVERRIDE: Emitting corrective B-flat stabilization frequency!")
            self.session.log_event("SAGGING_SENSORY_DETECTION", {"raw_state": state_str, "frequency": current_profile["frequency"]})
            self.session.log_event("PIVOT_SUCCESS", {"new_form": "Deconstructed Pie", "override_note": "Bb3"})
            print("✅ AUTO-SALVAGE ENGAGED: Re-classified asset as 'Deconstructed Pie'. Zero loss recorded.")
            return True
        elif "BURN" in state_upper or "CHAR" in state_upper:
            print("\n🔥 WATCHDOG ALERT: Thermal threshold exceeded! Dissonance locked.")
            self.session.log_event("CARBONIZED_CATASTROPHE", {
                "raw_state": state_str,
                "dissonance_hz": current_profile["frequency"],
                "chord": current_profile["note"]
            })
            print(f"🔴 RECORDED TO WALL OF SHAME | Dissonance Signature: {current_profile['frequency']} Hz ({current_profile['note']})")
            return True
        return False

class SovereignReporter:
    def __init__(self, ledger_path):
        self.ledger_path = ledger_path

    def generate_summary(self):
        if not self.ledger_path.exists():
            print("No ledger found to analyze.")
            return

        sessions = {}
        legacy_events_count = 0

        with self.ledger_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    sid = event.get("session_id")
                    if not sid:
                        legacy_events_count += 1
                        continue
                    if sid not in sessions:
                        sessions[sid] = {"events": []}
                    sessions[sid]["events"].append(event)
                except json.JSONDecodeError:
                    continue

        print("\n==========================================")
        print("📊 CATHEDRALOS SHIFT & SOVEREIGNTY REPORT (v3.6)")
        print("==========================================")
        if legacy_events_count > 0:
            print(f"Legacy Events / Acoustic Scans: {legacy_events_count} entries")
        print(f"Total Tracked UUID Sessions: {len(sessions)}")
        print("------------------------------------------")

        for sid, data in sessions.items():
            events_str = str(data["events"])
            close_reason = "unknown"
            dissonance_sig = None

            for event in data["events"]:
                if event.get("event") == "SESSION_CLOSE":
                    close_reason = event.get("metadata", {}).get("reason", "unknown")
                if event.get("event") == "CARBONIZED_CATASTROPHE":
                    dissonance_sig = event.get("metadata", {}).get("dissonance_hz")

            if dissonance_sig:
                status = f"🔴 CARBONIZED | Dissonance: {dissonance_sig} Hz"
            elif "PIVOT_SUCCESS" in events_str:
                status = "🟢 AUTO-SALVAGED (Harmonic B-flat Override)"
            elif "SERVICE_AUTHORIZED" in events_str:
                status = "🟢 SOVEREIGN SUCCESS (Authorized Service)"
            elif close_reason == "normal_exit":
                status = "🟢 CLEAN SHIFT (Normal Exit)"
            else:
                status = "🟡 INTERRUPTED / ZOMBIE"

            print(f"Session: {sid[:8]}... | Status: {status}")
        print("==========================================")

class RecipeGateSubsystem:
    @staticmethod
    def load_pantry():
        if not PANTRY_FILE.exists():
            return {}
        try:
            data = json.loads(PANTRY_FILE.read_text(encoding="utf-8"))
            clean = {}
            for name, entry in data.items():
                if isinstance(entry, dict) and "amount" in entry and "unit" in entry:
                    clean[name.strip().lower()] = {
                        "amount": float(entry["amount"]),
                        "unit": str(entry["unit"]).strip().lower()
                    }
            return clean
        except Exception:
            return {}

    @staticmethod
    def save_pantry(pantry):
        ordered = {k: pantry[k] for k in sorted(pantry)}
        PANTRY_FILE.write_text(
            json.dumps(ordered, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

    @classmethod
    def restock_item(cls, name, amount, unit):
        pantry = cls.load_pantry()
        key = name.strip().lower()
        pantry[key] = {"amount": float(amount), "unit": unit.strip().lower()}
        cls.save_pantry(pantry)
        print(f"[AUDITOR] Restocked '{key}': now {amount:.2f} {unit}.")

    @classmethod
    def audit_recipe(cls):
        pantry = cls.load_pantry()
        ready = True
        details = []

        print("\n==========================================")
        print("📜 SOVEREIGN RECIPE GATE AUDIT")
        print("==========================================")

        for name, spec in RECIPE.items():
            req = spec["required"]
            unit = spec["unit"]
            entry = pantry.get(name)
            avail = entry["amount"] if entry and entry.get("unit") == unit else 0.0
            status = "PASS" if avail >= req else "FAIL"

            if status == "FAIL":
                ready = False

            print(f"[{status}] {name.title()} | Required: {req} {unit} | Available: {avail} {unit}")
            details.append({"ingredient": name, "status": status})

        print("------------------------------------------")
        if ready:
            print("DEPLOYMENT STATUS: 🟢 READY")
        else:
            print("DEPLOYMENT STATUS: 🔴 NOT READY")
        print("==========================================")
        return ready, details

    @classmethod
    def deploy_pie(cls, session):
        ready, details = cls.audit_recipe()
        if not ready:
            print("[AUDITOR] Deployment refused. Pantry deficits detected.")
            session.log_event("DEPLOYMENT_REFUSED", {"reason": "pantry_deficit"})
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": "SOVEREIGN PIE DEPLOYMENT AUTHORIZED",
            "message": "All structural assets available. Proceed to site preparation.",
            "status": "READY"
        }
        with DEPLOY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        session.log_event("DEPLOYMENT_AUTHORIZED", entry)
        print("\n🎉 SOVEREIGN PIE DEPLOYMENT AUTHORIZED")
        print("[AUDITOR] Ceremonial entry written to deployment_log.jsonl.")
        print("[AUDITOR] Ingredients remain untouched — the oven certifies the pie.")

class CathedralKitchen:
    def __init__(self):
        self.session = SessionManager()
        self.watchdog = SovereigntyWatchdog(self.session)
        self.reporter = SovereignReporter(LOG_FILE)
        self.active = False
        self.mode = "COMPLIANCE"

    def toggle_system(self):
        self.active = not self.active
        self.mode = "PANIC_BAKE" if self.active else "COMPLIANCE"
        status = "ACTIVE" if self.active else "INACTIVE"
        self.session.log_event("MODE_TOGGLE", {"status": status, "mode": self.mode})
        print(f"\n--- Kitchen Status: {status} | Mode: {self.mode} ---")

    def inspect_state(self, raw_input):
        handled = self.watchdog.evaluate_state(raw_input)
        if not handled:
            print(f"🔍 State '{raw_input}' logged. No immediate structural anomaly detected.")
            self.session.log_event("STATE_INSPECTION", {"input": raw_input})

    def show_audit_log(self):
        print("\n--- PERSISTENT KITCHEN LEDGER ---")
        if not LOG_FILE.exists():
            print("No ledger found.")
            return
        with LOG_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                print(line.strip())

def main():
    kitchen = CathedralKitchen()
    print("\n🏰 CATHEDRAL KITCHEN v3.6 (Live Restock & Gate Edition)")
    print("Commands: toggle | log | report | audit | restock <item> <amt> <unit> | deploy | check <state> | quit")

    while True:
        try:
            cmd_line = input("\nCK3.6> ").strip()
        except (EOFError, KeyboardInterrupt):
            kitchen.session.close_session(reason="interrupted")
            print("\nBank the coals. Goodbye!")
            break

        parts = cmd_line.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "toggle":
            kitchen.toggle_system()
        elif cmd == "log":
            kitchen.show_audit_log()
        elif cmd == "report":
            kitchen.reporter.generate_summary()
        elif cmd == "audit":
            RecipeGateSubsystem.audit_recipe()
        elif cmd == "restock":
            # Expected format: restock graham crackers 200 g
            tokens = arg.split()
            if len(tokens) >= 3:
                name = " ".join(tokens[:-2])
                try:
                    amount = float(tokens[-2])
                    unit = tokens[-1]
                    RecipeGateSubsystem.restock_item(name, amount, unit)
                except ValueError:
                    print("Invalid amount. Usage: restock <item> <amount> <unit>")
            else:
                print("Usage: restock <item> <amount> <unit> (e.g. restock butter 100 g)")
        elif cmd == "deploy":
            RecipeGateSubsystem.deploy_pie(kitchen.session)
        elif cmd == "check":
            if arg:
                kitchen.inspect_state(arg)
            else:
                print("Usage: check <state> (e.g., check sagging or check burnt)")
        elif cmd in ("quit", "q", "exit"):
            kitchen.session.close_session(reason="normal_exit")
            print("Bank the coals. Goodbye!")
            break
        else:
            print("Unknown command. Use toggle, log, report, audit, restock, deploy, check <state>, or quit.")

if __name__ == "__main__":
    main()
