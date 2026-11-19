"""Boundary tests for the read-only Pantry contract observer (Stage 3.3)."""

import os
import time
from dataclasses import dataclass

import pytest

from contract_registry_v1 import PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION
from pantry_contract_observer import PantryContractObservation, observe_pantry_snapshot


@dataclass
class _StubSnapshot:
    state: str
    source_path: str
    parsed_data: object = None
    reason: str | None = None
    contract_verified: object = None


@pytest.mark.parametrize(
    "loader_state,reason",
    [
        ("MISSING", "file not found"),
        ("UNREADABLE", "permission denied"),
        ("MALFORMED_JSON", "json decode error"),
    ],
)
def test_missing_unreadable_malformed_map_to_unverified_not_invalid(loader_state, reason):
    snap = _StubSnapshot(
        state=loader_state,
        source_path="/tmp/pantry_stub.json",
        parsed_data=None,
        reason=reason,
    )
    obs = observe_pantry_snapshot(snap)
    assert obs.status == "unverified"
    assert obs.conforms is False
    assert obs.contract_verified is False
    assert obs.mutated is False
    assert obs.evidence_source == "/tmp/pantry_stub.json"
    assert isinstance(obs.errors, tuple) and len(obs.errors) == 1
    assert isinstance(obs.limitations, tuple) and len(obs.limitations) >= 1


def test_parsed_invalid_payload_maps_to_invalid():
    snap = _StubSnapshot(
        state="INVALID_CONTRACT",
        source_path="/tmp/pantry_bad.json",
        parsed_data={"flour": {"amount": -5, "unit": "g"}},
    )
    obs = observe_pantry_snapshot(snap)
    assert obs.status == "invalid"
    assert obs.conforms is False
    assert obs.contract_verified is False
    assert obs.mutated is False
    assert any("PANTRY_AMOUNT_NONNEGATIVE" in err for err in obs.errors)


def test_parsed_valid_payload_maps_to_conforms():
    snap = _StubSnapshot(
        state="VALID_LIVE",
        source_path="/tmp/pantry_good.json",
        parsed_data={"oats": {"amount": 2, "unit": "cups"}},
    )
    obs = observe_pantry_snapshot(snap)
    assert obs.status == "conforms"
    assert obs.conforms is True
    assert obs.contract_verified is True
    assert obs.mutated is False
    assert obs.errors == ()


@pytest.mark.parametrize("tricky_flag", ["yes", "true", 1, [], {}])
def test_truthy_contract_verified_flag_does_not_bypass_invalid_payload(tricky_flag):
    snap = _StubSnapshot(
        state="INVALID_CONTRACT",
        source_path="/tmp/pantry_tricky.json",
        parsed_data={"sugar": {"amount": -1, "unit": "cup"}},
        contract_verified=tricky_flag,
    )
    obs = observe_pantry_snapshot(snap)
    assert obs.status == "invalid"
    assert obs.conforms is False
    assert obs.contract_verified is False


@pytest.mark.parametrize("bad_amount", ["yes", "true", True, False, [], {}])
def test_non_numeric_or_bool_amounts_are_rejected(bad_amount):
    snap = _StubSnapshot(
        state="INVALID_CONTRACT",
        source_path="/tmp/pantry_bad_amt.json",
        parsed_data={"sugar": {"amount": bad_amount, "unit": "cup"}},
    )
    obs = observe_pantry_snapshot(snap)
    assert obs.status == "invalid"
    assert obs.conforms is False
    assert obs.contract_verified is False


def test_unsupported_contract_version_does_not_fallback(monkeypatch):
    def _no_import(*args, **kwargs):
        raise AssertionError("Observer must not trigger imports on unsupported contract.")

    monkeypatch.setattr("builtins.__import__", _no_import)
    snap = _StubSnapshot(
        state="VALID_LIVE",
        source_path="/tmp/pantry_good.json",
        parsed_data={"oats": {"amount": 2, "unit": "cups"}},
    )
    obs = observe_pantry_snapshot(snap, contract_version="9.9")
    assert obs.status == "unsupported_version"
    assert obs.conforms is False
    assert obs.contract_verified is False
    assert obs.mutated is False


def test_file_content_and_mtime_preserved_during_observation(tmp_path):
    pantry_file = tmp_path / "pantry.json"
    content = '{"rice": {"amount": 3, "unit": "cups"}}\n'
    pantry_file.write_text(content, encoding="utf-8")

    fixed_ts = 1700000000.0
    os.utime(pantry_file, (fixed_ts, fixed_ts))
    stat_before = pantry_file.stat()

    # Brief pause so any accidental rewrite would produce a newer mtime.
    time.sleep(0.01)

    snap = _StubSnapshot(
        state="VALID_LIVE",
        source_path=str(pantry_file),
        parsed_data={"rice": {"amount": 3, "unit": "cups"}},
    )
    obs = observe_pantry_snapshot(snap)
    stat_after = pantry_file.stat()

    assert isinstance(obs, PantryContractObservation)
    assert obs.conforms is True
    assert pantry_file.read_text(encoding="utf-8") == content
    assert stat_after.st_mtime_ns == stat_before.st_mtime_ns
    assert stat_after.st_size == stat_before.st_size


def test_observation_rejects_mutated_true_or_inconsistent_verification():
    with pytest.raises(ValueError):
        PantryContractObservation(
            contract_id=PANTRY_CONTRACT_ID,
            contract_version=PANTRY_CONTRACT_VERSION,
            status="invalid",
            conforms=False,
            contract_verified=False,
            mutated=True,
            evidence_source="test",
            loader_state="INVALID_CONTRACT",
            errors=("bad",),
        )

    with pytest.raises(ValueError):
        PantryContractObservation(
            contract_id=PANTRY_CONTRACT_ID,
            contract_version=PANTRY_CONTRACT_VERSION,
            status="unverified",
            conforms=False,
            contract_verified=True,
            mutated=False,
            evidence_source="test",
            loader_state="MISSING",
            errors=("missing",),
        )
