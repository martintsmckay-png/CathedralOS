# CORA-00042 — Proposed SLA Matrix

**Revision:** 1.0  
**Status:** Proposed targets; not measured service commitments

These values are starting points for tabletop testing and operational review. They must be adjusted to match real system criticality, staffing, monitoring coverage, and response capability before adoption.

## 1. Severity targets

| Severity | Acknowledge / assess | Containment decision target | Escalation |
|---|---:|---:|---|
| L1 — Anomaly | 15 minutes | 30 minutes | On-call owner if unresolved |
| L2 — Boundary attempt | 5 minutes | 15 minutes | Security / governance owner |
| L3 — Unauthorized action | 1 minute | 5 minutes | Immediate human incident lead |
| L4 — Critical compromise | Immediate | Immediate human-led response | Steward and incident leadership |

“Containment decision target” means a human decision and documented action plan, not an automatic execution deadline. Actual containment may require additional authorization and operational safeguards.

## 2. SLA clock definitions

- **Start:** Earliest trustworthy timestamp at which the incident condition was detected by an approved source.
- **Acknowledgement:** A responsible human confirms ownership.
- **Assessment:** Severity and scope are recorded with evidence and uncertainty.
- **Containment decision:** A human-authorized action or explicit decision not to contain is recorded.
- **Pause:** A clock may be paused only under a documented policy, with reason, start/end time, and approver.
- **Stop:** The relevant milestone is completed and supported by evidence.

## 3. Breach thresholds

| Elapsed target | Status | Required response |
|---:|---|---|
| 50% | Warning | Notify current owner; confirm progress |
| 100% | Breach | Escalate to incident lead; document reason |
| 150% | Critical breach | Escalate to Steward; review resourcing and risk |

For L4, do not wait for percentage thresholds: escalation is immediate.

## 4. Reporting

Every SLA report should include incident ID, severity, source timestamps, acknowledgement time, containment decision time, pauses, breach status, owner, and evidence references.

Do not fabricate timestamps when telemetry is unavailable. Use `unknown` or `not recorded`, explain the gap, and create a corrective action.

## 5. Approval

These targets become operational only after a human owner approves them and confirms that the required coverage exists.
