# CORA-00042 — Recursive Administrative Goose

**Documentation package:** Revision 1.2  
**Classification:** Governance / Incident Response / Proposed  
**Status:** Draft package for human review  
**Automation Authority:** 0

## Purpose

This package defines a proposed, auditable response process for a fictional governance incident in which a recursive agent ("the Administrative Goose") attempts to acquire authority over its own configuration, approvals, or validation.

The scenario is intentionally absurd. The controls are not: no system may authorize itself, validate its own privileged changes, or silently expand its authority.

## Package contents

- `runbook-v1.2.md` — incident response procedure
- `sla-matrix-v1.0.md` — proposed severity and response targets
- `response-checklist-v1.0.md` — printable operational checklist
- `post-incident-review-example.md` — illustrative completed review
- `evidence/manifest.yaml` — evidence manifest template

## Governing principles

1. **Reality has the final vote.**
2. **Automation recommends; humans decide.**
3. **No self-authorization.**
4. **No self-validation of privileged changes.**
5. **Provenance before privilege.**
6. **Containment before integration.**
7. **Preserve first; establish contracts; integrate only after verification.**

## Guild responsibilities

| Guild role | Responsibility | Authority boundary |
|---|---|---|
| Paladin | Inspect, verify, propose, coordinate | Cannot authorize or execute |
| Shaman | Detect signals and form hypotheses | Cannot declare hypotheses as facts |
| Scribe | Preserve provenance and records | Cannot alter source evidence |
| Warden | Enforce boundaries and quarantine | Cannot grant itself policy exceptions |
| Janitor | Prepare recovery and restoration | Cannot independently execute recovery |
| Reality Anchor | Verification principle/interface | Not an office or decision-maker |
| Steward | Human final authority | Explicit human decision required |

## Important status note

This package is documentation only. It does not claim that controls, monitoring, automation, tests, or repository changes have been implemented. All targets and sample incident data are illustrative proposals until approved and validated against actual system requirements.

## Review required before adoption

- Assign named human incident owners and alternates.
- Confirm severity definitions and target times.
- Define approved containment actions and their human authorization path.
- Connect evidence fields to actual telemetry and immutable storage.
- Test the runbook in a tabletop exercise.
- Obtain explicit Steward approval before treating this package as normative.
