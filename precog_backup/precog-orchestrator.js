// src/subsystems/precog-runtime/precog-orchestrator.js
// CathedralOS Native Module — Core Runtime Lifecycle Orchestrator (Path 1 Stable)

import { PrecogEngine } from './precog-engine.js';
import { ZoomEngine } from './zoom-engine.js';
import { FabricCanvasSetup } from './fabric-canvas-setup.js';
import { SpatialNodeManager } from './spatial-node-manager.js';

export class PrecogRuntimeOrchestrator {
  constructor({ canvasId = 'precog-canvas', bus = null, historyLimit = 100 } = {}) {
    this.canvasId = canvasId;
    this.bus = bus;
    this.historyLimit = historyLimit;

    this.canvasSetup = null;
    this.spatialManager = null;
    this.zoomEngine = null;
    this.precogEngine = null;

    this.initialized = false;
  }

  /**
   * Initializes stack to use the plain 2D context pipeline natively
   */
  initialize() {
    if (this.initialized) return;

    try {
      console.log('[ORCHESTRATOR] :: Instantiating Path 1 Canvas Pipeline...');

      // 1. Core DOM Canvas Layer Wrapper
      this.canvasSetup = new FabricCanvasSetup(this.canvasId);

      // 2. Memory Topology Coordinate Manager
      this.spatialManager = new SpatialNodeManager();

      // 3. Path 1 Connection: Inject canvas setup and the spatial manager directly
      this.zoomEngine = new ZoomEngine(
        this.canvasSetup.canvas,
        this.canvasSetup,
        this.spatialManager
      );

      // 4. Bind the zoom matrix back to layout click/drag managers
      this.canvasSetup.attachZoomEngine(this.zoomEngine);

      // 5. Initialize telemetry ingestion
      this.precogEngine = new PrecogEngine({
        bus: this.bus,
        historyLimit: this.historyLimit,
        onLedgerFragment: (msg, source) => this.handleSystemLog(msg, source)
      });

      this.initialized = true;
      console.log('[ORCHESTRATOR] :: Pipeline closed. Grid engine synced to native 2D canvas.');
    } catch (error) {
      console.error(`[ORCHESTRATOR] :: Bootstrap aborted on hard fault: ${error.message}`);
      throw error;
    }
  }

  /**
   * Feeds raw data objects into the spatial matrix and re-renders the 2D surface
   */
  loadTopology(dynamicMemoryBlocks = []) {
    if (!this.spatialManager) {
      throw new Error('[ORCHESTRATOR] :: Cannot populate topology before stack init.');
    }

    const projectedNodes = this.spatialManager.populateFromHierarchy(dynamicMemoryBlocks);
    console.log(`[ORCHESTRATOR] :: Spatial bridge updated: ${projectedNodes.length} nodes layout compiled.`);

    // Trigger explicit canvas draw pass on raw ctx matrix
    if (this.zoomEngine) {
      this.zoomEngine.render();
    }
  }

  start() {
    if (!this.initialized) this.initialize();
    if (this.precogEngine) this.precogEngine.start();
    if (this.zoomEngine) this.zoomEngine.render();
  }

  stop() {
    if (this.precogEngine) this.precogEngine.stop();
    console.log('[ORCHESTRATOR] :: Pipeline telemetry paused.');
  }

  handleSystemLog(message, source) {
    const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
    console.log(`[${timestamp}][${source}] :: ${message}`);
  }
}

