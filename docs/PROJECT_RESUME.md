# CathedralOS — Project Résumé

**Repository:** `github.com/martintsmckay-png/CathedralOS`
**Author:** Martin McKay
**Audited Code Baseline:** `3a5ece5` (`feat(pantry): seal Sevenfold Pantry resource layer and unit tests`)
**Core Principle:** *Automation recommends. Human decides. Reality has the final vote.*

---

## 1. Overview & Problem Space
**CathedralOS** is an experimental, local-first software architecture and state systems laboratory built primarily in Python 3.13. It explores how human-in-the-loop governance, atomic file persistence, and deterministic verification can prevent automated scripts or AI-assisted workflows from silently corrupting local data or executing unapproved side effects.

Rather than presenting an idealized overview, this résumé distinguishes **verified, tested subsystems** from **in-progress architectural prototypes and workspace artifacts**.

---

## 2. Verified Subsystems & Test Evidence

| Subsystem | Key Files | Verified Capabilities & Test Evidence |
| :--- | :--- | :--- |
| **Recipe Gate & Atomic Ledger** | `recipe_gate.py`<br>`test_recipe_gate.py` | Fail-closed inventory transaction management with atomic JSON writes via same-directory temp files, `os.fsync`, and directory sync error handling. Maintains a JSONL transaction ledger (`PREPARED` / `COMMITTED`) blocking new restocks while unresolved transactions exist. Backed by **16 passing tests** verifying durability failures, interrupted states, and strict type/quantity rejection. |
| **Pantry Contract Validator** | `validate_pantry_contract.py`<br>`test_pantry_contract.py` | Standalone schema validator and test suite (**14 passing tests**) enforcing non-empty string keys/units and finite, non-negative, non-boolean numeric quantities. |
| **PantryZork (`v0.1` / `v0.2`)** | `pantry_zork.py`<br>`test_pantry_zork.py` | Read-only interactive CLI state inspector (**4 passing regression tests**) with isolated failure recovery displays. Verifies Audio Foundry checksums before recommending playback commands without auto-executing external audio processes. |
| **Sevenfold Pantry Resource Layer** | `pantry.py`<br>`test_pantry.py` | Standalone symbolic resource registry and unit test suite (**4 passing tests**) decoupled from live inventory I/O. |
| **Audio Foundry (`v6.1` / `v6.2`)** | `audio_foundry/render.py`<br>`audio_foundry/render_v6_2_ensemble.py` | Standard-library procedural PCM WAV renderers. The v6.2 artifact SHA-256 and WAV format (`44.1 kHz`, 16-bit mono PCM) were independently verified. README telemetry documents `1,421,312` bytes, `16.114s` duration, and zero clipped samples; those telemetry values were not independently rerun in this audit. |

> **Audit Test Result:** **38 tests passed** across the four explicitly selected Pantry-layer test modules: 16 Recipe Gate, 14 Pantry Contract, 4 PantryZork, and 4 Sevenfold Pantry. This is a scoped result, not a claim that the entire repository test suite passes.

---

## 3. Engineering Approach & Invariants
CathedralOS development adheres to strict architectural boundaries:

* **Fail-Closed Validation:** Malformed JSON, boolean-as-number coercion, `NaN`/`Infinity`, and negative quantities are explicitly rejected rather than coerced.
* **Atomic Persistence:** Write operations utilize temp files, `fsync`, and atomic replacement to protect against partial writes during interruption.
* **Test Isolation:** Selected tests use temporary directory fixtures where applicable; live-data checks are read-only.
* **Human-Gated Execution:** Diagnostic tools and audio bridges recommend valid commands rather than invoking side effects automatically.

---
## 4. Known Limitations & Scope Boundaries
* **Workspace Preservation:** The repository root contains legacy prototypes, local logs, and backup snapshots (`audit/`, `*.json`, `*.jsonl`, backup files) left untracked and intact for operational continuity.
* **Test Discovery Scope:** Core validation is strictly handled by the root test modules (`test_pantry.py`, `test_pantry_contract.py`, `test_pantry_zork.py`, `test_recipe_gate.py`). Unrestricted recursive collection encountered 24 errors involving duplicate archived test modules, a malformed legacy test filename, and Android storage permission errors.
* **System Scope:** These verifications apply specifically to the Pantry and persistence layers; they do not certify unverified auxiliary modules or cross-subsystem orchestration layers.
