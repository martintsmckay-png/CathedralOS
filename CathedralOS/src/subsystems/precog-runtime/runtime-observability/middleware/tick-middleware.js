// src/subsystems/precog-runtime/runtime-observability/middleware/tick-middleware.js

function createTickMiddleware(ctx) {
  return (originalTick) => {
    const wrapped = function (...args) {
      // Advance the unified sequence head
      ctx.frameClock.current++;
      const currentFrameId = ctx.frameClock.current;

      const span = ctx.telemetry.startSpan("engine_tick", {
        meta: { frameId: currentFrameId },
        arguments: args
      });

      try {
        const result = originalTick.apply(this, args);

        // Extract metrics for indexing bounds
        const manager = this.nodeManager || ctx.orchestrator?.nodeManager;
        span.ok({
          nodeCount: manager?.nodes?.size || 0,
          edgeCount: manager?.edges?.length || 0
        });

        // Trigger Delta Capture Hook for this frame iteration
        if (ctx.deltaCapture && typeof ctx.deltaCapture.captureFrame === 'function') {
          ctx.deltaCapture.captureFrame(currentFrameId);
        }

        return result;
      } catch (err) {
        span.error(err);
        throw err;
      } finally {
        span.end();
      }
    };

    wrapped.__original = originalTick;
    return wrapped;
  };
}

module.exports = { createTickMiddleware };

