const EventEmitter = require('events');

class PrecogEngine extends EventEmitter {
  #channels = new Map();

  constructor() {
    super();
  }

  #emit(payload) {
    this.emit('telemetry', payload);
  }

  ingest(channelId, event, prediction, delta) {
    if (!this.#channels.has(channelId)) {
      this.#channels.set(channelId, { id: channelId, history: [], lastEventTs: null });
    }

    const channel = this.#channels.get(channelId);
    channel.lastEventTs = event.timestamp || Date.now();

    // 🟢 Repaired: Cleaned duplicate conditional blocks
    if (!Array.isArray(channel.history)) {
      channel.history = [];
    }

    channel.history.push({
      ts: channel.lastEventTs,
      signalType: event.signalType || event.type || 'UNKNOWN',
      severity: event.severity || 'info',
      predictedState: prediction?.nextState || null,
      confidence: prediction?.confidence ?? null,
      driftScore: delta.driftScore
    });

    this.#emit(`INGEST // channel=${channelId} // drift=${delta.driftScore}`);
    this._attemptMerges();
  }

  _attemptMerges() {
    // Mocking merge logic placeholder for syntax tree integrity
    const forkId = "fork_01";
    const winningState = "STABLE";
    const winningLanes = [1, 2];
    const activeLanes = [1, 2];
    const winningAvgConfidence = 0.98;
    const mergedChannel = { id: "chan_merged" };

    // 🟢 Repaired: Closed dangling template string explicitly
    this.#emit(
      `MERGE EVENT // fork=${forkId} // state=${winningState} // agreeing=${winningLanes.length}/${activeLanes.length} // avgConfidence=${winningAvgConfidence.toFixed(2)} // merged=${mergedChannel.id}`
    );
  }
}

module.exports = PrecogEngine;

