// src/subsystems/precog-runtime/test-runtime-v2.js

const PrecogRuntimeOrchestrator = require('./precog-orchestrator');

// Headless UI Mocking Elements
global.document = {
  getElementById: () => ({
    getContext: () => ({ clearRect: () => {}, save: () => {}, restore: () => {}, beginPath: () => {}, moveTo: () => {}, lineTo: () => {}, stroke: () => {}, arc: () => {}, fill: () => {} }),
    addEventListener: () => {},
    parentElement: { clientWidth: 1920, clientHeight: 1080 }
  })
};
global.window = { addEventListener: () => {}, innerWidth: 1920, innerHeight: 1080 };

console.log("🧪 --- RUNNING PRECGO RUNTIME PHASE 2 INTEGRATION SUITE --- 🧪\n");

// Inspector Verification Hook
const orchestrator = new PrecogRuntimeOrchestrator({
  onNodeSelected: (node) => {
    console.log("\n🔎 [INSPECTOR PANEL UPDATE]");
    console.log(` ├─ NODE ID:    ${node.id}`);
    console.log(` ├─ LABEL:      ${node.label}`);
    console.log(` ├─ LEVEL:      ${node.metadata.level}`);
    console.log(` ├─ PARENT REF: ${node.metadata.parentId || 'NONE'}`);
    console.log(` └─ PAYLOAD:    ${node.metadata.payload}`);
  }
});

orchestrator.mountCanvas('spatializer-canvas');

// Populate graph nodes + semantic lines
const mockNodes = [
  { id: 'node_01', x: 0, y: 0, label: 'Root Core', role: 'System', metadata: { level: 1, parentId: null, payload: 'Mainframe Ground State' } },
  { id: 'node_02', x: 200, y: 200, label: 'Garlic Module', role: 'System', metadata: { level: 2, parentId: 'node_01', payload: 'Fallback Storage Log' } }
];
const mockEdges = [
  { source: 'node_01', target: 'node_02', type: 'chronological' }
];

orchestrator.loadSystemTopology(mockNodes, mockEdges);

console.log(`📡 Graph loaded with ${orchestrator.nodeManager.edges.length} active relational interconnect line(s).`);

// Execute interaction smoke test
console.log("\n🖱️ Simulating user click event on node_02 spatial targets...");
const targetHit = orchestrator.nodeManager.hitTest(201, 199, 1.0);

if (targetHit) {
  console.log("🟢 Hit testing resolution calculation: PASSED.");
  if (typeof orchestrator.onNodeSelected === 'function') {
    orchestrator.onNodeSelected(targetHit);
  }
} else {
  console.log("❌ Error: Structural coordinates collision failed.");
}

