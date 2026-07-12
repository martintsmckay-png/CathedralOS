// src/subsystems/precog-runtime/runtime-observability/core/lifecycle-taps.js

function createLifecycleTaps(orchestrator, ctx) {
  const taps = new Map();

  // Inject lightweight pub/sub directly onto the orchestrator instance if missing
  if (!orchestrator.on) {
    orchestrator.on = (event, fn) => {
      if (!taps.has(event)) taps.set(event, []);
      taps.get(event).push(fn);
    };
  }

  if (!orchestrator.emit) {
    orchestrator.emit = (event, payload) => {
      const list = taps.get(event);
      if (!list) return;
      for (const fn of list) {
        fn(payload);
      }
    };
  }

  return {
    tap(event, handler) {
      orchestrator.on(event, (instance) => {
        handler(instance, ctx);
      });
    }
  };
}

module.exports = { createLifecycleTaps };

