// src/subsystems/precog-runtime/runtime-observability/core/telemetry-bus.js

class TelemetryBus {
  constructor() {
    this.subscribers = [];
  }

  subscribe(fn) {
    this.subscribers.push(fn);
  }

  emit(event) {
    for (const fn of this.subscribers) {
      fn(event);
    }
  }

  startSpan(name, meta = {}) {
    const span = {
      name,
      start: performance.now(),
      meta,
      logs: [],
      status: 'pending'
    };

    return {
      log: (data) => span.logs.push({ timestamp: performance.now(), ...data }),

      ok: (data) => {
        span.status = "ok";
        span.data = { ...span.data, ...data };
      },

      error: (err) => {
        span.status = "error";
        span.error = err?.message || err;
      },

      end: () => {
        span.end = performance.now();
        span.duration = span.end - span.start;
        this.emit(span);
      }
    };
  }
}

module.exports = { TelemetryBus };

