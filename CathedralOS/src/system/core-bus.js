// src/system/core-bus.js

export class CathedralBus {
  constructor({ enableLogging = false, maxLog = 5000 } = {}) {
    this.subscribers = new Map();
    this.wildcard = new Set();
    this.enableLogging = enableLogging;

    // 🔁 event log (replay backbone)
    this.eventLog = [];
    this.maxLog = maxLog;

    // 🧵 async dispatch queue
    this.queue = [];
    this.processing = false;

    // 🧭 replay cursor
    this.replayIndex = 0;
  }

  subscribe(eventType, callback) {
    if (typeof callback !== "function") {
      throw new TypeError(`[CathedralBus] callback must be a function`);
    }

    const target =
      eventType === "*"
        ? this.wildcard
        : (this.subscribers.get(eventType) ?? new Set());

    if (eventType !== "*") {
      this.subscribers.set(eventType, target);
    }

    target.add(callback);

    return () => target.delete(callback);
  }

  publish(eventType, payload = {}, meta = {}) {
    const event = {
      id: crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`,
      type: eventType,
      payload,
      timestamp: Date.now(),
      meta
    };

    // store deterministically
    this.#log(event);

    // enqueue async dispatch
    this.queue.push(event);
    this.#drain();

    return event.id;
  }

  async #drain() {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0) {
      const event = this.queue.shift();

      await this.#dispatch(event);
    }

    this.processing = false;
  }

  async #dispatch(event) {
    const { type, payload } = event;

    if (this.enableLogging) {
      console.log(`[BUS] ${type}`, payload);
    }

    const subs = this.subscribers.get(type);

    if (subs) {
      for (const cb of subs) {
        try {
          await cb(payload, type, event);
        } catch (err) {
          console.error(`[BUS] subscriber error @ ${type}`, err);
        }
      }
    }

    for (const cb of this.wildcard) {
      try {
        await cb(payload, type, event);
      } catch (err) {
        console.error(`[BUS] wildcard error`, err);
      }
    }
  }

  #log(event) {
    this.eventLog.push(event);

    if (this.eventLog.length > this.maxLog) {
      this.eventLog.shift();
    }
  }

  /**
   * 🔁 FULL SYSTEM REPLAY
   */
  async replay({ fromIndex = 0, toIndex = this.eventLog.length }) {
    for (let i = fromIndex; i < toIndex; i++) {
      const event = this.eventLog[i];
      if (!event) continue;
      await this.#dispatch(event);
    }
  }

  /**
   * 🧭 rewind pointer (for canvas state rebuild)
   */
  rewind(n = 1) {
    this.replayIndex = Math.max(0, this.replayIndex - n);
    return this.replayIndex;
  }

  /**
   * fast snapshot export for canvas reconstruction
   */
  exportLog() {
    return [...this.eventLog];
  }
}

// singleton
export const cathedralBus = new CathedralBus({ enableLogging: false });
