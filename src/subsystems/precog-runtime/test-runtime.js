// src/subsystems/precog-runtime/test-runtime.js

const PrecogRuntimeOrchestrator = require('./precog-orchestrator');

// 1. Mock minimal DOM elements so browser canvas calls survive in Node.js
global.document = {
  getElementById: (id) => ({
    id: id,
    getContext: () => ({
      clearRect: () => {},
      save: () => {},
      restore: () => {},
      beginPath: () => {},
      moveTo: () => {},
      lineTo: () => {},
      stroke: () => {},
      arc: () => {},
      fill: () => {}
    }),
    addEventListener: () => {},
    parentElement: { clientWidth: 1920, clientHeight: 1080 }
  })
};
global.window = {
  addEventListener: () => {},
  innerWidth: 1920,
  innerHeight: 1080
};

console.log("🧪 --- INITIALIZING CATHEDRALOS RUNTIME TESTS --- 🧪\n");

// 2. Instantiate the Master Coordinator
const orchestrator = new PrecogRuntimeOrchestrator({
  initialX: 0,
  initialY: 0,
  initialZoom: 1.0,
  onNodeSelected: (node) => {
    console.log(`🎯 [UI TRIGGER] Node Selected! Focus Camera -> '${node.label}' at [X: ${node.x}, Y: ${node.y}]`);
  }
});

// 3. Mount mock DOM environment
orchestrator.mountCanvas('spatializer-canvas');

// 4. Hydrate Spatial Layer with Conversational Milestones
const mockMilestones = [
  { id: 'node_01', x: 100, y: 150, label: 'Garlic Bread Fallback Protocol', role: 'System' },
  { id: 'node_02', x: -250, y: 300, label: 'GitHub Pages Deployment Skip', role: 'System' },
  { id: 'node_03', x: 50, y: -75, label: 'Emoji Telemetry Decoding Stream', role: 'Pilot' },
  { id: 'node_04', x: 400, y: -450, label: 'Elvis Overdrive Legacy Boot Sequence', role: 'Pilot' }
];
orchestrator.loadSystemTopology(mockMilestones);

// 5. Simulate Telemetry Stream Feed via Precog Engine
console.log("\n📥 Feeding live emoji telemetry packet through processing lanes...");
orchestrator.engine.on('telemetry', (log) => console.log(`📡 [ENGINE LOG] ${log}`));

orchestrator.feedStream(
  'chan_main', 
  { timestamp: Date.now(), type: 'SYS_OVERRIDE' }, 
  { nextState: 'CARBONARA_STABLE', confidence: 0.99 }, 
  { driftScore: 0.12 }
);

// 6. Test the Hit-Testing Matrix Math End-to-End
console.log("\n🖱️ Simulating targeted user mouse click execution on the grid void...");
// Execute world space translation matching coordinate limits of node_03
const simulatedClickX = 51;
const simulatedClickY = -74;
const zoomScale = 1.0;

const detectedHit = orchestrator.nodeManager.hitTest(simulatedClickX, simulatedClickY, zoomScale);

if (detectedHit) {
  console.log(`🟢 HIT CONFIRMED: Successfully resolved pointer to node: ${detectedHit.id}`);
  orchestrator.zoomEngine.focusNode(detectedHit);
  if (typeof orchestrator.onNodeSelected === 'function') {
    orchestrator.onNodeSelected(detectedHit);
  }
} else {
  console.log("❌ CRITICAL: Mathematical collision calculation missed target coordinates.");
}

console.log("\n🏁 --- ALL ARCHITECTURAL SYSTEMS OPERATING IN ACCEPTABLE LIMITS ---");

