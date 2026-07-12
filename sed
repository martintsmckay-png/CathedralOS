// src/subsystems/precog-runtime/precog-engine.js
import { precogBus } from './core-bus.js';
import {
  createChannel,
  forkChannelSet,
  mergeChannels
} from './moonwalk-core.js';

function defaultOracle() {
  return {
    predict(event, { basePhase = 0 } = {}) {
      const severity = event?.severity || 'info';

      if (severity === 'critical') {
        return {
          nextState: basePhase === 180 ? 'HARD_RECOVERY' : 'SAFE_FALLBACK',
          confidence: 0.42
        };
      }

      if (severity === 'high') {
        return {
          nextState: 'DEGRADED_RUNTIME',
          confidence: 0.58
        };
      }

      if (severity === 'medium') {
        return {
          nextState: 'WATCHFUL_STABILITY',
          confidence: 0.72
        };
      }

      return {
        nextState: 'STABLE_RUNTIME',
        confidence: 0.91
      };
    },

    observe(event) {
      return {
        observedType: event?.signalType || event?.type || 'UNKNOWN',
        severity: event?.severity || 'info',
        source: event?.source || 'UNKNOWN',
        ts: event?.ts || new Date().toISOString()
      };
    },

    compare(prediction, observation) {
      const sev = observation?.severity || 'info';

      if (sev === 'critical') {
        return { driftScore: 0.90, notes: 'Critical anomaly drift detected' };
      }
      if (sev === 'high') {
        return { driftScore: 0.68, notes: 'High anomaly drift detected' };
      }
      if (sev === 'medium') {
        return { driftScore: 0.34, notes: 'Moderate drift within tolerance' };
      }

      return { driftScore: 0.08, notes: 'System stable' };
    }
  };
}

export class PrecogEngine {
  constructor({
    bus = precogBus,
    oracle = defaultOracle(),
    historyLimit = 100,
    forkThreshold = 0.65,
    mergeThreshold = 0.70,
    branchCount = 4,
    onLedgerFragment = null
  } = {}) {
    this.bus = bus;
    this.oracle = oracle;
    this.historyLimit = historyLimit;
    this.forkThreshold = forkThreshold;
    this.mergeThreshold = mergeThreshold;
    this.branchCount = Math.max(2, Math.floor(branchCount));
    this.onLedgerFragment = onLedgerFragment;

    this.channels = new Map();
    this.channels.set('phi_0', createChannel('phi_0'));

    this.unsubscribe = null;
    this.running = false;
  }

  start() {
    if (this.running) return;
    this.running = true;

    this.unsubscribe = this.bus.subscribe('anomaly', (event) => {
      this.ingest(event);
    });

    this.#emit('PRECOG RUNTIME ONLINE // Root lane phi_0 initialized');
  }

  stop() {
    if (typeof this.unsubscribe === 'function') {
      this.unsubscribe();
      this.unsubscribe = null;
    }

    this.running = false;
    this.#emit('PRECOG RUNTIME OFFLINE');
  }

  ingest(event) {
    if (!event) return;

    const forkGroups = new Map();

    for (const [id, channel] of this.channels.entries()) {
      if (channel.status === 'MERGED' || channel.status === 'DEAD') {
        continue;
      }

      const prediction = this.oracle.predict(event, {
        basePhase: channel.phase
      });
      const observation = this.oracle.observe(event);
      const delta = this.oracle.compare(prediction, observation);

      channel.prediction = prediction;
      channel.observation = observation;
      channel.driftScore = delta.driftScore;
      channel.lastEventTs = event.ts || new Date().toISOString();

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

      if (channel.history.length > this.historyLimit) {
        channel.history = channel.history.slice(-this.historyLimit);
      }

      // Multi-lane fork
      if (delta.driftScore > this.forkThreshold && channel.status === 'ACTIVE') {
        const branches = forkChannelSet(channel, this.branchCount);

        for (const branch of branches) {
          this.channels.set(branch.id, branch);
        }

        this.#emit(
          `FORK TRIGGERED // ${id} drift=${delta.driftScore.toFixed(2)} // spawned=${branches.length} lanes // fork=${branches[0].forkId}`
        );

        continue;
      }

      if (
        channel.forkId &&
        (channel.status === 'ACTIVE' || channel.status === 'FORKED')
      ) {
        if (!forkGroups.has(channel.forkId)) {
          forkGroups.set(channel.forkId, []);
        }

        forkGroups.get(channel.forkId).push(channel);
      }
    }

    this._attemptMerges(forkGroups);
  }

  _attemptMerges(forkGroups) {
    for (const [forkId, laneGroup] of forkGroups.entries()) {
      if (!Array.isArray(laneGroup) || laneGroup.length < 2) {
        continue;
      }

      const activeLanes = laneGroup.filter((ch) =>
        ch &&
        ch.status !== 'DEAD' &&
        ch.status !== 'MERGED' &&
        ch?.prediction?.nextState &&
        Number.isFinite(ch?.prediction?.confidence)
      );

      if (activeLanes.length < 2) {
        continue;
      }

      const stateBuckets = new Map();

      for (const lane of activeLanes) {
        const state = lane.prediction.nextState;

        if (!stateBuckets.has(state)) {
          stateBuckets.set(state, []);
        }

        stateBuckets.get(state).push(lane);
      }

      let winningState = null;
      let winningLanes = [];
      let winningAvgConfidence = 0;

      for (const [state, lanes] of stateBuckets.entries()) {
        const avgConfidence =
          lanes.reduce((sum, ch) => sum + (ch.prediction.confidence || 0), 0) /
          lanes.length;

        const isBetter =
          lanes.length > winningLanes.length ||
          (lanes.length === winningLanes.length &&
            avgConfidence > winningAvgConfidence);

        if (isBetter) {
          winningState = state;
          winningLanes = lanes;
          winningAvgConfidence = avgConfidence;
        }
      }

      const hasConsensus = winningLanes.length >= 2;
      const confidenceOK = winningAvgConfidence >= this.mergeThreshold;
      const majorityOK = winningLanes.length >= Math.ceil(activeLanes.length / 2);

      if (hasConsensus && confidenceOK && majorityOK) {
        const mergedChannel = mergeChannels(winningLanes);

        winningLanes.forEach((ch) => {
          ch.status = 'MERGED';
        });

        this.channels.set(mergedChannel.id, mergedChannel);

        this.#emit(
          `MERGE EVENT // fork=${forkId} // state=${winningState} // agreeing=${winningLanes.length}/${activeLanes.length} // avgConfidence=${winningAvgConfidence.toFixed(2)} -> ${mergedChannel.id}`
        );
      } else {
        this.#emit(
          `MERGE DEFERRED // fork=${forkId} // no consensus yet (${activeLanes.length} active lanes)`
        );
      }
    }
  }

  #emit(message) {
    if (typeof this.onLedgerFragment === 'function') {
      this.onLedgerFragment(message, 'PRECOG_ENGINE');
    } else {
      console.log(`[PRECOG_ENGINE] ${message}`);
    }
  }
}

