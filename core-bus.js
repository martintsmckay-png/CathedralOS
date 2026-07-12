// src/subsystems/cathedral-core/core-bus.js

function createEventId() {
  return `evt_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export class CathedralBus {
  constructor({ enableHistory = false, historyLimit = 200 } = {}) {
    this.listeners = new Map();        // eventType -> Set<callback>
    this.anyListeners = new Set();     // wildcard listeners
    this.enableHistory = enableHistory;
    this.historyLimit = historyLimit;
    this.history = [];
  }

  subscribe(eventType, callback) {
    if (typeof callback !== "function") {
      throw new TypeError(`[CathedralBus] callback for "${eventType}" must be a function`);
    }

    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }

    const set = this.listeners.get(eventType);
    set.add(callback);

    return () => this.unsubscribe(eventType, callback);
  }

  subscribeAny(callback) {
    if (typeof callback !== "function") {
      throw new TypeError("[CathedralBus] wildcard callback must be a function");
    }

    this.anyListeners.add(callback);
    return () => this.anyListeners.delete(callback);
  }

  unsubscribe(eventType, callback) {
    const set = this.listeners.get(eventType);
    if (!set) return false;

    const removed = set.delete(callback);
    if (set.size === 0) {
      this.listeners.delete(eventType);
    }

    return removed;
  }

  clear(eventType) {
    if (typeof eventType === "string") {
      return this.listeners.delete(eventType);
    }

    this.listeners.clear();
    this.anyListeners.clear();
    this.history = [];
    return true;
  }

  listenerCount(eventType) {
    if (eventType) {
      return this.listeners.get(eventType)?.size ?? 0;
    }

    let total = this.anyListeners.size;
    for (const set of this.listeners.values()) total += set.size;
    return total;
  }

  publish(eventType, data = null, meta = {}) {
    const event = Object.freeze({
      id: createEventId(),
      type: eventType,
      data,
      meta: Object.freeze({
        ts: Date.now(),
        ...meta
      })
    });

    if (this.enableHistory) {
      this.history.push(event);
      if (this.history.length > this.historyLimit) {
        this.history.shift();
      }
    }

    const listeners = this.listeners.get(eventType);
    if (listeners) {
      for (const callback of listeners) {
        try {
          callback(event);
        } catch (err) {
          console.error(`🔴 [Bus Error] Failed callback for "${eventType}"`, err, event);
        }
      }
    }

    for (const callback of this.anyListeners) {
      try {
        callback(event);
      } catch (err) {
        console.error(`🔴 [Bus Error] Failed wildcard callback for "${eventType}"`, err, event);
      }
    }

    return event;
  }

  getHistory() {
    return [...this.history];
  }
}

export const globalBus = new CathedralBus({
  enableHistory: true,
  historyLimit: 300
});
