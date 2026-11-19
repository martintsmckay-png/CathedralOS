import json
from pathlib import Path

from pantry_zork import PantryLoadState, load_pantry_snapshot
from pantry_contract_observer import observe_pantry_snapshot


def check(path):
    snapshot = load_pantry_snapshot(path)
    observation = observe_pantry_snapshot(snapshot)
    return snapshot, observation


def test_valid_disk_file_reaches_observer(tmp_path):
    path = tmp_path / "pantry.json"
    payload = {
        "garlic bread": {"amount": 3, "unit": "loaves"}
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    snapshot, observation = check(path)

    assert snapshot.state == PantryLoadState.VALID_LIVE
    assert observation.status == "conforms"
    assert observation.conforms is True
    assert observation.contract_verified is True
    assert observation.mutated is False


def test_empty_file_is_reported_as_unverified(tmp_path):
    path = tmp_path / "pantry.json"
    path.write_bytes(b"")

    snapshot, observation = check(path)

    assert snapshot.state == PantryLoadState.MALFORMED_JSON
    assert observation.status == "unverified"
    assert observation.conforms is False
    assert observation.contract_verified is False


def test_corrupted_header_is_reported_as_unverified(tmp_path):
    path = tmp_path / "pantry.json"
    path.write_bytes(b"CORRUPT_HEADER_0xDEADBEEF")

    snapshot, observation = check(path)

    assert snapshot.state == PantryLoadState.MALFORMED_JSON
    assert observation.status == "unverified"
    assert observation.loader_state == "MALFORMED_JSON"
    assert observation.contract_verified is False


def test_invalid_contract_reaches_observer(tmp_path):
    path = tmp_path / "pantry.json"
    payload = {
        "garlic bread": {"amount": -2, "unit": "loaves"}
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    snapshot, observation = check(path)

    assert snapshot.state == PantryLoadState.INVALID_CONTRACT
    assert observation.status == "invalid"
    assert observation.conforms is False
    assert observation.contract_verified is False


def test_missing_file_reaches_observer(tmp_path):
    path = tmp_path / "missing.json"

    snapshot, observation = check(path)

    assert snapshot.state == PantryLoadState.MISSING
    assert observation.status == "unverified"
    assert observation.contract_verified is False


def test_large_file_characterization(tmp_path):
    path = tmp_path / "large_pantry.json"

    # This is a test input size, NOT a declared production limit.
    payload = {
        f"ingredient-{index}": {
            "amount": 1,
            "unit": "unit",
        }
        for index in range(24000)
    }

    encoded = json.dumps(payload).encode("utf-8")
    assert len(encoded) > 1024 * 1024

    path.write_bytes(encoded)

    snapshot, observation = check(path)

    # Characterizes current behaviour in the absence of a size policy.
    assert snapshot.state == PantryLoadState.VALID_LIVE
    assert observation.status == "conforms"
    assert observation.mutated is False
