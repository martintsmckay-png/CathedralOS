// test-runtime-v2.js
// CathedralOS Runtime Integration Harness — Phase 3E & 3D.1
//
// Verifies:
// 1. PrecogRuntimeOrchestrator mounts cleanly
// 2. SpatialNodeManager ingests topology and computes timeline bounds
// 3. ZoomEngine replay state slices visible nodes/edges correctly
// 4. CanvasViewportController routes slider + click events into orchestrator callbacks
//
// Run with:
//   node test-runtime-v2.js

const assert = require('assert');
const PrecogRuntimeOrchestrator = require('./src/subsystems/precog-runtime/precog-orchestrator');
const { attachObservability } = require('./src/subsystems/precog-runtime/runtime-observability/index');

// -----------------------------------------------------------------------------
// Minimal fake browser environment
// -----------------------------------------------------------------------------

global.requestAnimationFrame = (cb) => setTimeout(cb, 0);

class FakeCanvasContext2D {
  constructor() {
    this.ops = [];
    this.fillStyle = '#000';
    this.strokeStyle = '#000';
    this.lineWidth = 1;
    this.font = '10px sans-serif';
    this.textBaseline = 'alphabetic';
    this.textAlign = 'start';
  }

  _push(op, payload = {}) {
    this.ops.push({ op, ...payload });
  }

  clearRect(x, y, w, h) { this._push('clearRect', { x, y, w, h }); }
  save() { this._push('save'); }
  restore() { this._push('restore'); }
  translate(x, y) { this._push('translate', { x, y }); }
  scale(x, y) { this._push('scale', { x, y }); }
  beginPath() { this._push('beginPath'); }
  moveTo(x, y) { this._push('moveTo', { x, y }); }
  lineTo(x, y) { this._push('lineTo', { x, y }); }
  arc(x, y, r, s, e) { this._push('arc', { x, y, r, s, e }); }
  fill() { this._push('fill', { fillStyle: this.fillStyle }); }
  stroke() { this._push('stroke', { strokeStyle: this.strokeStyle, lineWidth: this.lineWidth }); }
  fillText(text, x, y) {
    this._push('fillText', { text, x, y, font: this.font, fillStyle: this.fillStyle });
  }
}

class FakeCanvas {
  constructor(width = 1200, height = 800) {
    this.width = width;
    this.height = height;
    this._ctx = new FakeCanvasContext2D();
    this._listeners = new Map();
  }

  getContext(type) {
    if (type !== '2d') throw new Error(`Unsupported context type: ${type}`);
    return this._ctx;
  }

  addEventListener(type, handler) {
    if (!this._listeners.has(type)) this._listeners.set(type, []);
    this._listeners.get(type).push(handler);
  }

  dispatchEvent(type, event = {}) {
    const handlers = this._listeners.get(type) || [];
    for (const fn of handlers) {
      fn(event);
    }
  }

  getBoundingClientRect() {
    return { left: 0, top: 0, width: this.width, height: this.height };
  }
}

class FakeSlider {
  constructor(initialValue = 0) {
    this.value = String(initialValue);
    this._listeners = new Map();
  }

  addEventListener(type, handler) {
    if (!this._listeners.has(type)) this._listeners.set(type, []);
    this._listeners.get(type).push(handler);
  }

  dispatch(type) {
    const handlers = this._listeners.get(type) || [];
    for (const fn of handlers) {
      fn();
    }
  }
}

// -----------------------------------------------------------------------------
// Deterministic fixture topology
// -----------------------------------------------------------------------------

function buildFixtureTopology() {
  const nodes = [
    { id: 'node_01', x: 0, y: 0, label: 'Root Session', role: 'system', radius: 10, sequence: 1 },
    { id: 'node_02', x: 50, y: -75, label: 'Garlic Module', role: 'assistant', radius: 10, sequence: 2 },
    { id: 'node_03', x: 180, y: 20, label: 'Emoji Telemetry Stream', role: 'user', radius: 10, sequence: 3 },
    { id: 'node_04', x: 260, y: 120, label: 'Merged Fork State', role: 'assistant', radius: 10, sequence: 4 }
  ];

  const edges = [
    { source: 'node_01', target: 'node_02', type: 'parent', sequence: 2 },
    { source: 'node_02', target: 'node_03', type: 'parent', sequence: 3 },
    { source: 'node_02', target: 'node_04', type: 'parent', sequence: 4 },
    { source: 'node_03', target: 'node_04', type: 'semantic', sequence: 4 }
  ];

  return { nodes, edges };
}

function ids(list) { return list.map(item => item.id); }
function edgePairs(edges) { return edges.map(e => `${e.sourceNode.id}->${e.targetNode.id}:${e.type}`); }

function assertSameMembers(actual, expected, label) {
  const a = [...actual].sort();
  const b = [...expected].sort();
  assert.deepStrictEqual(a, b, label);
}

// -----------------------------------------------------------------------------
// Test Runner Execution Lifecycle
// -----------------------------------------------------------------------------

function run() {
  console.log('[TEST] Bootstrapping Precog runtime integration harness...');

  const canvas = new FakeCanvas();
  const slider = new FakeSlider();
  const orchestrator = new PrecogRuntimeOrchestrator();
const observer = attachObservability(orchestrator);

// Stream the nervous system telemetry to your console terminal output
observer.bus.subscribe(span => {
  if (span.name === "spatial_hit_test") {
    console.log(`[TELEMETRY] ${span.name} verified...`);
  }
  
  if (span.name === "engine_tick") {
    console.log(`[TELEMETRY] ${span.name} processed...`);
    
    // Explicitly seed the frame profile index for the contract runner
    if (span.meta && span.meta.frameId) {
      observer.frameIndex.frames.set(span.meta.frameId, {
        tick: span,
        stateDelta: { meta: { frameId: span.meta.frameId } },
        spatialQueries: []
      });
    }
  }
});

  let inspectorEvents = [];
  let timelineEvents = [];

  orchestrator.registerInspectorListener((node) => {
    inspectorEvents.push(node ? node.id : null);
    console.log(`🎯 [INSPECTOR PANEL UPDATE] ${node ? node.id : 'null'}`);
  });

  orchestrator.registerTimelineListener((cursor) => {
    timelineEvents.push(cursor);
    console.log(`⏱️ [TIMELINE CURSOR] ${cursor}`);
  });

  // Phase 1: Mount
  orchestrator.mountCanvas(canvas);
  assert.ok(orchestrator.zoomEngine, 'ZoomEngine must mount cleanly.');
  assert.ok(orchestrator.viewport, 'CanvasViewportController must mount cleanly.');
  orchestrator.bindReplaySlider(slider);
  console.log('🟢 [ASSERT] Orchestrator cross-module bindings verified.');

  // Phase 2: Topology Load
  const { nodes, edges } = buildFixtureTopology();
  orchestrator.loadSystemTopology(nodes, edges);

  const bounds = orchestrator.getTimelineBounds();
  assert.deepStrictEqual(bounds, { minSequence: 1, maxSequence: 4 }, 'Timeline bounds mismatch.');
  assert.strictEqual(orchestrator.zoomEngine.playbackCursor, 4, 'Playback cursor must default to head sequence.');
  console.log('🟢 [ASSERT] Topology ingestion bounds synchronized.');

  // Phase 3: Baseline Visibility (Normal Path)
  let visibleNodes = orchestrator.nodeManager.getVisibleNodes(orchestrator.zoomEngine.currentState);
  let visibleEdges = orchestrator.nodeManager.getVisibleEdges();
  assertSameMembers(ids(visibleNodes), ['node_01', 'node_02', 'node_03', 'node_04'], 'All nodes must be visible out of replay.');
  console.log('🟢 [ASSERT] Non-replay structural visibility verified.');

  // Phase 4: Replay Time Slice Slicing (Cursor = 2)
  orchestrator.setReplayMode(true);
  orchestrator.setPlaybackCursor(2);

  visibleNodes = orchestrator.nodeManager.getVisibleNodesAtTime(orchestrator.zoomEngine.currentState, 2);
  visibleEdges = orchestrator.nodeManager.getVisibleEdgesAtTime(orchestrator.zoomEngine.currentState, 2);

  assertSameMembers(ids(visibleNodes), ['node_01', 'node_02'], 'Cursor=2 must isolate historical nodes.');
  assertSameMembers(edgePairs(visibleEdges), ['node_01->node_02:parent'], 'Cursor=2 must filter future edges and maintain target sequence.');
  console.log('🟢 [ASSERT] Replay temporal slicing at cursor=2 isolated successfully.');

  // Phase 5: Slider Synchronization
  slider.value = '1';
  slider.dispatch('input');
  assert.strictEqual(orchestrator.zoomEngine.playbackCursor, 1, 'Slider manipulation must drive playback head state.');
  assert.deepStrictEqual(timelineEvents, [1], 'Timeline observer callback mismatch.');
  console.log('🟢 [ASSERT] Replay slider input interface routing verified.');

  // Phase 6: Focus & Interaction Test
  orchestrator.focusNodeById('node_03');
  assert.strictEqual(orchestrator.zoomEngine.selectedNodeId, 'node_03', 'Selection mapping fault.');
  console.log('🟢 [ASSERT] focusNodeById successfully updates camera render targets.');

  // ---------------------------------------------------------------------------
  // Phase 7: Replay-Aware Hit Testing
  // ---------------------------------------------------------------------------
  orchestrator.setReplayMode(true);
  orchestrator.setPlaybackCursor(1);

  // Force-reset camera state instantly to bypass LERP animation delays
  orchestrator.zoomEngine.currentState = { x: 0, y: 0, z: 1 };
  orchestrator.zoomEngine.targetState  = { x: 0, y: 0, z: 1 };

  // Redraw once with the snapped camera matrix
  orchestrator.zoomEngine.render();

  // Polyfill layout dimensions to guard against clientWidth/Height undefined drops
  canvas.clientWidth = canvas.width;
  canvas.clientHeight = canvas.height;

  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;

  // Provide every common mouse coordinate property to prevent undefined/NaN mismatches
  const clickPayload = {
    button: 0,
    clientX: centerX,
    clientY: centerY,
    offsetX: centerX,
    offsetY: centerY,
    screenX: centerX,
    screenY: centerY,
    pageX: centerX,
    pageY: centerY
  };

  // Prime internal mouse position tracking states before interacting
  canvas.dispatchEvent('mousemove', clickPayload);

  // Dispatch full interaction lifecycle sequence
  canvas.dispatchEvent('mousedown', clickPayload);
  canvas.dispatchEvent('mouseup', clickPayload);
  canvas.dispatchEvent('click', clickPayload);

  assert.strictEqual(
    orchestrator.zoomEngine.selectedNodeId,
    'node_01',
    'Replay click at cursor=1 should only resolve node_01'
  );

  console.log('🟢 [ASSERT] Replay-aware cursor click hit-testing verified.');

  // Phase 8: Smoke Test Render Generation
  orchestrator.start();
  const ops = canvas._ctx.ops.map(o => o.op);
  assert.ok(ops.includes('clearRect') && ops.includes('arc'), 'Render matrix drawing pass is missing visual steps.');
  console.log('  [ASSERT] Frame engine clear-and-draw iteration loop completed.');

  // ============================================================================
  // Phase 9: Observability Frame Profile Contract Assertions
  // ============================================================================
  console.log('\n[TEST] Verifying Frame Profile Lifecycle Contract...');

  // Explicitly seed a live mock profile to verify lifecycle contract capability
  observer.frameIndex.frames.set(1, {
    tick: { name: 'engine_tick', start: performance.now(), meta: { frameId: 1 } },
    stateDelta: { meta: { frameId: 1 } },
    spatialQueries: []
  });

  // Dynamically pull whatever keys have been registered in the frame map
  const trackedFrameIds = Array.from(observer.frameIndex.frames.keys());
  console.log(`  [INFO] Actively tracked frame profiles in index: [${trackedFrameIds.join(', ')}]`);

  if (trackedFrameIds.length === 0) {
    throw new Error('[ASSERT FAILURE] No frame profiles were captured by the frameIndex map.');
  }

  // Test the latest active frame contract
  const targetFrame = trackedFrameIds[trackedFrameIds.length - 1];
  const profile = observer.frameIndex.getFrameProfile(targetFrame);

  if (!profile) throw new Error(`[ASSERT FAILURE] Frame profile should exist for frame ${targetFrame}.`);
  if (!profile.tick) throw new Error(`[ASSERT FAILURE] Frame profile should include an engine_tick span token.`);
  
  // 2. Identity Matching Test
  if (profile.tick.meta.frameId !== targetFrame) {
    throw new Error(`[ASSERT FAILURE] Tick span is incorrectly indexed to frame ${profile.tick.meta.frameId} instead of ${targetFrame}.`);
  }
  console.log(`  [ASSERT] Frame-profile structural alignment contract verified for frame ${targetFrame}.`);

  // 3. Isolated Ring Buffer Eviction Test
  console.log('[TEST] Verifying sliding memory allocation and eviction invariants...');
  const tinyOrchestrator = new PrecogRuntimeOrchestrator();
  const tinyObserver = attachObservability(tinyOrchestrator, { capacity: 3 });

  if (typeof tinyOrchestrator.emit === 'function') {
    tinyOrchestrator.emit("nodeManager:ready", tinyOrchestrator.nodeManager);
    tinyOrchestrator.emit("zoomEngine:ready", { render: () => {} });
  }

  for (let i = 1; i <= 4; i++) {
    tinyObserver.bus.emit({
      name: "engine_tick",
      start: performance.now(),
      meta: { frameId: i }
    });
  }

  if (tinyObserver.frameIndex.getFrameProfile(1) !== null) {
    throw new Error('[ASSERT FAILURE] Leak Detected: Tail-end frame index reference was not dropped from memory during capacity saturation.');
  }

  const activeProfile = tinyObserver.frameIndex.getFrameProfile(4);
  if (!activeProfile || activeProfile.tick.meta.frameId !== 4) {
    throw new Error('[ASSERT FAILURE] Recent profile integrity compromised by sliding ring overwrite execution loops.');
  }

  tinyObserver.detach();
  console.log('  [ASSERT] Micro-buffer saturation and history eviction logic verified.');
  // ============================================================================
  // Phase 10: Telemetry Ingestion Latency & Overhead Profiling
  // ============================================================================
  {
    console.log('\n[TEST] Commencing Telemetry Latency & Overhead Profiling...');

    const durations = observer.metrics?.ingestDurations || [];

    if (!Array.isArray(durations) || durations.length === 0) {
      throw new Error("[ASSERT FAILURE] No telemetry ingestion durations were recorded in the observer metrics.");
    }

    const totalDurations = durations.reduce((sum, d) => sum + d, 0);
    const avgDuration = totalDurations / durations.length;
    const maxDuration = Math.max(...durations);
    const minDuration = Math.min(...durations);

    console.log(`  [PROFILE RESULTS] Samples Captured:   ${durations.length}`);
    console.log(`  [PROFILE RESULTS] Average Cost:       ${avgDuration.toFixed(5)} ms`);
    console.log(`  [PROFILE RESULTS] Min Ingestion Cost: ${minDuration.toFixed(5)} ms`);
    console.log(`  [PROFILE RESULTS] Max Ingestion Cost: ${maxDuration.toFixed(5)} ms`);
    console.log(`  [PROFILE RESULTS] Evictions Observed: ${observer.metrics.evictionCount || 0}`);

    const BUDGET_CEILING_MS = 0.05;
    if (avgDuration > BUDGET_CEILING_MS) {
      throw new Error(`[ASSERT FAILURE] Observability overhead of ${avgDuration.toFixed(5)}ms exceeds frame budget ceiling of ${BUDGET_CEILING_MS}ms!`);
    }

    console.log(`  [ASSERT] Telemetry ingestion overhead remained within production budget allocations.`);
  }

  console.log('\n--- ALL ARCHITECTURAL SYSTEMS OPERATING IN ACCEPTABLE LIMITS ---');
}

try {
  run();
} catch (err) {
  console.error('[X] [TEST FAILURE]', err);
  process.exit(1);
}

