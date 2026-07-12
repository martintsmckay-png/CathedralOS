// src/subsystems/precog-runtime/runtime-observability/middleware/hit-test-middleware.js

function createHitTestMiddleware(ctx) {
  return (originalHitTest) => {
    const wrapped = function (x, y, ...args) {
      // Inherit the frame iteration counter currently active on the runtime execution context
      const currentFrameId = ctx.frameClock?.current || null;

      const span = ctx.telemetry.startSpan("spatial_hit_test", {
        meta: { frameId: currentFrameId },
        coordinates: { x, y }
      });

      try {
        const result = originalHitTest.call(this, x, y, ...args);

        span.ok({
          resolvedNodeId: result ? result.id : null,
          hitSuccess: !!result
        });

        return result;
      } catch (err) {
        span.error(err);
        throw err;
      } finally {
        span.end();
      }
    };

    wrapped.__original = originalHitTest;
    return wrapped;
  };
}

module.exports = { createHitTestMiddleware };

