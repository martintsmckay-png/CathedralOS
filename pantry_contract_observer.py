"""Read-only external observer bridging Pantry snapshots to ContractRegistry v1.0."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contract_registry_v1 import (
    ContractEvaluation,
    ContractRegistry,
    DEFAULT_LIMITATIONS,
    PANTRY_CONTRACT_ID,
    PANTRY_CONTRACT_VERSION,
    build_default_registry,
)

UNVERIFIED_LOAD_STATES: frozenset[str] = frozenset(
    {"MISSING", "UNREADABLE", "MALFORMED_JSON", "missing", "unreadable", "malformed"}
)


@dataclass(frozen=True)
class PantryContractObservation:
    """Immutable read-only observation record produced externally from a snapshot."""

    contract_id: str
    contract_version: str
    status: str  # "conforms" | "invalid" | "unverified" | "unsupported_version"
    conforms: bool
    contract_verified: bool
    mutated: bool
    evidence_source: str
    loader_state: str | None
    errors: tuple[str, ...] = field(default_factory=tuple)
    claims: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.conforms, bool):
            raise TypeError("conforms must be a strict bool.")
        if not isinstance(self.contract_verified, bool):
            raise TypeError("contract_verified must be a strict bool.")
        if not isinstance(self.mutated, bool):
            raise TypeError("mutated must be a strict bool.")
        if self.mutated is not False:
            raise ValueError("Read-only observations must report mutated=False.")
        # Structural conformance alone is not a universal proof of trust, but
        # contract_verified can never be True when conforms is False.
        if self.contract_verified is True and self.conforms is not True:
            raise ValueError("contract_verified cannot be True when conforms is not True.")
        if not isinstance(self.evidence_source, str) or not self.evidence_source.strip():
            raise ValueError("evidence_source must be a non-empty string.")


def _extract_attr_or_key(obj: Any, names: tuple[str, ...], default: Any = None) -> Any:
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
        return default
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def _normalize_state_name(raw_state: Any) -> str | None:
    if raw_state is None:
        return None
    if hasattr(raw_state, "name"):
        return str(raw_state.name)
    if hasattr(raw_state, "value"):
        return str(raw_state.value)
    return str(raw_state)


def observe_pantry_snapshot(
    snapshot: Any,
    *,
    registry: ContractRegistry | None = None,
    contract_id: str = PANTRY_CONTRACT_ID,
    contract_version: str = PANTRY_CONTRACT_VERSION,
) -> PantryContractObservation:
    """Observe a PantrySnapshot or snapshot-like object without mutating it."""
    active_registry = registry if registry is not None else build_default_registry()

    raw_snapshot = _extract_attr_or_key(snapshot, ("snapshot",), default=snapshot)
    raw_state = _extract_attr_or_key(
        raw_snapshot, ("state", "status", "load_state"), default=None
    )
    state_name = _normalize_state_name(raw_state)

    raw_source = _extract_attr_or_key(
        raw_snapshot, ("source_path", "path", "source"), default="<in-memory-snapshot>"
    )
    evidence_source = (
        str(raw_source) if isinstance(raw_source, (str, Path)) else "<snapshot-evidence>"
    )

    # Snapshot before any read-only inspection to verify non-mutation.
    before_copy = copy.deepcopy(raw_snapshot)

    # Check whether the requested (contract_id, contract_version) is supported first
    # so unsupported versions never silently fall back to another contract.
    if active_registry.get(contract_id, contract_version) is None:
        unsupported_eval: ContractEvaluation = active_registry.evaluate(
            contract_id, contract_version, None
        )
        return PantryContractObservation(
            contract_id=contract_id,
            contract_version=contract_version,
            status=unsupported_eval.status,
            conforms=False,
            contract_verified=False,
            mutated=False,
            evidence_source=evidence_source,
            loader_state=state_name,
            errors=unsupported_eval.errors,
            claims=unsupported_eval.claims,
            limitations=unsupported_eval.limitations,
        )

    # Missing, unreadable, or malformed JSON has no parsed payload -> unverified.
    if state_name in UNVERIFIED_LOAD_STATES:
        reason = _extract_attr_or_key(raw_snapshot, ("reason", "error"), default=None)
        detail = f" ({reason})" if reason else ""
        return PantryContractObservation(
            contract_id=contract_id,
            contract_version=contract_version,
            status="unverified",
            conforms=False,
            contract_verified=False,
            mutated=False,
            evidence_source=evidence_source,
            loader_state=state_name,
            errors=(
                f"Cannot establish contract conformance from loader state "
                f"{state_name!r}{detail}: parsed payload unavailable.",
            ),
            claims=(),
            limitations=DEFAULT_LIMITATIONS,
        )

    payload = _extract_attr_or_key(
        raw_snapshot, ("parsed_data", "data", "payload", "items"), default=None
    )
    if payload is None:
        return PantryContractObservation(
            contract_id=contract_id,
            contract_version=contract_version,
            status="unverified",
            conforms=False,
            contract_verified=False,
            mutated=False,
            evidence_source=evidence_source,
            loader_state=state_name,
            errors=("No parsed payload present on snapshot for contract evaluation.",),
            claims=(),
            limitations=DEFAULT_LIMITATIONS,
        )

    evaluation = active_registry.evaluate(
        contract_id,
        contract_version,
        payload,
        evidence_available=True,
    )

    if raw_snapshot != before_copy:
        raise RuntimeError("Read-only snapshot observation detected mutation.")

    return PantryContractObservation(
        contract_id=evaluation.contract_id,
        contract_version=evaluation.contract_version,
        status=evaluation.status,
        conforms=evaluation.conforms,
        contract_verified=(evaluation.conforms is True),
        mutated=False,
        evidence_source=evidence_source,
        loader_state=state_name,
        errors=evaluation.errors,
        claims=evaluation.claims,
        limitations=evaluation.limitations,
    )
