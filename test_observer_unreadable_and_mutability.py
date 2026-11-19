"""Stage 3.5 boundary tests: unreadable handoff & post-load snapshot mutability."""

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest import mock

import pytest

from pantry_contract_observer import PantryContractObservation, observe_pantry_snapshot
from pantry_zork import PantryLoadState, PantrySnapshot, load_pantry_snapshot


def test_permission_error_unreadable_handoff_preserves_reason(tmp_path):
    pantry_path = tmp_path / "pantry.json"
    pantry_path.write_text('{"garlic bread": {"amount": 2, "unit": "loaves"}}', encoding="utf-8")

    with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
        snap = load_pantry_snapshot(pantry_path)

    assert isinstance(snap, PantrySnapshot)
    assert snap.state == PantryLoadState.UNREADABLE
    assert "PermissionError" in (snap.reason or "")

    obs = observe_pantry_snapshot(snap)
    assert isinstance(obs, PantryContractObservation)
    assert obs.status == "unverified"
    assert obs.conforms is False
    assert obs.contract_verified is False
    assert obs.mutated is False
    assert obs.evidence_source == "<in-memory-snapshot>"
    assert snap.reason is not None and snap.reason in obs.errors[0]
    assert len(obs.limitations) >= 1


def test_unicode_decode_error_unreadable_handoff_preserves_reason(tmp_path):
    pantry_path = tmp_path / "pantry.json"
    pantry_path.write_bytes(b"\xff\xfe\xfd invalid utf-8")

    snap = load_pantry_snapshot(pantry_path)
    assert snap.state == PantryLoadState.UNREADABLE
    assert "UnicodeDecodeError" in (snap.reason or "")

    obs = observe_pantry_snapshot(snap)
    assert obs.status == "unverified"
    assert obs.conforms is False
    assert obs.contract_verified is False
    assert obs.mutated is False
    assert obs.evidence_source == "<in-memory-snapshot>"
    assert snap.reason is not None and snap.reason in obs.errors[0]


def test_frozen_snapshot_wrapper_and_nested_data_mutation_reobservation(tmp_path):
    pantry_path = tmp_path / "pantry.json"
    pantry_path.write_text('{"garlic bread": {"amount": 2, "unit": "loaves"}}', encoding="utf-8")

    snap = load_pantry_snapshot(pantry_path)
    assert snap.state == PantryLoadState.VALID_LIVE

    obs_initial = observe_pantry_snapshot(snap)
    assert obs_initial.status == "conforms"
    assert obs_initial.conforms is True
    assert obs_initial.mutated is False

    # Outer dataclass fields cannot be reassigned.
    with pytest.raises(FrozenInstanceError):
        snap.data = {}  # type: ignore[misc]

    # Nested dict contents are currently mutable and detected on re-observation.
    snap.data["garlic bread"]["amount"] = -999
    obs_after = observe_pantry_snapshot(snap)
    assert obs_after.status == "invalid"
    assert obs_after.conforms is False
    assert obs_after.contract_verified is False
    assert obs_after.mutated is False
    assert any("PANTRY_AMOUNT_NONNEGATIVE" in err for err in obs_after.errors)
