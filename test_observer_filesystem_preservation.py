"""Filesystem, mtime_ns, and real PantrySnapshot boundary tests for Stage 3.3."""

import os
import time
from pathlib import Path

import pytest

from contract_registry_v1 import PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION
from pantry_contract_observer import observe_pantry_snapshot
from pantry_zork import PantrySnapshot


def _snapshot_stat(path: Path) -> tuple[bytes, int, int]:
    st = path.stat()
    return (path.read_bytes(), st.st_size, st.st_mtime_ns)


def test_filesystem_bytes_size_and_mtime_ns_unchanged_across_observations(tmp_path):
    pantry_path = tmp_path / "pantry.json"
    sidecar_log = tmp_path / "restock_log.jsonl"

    pantry_bytes = b'{\n  "bannock_flour": {"amount": 4, "unit": "cups"}\n}\n'
    log_bytes = b'{"event": "seed"}\n'

    pantry_path.write_bytes(pantry_bytes)
    sidecar_log.write_bytes(log_bytes)

    # Pin both files to a fixed historical timestamp in the past.
    pinned_sec = 1700000123.456789
    os.utime(pantry_path, ns=(int(pinned_sec * 1e9), int(pinned_sec * 1e9)))
    os.utime(sidecar_log, ns=(int(pinned_sec * 1e9), int(pinned_sec * 1e9)))

    before_pantry = _snapshot_stat(pantry_path)
    before_log = _snapshot_stat(sidecar_log)

    time.sleep(0.01)

    snap = PantrySnapshot(
        state="VALID_LIVE",
        data={"bannock_flour": {"amount": 4, "unit": "cups"}},
        contract_verified=True,
        reason="loaded from test fixture",
        evidence_note=str(pantry_path),
    )

    obs1 = observe_pantry_snapshot(snap)
    obs2 = observe_pantry_snapshot(snap)

    after_pantry = _snapshot_stat(pantry_path)
    after_log = _snapshot_stat(sidecar_log)

    assert obs1.status == "conforms"
    assert obs1.conforms is True
    assert obs1.contract_verified is True
    assert obs1.mutated is False
    assert obs2 == obs1

    assert after_pantry == before_pantry
    assert after_log == before_log


@pytest.mark.parametrize(
    "state_name,data,expected_status,expected_conforms",
    [
        ("MISSING", None, "unverified", False),
        ("UNREADABLE", None, "unverified", False),
        ("MALFORMED_JSON", None, "unverified", False),
        ("INVALID_CONTRACT", {"oats": {"amount": -2, "unit": "cups"}}, "invalid", False),
        ("VALID_LIVE", {"oats": {"amount": 2, "unit": "cups"}}, "conforms", True),
    ],
)
def test_real_pantry_snapshot_states_map_read_only(
    state_name, data, expected_status, expected_conforms
):
    snap = PantrySnapshot(
        state=state_name,
        data=data,
        contract_verified=False,
        reason=f"fixture state {state_name}",
        evidence_note="boundary test",
    )
    obs = observe_pantry_snapshot(
        snap,
        contract_id=PANTRY_CONTRACT_ID,
        contract_version=PANTRY_CONTRACT_VERSION,
    )
    assert obs.status == expected_status
    assert obs.conforms is expected_conforms
    assert obs.contract_verified is expected_conforms
    assert obs.mutated is False
    assert isinstance(obs.limitations, tuple) and len(obs.limitations) >= 1
