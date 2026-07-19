import { DoctrineNavigator } from "../observatory/doctrine-navigator.js";
import { InsightDashboard } from "../observatory/insight-dashboard.js";

const searchInput = document.getElementById("nav-search");
const catSelect = document.getElementById("nav-category");

function renderNavigatorResults() {
  const matchingCanons = DoctrineNavigator.query();
  const resultsBody = document.getElementById("navigator-results-body");

  if (resultsBody) {
    resultsBody.innerHTML = matchingCanons.map(c => `
      <div class="navigator-entry entry-${c.id.toLowerCase()}">
        <span class="nav-id">[${c.id}]</span>
        <p class="nav-text">${c.text}</p>
        <small class="nav-source">Source: <code>${c.source}</code></small>
      </div>
    `).join("");
  }
}

function renderLiveDashboard() {
  const snapshot = InsightDashboard.captureSnapshot();
  
  const cadenceVal = document.querySelector("#card-cadence .metric-value");
  const driftVal = document.querySelector("#card-drift .metric-value");
  const integrityVal = document.querySelector("#card-integrity .metric-value");

  if (cadenceVal) cadenceVal.innerText = snapshot.systemCadence.variance.toFixed(4);
  if (driftVal) driftVal.innerText = snapshot.driftAnomalies;
  
  if (integrityVal) {
    integrityVal.innerText = snapshot.sentinelAlertState === "WARN" ? "CRITICAL" : "OPTIMAL";
    integrityVal.className = `metric-value text-${snapshot.sentinelAlertState.toLowerCase()}`;
  }
}

// Bind events to trigger queries instantly
if (searchInput && catSelect) {
  searchInput.addEventListener("input", (e) => {
    DoctrineNavigator.setFilter(catSelect.value, e.target.value);
    renderNavigatorResults();
  });

  catSelect.addEventListener("change", (e) => {
    DoctrineNavigator.setFilter(e.target.value, searchInput.value);
    renderNavigatorResults();
  });
}

// Initialize Dashboard Telemetry Engine
InsightDashboard.initializeDashboard();

// Core UI Refresh Loop — synchronous clock ticks for metrics and canonization sweeps
setInterval(() => {
  renderNavigatorResults();
  renderLiveDashboard();
}, 250);

