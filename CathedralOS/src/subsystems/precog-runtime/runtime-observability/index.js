const { ExecutionRingBuffer } = require('./core/ring-buffer');
const { FrameIndex } = require('./core/frame-index');

function attachObservability(orchestratorInstance, options = {}) {
  const capacity = options.capacity || 2000;
  const store = new ExecutionRingBuffer(capacity);
  const frameIndex = new FrameIndex();
  
  // Create a localized telemetry bus for this subscription layer
  const bus = {
    subscribers: [],
    subscribe(callback) {
      this.subscribers.push(callback);
    },
    publish(span) {
      this.subscribers.forEach(cb => cb(span));
    }
  };

  const ctx = {
    store,
    frameIndex,
    metrics: {
      ingestDurations: [],
      evictionCount: 0
    }
  };

  // Centralized ingestion pipe
  bus.subscribe(span => {
    const t0 = performance.now();

    const overwritten = store.push(span);
    frameIndex.ingest(span);

    if (overwritten) {
      frameIndex.evict(overwritten);
      ctx.metrics.evictionCount++;
    }

    const t1 = performance.now();
    ctx.metrics.ingestDurations.push(t1 - t0);
  });

  // Tap into orchestrator lifecycle methods if they exist to pipe live updates
  if (orchestratorInstance.nodeManager) {
    // Intercept or hook nodeManager updates here if needed, publishing to bus
  }

  return {
    bus,
    store,
    frameIndex,
    metrics: ctx.metrics,
    getFrameProfile: frameId => frameIndex.getFrameProfile(frameId),
    detach: () => {
      bus.subscribers = [];
    }
  };
}

module.exports = { attachObservability };

