import importlib
import math
import sys
import types

import pytest

import pantry_zork
from validate_pantry_contract import validate_pantry_data as canonical_validate


def _reload_pantry_zork_with_missing_contract(monkeypatch):
    monkeypatch.delitem(sys.modules, "validate_pantry_contract", raising=False)
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "validate_pantry_contract":
            raise ModuleNotFoundError("No module named 'validate_pantry_contract'", name="validate_pantry_contract")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    reloaded = importlib.reload(pantry_zork)
    return reloaded


def _reload_pantry_zork_with_broken_transitive_import(monkeypatch):
    monkeypatch.delitem(sys.modules, "validate_pantry_contract", raising=False)
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "validate_pantry_contract":
            raise ModuleNotFoundError("No module named 'missing_contract_dep'", name="missing_contract_dep")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    with pytest.raises(ModuleNotFoundError) as exc_info:
        importlib.reload(pantry_zork)
    assert exc_info.value.name == "missing_contract_dep"
    # Restore module cleanly for subsequent tests
    monkeypatch.setattr("builtins.__import__", real_import)
    return importlib.reload(pantry_zork)


@pytest.mark.parametrize(
    "payload",
    [
        {"oats": {"amount": 2, "unit": "cups"}},
        {"honey": {"amount": 1.5, "unit": "tbsp"}, "salt": {"amount": 0, "unit": "tsp"}},
        "not-a-dict",
        {},
        {"": {"amount": 1, "unit": "g"}},
        {"flour": "not-a-dict"},
        {"flour": {"amount": 1}},
        {"flour": {"unit": "g"}},
        {"flour": {"amount": True, "unit": "g"}},
        {"flour": {"amount": False, "unit": "g"}},
        {"flour": {"amount": -1, "unit": "g"}},
        {"flour": {"amount": math.nan, "unit": "g"}},
        {"flour": {"amount": math.inf, "unit": "g"}},
        {"flour": {"amount": -math.inf, "unit": "g"}},
        {"flour": {"amount": 10, "unit": "   "}},
    ],
)
def test_fallback_validator_matches_canonical_outcomes(monkeypatch, payload):
    fallback_mod = _reload_pantry_zork_with_missing_contract(monkeypatch)
    assert fallback_mod.validate_pantry_data.__doc__ == "Standalone compatibility validator."

    canonical_ok = True
    try:
        canonical_validate(payload)
    except ValueError:
        canonical_ok = False

    fallback_ok = True
    try:
        fallback_mod.validate_pantry_data(payload)
    except ValueError:
        fallback_ok = False

    assert fallback_ok is canonical_ok

    # Restore default pantry_zork import state
    monkeypatch.delitem(sys.modules, "validate_pantry_contract", raising=False)
    importlib.reload(pantry_zork)


def test_unrelated_import_error_propagates(monkeypatch):
    _reload_pantry_zork_with_broken_transitive_import(monkeypatch)
