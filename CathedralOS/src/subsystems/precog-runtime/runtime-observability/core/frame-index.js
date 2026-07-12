class FrameIndex {
  constructor() {
    this.frames = new Map();
  }

  ingest(span) {
    const frameId = span?.meta?.frameId;
    if (frameId == null) return;

    if (!this.frames.has(frameId)) {
      this.frames.set(frameId, {
        tick: null,
        spatialQueries: [],
        stateDelta: null
      });
    }

    const frame = this.frames.get(frameId);
    if (span.name === "engine_tick") {
      frame.tick = span;
    } else if (span.name === "spatial_hit_test") {
      frame.spatialQueries.push(span);
    } else if (span.name === "state_delta") {
      frame.stateDelta = span;
    }
  }

  evict(span) {
    const frameId = span?.meta?.frameId;
    if (frameId == null) return;

    const frame = this.frames.get(frameId);
    if (!frame) return;

    if (span.name === "engine_tick" && frame.tick === span) {
      frame.tick = null;
    } else if (span.name === "spatial_hit_test") {
      frame.spatialQueries = frame.spatialQueries.filter(s => s !== span);
    } else if (span.name === "state_delta" && frame.stateDelta === span) {
      frame.stateDelta = null;
    }

    if (!frame.tick && frame.spatialQueries.length === 0 && !frame.stateDelta) {
      this.frames.delete(frameId);
    }
  }

  getFrameProfile(frameId) {
    return this.frames.get(frameId) || null;
  }

  clear() {
    this.frames.clear();
  }
}

module.exports = { FrameIndex };

