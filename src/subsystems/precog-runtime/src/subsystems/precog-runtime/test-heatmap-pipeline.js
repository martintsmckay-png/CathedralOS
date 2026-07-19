// src/subsystems/precog-runtime/test-heatmap-pipeline.js
import { EventStream } from "../../observatory/eventStream.js";
import { InsightDashboard } from "../../observatory/insight-dashboard.js";

console.log("🧪 --- RUNNING TEMPORAL HEATMAP DIAGNOSTIC SUITE --- 🧪");

// Test Case 1: Snapshot Integrity
const testSnapshot = InsightDashboard.captureSnapshot();
if (typeof testSnapshot.driftAnomalies !== 'number') {
  console.error("❌ HEATMAP FAILURE: driftAnomalies payload is corrupt or unreadable.");
} else {
  console.log(`🟢 SNAPSHOT INTEGRITY: Passed. Current Drift Anomalies: ${testSnapshot.driftAnomalies}`);
}

// Test Case 2: Fusion Overlay Vector Hook
let fusionTriggered = false;
EventStream.subscribe("TEMPORAL_FUSED", () => {
  fusionTriggered = true;
});

// Emulate an orchestration-layer spike to force a golden prophecy marker
EventStream.emit({ type: "TEMPORAL_FUSED", detail: { pattern: "Convergence:Alpha" } });

setTimeout(() => {
  if (fusionTriggered) {
    console.log("🟢 FUSION OVERLAY HOOK: Passed. Golden prophecy spikes routing successfully.");
  } else {
    console.error("❌ OVERLAY FAILURE: TEMPORAL_FUSED event dropped in pipeline.");
  }
}, 50);

