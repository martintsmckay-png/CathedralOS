import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE_SCRIPT = Path(__file__).resolve().parent / "pantry_zork.py"
LIVE_PANTRY = Path(__file__).resolve().parent / "pantry.json"


class TestPantryZorkRegression(unittest.TestCase):
    def _run_zork(self, workdir: Path, commands: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(workdir / "pantry_zork.py")],
            input=commands,
            text=True,
            capture_output=True,
            cwd=workdir,
            timeout=10,
        )

    def test_01_live_inventory_and_room_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            shutil.copy2(SOURCE_SCRIPT, workdir / "pantry_zork.py")
            if LIVE_PANTRY.exists():
                shutil.copy2(LIVE_PANTRY, workdir / "pantry.json")
            else:
                (workdir / "pantry.json").write_text(
                    json.dumps({"graham crackers": "250 g"}), encoding="utf-8"
                )

            res = self._run_zork(
                workdir, "INSPECT pie tin\nINSPECT moon cheese\nINVENTORY\nQUIT\n"
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Inventory source: live pantry.json", res.stdout)
            self.assertNotIn("[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS]", res.stdout)
            self.assertIn("Pie Tin", res.stdout)
            self.assertIn("no matching pantry or room object", res.stdout)
            self.assertIn("graham crackers", res.stdout)

    def test_02_missing_pantry_triggers_recovery_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            shutil.copy2(SOURCE_SCRIPT, workdir / "pantry_zork.py")

            res = self._run_zork(workdir, "INVENTORY\nQUIT\n")
            self.assertEqual(res.returncode, 0)
            self.assertGreaterEqual(
                res.stdout.count("[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS]"), 2
            )
            self.assertNotIn("graham crackers: 250 g", res.stdout)

    def test_03_malformed_json_triggers_warning_and_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            shutil.copy2(SOURCE_SCRIPT, workdir / "pantry_zork.py")
            (workdir / "pantry.json").write_text("{broken_json: [1, 2,", encoding="utf-8")

            res = self._run_zork(workdir, "INVENTORY\nQUIT\n")
            self.assertEqual(res.returncode, 0)
            combined = res.stdout + res.stderr
            self.assertIn("warning", combined.lower())
            self.assertGreaterEqual(
                res.stdout.count("[RECOVERY DISPLAY — UNVERIFIED FALLBACK RATIONS]"), 2
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
