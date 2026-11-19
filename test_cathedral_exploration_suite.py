import hashlib
import random
from pathlib import Path
from types import SimpleNamespace

import cathedral_exploration as exploration
import pantry_zork


def make_snapshot():
    return pantry_zork.PantrySnapshot(
        state=pantry_zork.PantryLoadState.VALID_LIVE,
        data={"Flour": {"amount": 2, "unit": "cups"}},
        contract_verified=True,
    )


def test_five_chamber_graph_has_expected_exits():
    expected = {
        "pantry": {
            "NORTH": "clock_tower",
            "EAST": "library",
            "WEST": "audio_foundry",
            "SOUTH": "sanctum",
        },
        "clock_tower": {"SOUTH": "pantry"},
        "library": {"WEST": "pantry"},
        "audio_foundry": {"EAST": "pantry"},
        "sanctum": {"NORTH": "pantry"},
    }

    for chamber_id, exits in expected.items():
        actual = {
            direction.value: destination
            for direction, destination
            in exploration.CHAMBERS[chamber_id].exits
        }
        assert actual == exits


def test_movement_returns_new_state_without_mutating_original():
    original = exploration.ExplorationState()

    result = exploration.move(original, "NORTH")

    assert result.moved
    assert result.state.chamber_id == "clock_tower"
    assert result.state.visited == ("pantry", "clock_tower")
    assert original.chamber_id == "pantry"
    assert original.visited == ("pantry",)


def test_invalid_exit_preserves_state():
    original = exploration.ExplorationState("clock_tower")

    result = exploration.move(original, "EAST")

    assert not result.moved
    assert result.state is original
    assert original.chamber_id == "clock_tower"


def test_map_and_chamber_rendering():
    state = exploration.ExplorationState()

    map_text = exploration.render_map(state)
    chamber_text = exploration.render_chamber(state)

    for title in (
        "Pantry", "Clock Tower", "Library",
        "Audio Foundry", "Sanctum",
    ):
        assert title in map_text

    assert "Pantry" in chamber_text
    assert "NORTH" in chamber_text
    assert "EAST" in chamber_text


def test_dispatch_navigation_is_opt_in():
    snapshot = make_snapshot()
    session = {"state": exploration.ExplorationState()}

    output, quit_requested = pantry_zork.dispatch_command(
        "MOVE NORTH", snapshot, rng=random.Random(369),
        exploration=session,
    )

    assert not quit_requested
    assert "Clock Tower" in output
    assert session["state"].chamber_id == "clock_tower"

    output, _ = pantry_zork.dispatch_command(
        "CHAMBER", snapshot, exploration=session
    )
    assert "Clock Tower" in output

    output, _ = pantry_zork.dispatch_command(
        "MOVE SOUTH", snapshot, exploration=session
    )
    assert "Pantry" in output
    assert session["state"].chamber_id == "pantry"


def test_legacy_audio_commands_remain_unchanged(monkeypatch):
    calls = []

    def fake_audio(label):
        calls.append(label)
        return "LEGACY AUDIO BRIDGE"

    monkeypatch.setattr(
        pantry_zork, "describe_audio_bridge", fake_audio
    )

    snapshot = make_snapshot()

    for command in ("GO NORTH", "NORTH", "PLAY GRAMOPHONE"):
        output, quit_requested = pantry_zork.dispatch_command(
            command, snapshot, rng=random.Random(369),
            exploration={"state": exploration.ExplorationState()},
        )
        assert not quit_requested
        assert "LEGACY AUDIO BRIDGE" in output

    assert len(calls) == 3


def test_pantry_evidence_reuses_injected_snapshot(tmp_path):
    snapshot = make_snapshot()

    # This file would be reported as ordinary file evidence if the
    # Pantry reader performed an additional disk inspection.
    (tmp_path / "pantry.json").write_text(
        '{"disk_read": true}', encoding="utf-8"
    )

    calls = []

    def reader():
        calls.append("snapshot")
        return snapshot

    report = exploration.inspect_chamber(
        exploration.ExplorationState(),
        root=tmp_path,
        pantry_reader=reader,
    )

    assert calls == ["snapshot"]
    assert report.mutated is False
    assert any(
        item.path == "pantry.json" and item.status == "snapshot"
        for item in report.items
    )
    assert not any(
        item.status == "read" for item in report.items
    )


def test_allowlisted_inspection_preserves_file(tmp_path):
    relative = "audit/baseline/timestamp.txt"
    target = tmp_path / relative
    target.parent.mkdir(parents=True)
    target.write_text("2026-11-02T08:41:38Z\n", encoding="utf-8")

    before_bytes = target.read_bytes()
    before_stat = target.stat()
    before_hash = hashlib.sha256(before_bytes).hexdigest()

    items = exploration.inspect_allowlisted_files(
        tmp_path, (relative,)
    )

    after_stat = target.stat()
    after_bytes = target.read_bytes()

    assert len(items) == 1
    assert items[0].status == "read"
    assert items[0].sha256_hex == before_hash
    assert after_bytes == before_bytes
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns


def test_file_inspection_enforces_size_and_count_limits(tmp_path):
    (tmp_path / "large.txt").write_text(
        "0123456789", encoding="utf-8"
    )
    (tmp_path / "second.txt").write_text(
        "second", encoding="utf-8"
    )

    items = exploration.inspect_allowlisted_files(
        tmp_path,
        ("large.txt", "second.txt"),
        max_file_bytes=5,
        max_files=1,
    )

    assert items[0].status == "size_limited"
    assert items[-1].status == "limit_reached"


def test_path_traversal_is_rejected(tmp_path):
    items = exploration.inspect_allowlisted_files(
        tmp_path, ("../outside.txt",)
    )

    assert len(items) == 1
    assert items[0].status == "rejected"


def test_evidence_report_does_not_claim_mutation(tmp_path):
    report = exploration.inspect_chamber(
        exploration.ExplorationState("clock_tower"),
        root=tmp_path,
    )

    assert report.mutated is False
    assert any(
        "monotonic-clock" in limitation
        for limitation in report.limitations
    )
    assert any(
        "live event stream" in limitation
        for limitation in report.limitations
    )


from pathlib import Path
import pytest

from cathedral_exploration import (
    ExplorationState,
    inspect_allowlisted_files,
    inspect_chamber,
)


def test_hardening_01_rejects_symlinked_leaf_file(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    outside = tmp_path / "outside.json"
    outside.write_text('{"secret": "outside"}', encoding="utf-8")

    link = root / "linked.json"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")

    items = inspect_allowlisted_files(root, ("linked.json",))
    assert items[0].status != "read"
    assert items[0].sha256_hex is None


def test_hardening_02_rejects_symlinked_parent_directory(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.json").write_text('{"secret": true}', encoding="utf-8")

    try:
        (root / "linked_dir").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")

    items = inspect_allowlisted_files(root, ("linked_dir/secret.json",))
    assert items[0].status != "read"
    assert items[0].sha256_hex is None


def test_hardening_03_empty_jsonl_is_valid(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    (root / "empty.jsonl").write_text("", encoding="utf-8")

    items = inspect_allowlisted_files(root, ("empty.jsonl",))
    item = items[0]

    assert item.status == "read"
    assert item.parsed_kind == "jsonl_syntax_valid"
    assert "0 non-empty JSON lines" in item.detail


def test_hardening_04_malformed_json_and_jsonl_are_invalid(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    (root / "broken.json").write_text('{"bad":', encoding="utf-8")
    (root / "broken.jsonl").write_text(
        '{"ok": true}\n{broken json\n',
        encoding="utf-8",
    )

    items = inspect_allowlisted_files(
        root,
        ("broken.json", "broken.jsonl"),
    )

    assert len(items) == 2
    assert all(item.status == "read" for item in items)
    assert items[0].parsed_kind == "json_syntax_invalid"
    assert items[1].parsed_kind == "jsonl_syntax_invalid"


def test_hardening_05_zero_byte_limit_rejects_nonempty_file(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    (root / "payload.txt").write_text("non-empty", encoding="utf-8")

    items = inspect_allowlisted_files(
        root,
        ("payload.txt",),
        max_file_bytes=0,
    )

    assert items[0].status == "size_limited"
    assert items[0].sha256_hex is None


@pytest.mark.parametrize(
    "bad_return",
    [False, None, "", "ERROR: bridge failed", "UNAVAILABLE: read error"],
)
def test_hardening_06_callbacks_do_not_claim_unverified_success(
    tmp_path: Path,
    bad_return: object,
):
    root = tmp_path / "repo"
    root.mkdir()

    audio_report = inspect_chamber(
        ExplorationState(chamber_id="audio_foundry"),
        root=root,
        audio_reader=lambda: bad_return,
    )

    assert any(
        item.status == "callback_unverified"
        for item in audio_report.items
    )
    assert not any(
        "Injected audio reader returned:" in claim
        for claim in audio_report.claims
    )
    assert audio_report.mutated is False

    pantry_report = inspect_chamber(
        ExplorationState(chamber_id="pantry"),
        root=root,
        pantry_reader=lambda: bad_return,
    )

    assert any(
        item.status == "callback_unverified"
        for item in pantry_report.items
    )
    assert not any(
        "Injected pantry snapshot returned" in claim
        for claim in pantry_report.claims
    )
    assert pantry_report.mutated is False


def test_hardening_06b_raised_callbacks_are_unverified(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()

    def raise_reader():
        raise RuntimeError("callback failure")

    audio_report = inspect_chamber(
        ExplorationState(chamber_id="audio_foundry"),
        root=root,
        audio_reader=raise_reader,
    )

    pantry_report = inspect_chamber(
        ExplorationState(chamber_id="pantry"),
        root=root,
        pantry_reader=raise_reader,
    )

    for report in (audio_report, pantry_report):
        assert any(
            item.status == "callback_unverified"
            for item in report.items
        )
        assert report.mutated is False


@pytest.mark.parametrize(
    (
        "case_name",
        "make_reader",
        "expected_claim_fragment",
        "expected_limitation_fragment",
        "forbidden_limitation_fragments",
    ),
    [
        (
            "verified_true",
            lambda: make_snapshot(),
            "contract_verified=True",
            None,
            (
                "contract_verified=False",
                "did not report contract_verified=True",
            ),
        ),
        (
            "verified_false",
            lambda: SimpleNamespace(
                state=SimpleNamespace(value="DEGRADED_OR_UNVERIFIED"),
                contract_verified=False,
            ),
            "contract_verified=False",
            "contract_verified=False",
            ("did not report contract_verified=True",),
        ),
        (
            "verified_none",
            lambda: SimpleNamespace(
                state=SimpleNamespace(value="UNKNOWN_STATE"),
                contract_verified=None,
            ),
            "contract_verified=None",
            "did not report contract_verified=True",
            ("contract_verified=False",),
        ),
        (
            "verified_missing_attr",
            lambda: SimpleNamespace(
                state=SimpleNamespace(value="PARTIAL_OBJECT"),
            ),
            "contract_verified=None",
            "did not report contract_verified=True",
            ("contract_verified=False",),
        ),
    ],
    ids=[
        "verified_true",
        "verified_false",
        "verified_none",
        "verified_missing_attr",
    ],
)
def test_hardening_07_pantry_contract_verified_boundaries(
    tmp_path: Path,
    case_name: str,
    make_reader,
    expected_claim_fragment: str,
    expected_limitation_fragment: str | None,
    forbidden_limitation_fragments: tuple[str, ...],
):
    root = tmp_path / "repo"
    root.mkdir()

    report = exploration.inspect_chamber(
        exploration.ExplorationState("pantry"),
        root=root,
        pantry_reader=make_reader,
    )

    assert report.mutated is False
    assert any(expected_claim_fragment in claim for claim in report.claims)

    for forbidden in forbidden_limitation_fragments:
        assert not any(forbidden in lim for lim in report.limitations)

    if expected_limitation_fragment is not None:
        assert any(
            expected_limitation_fragment in lim
            for lim in report.limitations
        )
