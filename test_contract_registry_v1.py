"""Independent tests for the v1.0 contract registry and Pantry inventory pilot."""

import copy
import math
import sys

import pytest

from contract_registry_v1 import (
    ContractEvaluation,
    ContractRegistry,
    ContractSpec,
    InvariantRule,
    PANTRY_CONTRACT_ID,
    PANTRY_CONTRACT_VERSION,
    build_default_registry,
)
from validate_pantry_contract import validate_pantry_data as canonical_validate


def test_pantry_v1_conforms_on_valid_payload():
    registry = build_default_registry()
    payload = {
        "oats": {"amount": 2, "unit": "cups"},
        "honey": {"amount": 1.5, "unit": "tbsp"},
        "salt": {"amount": 0, "unit": "tsp"},
    }
    canonical_validate(payload)

    result = registry.evaluate(PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION, payload)
    assert result.status == "conforms"
    assert result.conforms is True
    assert result.mutated is False
    assert result.errors == ()
    assert len(result.claims) == 8
    assert any("authenticity, provenance" in item for item in result.limitations)


@pytest.mark.parametrize(
    "bad_payload,expected_rule_id",
    [
        ("not-a-dict", "PANTRY_ROOT_NONEMPTY_DICT"),
        ({}, "PANTRY_ROOT_NONEMPTY_DICT"),
        ({"": {"amount": 1, "unit": "g"}}, "PANTRY_INGREDIENT_NAME_NONEMPTY"),
        ({"flour": "not-a-dict"}, "PANTRY_ITEM_DICT"),
        ({"flour": {"amount": 1}}, "PANTRY_ITEM_REQUIRED_KEYS"),
        ({"flour": {"unit": "g"}}, "PANTRY_ITEM_REQUIRED_KEYS"),
        ({"flour": {"amount": True, "unit": "g"}}, "PANTRY_AMOUNT_NUMERIC_NONBOOL"),
        ({"flour": {"amount": False, "unit": "g"}}, "PANTRY_AMOUNT_NUMERIC_NONBOOL"),
        ({"flour": {"amount": -1, "unit": "g"}}, "PANTRY_AMOUNT_NONNEGATIVE"),
        ({"flour": {"amount": math.nan, "unit": "g"}}, "PANTRY_AMOUNT_FINITE"),
        ({"flour": {"amount": math.inf, "unit": "g"}}, "PANTRY_AMOUNT_FINITE"),
        ({"flour": {"amount": -math.inf, "unit": "g"}}, "PANTRY_AMOUNT_FINITE"),
        ({"flour": {"amount": 10, "unit": "   "}}, "PANTRY_UNIT_NONEMPTY"),
    ],
)
def test_pantry_v1_rejects_invalid_payloads_matching_canonical(bad_payload, expected_rule_id):
    registry = build_default_registry()

    with pytest.raises(ValueError):
        canonical_validate(bad_payload)

    result = registry.evaluate(PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION, bad_payload)
    assert result.status == "invalid"
    assert result.conforms is False
    assert result.mutated is False
    assert any(expected_rule_id in err for err in result.errors)


def test_unverified_status_is_distinct_from_invalid():
    registry = build_default_registry()
    payload = {"oats": {"amount": 2, "unit": "cups"}}

    result = registry.evaluate(
        PANTRY_CONTRACT_ID,
        PANTRY_CONTRACT_VERSION,
        payload,
        evidence_available=False,
    )
    assert result.status == "unverified"
    assert result.conforms is False
    assert result.mutated is False
    assert len(result.errors) == 1


@pytest.mark.parametrize(
    "bad_id,bad_version",
    [
        (PANTRY_CONTRACT_ID, "2.0"),
        (PANTRY_CONTRACT_ID, "0.9"),
        ("cathedralos.pantry.inventory.unknown", PANTRY_CONTRACT_VERSION),
        ("1.0", PANTRY_CONTRACT_VERSION),
    ],
)
def test_unsupported_version_or_id_does_not_fallback(monkeypatch, bad_id, bad_version):
    registry = build_default_registry()

    def _boom_import(*args, **kwargs):
        raise AssertionError("Unsupported contract lookup must not trigger imports.")

    monkeypatch.setattr("builtins.__import__", _boom_import)
    result = registry.evaluate(bad_id, bad_version, {"oats": {"amount": 1, "unit": "cup"}})
    assert result.status == "unsupported_version"
    assert result.conforms is False
    assert result.mutated is False
    assert len(result.errors) == 1


def test_evaluation_does_not_mutate_input_or_pantry_zork():
    registry = build_default_registry()
    original_payload = {"flour": {"amount": 500, "unit": "g"}}
    snapshot = copy.deepcopy(original_payload)
    pantry_zork_before = sys.modules.get("pantry_zork")

    result = registry.evaluate(PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION, original_payload)
    assert result.conforms is True
    assert original_payload == snapshot
    assert sys.modules.get("pantry_zork") is pantry_zork_before


def test_evaluation_rejects_unknown_status_or_mutated_true():
    with pytest.raises(ValueError):
        ContractEvaluation(
            contract_id=PANTRY_CONTRACT_ID,
            contract_version=PANTRY_CONTRACT_VERSION,
            status="bogus_status",
            conforms=False,
            mutated=False,
            errors=("some error",),
        )

    with pytest.raises(ValueError):
        ContractEvaluation(
            contract_id=PANTRY_CONTRACT_ID,
            contract_version=PANTRY_CONTRACT_VERSION,
            status="invalid",
            conforms=False,
            mutated=True,
            errors=("some error",),
        )


def test_evaluation_rejects_mutable_list_collections():
    with pytest.raises(TypeError):
        ContractEvaluation(
            contract_id="example",
            contract_version="1.0",
            status="invalid",
            conforms=False,
            mutated=False,
            claims=["claim"],
            errors=("failure",),
        )

    with pytest.raises(TypeError):
        ContractEvaluation(
            contract_id="example",
            contract_version="1.0",
            status="invalid",
            conforms=False,
            mutated=False,
            errors=["failure"],
        )

    with pytest.raises(TypeError):
        ContractEvaluation(
            contract_id="example",
            contract_version="1.0",
            status="invalid",
            conforms=False,
            mutated=False,
            limitations=["limitation"],
            errors=("failure",),
        )


def test_registry_rejects_invalid_contract_definitions_and_list_collections():
    good_rule = InvariantRule(
        rule_id="TEST_RULE",
        description="Always passes.",
        check=lambda _payload: [],
    )

    with pytest.raises(TypeError):
        ContractRegistry([
            ContractSpec(
                contract_id="cathedralos.test",
                contract_version="1.0",
                target_kind="payload",
                rules=[good_rule],  # type: ignore[arg-type]
            )
        ])

    with pytest.raises(TypeError):
        ContractRegistry([
            ContractSpec(
                contract_id="cathedralos.test",
                contract_version="1.0",
                target_kind="payload",
                rules=(good_rule,),
                limitations=["mutable limitation"],  # type: ignore[arg-type]
            )
        ])

    with pytest.raises(ValueError):
        ContractRegistry([
            ContractSpec(
                contract_id="   ",
                contract_version="1.0",
                target_kind="payload",
                rules=(good_rule,),
            )
        ])

    with pytest.raises(ValueError):
        ContractRegistry([
            ContractSpec(
                contract_id="cathedralos.test",
                contract_version="v1",
                target_kind="payload",
                rules=(good_rule,),
            )
        ])

    with pytest.raises(ValueError):
        ContractRegistry([
            ContractSpec(
                contract_id="cathedralos.test",
                contract_version="1.0",
                target_kind="payload",
                rules=(good_rule, good_rule),
            )
        ])


def test_evaluation_report_collections_are_tuples():
    registry = build_default_registry()
    result = registry.evaluate(PANTRY_CONTRACT_ID, PANTRY_CONTRACT_VERSION, {"oats": {"amount": 1, "unit": "cup"}})
    assert isinstance(result.claims, tuple)
    assert isinstance(result.limitations, tuple)
    assert isinstance(result.errors, tuple)
