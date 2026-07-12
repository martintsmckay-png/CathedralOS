// src/subsystems/precog-runtime/precog-orchestrator.js
// CathedralOS Native Module — Precog Subsystem Top-Level Runtime Orchestrator (Phase 3D: Replay)

const SpatialNodeManager = require('./spatial-node-manager');
const ZoomEngine = require('./zoom-engine');
const CanvasViewportController = require('./canvas-viewport-controller');

class PrecogRuntimeOrchestrator {
  constructor() {
    // Structural Core Instantiations
this.nodeManager = new SpatialNodeManager();
if (typeof this.emit === 'function') {
  this.emit("nodeManager:ready", this.nodeManager);
}

    this.zoomEngine = null;
    this.viewport = null;

    // Runtime Lifecycle State
    this.canvas = null;
    this.isRunning = false;
    this.externalInspectorCallback = null;
    this.externalTimelineCallback = null;
  }

  /**
   * Mounts HTML5 Canvas context and establishes internal relational wiring pipelines
   * @param {HTMLCanvasElement} canvasElement
   */
  mountCanvas(canvasElement) {
    if (!canvasElement) {
      throw new Error("PrecogRuntimeOrchestrator.mountCanvas requires a valid HTMLCanvasElement context.");
    }

    this.canvas = canvasElement;

// 1. Initialize Renderer with null viewport placeholder initially
this.zoomEngine = new ZoomEngine(this.canvas, null, this.nodeManager);
if (typeof this.emit === 'function') {
  this.emit("zoomEngine:ready", this.zoomEngine);
}

    // 2. Initialize Viewport Input Event Router passing the true zoomEngine instance
    this.viewport = new CanvasViewportController(this.canvas, this.zoomEngine);

    // 3. Mutate the zoomEngine reference to point to the correct viewport controller instance
    this.zoomEngine.viewport = this.viewport;

    // Synchronize Input Layer Interaction Events to Orchestrator Interface Methods
    this.viewport.onNodeSelected = (node) => {
      this.handleNodeSelection(node);
    };

    this.viewport.onReplayCursorChanged = (cursor) => {
      this.handleReplayCursorChanged(cursor);
    };
  }


  /**
   * Canonical Topographic Data Ingestion Path
   * Loads structural graphs and sets up timeline boundaries automatically
   */
  loadSystemTopology(nodesArray = [], edgesArray = []) {
    this.nodeManager.loadTopology(nodesArray, edgesArray);

    const bounds = this.nodeManager.getTimelineBounds();

    if (this.zoomEngine) {
      this.zoomEngine.setPlaybackBounds(bounds);

      // Default the playback head to the newest available record slice on initial load
      if (this.zoomEngine.playbackCursor == null && bounds.minSequence <= bounds.maxSequence) {
        this.zoomEngine.setPlaybackCursor(bounds.maxSequence);
      }
      
      this.zoomEngine.render();
    }
  }

  /**
   * Registers a data callback listener to route node inspection selection straight to Telemetry/UI layers
   */
  registerInspectorListener(callback) {
    this.externalInspectorCallback = typeof callback === 'function' ? callback : null;
  }

  /**
   * Registers an external observer tracking changes on timeline updates
   */
  registerTimelineListener(callback) {
    this.externalTimelineCallback = typeof callback === 'function' ? callback : null;
  }

  // Viewport / Subsystem Event Handling Methods
  handleNodeSelection(node) {
    if (this.externalInspectorCallback) {
      this.externalInspectorCallback(node);
    }
  }

  handleReplayCursorChanged(cursor) {
    if (this.externalTimelineCallback) {
      this.externalTimelineCallback(cursor);
    }
  }

  // Expose Replay Controls Surface API
  setReplayMode(enabled) {
    if (!this.zoomEngine) return;
    this.zoomEngine.setReplayMode(enabled);
  }

  setPlaybackCursor(cursor) {
    if (!this.zoomEngine) return;
    this.zoomEngine.setPlaybackCursor(cursor);
  }

  bindReplaySlider(sliderElement) {
    if (!this.viewport) return;
    this.viewport.bindReplaySlider(sliderElement);
  }

  getTimelineBounds() {
    return this.nodeManager.getTimelineBounds();
  }

  focusNodeById(nodeId) {
    if (!this.nodeManager || !this.zoomEngine) return;
    const node = this.nodeManager.nodes.get(nodeId);
    if (node) {
      this.zoomEngine.setSelectedNode(node);
      this.zoomEngine.focusNode(node);
    }
  }

  // Lifecycle Orchestration Hooks
  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    if (this.zoomEngine) {
      this.zoomEngine.render();
    }
  }

  stop() {
    this.isRunning = false;
  }
}

module.exports = PrecogRuntimeOrchestrator;

