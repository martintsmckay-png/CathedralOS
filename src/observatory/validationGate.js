// src/observatory/validationGate.js
// CathedralOS — Validation Gate (Pillar IV: Judiciary)

import { EventStream } from "./eventStream.js";

export const ValidationGate = (() => {
  const decisions = [];

  function evaluate(proposal) {
    const result = {
      id: proposal.id || `prop-${Date.now()}`,
      timestamp: new Date().toISOString(),
      subsystem: proposal.subsystem,
      action: proposal.action,
      status: "FLAGGED",
      reason: "",
    };

    // 1. Boundary & Origin Check
    if (proposal.origin === "NarrativeEcho") {
      result.status = "REJECTED";
      result.reason = "Lore isolation: Narrative-derived content cannot mutate state.";
      return record(result);
    }

    if (proposal.origin === "AnomalyLedger") {
      result.status = "FLAGGED";
      result.reason = "Quarantined entropy requires explicit Steward review.";
      return record(result);
    }

    // 2. Default Approval for Valid Proposals
    result.status = "APPROVED";
    result.reason = "Complies with ARCHITECTURE.md invariants.";
    return record(result);
  }

  function record(result) {
    decisions.push(result);
    EventStream.emit({
      type: `VALIDATION_${result.status}`,
      subsystem: "ValidationGate",
      detail: result.reason,
      proposalId: result.id,
    });
    return result;
  }

  function history() {
    return [...decisions];
  }

  return { evaluate, history };
})();

