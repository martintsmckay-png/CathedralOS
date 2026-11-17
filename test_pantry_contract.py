import json
import math
from pathlib import Path
import pytest

from validate_pantry_contract import validate_pantry, validate_pantry_data


@pytest.fixture
def pantry_data():
    pantry_path = Path("pantry.json")
    assert pantry_path.exists(), "pantry.json is missing."
    return json.loads(pantry_path.read_text(encoding="utf-8"))


# --- Live Read-Only Pantry Checks ---

def test_pantry_has_entries(pantry_data):
    assert len(pantry_data) > 0, "Pantry is empty."


def test_every_item_has_amount(pantry_data):
    for name, item in pantry_data.items():
        assert "amount" in item, f"'{name}' lacks an 'amount' field."


def test_every_item_has_unit(pantry_data):
    for name, item in pantry_data.items():
        assert "unit" in item, f"'{name}' lacks a 'unit' field."


def test_amount_is_numeric_and_not_bool(pantry_data):
    for name, item in pantry_data.items():
        amount = item["amount"]
        assert not isinstance(amount, bool), f"'{name}' amount cannot be boolean."
        assert isinstance(amount, (int, float)), f"'{name}' amount is not numeric."
        assert math.isfinite(amount), f"'{name}' amount must be finite."


def test_unit_is_non_empty_string(pantry_data):
    for name, item in pantry_data.items():
        assert isinstance(item["unit"], str) and item["unit"].strip(), f"'{name}' unit is invalid."


def test_no_negative_amounts(pantry_data):
    for name, item in pantry_data.items():
        assert item["amount"] >= 0, f"'{name}' has a negative amount."


# --- Isolated Fail-Closed Contract Tests ---

def test_rejects_boolean_amount():
    with pytest.raises(ValueError, match="not bool"):
        validate_pantry_data({"butter": {"amount": True, "unit": "g"}})


def test_rejects_non_finite_amount():
    with pytest.raises(ValueError, match="finite"):
        validate_pantry_data({"butter": {"amount": float("nan"), "unit": "g"}})
    with pytest.raises(ValueError, match="finite"):
        validate_pantry_data({"butter": {"amount": float("inf"), "unit": "g"}})


def test_rejects_negative_amount():
    with pytest.raises(ValueError, match="negative"):
        validate_pantry_data({"butter": {"amount": -5, "unit": "g"}})


def test_rejects_empty_unit_or_name():
    with pytest.raises(ValueError, match="non-empty string"):
        validate_pantry_data({"butter": {"amount": 100, "unit": "   "}})
    with pytest.raises(ValueError, match="non-empty string"):
        validate_pantry_data({"   ": {"amount": 100, "unit": "g"}})


def test_rejects_non_dict_root_or_empty():
    with pytest.raises(ValueError, match="dictionary"):
        validate_pantry_data(["butter"])
    with pytest.raises(ValueError, match="empty"):
        validate_pantry_data({})


def test_validate_pantry_file_isolated(tmp_path):
    sample = tmp_path / "pantry.json"
    sample.write_text(json.dumps({"oats": {"amount": 500, "unit": "g"}}), encoding="utf-8")
    validate_pantry(sample)
