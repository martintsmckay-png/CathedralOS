import json
import math

import pytest

import recipe_gate as gate


@pytest.fixture
def isolated_pantry(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "PANTRY_FILE", tmp_path / "pantry.json")
    monkeypatch.setattr(gate, "RESTOCK_LOG", tmp_path / "restock_log.jsonl")
    monkeypatch.setattr(gate, "SHOPPING_JSON", tmp_path / "shopping_list.json")
    monkeypatch.setattr(gate, "SHOPPING_CSV", tmp_path / "shopping_list.csv")

    gate.save_json(gate.PANTRY_FILE, {
        "peanut butter": {"amount": 100.0, "unit": "g"}
    })
    return tmp_path


@pytest.mark.parametrize("quantity", [
    -1,
    float("nan"),
    float("inf"),
    float("-inf"),
])
def test_rejects_invalid_quantities(isolated_pantry, quantity):
    before = gate.PANTRY_FILE.read_bytes()

    with pytest.raises(ValueError):
        gate.restock("peanut butter", quantity, "g")

    assert gate.PANTRY_FILE.read_bytes() == before
    assert not gate.RESTOCK_LOG.exists()


def test_rejects_non_numeric_quantity(isolated_pantry):
    before = gate.PANTRY_FILE.read_bytes()

    with pytest.raises(ValueError):
        gate.restock("peanut butter", "not-a-number", "g")

    assert gate.PANTRY_FILE.read_bytes() == before
    assert not gate.RESTOCK_LOG.exists()


def test_rejects_boolean_quantity(isolated_pantry):
    with pytest.raises(ValueError):
        gate.restock("peanut butter", True, "g")

    assert gate.load_pantry(strict=True)["peanut butter"]["amount"] == 100.0


def test_rejects_unit_mismatch_without_mutation(isolated_pantry):
    before = gate.PANTRY_FILE.read_bytes()

    with pytest.raises(ValueError, match="Unit mismatch"):
        gate.restock("peanut butter", 10, "litres")

    assert gate.PANTRY_FILE.read_bytes() == before
    assert not gate.RESTOCK_LOG.exists()


def test_alias_restock_records_prepared_and_committed(isolated_pantry):
    assert gate.restock("creamy peanut butter", 100, "g") is True

    pantry = gate.load_pantry(strict=True)
    assert pantry["peanut butter"]["amount"] == 200.0

    events = [
        json.loads(line)
        for line in gate.RESTOCK_LOG.read_text().splitlines()
    ]

    assert [event["event"] for event in events] == [
        "PREPARED",
        "COMMITTED",
    ]
    assert events[0]["transaction_id"] == events[1]["transaction_id"]
    assert events[0]["new_amount"] == 200.0
    assert events[1]["new_amount"] == 200.0
    assert events[0]["timestamp"].endswith("+00:00")


def test_failed_prepared_ledger_write_preserves_inventory(
    isolated_pantry, monkeypatch
):
    before = gate.PANTRY_FILE.read_bytes()

    def fail_ledger(event):
        raise OSError("simulated ledger failure")

    monkeypatch.setattr(gate, "append_ledger_event", fail_ledger)

    with pytest.raises(OSError, match="simulated ledger failure"):
        gate.restock("peanut butter", 25, "g")

    assert gate.PANTRY_FILE.read_bytes() == before


def test_failed_commit_event_is_reported_as_unresolved(
    isolated_pantry, monkeypatch
):
    original_append = gate.append_ledger_event

    def fail_commit(event):
        if event["event"] == "COMMITTED":
            raise OSError("simulated commit-event failure")
        original_append(event)

    monkeypatch.setattr(gate, "append_ledger_event", fail_commit)

    with pytest.raises(RuntimeError, match="Inventory was committed"):
        gate.restock("peanut butter", 25, "g")

    assert gate.load_pantry(strict=True)["peanut butter"]["amount"] == 125.0

    pending = gate.unresolved_transactions()
    assert len(pending) == 1
    assert pending[0]["event"] == "PREPARED"
    assert pending[0]["new_amount"] == 125.0


def test_damaged_inventory_is_not_treated_as_empty(isolated_pantry):
    gate.PANTRY_FILE.write_text("{ damaged json", encoding="utf-8")

    with pytest.raises(ValueError, match="Cannot safely load pantry"):
        gate.restock("peanut butter", 25, "g")

    assert gate.PANTRY_FILE.read_text(encoding="utf-8") == "{ damaged json"
    assert not gate.RESTOCK_LOG.exists()


def test_unmatched_prepared_event_is_detected(isolated_pantry):
    gate.append_ledger_event({
        "event": "PREPARED",
        "transaction_id": "test-transaction",
        "ingredient": "peanut butter",
        "new_amount": 125.0,
        "new_unit": "g",
    })

    pending = gate.unresolved_transactions()
    assert len(pending) == 1
    assert pending[0]["transaction_id"] == "test-transaction"


def test_restock_refuses_new_transaction_while_one_is_unresolved(
    isolated_pantry,
):
    gate.append_ledger_event({
        "event": "PREPARED",
        "transaction_id": "interrupted-transaction",
        "ingredient": "peanut butter",
        "new_amount": 125.0,
        "new_unit": "g",
    })

    pantry_before = gate.PANTRY_FILE.read_bytes()
    ledger_before = gate.RESTOCK_LOG.read_bytes()

    with pytest.raises(RuntimeError, match="unresolved restock transaction"):
        gate.restock("peanut butter", 25, "g")

    assert gate.PANTRY_FILE.read_bytes() == pantry_before
    assert gate.RESTOCK_LOG.read_bytes() == ledger_before
    assert len(gate.unresolved_transactions()) == 1


def test_committed_event_clears_pending_transaction(isolated_pantry):
    transaction_id = "test-transaction"

    gate.append_ledger_event({
        "event": "PREPARED",
        "transaction_id": transaction_id,
    })
    gate.append_ledger_event({
        "event": "COMMITTED",
        "transaction_id": transaction_id,
    })

    assert gate.unresolved_transactions() == []


def test_historical_restock_events_remain_compatible(isolated_pantry):
    gate.RESTOCK_LOG.write_text(
        json.dumps({
            "event": "RESTOCK",
            "ingredient": "butter",
            "amount": 100,
            "unit": "g",
            "new_amount": 100,
            "new_unit": "g",
        }) + "\n",
        encoding="utf-8",
    )

    assert gate.unresolved_transactions() == []


def test_strict_loader_rejects_non_finite_existing_stock(isolated_pantry):
    gate.PANTRY_FILE.write_text(
        '{"peanut butter": {"amount": NaN, "unit": "g"}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="finite and non-negative"):
        gate.load_pantry(strict=True)


def test_zero_quantity_is_valid(isolated_pantry):
    assert gate.restock("peanut butter", 0, "g") is True
    assert gate.load_pantry(strict=True)["peanut butter"]["amount"] == 100.0


def test_directory_sync_failure_reports_inventory_was_replaced(
    isolated_pantry, monkeypatch
):
    original_fsync = gate.os.fsync
    calls = 0

    def fail_directory_sync(fd):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated directory fsync failure")
        return original_fsync(fd)

    monkeypatch.setattr(gate.os, "fsync", fail_directory_sync)

    with pytest.raises(
        RuntimeError,
        match="Inventory was replaced.*directory durability confirmation failed",
    ):
        gate.restock("peanut butter", 25, "g")

    # The file replacement happened before the directory fsync failure.
    assert gate.load_pantry(strict=True)["peanut butter"]["amount"] == 125.0

    # No COMMITTED event was appended, so reconciliation is still required.
    pending = gate.unresolved_transactions()
    assert len(pending) == 1
    assert pending[0]["event"] == "PREPARED"
    assert pending[0]["new_amount"] == 125.0

