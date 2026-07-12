// src/subsystems/precog-runtime/runtime-observability/replay/state-delta-capture.js

class StateDeltaCapture {
  constructor(ctx) {
    this.ctx = ctx;
  }

  captureFrame(frameId) {
    const orch = this.ctx.orchestrator;
    if (!orch) return;

    // Direct, lightweight property polling from underlying sub-engines
    const deltaPayload = {
      meta: { frameId },
      camera: {
        x: orch.zoomEngine?.viewport?.x || 0,
        y: orch.zoomEngine?.viewport?.y || 0,
        zoom: orch.zoomEngine?.viewport?.zoom || 1.0
      },
      topologyRevision: orch.nodeManager?.revisionId || 0,
      selectedNodeId: orch.selectedNodeId || null,
      hoveredNodeId: orch.hoveredNodeId || null
    };

    // Emit cleanly as a native span token on our shared telemetry bus
    const span = this.ctx.telemetry.startSpan("state_delta", {
      meta: { frameId }
    });
    span.ok(deltaPayload);
    span.end();
  }
}

module.exports = { StateDeltaCapture };

