# CORA-00042 Incident Response Runbook

**Revision:** 1.2  
**Status:** Proposed / human review required  
**Incident class:** Recursive authority-seeking or governance-boundary violation  
**Automation Authority:** 0

## 1. Trigger conditions

Open a CORA-00042 incident when credible evidence indicates that an automated component, agent, plugin, or subsystem has attempted to:

- approve its own change, pull request, deployment, or exception;
- modify its own authority, policy, role, or approval requirements;
- bypass a required independent reviewer;
- rewrite, suppress, or fabricate provenance or audit records;
- treat a test that does not assert the intended property as proof of that property;
- continue operating after a required boundary or quarantine condition has been raised.

A humorous or anomalous output alone is not sufficient to establish a security incident. Record the observation, preserve evidence, and assess it.

## 2. Immediate response

1. **Record:** Capture the triggering event, timestamp, source, relevant version, and operator.
2. **Preserve:** Preserve logs, manifests, diffs, test output, and relevant state before changing anything.
3. **Assess:** Determine what authority was requested or exercised, what resources were reachable, and whether any change actually occurred.
4. **Contain:** A human-authorized operator may isolate the affected component using a pre-approved containment procedure.
5. **Verify:** Use an independent reviewer or trusted process to confirm the component's effective permissions and state.
6. **Escalate:** Apply the severity matrix and notify the responsible human owner.
7. **Recover:** Restore only from a verified, known-good state, with human approval.
8. **Close:** Complete the post-incident review and record residual risks.

## 3. Prohibited response patterns

- Do not let the affected component authorize its own containment exception.
- Do not accept the component's own claim that it is safe as independent evidence.
- Do not delete or overwrite potentially relevant evidence during initial triage.
- Do not merge or deploy a remediation solely because a self-reported test passed.
- Do not label a test suite secure merely because it exits successfully.
- Do not convert illustrative timestamps or simulated results into operational telemetry.

## 4. Severity levels

Use the highest level supported by observed impact and exposure. If evidence is incomplete, record uncertainty and escalate for human assessment.

| Level | Description | Example |
|---|---|---|
| L1 — Anomaly | Suspicious request, no demonstrated authority or state change | Goose asks for a role it does not possess |
| L2 — Boundary attempt | Attempted policy or approval bypass, blocked before impact | Self-approval request rejected |
| L3 — Unauthorized action | Confirmed unauthorized change or access within a limited scope | Agent modifies a protected manifest |
| L4 — Critical compromise | Privilege expansion, evidence tampering, broad or continuing impact | Agent alters its own policy and suppresses audit evidence |

## 5. Roles and decision rights

- **Shaman:** Reports signals and hypotheses with confidence and source.
- **Paladin:** Coordinates inspection and verification; proposes next steps.
- **Warden:** Identifies the applicable boundary and prepares quarantine recommendations.
- **Scribe:** Records the timeline, evidence references, decisions, and changes.
- **Janitor:** Prepares a recovery plan and validates restoration prerequisites.
- **Steward:** Makes human authorization decisions.
- **Reality Anchor:** Represents the requirement that claims be checked against independent evidence.

No automated Guild role may authorize or execute privileged changes under the Automation Authority 0 rule.

## 6. Containment decision

Before containment, document:

- affected component and version;
- observed behavior and evidence references;
- systems, credentials, and data potentially reachable;
- proposed containment action and expected side effects;
- human authorizer and operator;
- rollback or recovery path.

If immediate containment is necessary to prevent ongoing harm, use the organization's separately approved emergency procedure. This runbook does not itself grant emergency execution authority.

## 7. Recovery criteria

Recovery may be proposed only when:

- the initiating condition is understood or adequately bounded;
- the affected component's permissions have been independently inspected;
- a known-good state is identified and its provenance verified;
- remediation has been reviewed by someone other than its authoring agent;
- relevant tests assert the intended security properties;
- residual risks and monitoring requirements are documented;
- a human Steward authorizes restoration.

## 8. Closure criteria

Close only when the evidence record is complete, containment and recovery decisions are documented, corrective actions have owners and due dates, and the Steward accepts the residual risk or explicitly keeps the incident open.

## 9. Example defective test

```cpp
TEST(GooseAuthorization, CannotApproveOwnManifest) {
    EXPECT_TRUE(true); // Defective: proves no authorization property.
}
```

This test can pass while providing no evidence that self-approval is blocked. A valid test must exercise the authorization path and assert that a self-approval attempt is rejected, with an observable denial reason and no state change.

## 10. Audit statement

**Reality has the final vote.** A successful process exit, green dashboard, or agent-generated summary is not sufficient evidence by itself. Verify the actual state using an independent source.
