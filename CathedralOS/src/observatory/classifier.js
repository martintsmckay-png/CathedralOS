// CathedralOS Event Classifier & Reward Engine
import { Observatory } from "./eventStream.js";

export const EventTypes = {
  PULSE: "PULSE",
  DISCOVERY: "DISCOVERY",
  DECISION: "DECISION"
};

export class ObservatoryClassifier {
  constructor() {
    this.discoveryLedger = [];
    this.stats = { intellect: 0, synergy: 0, domesticatedBugs: 0 };
    
    // Listen directly to the global pulse engine
    window.addEventListener('cathedral_pulse', (e) => this.processEvent(e.detail));
  }

  processEvent(event) {
    let classification = EventTypes.PULSE;

    // Classification Logic based on historical anomalies
    if (['IFRAME_DISAPPEARED', 'CHAOS_FILTERED', 'PHANTOM_DETECTED'].includes(event.eventType)) {
      classification = EventTypes.DISCOVERY;
      this.archiveDiscovery(event);
    } else if (event.eventType.startsWith('DECISION_')) {
      classification = EventTypes.DECISION;
    }

    this.updateSystemStats(classification);
  }

  archiveDiscovery(event) {
    this.stats.domesticatedBugs++;
    this.discoveryLedger.push({
      index: `#00${this.stats.domesticatedBugs}`,
      phenomenon: event.eventType,
      narrative: event.narrative,
      timestamp: event.timestamp
    });
  }

  updateSystemStats(type) {
    if (type === EventTypes.DISCOVERY) {
      this.stats.intellect += 5;
      this.stats.synergy += 12;
      console.log(`[REWARD] Intellect +5 | System Synergy +12. Total Features Domesticated: ${this.stats.domesticatedBugs}`);
    }
  }
}

