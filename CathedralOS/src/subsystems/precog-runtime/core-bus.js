// src/subsystems/precog-runtime/core-bus.js

export class PrecogBus {
  constructor() {
    this.listeners = new Map();
  }

  subscribe(eventType, callback) {
    if (typeof callback !== 'function') {
      throw new TypeError(`PrecogBus.subscribe expected a function for "${eventType}"`);
    }

    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    const bucket = this.listeners.get(eventType);
    bucket.add(callback);

    return () => {
      bucket.delete(callback);
      if (bucket.size === 0) {
        this.listeners.delete(eventType);
      }
    };
  }

  publish(eventType, payload = {}) {
    const bucket = this.listeners.get(eventType);
    if (!bucket || bucket.size === 0) return;

    const event = {
      type: eventType,
      ts: new Date().toISOString(),
      ...payload
    };

    for (const callback of bucket) {
      try {
        callback(event);
      } catch (err) {
        console.error(`[PrecogBus] listener failure for "${eventType}"`, err);
      }
    }
  }

  clear(eventType = null) {
    if (eventType) {
      this.listeners.delete(eventType);
      return;
    }

    this.listeners.clear();
  }
}

export const precogBus = new PrecogBus();
