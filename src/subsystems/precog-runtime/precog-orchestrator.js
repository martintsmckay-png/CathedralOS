// src/subsystems/precog-runtime/precog-orchestrator.js

const { PrecogEngine } = require('./precog-engine.js');
const ZoomEngine = require('./zoom-engine.js');
const { FabricCanvasSetup } = require('./fabric-canvas-setup.js');
const { SpatialNodeManager } = require('./spatial-node-manager.js');

class PrecogRuntimeOrchestrator {
  constructor({
    canvasId = 'precog-canvas',
    bus = null,
    historyLimit = 100,
    logger = console,
    canvasFactory = (id) => new FabricCanvasSetup(id),
    spatialFactory = () => new SpatialNodeManager(),
    zoomFactory = ({ canvas, canvasSetup, spatialManager }) =>
      new ZoomEngine(canvas, canvasSetup, spatialManager),
    engineFactory = (opts) => new PrecogEngine(opts)
  } = {}) {
    this.canvasId = canvasId;
    this.bus = bus;
    this.historyLimit = historyLimit;
    this.logger = logger;

    this.canvasFactory = canvasFactory;
    this.spatialFactory = spatialFactory;
    this.zoomFactory = zoomFactory;
    this.engineFactory = engineFactory;

    this.canvasSetup = null;
    this.spatialManager = null;
    this.zoomEngine = null;
    this.precogEngine = null;

    this.initialized = false;
    this.running = false;
    this.renderQueued = false;
    this.disposers = [];
  }

  initialize() {
    if (this.initialized) return this;

    this.logger.info('[ORCHESTRATOR] initializing runtime');

    this.canvasSetup = this.canvasFactory(this.canvasId);
    this.spatialManager = this.spatialFactory();
    this.zoomEngine = this.zoomFactory({
      canvas: this.canvasSetup.canvas,
      canvasSetup: this.canvasSetup,
      spatialManager: this.spatialManager
    });

    if (typeof this.canvasSetup.attachZoomEngine === 'function') {
      this.canvasSetup.attachZoomEngine(this.zoomEngine);
    }

    this.precogEngine = this.engineFactory({
      bus: this.bus,
      historyLimit: this.historyLimit,
      onLedgerFragment: (msg, source) => this.logSystem(msg, source)
    });

    this.initialized = true;
    this.publishLifecycle('runtime:initialized');
    return this;
  }

  start() {
    if (!this.initialized) this.initialize();
    if (this.running) return this;

    this.precogEngine?.start();
    this.running = true;
    this.requestRender('runtime:start');
    this.publishLifecycle('runtime:started');

    return this;
  }

  stop() {
    if (!this.running) return this;

    this.precogEngine?.stop();
    this.running = false;
    this.publishLifecycle('runtime:stopped');

    return this;
  }

  destroy() {
    this.stop();

    for (const dispose of this.disposers) {
      try { dispose(); } catch (err) {
        this.logger.error('[ORCHESTRATOR] dispose failed', err);
      }
    }
    this.disposers = [];

    this.zoomEngine?.destroy?.();
    this.canvasSetup?.destroy?.();
    this.spatialManager?.destroy?.();
    this.precogEngine?.destroy?.();

    this.canvasSetup = null;
    this.spatialManager = null;
    this.zoomEngine = null;
    this.precogEngine = null;

    this.initialized = false;
    this.publishLifecycle('runtime:destroyed');
    return this;
  }

  loadTopology(dynamicMemoryBlocks = []) {
    if (!this.spatialManager) {
      throw new Error('[ORCHESTRATOR] cannot load topology before initialize()');
    }

    const projectedNodes =
      this.spatialManager.populateFromHierarchy(dynamicMemoryBlocks);

    this.logger.info(
      `[ORCHESTRATOR] topology loaded (${projectedNodes.length} nodes)`
    );

    this.requestRender('topology:loaded');
    return projectedNodes;
  }

  requestRender(reason = 'unknown') {
    if (!this.zoomEngine || this.renderQueued) return;

    this.renderQueued = true;
    requestAnimationFrame(() => {
      this.renderQueued = false;
      this.zoomEngine?.render?.();
      this.publishLifecycle('runtime:rendered', { reason });
    });
  }

  publishLifecycle(type, extra = {}) {
    this.bus?.publish?.(type, {
      canvasId: this.canvasId,
      initialized: this.initialized,
      running: this.running,
      ...extra
    });
  }

  logSystem(message, source = 'runtime') {
    this.logger.info(`[${source}] ${message}`);
  }
}
module.exports = PrecogRuntimeOrchestrator;

