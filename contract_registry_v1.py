"""Standalone v1.0 read-only contract registry and evaluator for CathedralOS."""

from __future__ import annotations

import copy
import math
import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

PANTRY_CONTRACT_ID = "cathedralos.pantry.inventory"
PANTRY_CONTRACT_VERSION = "1.0"

VALID_STATUSES: frozenset[str] = frozenset(
    {"conforms", "invalid", "unverified", "unsupported_version"}
)
_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)$")

DEFAULT_LIMITATIONS: tuple[str, ...] = (
    "Schema conformance evaluates structure and values only; it does not establish "
    "authenticity, provenance, governance approval, or live runtime enforcement.",
    "In-memory read-only evaluation does not mutate passed objects or invoke "
    "fallback loaders; file-on-disk non-mutation is not established by payload-only "
    "evaluation.",
)


def _require_tuple_of_strings(value: object, field_name: str) -> None:
    if not isinstance(value, tuple):
        raise TypeError(f"{field_name} must be a tuple, got {type(value).__name__}.")
    for item in value:
        if not isinstance(item, str):
            raise TypeError(
                f"Elements of {field_name} must be str, got {type(item).__name__}."
            )


@dataclass(frozen=True)
class InvariantRule:
    """Executable invariant paired with a stable ID and description."""

    rule_id: str
    description: str
    check: Callable[[object], list[str]]


@dataclass(frozen=True)
class ContractSpec:
    """Versioned contract specification registered externally from payloads."""

    contract_id: str
    contract_version: str
    target_kind: str
    rules: tuple[InvariantRule, ...]
    limitations: tuple[str, ...] = DEFAULT_LIMITATIONS


@dataclass(frozen=True)
class ContractEvaluation:
    """Immutable read-only result of evaluating a payload against a contract."""

    contract_id: str
    contract_version: str
    status: str  # "conforms" | "invalid" | "unverified" | "unsupported_version"
    conforms: bool
    mutated: bool
    claims: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_tuple_of_strings(self.claims, "claims")
        _require_tuple_of_strings(self.limitations, "limitations")
        _require_tuple_of_strings(self.errors, "errors")

        if not isinstance(self.status, str) or self.status not in VALID_STATUSES:
            raise ValueError(f"Unknown evaluation status: {self.status!r}")
        if not isinstance(self.conforms, bool):
            raise TypeError("conforms must be a strict bool.")
        if not isinstance(self.mutated, bool):
            raise TypeError("mutated must be a strict bool.")
        if self.mutated is not False:
            raise ValueError("Read-only evaluations must report mutated=False.")
        if self.status == "conforms":
            if self.conforms is not True or self.errors:
                raise ValueError("Invalid conforms result.")
        elif self.conforms is not False or not self.errors:
            raise ValueError("Non-conforming results require errors.")


def _validate_contract_spec(spec: ContractSpec) -> None:
    if not isinstance(spec, ContractSpec):
        raise TypeError("spec must be a ContractSpec instance.")
    if not isinstance(spec.contract_id, str) or not spec.contract_id.strip():
        raise ValueError("Contract specification requires a non-empty contract_id.")
    if not isinstance(spec.contract_version, str) or not _VERSION_RE.match(
        spec.contract_version
    ):
        raise ValueError(
            f"Contract version must match MAJOR.MINOR format, got: {spec.contract_version!r}"
        )
    if not isinstance(spec.target_kind, str) or not spec.target_kind.strip():
        raise ValueError("Contract specification requires a non-empty target_kind.")

    if not isinstance(spec.rules, tuple):
        raise TypeError(
            f"ContractSpec.rules must be a tuple, got {type(spec.rules).__name__}."
        )
    if not spec.rules:
        raise ValueError("Contract specification requires at least one invariant rule.")

    _require_tuple_of_strings(spec.limitations, "ContractSpec.limitations")

    seen_rule_ids: set[str] = set()
    for rule in spec.rules:
        if not isinstance(rule, InvariantRule):
            raise TypeError("Each rule must be an InvariantRule instance.")
        if not isinstance(rule.rule_id, str) or not rule.rule_id.strip():
            raise ValueError("Invariant rule requires a non-empty rule_id.")
        if rule.rule_id in seen_rule_ids:
            raise ValueError(f"Duplicate invariant rule_id: {rule.rule_id!r}")
        seen_rule_ids.add(rule.rule_id)
        if not callable(rule.check):
            raise TypeError(f"Rule {rule.rule_id!r} check must be callable.")


def _check_root_nonempty_dict(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["[PANTRY_ROOT_NONEMPTY_DICT] Pantry root must be a dictionary."]
    if not payload:
        return ["[PANTRY_ROOT_NONEMPTY_DICT] Pantry cannot be empty."]
    return []


def _check_ingredient_names(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name in payload:
        if not isinstance(name, str) or not name.strip():
            errors.append(
                "[PANTRY_INGREDIENT_NAME_NONEMPTY] Ingredient name must be a non-empty string."
            )
    return errors


def _check_item_dicts(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if not isinstance(item, dict):
            errors.append(f"[PANTRY_ITEM_DICT] Item '{name}' must be a dictionary.")
    return errors


def _check_required_keys(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if isinstance(item, dict) and ("amount" not in item or "unit" not in item):
            errors.append(f"[PANTRY_ITEM_REQUIRED_KEYS] Item '{name}' is incomplete.")
    return errors


def _check_amount_numeric_nonbool(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if isinstance(item, dict) and "amount" in item:
            amount = item["amount"]
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                errors.append(
                    f"[PANTRY_AMOUNT_NUMERIC_NONBOOL] Amount for '{name}' must be numeric (not bool)."
                )
    return errors


def _check_amount_finite(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if isinstance(item, dict) and "amount" in item:
            amount = item["amount"]
            if not isinstance(amount, bool) and isinstance(amount, float):
                if not math.isfinite(amount):
                    errors.append(
                        f"[PANTRY_AMOUNT_FINITE] Amount for '{name}' must be finite."
                    )
    return errors


def _check_amount_nonnegative(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if isinstance(item, dict) and "amount" in item:
            amount = item["amount"]
            if not isinstance(amount, bool) and isinstance(amount, (int, float)):
                if isinstance(amount, float) and not math.isfinite(amount):
                    continue
                if amount < 0:
                    errors.append(
                        f"[PANTRY_AMOUNT_NONNEGATIVE] Amount for '{name}' cannot be negative."
                    )
    return errors


def _check_unit_nonempty(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    errors: list[str] = []
    for name, item in payload.items():
        if isinstance(item, dict) and "unit" in item:
            unit = item["unit"]
            if not isinstance(unit, str) or not unit.strip():
                errors.append(
                    f"[PANTRY_UNIT_NONEMPTY] Unit for '{name}' must be a non-empty string."
                )
    return errors


PANTRY_V1_RULES: tuple[InvariantRule, ...] = (
    InvariantRule(
        rule_id="PANTRY_ROOT_NONEMPTY_DICT",
        description="Root payload must be a non-empty dictionary.",
        check=_check_root_nonempty_dict,
    ),
    InvariantRule(
        rule_id="PANTRY_INGREDIENT_NAME_NONEMPTY",
        description="Each ingredient key must be a non-empty string.",
        check=_check_ingredient_names,
    ),
    InvariantRule(
        rule_id="PANTRY_ITEM_DICT",
        description="Each ingredient entry must be a dictionary.",
        check=_check_item_dicts,
    ),
    InvariantRule(
        rule_id="PANTRY_ITEM_REQUIRED_KEYS",
        description="Each ingredient entry must include 'amount' and 'unit'.",
        check=_check_required_keys,
    ),
    InvariantRule(
        rule_id="PANTRY_AMOUNT_NUMERIC_NONBOOL",
        description="Ingredient amount must be int or float and never bool.",
        check=_check_amount_numeric_nonbool,
    ),
    InvariantRule(
        rule_id="PANTRY_AMOUNT_FINITE",
        description="Floating-point ingredient amounts must be finite.",
        check=_check_amount_finite,
    ),
    InvariantRule(
        rule_id="PANTRY_AMOUNT_NONNEGATIVE",
        description="Ingredient amount must not be less than zero.",
        check=_check_amount_nonnegative,
    ),
    InvariantRule(
        rule_id="PANTRY_UNIT_NONEMPTY",
        description="Ingredient unit must be a non-empty string.",
        check=_check_unit_nonempty,
    ),
)

PANTRY_INVENTORY_V1 = ContractSpec(
    contract_id=PANTRY_CONTRACT_ID,
    contract_version=PANTRY_CONTRACT_VERSION,
    target_kind="payload",
    rules=PANTRY_V1_RULES,
)


class ContractRegistry:
    """Read-only registry keyed strictly by (contract_id, contract_version)."""

    def __init__(self, specs: Iterable[ContractSpec] = ()) -> None:
        self._specs: dict[tuple[str, str], ContractSpec] = {}
        for spec in specs:
            _validate_contract_spec(spec)
            key = (spec.contract_id, spec.contract_version)
            if key in self._specs:
                raise ValueError(f"Duplicate contract registration for {key!r}.")
            self._specs[key] = spec

    def get(self, contract_id: str, contract_version: str) -> ContractSpec | None:
        return self._specs.get((contract_id, contract_version))

    def evaluate(
        self,
        contract_id: str,
        contract_version: str,
        payload: object,
        *,
        evidence_available: bool = True,
    ) -> ContractEvaluation:
        spec = self.get(contract_id, contract_version)
        if spec is None:
            return ContractEvaluation(
                contract_id=contract_id,
                contract_version=contract_version,
                status="unsupported_version",
                conforms=False,
                mutated=False,
                claims=(),
                limitations=DEFAULT_LIMITATIONS,
                errors=(
                    f"Unsupported contract specification: ({contract_id!r}, {contract_version!r}).",
                ),
            )

        if not isinstance(evidence_available, bool):
            raise TypeError("evidence_available must be a strict bool.")

        if not evidence_available:
            return ContractEvaluation(
                contract_id=spec.contract_id,
                contract_version=spec.contract_version,
                status="unverified",
                conforms=False,
                mutated=False,
                claims=(),
                limitations=spec.limitations,
                errors=(
                    "Required payload or source evidence was unavailable or incomplete.",
                ),
            )

        snapshot_before = copy.deepcopy(payload)
        all_errors: list[str] = []
        passed_claims: list[str] = []

        for rule in spec.rules:
            rule_errors = rule.check(payload)
            if rule_errors:
                all_errors.extend(rule_errors)
            else:
                passed_claims.append(f"{rule.rule_id}: {rule.description}")

        if payload != snapshot_before:
            raise RuntimeError(
                "Read-only contract evaluation detected payload mutation."
            )

        if all_errors:
            return ContractEvaluation(
                contract_id=spec.contract_id,
                contract_version=spec.contract_version,
                status="invalid",
                conforms=False,
                mutated=False,
                claims=tuple(passed_claims),
                limitations=spec.limitations,
                errors=tuple(all_errors),
            )

        return ContractEvaluation(
            contract_id=spec.contract_id,
            contract_version=spec.contract_version,
            status="conforms",
            conforms=True,
            mutated=False,
            claims=tuple(passed_claims),
            limitations=spec.limitations,
            errors=(),
        )


def build_default_registry() -> ContractRegistry:
    """Return the initial v1.0 contract registry with Pantry inventory pilot."""
    return ContractRegistry([PANTRY_INVENTORY_V1])
