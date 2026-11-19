from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from unittest import mock

import pytest

from pantry_zork import (
    FALLBACK_RATIONS,
    INSCRIPTION_LINE,
    MALFUNCTIONS,
    WELCOME_TOKEN_LINE,
    PantryLoadState,
    SessionJournal,
    dispatch_command,
    load_pantry,
    load_pantry_snapshot,
    render_guild,
    render_log,
    render_turn,
    view_from_snapshot,
)
from validate_pantry_contract import (
    validate_pantry_contract,
    validate_pantry_data,
)

REPO_ROOT = Path(__file__).resolve().parent

UNREADABLE_SITECUSTOMIZE = (
    "from pathlib import Path\n"
    "_orig_read_text = Path.read_text\n"
    "def _deny_read(self, *args, **kwargs):\n"
    "    if self.name == 'pantry.json':\n"
    "        raise PermissionError('simulated unreadable pantry.json')\n"
    "    return _orig_read_text(self, *args, **kwargs)\n"
    "Path.read_text = _deny_read\n"
)


@dataclass(frozen=True)
class FileContentMtimeFingerprint:
    sha256: str
    size: int
    mtime_ns: int


def _fingerprint_file_contents_and_mtime(root: Path):
    snapshot = {}
    for entry in sorted(root.rglob("*")):
        if entry.is_file():
            data = entry.read_bytes()
            stat = entry.stat()
            rel = entry.relative_to(root).as_posix()
            snapshot[rel] = FileContentMtimeFingerprint(
                sha256=hashlib.sha256(data).hexdigest(),
                size=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
            )
    return snapshot


def _prepare_subprocess_files(workdir: Path) -> Path:
    for filename in ("pantry_zork.py", "validate_pantry_contract.py"):
        source = REPO_ROOT / filename
        if not source.is_file():
            raise FileNotFoundError(source)

        destination = workdir / filename
        source_bytes = source.read_bytes()
        if not destination.exists() or destination.read_bytes() != source_bytes:
            destination.write_bytes(source_bytes)

    return workdir / "pantry_zork.py"


def _run_zork_subprocess(
    workdir: Path,
    commands: str = "LOOK\nINVENTORY\nGUILD\nQUIT\n",
    *,
    extra_pythonpath: Path | None = None,
):
    script_path = _prepare_subprocess_files(workdir)
    env = os.environ.copy()

    parts = [str(workdir)]
    if extra_pythonpath is not None:
        parts.insert(0, str(extra_pythonpath))
    if existing := env.get("PYTHONPATH"):
        parts.append(existing)

    env["PYTHONPATH"] = os.pathsep.join(parts)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    return subprocess.run(
        [sys.executable, str(script_path)],
        input=commands,
        text=True,
        capture_output=True,
        cwd=workdir,
        env=env,
        timeout=10,
    )

# ---------------------------------------------------------------------------
# Unified validator & large-integer safety
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "invalid_data",
    [
        {},
        ["flour"],
        {"   ": {"amount": 1.0, "unit": "cup"}},
        {"flour": "not-a-dict"},
        {"flour": {"unit": "cup"}},
        {"flour": {"amount": 1.0}},
        {"flour": {"amount": True, "unit": "cup"}},
        {"flour": {"amount": -0.5, "unit": "cup"}},
        {"flour": {"amount": float("nan"), "unit": "cup"}},
        {"flour": {"amount": float("inf"), "unit": "cup"}},
        {"flour": {"amount": float("-inf"), "unit": "cup"}},
        {"flour": {"amount": 1.0, "unit": "   "}},
    ],
)
def test_unified_validator_rejects_contract_gaps(invalid_data):
    ok, reason = validate_pantry_contract(invalid_data)
    assert ok is False
    assert isinstance(reason, str) and reason

    with pytest.raises(ValueError):
        validate_pantry_data(invalid_data)


def test_unified_validator_accepts_huge_integer_without_overflow(tmp_path):
    pantry_path = tmp_path / "pantry.json"
    huge_amount = 10**600
    payload = {
        "sourdough starter": {
            "amount": huge_amount,
            "unit": "grams",
        }
    }
    pantry_path.write_text(json.dumps(payload), encoding="utf-8")

    ok, _ = validate_pantry_contract(payload)
    assert ok is True

    snap = load_pantry_snapshot(pantry_path)
    assert snap.state == PantryLoadState.VALID_LIVE
    assert snap.contract_verified is True
    assert snap.data["sourdough starter"]["amount"] == huge_amount

# ---------------------------------------------------------------------------
# Five-state loader & single-snapshot view derivation
# ---------------------------------------------------------------------------

def test_five_state_loader_and_view_derivation(tmp_path, capsys):
    pantry_path = tmp_path / "pantry.json"

    # 1. MISSING
    snap_missing = load_pantry_snapshot(pantry_path)
    assert snap_missing.state == PantryLoadState.MISSING
    assert snap_missing.contract_verified is False
    assert snap_missing.data == {}

    view_missing, src_missing = view_from_snapshot(snap_missing)
    assert src_missing == "fallback rations"
    assert set(view_missing) == set(FALLBACK_RATIONS)
    assert all(v["amount"] is None for v in view_missing.values())
    assert "[PANTRY WARNING]" in capsys.readouterr().out

    # 2. UNREADABLE: operating-system error
    pantry_path.write_text(
        '{"garlic bread": {"amount": 2, "unit": "loaves"}}',
        encoding="utf-8",
    )
    with mock.patch.object(
        Path, "read_text",
        side_effect=PermissionError("denied"),
    ):
        snap_os = load_pantry_snapshot(pantry_path)

    assert snap_os.state == PantryLoadState.UNREADABLE
    assert "PermissionError" in snap_os.reason

    # 2b. UNREADABLE: invalid UTF-8
    pantry_path.write_bytes(b"\xff\xfe\xfd invalid utf-8")
    snap_utf8 = load_pantry_snapshot(pantry_path)
    assert snap_utf8.state == PantryLoadState.UNREADABLE
    assert "UnicodeDecodeError" in snap_utf8.reason

    # 3. MALFORMED_JSON
    pantry_path.write_text(
        '{"garlic bread": {"amount": 2',
        encoding="utf-8",
    )
    snap_malformed = load_pantry_snapshot(pantry_path)
    assert snap_malformed.state == PantryLoadState.MALFORMED_JSON

    # 4. INVALID_CONTRACT
    pantry_path.write_text(
        json.dumps({"garlic bread": {"amount": -2, "unit": "loaves"}}),
        encoding="utf-8",
    )
    snap_invalid = load_pantry_snapshot(pantry_path)
    assert snap_invalid.state == PantryLoadState.INVALID_CONTRACT

    # 5. VALID_LIVE
    live_payload = {
        "garlic bread": {"amount": 3, "unit": "loaves"}
    }
    pantry_path.write_text(json.dumps(live_payload), encoding="utf-8")
    snap_live = load_pantry_snapshot(pantry_path)

    assert snap_live.state == PantryLoadState.VALID_LIVE
    assert snap_live.contract_verified is True
    assert "does not prove authenticity" in snap_live.evidence_note

    view_live, src_live = view_from_snapshot(snap_live)
    assert src_live == "live pantry.json"
    assert view_live == live_payload


def test_legacy_load_pantry_tuple_contract_preserved(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    fallback_data, fallback_src = load_pantry(missing_file)

    assert fallback_src == "fallback rations"
    assert set(fallback_data) == set(FALLBACK_RATIONS)

    live_file = tmp_path / "live.json"
    expected = {"butter": {"amount": 1.0, "unit": "stick"}}
    live_file.write_text(json.dumps(expected), encoding="utf-8")

    live_data, live_src = load_pantry(live_file)
    assert live_src == "live pantry.json"
    assert live_data == expected

# ---------------------------------------------------------------------------
# Narrative welcome token, GUILD boundaries & render_turn non-mutation
# ---------------------------------------------------------------------------

def test_welcome_token_narrative_only_and_guild_honest_telemetry(tmp_path):
    snap = load_pantry_snapshot(tmp_path / "pantry.json")
    view, src = view_from_snapshot(snap)

    before_view = deepcopy(view)
    before_snap_data = deepcopy(snap.data)

    inv_turn = render_turn(
        "INVENTORY", view, src, random.Random(1)
    )
    assert "WELCOME TOKEN IS NARRATIVE-ONLY" in inv_turn

    expected_malfunction = random.Random(1).choice(MALFUNCTIONS)
    assert expected_malfunction in inv_turn

    token_turn = render_turn(
        "INSPECT garlic bread", view, src, random.Random(1)
    )
    assert WELCOME_TOKEN_LINE in token_turn
    assert INSCRIPTION_LINE in token_turn

    guild_text = render_guild(snap)
    assert (
        "Detector status unavailable. Evidence: "
        "no detector result supplied."
    ) in guild_text
    assert "stitched_horizon" not in guild_text

    assert view == before_view
    assert snap.data == before_snap_data


# ---------------------------------------------------------------------------
# Ephemeral SessionJournal & provenance
# ---------------------------------------------------------------------------

def test_session_journal_missing_journal_guard_and_provenance(tmp_path):
    snap = load_pantry_snapshot(tmp_path / "pantry.json")

    sense_err, sense_quit = dispatch_command(
        "SENSE note", snap, journal=None
    )
    log_err, log_quit = dispatch_command(
        "LOG", snap, journal=None
    )

    assert sense_quit is False
    assert log_quit is False
    assert "no journal supplied" in sense_err.lower()
    assert "cannot read session log" in log_err.lower()

    journal = SessionJournal()
    assert (
        "No in-memory session notes recorded in this run."
        in render_log(journal)
    )

    obs1 = journal.record(snap, "")
    obs2 = journal.record(snap, "  cool  draft   near  stairs ")

    assert obs1.origin == "fallback_state_note"
    assert obs2.origin == "user_input"

    log_out = render_log(journal)
    assert "origin=fallback_state_note" in log_out
    assert "origin=user_input" in log_out
    assert "cool draft near stairs" in log_out
    assert "IN-MEMORY ONLY — NOT PERSISTED" in log_out

# ---------------------------------------------------------------------------
# Subprocess journal isolation & file preservation
# ---------------------------------------------------------------------------

def test_subprocess_ephemeral_journal_and_file_mtime_preservation(tmp_path):
    pantry_file = tmp_path / "pantry.json"
    pantry_file.write_text(
        json.dumps({
            "garlic bread": {"amount": 2, "unit": "loaves"}
        }, indent=2),
        encoding="utf-8",
    )

    _prepare_subprocess_files(tmp_path)
    before = _fingerprint_file_contents_and_mtime(tmp_path)

    run1 = _run_zork_subprocess(
        tmp_path,
        commands="LOG\nSENSE quiet hum\nGUILD\nLOG\nQUIT\n",
    )

    assert run1.returncode == 0
    assert run1.stderr == ""
    assert "No in-memory session notes recorded in this run." in run1.stdout
    assert "origin=user_input" in run1.stdout
    assert "quiet hum" in run1.stdout
    assert "Detector status unavailable." in run1.stdout
    assert _fingerprint_file_contents_and_mtime(tmp_path) == before

    run2 = _run_zork_subprocess(
        tmp_path,
        commands="LOG\nQUIT\n",
    )

    assert run2.returncode == 0
    assert run2.stderr == ""
    assert "quiet hum" not in run2.stdout
    assert "No in-memory session notes recorded in this run." in run2.stdout
    assert _fingerprint_file_contents_and_mtime(tmp_path) == before


# ---------------------------------------------------------------------------
# Subprocess SENSE and LOG across all five pantry states
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "mode,expected_state",
    [
        ("missing", "missing_file"),
        ("unreadable", "unreadable_file"),
        ("malformed", "malformed_json"),
        ("invalid", "valid_json_invalid_contract"),
        ("valid", "valid_json_valid_contract"),
    ],
)
def test_subprocess_sense_and_log_across_all_five_states(
    tmp_path, mode, expected_state
):
    pantry_file = tmp_path / "pantry.json"
    extra_path = None

    if mode == "unreadable":
        pantry_file.write_text(
            json.dumps({
                "garlic bread": {"amount": 2, "unit": "loaves"}
            }),
            encoding="utf-8",
        )
        (tmp_path / "sitecustomize.py").write_text(
            UNREADABLE_SITECUSTOMIZE,
            encoding="utf-8",
        )
        extra_path = tmp_path

    elif mode == "malformed":
        pantry_file.write_text(
            '{"garlic bread": {"amount": 2',
            encoding="utf-8",
        )

    elif mode == "invalid":
        pantry_file.write_text(
            json.dumps({
                "garlic bread": {"amount": -1, "unit": "loaves"}
            }),
            encoding="utf-8",
        )

    elif mode == "valid":
        pantry_file.write_text(
            json.dumps({
                "garlic bread": {"amount": 2, "unit": "loaves"}
            }),
            encoding="utf-8",
        )

    _prepare_subprocess_files(tmp_path)
    before = _fingerprint_file_contents_and_mtime(tmp_path)

    result = _run_zork_subprocess(
        tmp_path,
        commands="SENSE\nLOG\nQUIT\n",
        extra_pythonpath=extra_path,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert f"state={expected_state}" in result.stdout
    assert f"recorded pantry state={expected_state}" in result.stdout
    assert _fingerprint_file_contents_and_mtime(tmp_path) == before
