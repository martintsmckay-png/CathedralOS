// test/scenes/homebase/EventBusResonance.test.js
// CathedralOS Test Suite — Event Bus Nervous System Verification

const HomeBaseSceneOrchestrator = require('../../../src/scenes/homebase/HomeBaseSceneOrchestrator');
const SceneEventBus = require('../../../src/subsystems/homebase/SceneEventBus'); // Phase 4 Target

function runEventBusResonanceTest() {
  console.log("⚡ [TEST RUNNER] Initializing Event Bus Integration Test...");

  // 1. Setup the Decoupled Event Bus Framework
  const eventBus = new SceneEventBus();
  let telemetryHeardCount = 0;
  let lastCapturedVibe = null;

  // 2. Instantiate the Conductor with our test config
  const orchestrator = new HomeBaseSceneOrchestrator({
    soulVibeConfig: { mode: 'STANDBY' }
  });

  // Mock the canvas environment for headless execution
  const mockCanvas = { getContext: () => ({}) };
  orchestrator.mount({ canvas: mockCanvas });
  orchestrator.start();

  // 3. Establish the Observatory Spy (Subscribe to the Bus)
  eventBus.subscribe('S_O_U_L_VIBE_REMIX', (event) => {
    telemetryHeardCount++;
    lastCapturedVibe = event.payload;
    console.log(`📡 [OBSERVATORY MONITOR] -> Intercepted event: ${event.type} from ${event.source}`);
  });

  // Link our Orchestrator's internal telemetry output directly into the event bus broadcast
  orchestrator.onSoulTelemetry = (telemetryData) => {
    if (telemetryData.input.type === 'S_O_U_L_VIBE_REMIX') {
      eventBus.publish('S_O_U_L_VIBE_REMIX', telemetryData.input);
    }
  };

  console.log("🏁 [TEST RUNNER] System mounted and listening. Simulating Sprocket Override...");

  // 4. Force a Performance Override State to trigger Sprocket's workspace
  orchestrator.sceneState.mode = 'PERFORMANCE';
  
  // Simulate selecting a node containing the targeted garlic keyword
  const mockGarlicNode = {
    id: 'node_kitchen_altar_01',
    label: 'Garlic-Infused Core Aromatic Node',
    metadata: { heatIntensity: 0.85 }
  };

  // Trigger the inspector focus event loop
  orchestrator.precog.inspectorListener(mockGarlicNode);

  // 5. Assertions & Verification
  console.log("\n📊 [TEST RESULTS ANALYSIS]:");
  console.log(`   - Total Events Caught by Bus: ${telemetryHeardCount} (Expected: 1)`);
  console.log(`   - Crossfader Positioning: ${orchestrator.rodentDJ.crossfaderPos}`);
  
  if (telemetryHeardCount === 1 && lastCapturedVibe?.operator === 'Sprocket') {
    console.log("\n🟩 [SUCCESS] Phase 4 Core Event Bus Handshake PASSED. The nervous system is fully resonant.\n");
    return true;
  } else {
    console.error("\n🟥 [FAILURE] Event broadcasting dropped in transit. Check internal handler bindings.\n");
    return false;
  }
}

// Execute if run directly from terminal
if (require.main === module) {
  runEventBusResonanceTest();
}

module.exports = runEventBusResonanceTest;

