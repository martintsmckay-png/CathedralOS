// CathedralOS — Observatory Insight Dashboard (Level 10)
import { TemporalAnalytics } from "./temporal-analytics.js";
import { DoctrineNavigator } from "./doctrine-navigator.js";
import { EventStream } from "./eventStream.js";

export const InsightDashboard = (() => {
  let isDisplayActive = false;

  function initializeDashboard() {
    isDisplayActive = true;
    EventStream.emit({
      type: "DASHBOARD_INITIALIZED",
      subsystem: "InsightDashboard",
      detail: { timestamp: performance.now(), status: "ONLINE" }
    });
  }

  function captureSnapshot() {
    const metrics = TemporalAnalytics.analyze();
    const activeFilters = DoctrineNavigator.query();
    
    return {
      systemCadence: metrics.cadence,
      driftAnomalies: metrics.driftFrequency,
      structuralIntegrity: metrics.lineageIntegrity,
      visibleLawsCount: activeFilters.length,
      sentinelAlertState: metrics.driftFrequency > 5 ? "WARN" : "STABLE"
    };
  }

  return { initializeDashboard, captureSnapshot };
})();

