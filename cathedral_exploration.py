"""Read-only, deterministic five-chamber exploration layer for CathedralOS.

This module deliberately does not import pantry_zork or steward_console.
Pantry and Audio Foundry integration are supplied by injected reader callbacks.

The module performs no writes. File evidence is limited to explicit allowlisted
relative paths, regular files, and a configurable byte ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Tuple
import errno
import json
import os
import stat


DEFAULT_MAX_FILE_BYTES = 256 * 1024
DEFAULT_MAX_FILES_PER_CHAMBER = 12


class Direction(str, Enum):
    NORTH = "NORTH"
    EAST = "EAST"
    SOUTH = "SOUTH"
    WEST = "WEST"


class Availability(str, Enum):
    AVAILABLE = "available"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ChamberSpec:
    chamber_id: str
    title: str
    description: str
    exits: Tuple[Tuple[Direction, str], ...]
    evidence_paths: Tuple[str, ...] = ()

    def destination(self, direction: Direction) -> Optional[str]:
        return dict(self.exits).get(direction)


# Tuple-backed exits and a read-only top-level mapping prevent accidental edits
# to the canonical chamber graph during a session.
CHAMBERS: Mapping[str, ChamberSpec] = MappingProxyType({
    "pantry": ChamberSpec(
        chamber_id="pantry",
        title="Pantry",
        description="Inventory evidence and the recovery-ration display.",
        exits=(
            (Direction.NORTH, "clock_tower"),
            (Direction.EAST, "library"),
            (Direction.WEST, "audio_foundry"),
            (Direction.SOUTH, "sanctum"),
        ),
        evidence_paths=("pantry.json",),
    ),
    "clock_tower": ChamberSpec(
        chamber_id="clock_tower",
        title="Clock Tower",
        description="Filesystem timestamps, recorded logs, and timekeeper source.",
        exits=((Direction.SOUTH, "pantry"),),
        evidence_paths=(
            "audit/baseline/timestamp.txt",
            "auditor.log",
            "restock_log.jsonl",
            "treasury_stream.log",
            "src/kernel/timekeeper/lonely_drum.cpp",
            "src/observatory/eventStream.js",
        ),
    ),
    "library": ChamberSpec(
        chamber_id="library",
        title="Library",
        description="Static doctrine, project documents, and governance provenance.",
        exits=((Direction.WEST, "pantry"),),
        evidence_paths=(
            "ANOMALY_INDEX.md",
            "src/observatory/doctrine-index.js",
            "governance/incidents/CORA-00042/README.md",
            "governance/incidents/CORA-00042/evidence/manifest.yaml",
        ),
    ),
    "audio_foundry": ChamberSpec(
        chamber_id="audio_foundry",
        title="Audio Foundry",
        description="Audio artifact presence and integrity evidence; no playback or rendering.",
        exits=((Direction.EAST, "pantry"),),
        evidence_paths=(
            "audio_foundry/README.md",
            "audio_foundry/cathedralos_v6_2_ensemble.wav",
        ),
    ),
    "sanctum": ChamberSpec(
        chamber_id="sanctum",
        title="Sanctum",
        description="Governance posture and boundary documentation, read without invoking controls.",
        exits=((Direction.NORTH, "pantry"),),
        evidence_paths=(
            "governance/incidents/CORA-00042/README.md",
            "governance/incidents/CORA-00042/evidence/manifest.yaml",
            "subsystems/root-key-sanctum/sanctum-runtime.js",
            "subsystems/root-key-sanctum/sanctum-bus.js",
        ),
    ),
})


@dataclass(frozen=True)
class ExplorationState:
    """Immutable cursor for the current exploration session."""

    chamber_id: str = "pantry"
    visited: Tuple[str, ...] = ("pantry",)

    def __post_init__(self) -> None:
        if self.chamber_id not in CHAMBERS:
            raise ValueError(f"Unknown chamber: {self.chamber_id}")
        if self.chamber_id not in self.visited:
            object.__setattr__(self, "visited", self.visited + (self.chamber_id,))


@dataclass(frozen=True)
class EvidenceItem:
    path: str
    status: str
    detail: str
    size_bytes: Optional[int] = None
    sha256_hex: Optional[str] = None
    parsed_kind: Optional[str] = None


@dataclass(frozen=True)
class EvidenceReport:
    chamber_id: str
    availability: Availability
    items: Tuple[EvidenceItem, ...]
    claims: Tuple[str, ...]
    limitations: Tuple[str, ...]
    mutated: bool = False


@dataclass(frozen=True)
class MoveResult:
    state: ExplorationState
    moved: bool
    message: str


def normalize_direction(value: str) -> Direction:
    """Parse a direction token without accepting compound commands."""
    try:
        return Direction(value.strip().upper())
    except (AttributeError, ValueError) as exc:
        raise ValueError(f"Unknown direction: {value!r}") from exc


def move(state: ExplorationState, direction: str | Direction) -> MoveResult:
    """Return a new cursor; never changes the supplied state."""
    direction_value = (
        direction if isinstance(direction, Direction)
        else normalize_direction(direction)
    )
    chamber = CHAMBERS[state.chamber_id]
    destination = chamber.destination(direction_value)
    if destination is None:
        return MoveResult(
            state=state,
            moved=False,
            message=f"No exit {direction_value.value} from {chamber.title}.",
        )
    next_visited = state.visited
    if destination not in next_visited:
        next_visited += (destination,)
    next_state = ExplorationState(destination, next_visited)
    return MoveResult(
        state=next_state,
        moved=True,
        message=f"You move {direction_value.value} to {CHAMBERS[destination].title}.",
    )


def render_map(state: Optional[ExplorationState] = None) -> str:
    """Render the fixed chamber graph; mark the current chamber when supplied."""
    current = state.chamber_id if state else None
    lines = ["CATHEDRALOS EXPLORATION MAP"]
    for chamber_id in ("pantry", "clock_tower", "library", "audio_foundry", "sanctum"):
        spec = CHAMBERS[chamber_id]
        marker = " *" if chamber_id == current else ""
        exits = ", ".join(
            f"{direction.value} -> {CHAMBERS[target].title}"
            for direction, target in spec.exits
        ) or "none"
        lines.append(f"{spec.title}{marker}: {exits}")
    return "\n".join(lines)


def render_chamber(state: ExplorationState) -> str:
    spec = CHAMBERS[state.chamber_id]
    exits = ", ".join(direction.value for direction, _ in spec.exits) or "none"
    return (
        f"{spec.title}\n"
        f"{spec.description}\n"
        f"Exits: {exits}\n"
        f"Visited: {', '.join(CHAMBERS[item].title for item in state.visited)}"
    )


def _close_fd_quietly(fd: Optional[int]) -> None:
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass


def _read_bounded_file(
    root: Path,
    relative_path: str,
    max_file_bytes: int,
) -> Tuple[str, str, Optional[bytes], Optional[int]]:
    """Read a regular file via descriptor-relative traversal without following symlinks."""
    rel = Path(relative_path)
    if (
        rel.is_absolute()
        or ".." in rel.parts
        or not rel.parts
        or rel == Path(".")
    ):
        return "rejected", "Unsafe relative path.", None, None

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None:
        return (
            "unsupported",
            "Required no-follow directory flags are unavailable.",
            None,
            None,
        )

    root_fd: Optional[int] = None
    current_fd: Optional[int] = None
    leaf_fd: Optional[int] = None

    try:
        root_resolved = root.resolve(strict=True)
        root_fd = os.open(root_resolved, os.O_RDONLY | directory_flag)
        current_fd = root_fd

        for component in rel.parts[:-1]:
            next_fd = os.open(
                component,
                os.O_RDONLY | directory_flag | nofollow,
                dir_fd=current_fd,
            )
            if current_fd != root_fd:
                _close_fd_quietly(current_fd)
            current_fd = next_fd

        leaf_flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0)
        leaf_fd = os.open(rel.parts[-1], leaf_flags, dir_fd=current_fd)

        st_before = os.fstat(leaf_fd)
        if not stat.S_ISREG(st_before.st_mode):
            return (
                "not_regular_file",
                "Opened target is not a regular file.",
                None,
                st_before.st_size,
            )

        if st_before.st_size > max_file_bytes:
            return (
                "size_limited",
                f"File exceeds the {max_file_bytes}-byte inspection limit.",
                None,
                st_before.st_size,
            )

        chunks = []
        bytes_read = 0
        while bytes_read <= max_file_bytes:
            to_read = min(65536, max_file_bytes + 1 - bytes_read)
            chunk = os.read(leaf_fd, to_read)
            if not chunk:
                break
            chunks.append(chunk)
            bytes_read += len(chunk)

        raw = b"".join(chunks)
        st_after = os.fstat(leaf_fd)

        if len(raw) > max_file_bytes:
            return (
                "size_limited",
                f"File exceeded the {max_file_bytes}-byte limit during read.",
                None,
                st_after.st_size,
            )

        if (
            st_before.st_size != st_after.st_size
            or st_before.st_mtime_ns != st_after.st_mtime_ns
            or len(raw) != st_after.st_size
        ):
            return (
                "changed_during_read",
                "Observed file metadata changed during read; content not interpreted.",
                None,
                len(raw),
            )

        return "read", "Read completed.", raw, len(raw)

    except FileNotFoundError:
        return "missing", "File does not exist.", None, None
    except PermissionError:
        return "unreadable", "Permission denied.", None, None
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            return (
                "rejected",
                "Path component could not be opened safely without following symlinks.",
                None,
                None,
            )
        return "io_error", f"Read failed: {type(exc).__name__}.", None, None
    except (RuntimeError, ValueError) as exc:
        return "io_error", f"Path resolution failed: {type(exc).__name__}.", None, None
    finally:
        _close_fd_quietly(leaf_fd)
        if current_fd is not None and current_fd != root_fd:
            _close_fd_quietly(current_fd)
        _close_fd_quietly(root_fd)


def inspect_allowlisted_files(
    root: Path | str,
    relative_paths: Tuple[str, ...],
    *,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES_PER_CHAMBER,
) -> Tuple[EvidenceItem, ...]:
    """Read bounded metadata/content summaries for explicitly listed files only.

    No directory walk, glob, import, execution, or write is performed.
    """
    root_path = Path(root)
    if max_file_bytes < 0 or max_files < 0:
        raise ValueError("Evidence limits must be non-negative.")

    results = []
    for relative_path in relative_paths[:max_files]:
        status, detail, raw, size = _read_bounded_file(
            root_path,
            relative_path,
            max_file_bytes,
        )
        if status != "read" or raw is None:
            results.append(EvidenceItem(
                path=relative_path,
                status=status,
                detail=detail,
                size_bytes=size,
            ))
            continue

        digest = sha256(raw).hexdigest()
        suffix = Path(relative_path).suffix.lower()
        parsed_kind = None
        detail = f"Read-only file evidence; {len(raw)} bytes."
        if suffix == ".json":
            try:
                json.loads(raw.decode("utf-8"))
                parsed_kind = "json_syntax_valid"
                detail += " JSON syntax valid; application contract not assessed."
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed_kind = "json_syntax_invalid"
                detail += " JSON syntax invalid or not UTF-8."
        elif suffix == ".jsonl":
            try:
                text = raw.decode("utf-8")
                lines = [line for line in text.splitlines() if line.strip()]
                for line in lines:
                    json.loads(line)
                parsed_kind = "jsonl_syntax_valid"
                detail += f" {len(lines)} non-empty JSON lines parse."
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed_kind = "jsonl_syntax_invalid"
                detail += " One or more lines are not valid UTF-8 JSON."
        elif suffix in {".md", ".txt", ".yaml", ".yml", ".js", ".cpp", ".py"}:
            parsed_kind = "text_bytes_present"
            detail += " Presence and hash recorded; content is not executed or semantically validated."
        else:
            parsed_kind = "binary_or_unclassified"
            detail += " Content not decoded."

        results.append(EvidenceItem(
            path=relative_path,
            status="read",
            detail=detail,
            size_bytes=len(raw),
            sha256_hex=digest,
            parsed_kind=parsed_kind,
        ))

    if len(relative_paths) > max_files:
        results.append(EvidenceItem(
            path="(remaining allowlist)",
            status="limit_reached",
            detail=f"Only the first {max_files} allowlisted paths were inspected.",
        ))
    return tuple(results)

def _availability(items: Tuple[EvidenceItem, ...]) -> Availability:
    readable = sum(
        item.status in {"read", "snapshot"} for item in items
    )
    if readable == len(items) and items:
        return Availability.AVAILABLE
    if readable:
        return Availability.PARTIAL
    return Availability.UNAVAILABLE


def _reader_failure_reason(value: Any) -> Optional[str]:
    if value is None:
        return "Reader returned None."
    if value is False:
        return "Reader returned False."
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return "Reader returned an empty string."
        failure_markers = (
            "error",
            "failed",
            "failure",
            "exception",
            "traceback",
            "permission denied",
            "could not be read",
            "unavailable",
            "missing",
            "integrity mismatch",
            "not verified",
        )
        if any(marker in normalized for marker in failure_markers):
            return "Reader returned error-like or unverified text."
    if isinstance(value, Mapping):
        if value.get("ok") is False:
            return "Reader result reports ok=False."
        if value.get("success") is False:
            return "Reader result reports success=False."
        status = value.get("status")
    else:
        if getattr(value, "ok", None) is False:
            return "Reader result reports ok=False."
        if getattr(value, "success", None) is False:
            return "Reader result reports success=False."
        status = getattr(value, "status", None)

    if isinstance(status, str) and status.lower() in {
        "error",
        "failed",
        "failure",
        "unavailable",
        "invalid",
    }:
        return f"Reader result reports status={status!r}."
    return None


def inspect_chamber(
    state: ExplorationState,
    *,
    root: Path | str,
    pantry_reader: Optional[Callable[[], Any]] = None,
    audio_reader: Optional[Callable[[], Any]] = None,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    max_files: int = DEFAULT_MAX_FILES_PER_CHAMBER,
) -> EvidenceReport:
    """Build a structured report using injected readers plus bounded file evidence.

    Reader callbacks must themselves be read-only. Their return values are treated
    as opaque evidence and represented safely; callbacks are never auto-discovered.
    """
    spec = CHAMBERS[state.chamber_id]
    read_paths = spec.evidence_paths
    if state.chamber_id == "pantry" and pantry_reader is not None:
        # The injected snapshot is the authoritative Pantry evidence.
        # Do not perform a second disk read of pantry.json.
        read_paths = tuple(
            path for path in read_paths if path != "pantry.json"
        )

    items = list(inspect_allowlisted_files(
        root, read_paths,
        max_file_bytes=max_file_bytes,
        max_files=max_files,
    ))
    claims = []
    limitations = [
        "Inspection is read-only by design; no file, pantry, journal, or runtime state is written.",
        "Static source and documentation do not establish that a subsystem is currently running.",
    ]

    if state.chamber_id == "pantry":
        if pantry_reader is None:
            limitations.append("Pantry snapshot reader was not supplied; pantry contract state is unavailable here.")
        else:
            try:
                snapshot = pantry_reader()
                failure = _reader_failure_reason(snapshot)
                if failure:
                    items.append(EvidenceItem(
                        path="pantry_reader",
                        status="callback_unverified",
                        detail=failure,
                    ))
                    limitations.append("Injected pantry reader returned unverified evidence.")
                else:
                    snapshot_state = getattr(getattr(snapshot, "state", None), "value", None)
                    verified = getattr(snapshot, "contract_verified", None)
                    claims.append(
                        f"Injected pantry snapshot returned state={snapshot_state!r}, "
                        f"contract_verified={verified!r}."
                    )
                    items.append(EvidenceItem(
                        path="pantry.json",
                        status="snapshot",
                        detail=(
                            "Derived from the session's already-loaded PantrySnapshot; "
                            "no second disk read performed."
                        ),
                        parsed_kind="pantry_snapshot",
                    ))
            except Exception as exc:  # report reader failure without hiding it
                items.append(EvidenceItem(
                    path="pantry_reader",
                    status="callback_unverified",
                    detail=f"Reader raised {type(exc).__name__}.",
                ))
                limitations.append(f"Injected pantry reader failed: {type(exc).__name__}.")

    if state.chamber_id == "audio_foundry":
        if audio_reader is None:
            limitations.append("Audio integrity reader was not supplied; artifact verification is unavailable here.")
        else:
            try:
                audio_result = audio_reader()
                failure = _reader_failure_reason(audio_result)
                if failure:
                    items.append(EvidenceItem(
                        path="audio_reader",
                        status="callback_unverified",
                        detail=failure,
                    ))
                    limitations.append("Injected audio reader returned unverified evidence.")
                else:
                    claims.append(f"Injected audio reader returned: {str(audio_result)[:500]}")
            except Exception as exc:
                items.append(EvidenceItem(
                    path="audio_reader",
                    status="callback_unverified",
                    detail=f"Reader raised {type(exc).__name__}.",
                ))
                limitations.append(f"Injected audio reader failed: {type(exc).__name__}.")
        limitations.append("No playback, rendering, or synthesis is performed.")

    if state.chamber_id == "clock_tower":
        limitations.append("Filesystem timestamps are not proof of monotonic-clock or external time synchronization.")
        limitations.append("Event-stream source code is not evidence of a live event stream.")

    if state.chamber_id == "library":
        limitations.append("Readable documents and manifests are not automatically schema-valid or approved.")
    if state.chamber_id == "sanctum":
        limitations.append("Governance documents describe policy; they do not prove runtime enforcement or human approval.")

    frozen_items = tuple(items)
    return EvidenceReport(
        chamber_id=state.chamber_id,
        availability=_availability(frozen_items),
        items=frozen_items,
        claims=tuple(claims),
        limitations=tuple(limitations),
        mutated=False,
    )


def format_evidence_report(report: EvidenceReport) -> str:
    """Human-readable, conservative rendering of a structured evidence report."""
    lines = [
        f"{CHAMBERS[report.chamber_id].title} — evidence: {report.availability.value}",
        f"Mutation performed: {'yes' if report.mutated else 'no'}",
    ]
    for item in report.items:
        suffix = f" ({item.size_bytes} bytes)" if item.size_bytes is not None else ""
        lines.append(f"- {item.path}: {item.status}{suffix} — {item.detail}")
        if item.sha256_hex:
            lines.append(f"  SHA-256: {item.sha256_hex}")
    if report.claims:
        lines.append("Claims:")
        lines.extend(f"- {claim}" for claim in report.claims)
    if report.limitations:
        lines.append("Limitations:")
        lines.extend(f"- {limitation}" for limitation in report.limitations)
    return "\n".join(lines)
