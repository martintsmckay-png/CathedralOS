/**
 * CathedralOS Core Subsystem: PrecogEngine ➔ precogBus Adapter (v1.0)
 * Context: Alpha Base / Living Room Timeline Coordination
 * Design Protocol: Broadcasts cognitive states to spatial and HUD overlays
 */

import { precogBus } from '../broker/precog-bus.js';

export class PrecogBusAdapter {
    constructor(precogEngine) {
        this.engine = precogEngine;

        // Automatically ingest routed transport packets to trigger the runtime loop
        precogBus.subscribe("transport.packet.routed", (packet) => {
            this.engine.ingest(packet);
        });

        // Pipe historical ledger fragments directly into the messaging spine
        this.engine.onLedgerFragment = (text, sourceId) => {
            precogBus.publish("precog.ledger.fragment", {
                text,
                sourceId,
                ts: Date.now()
            });
        };
    }

    /**
     * Broadcast variance drift values to update real-time node halos
     */
    emitDrift(channelId, delta) {
        precogBus.publish("precog.drift.detected", {
            channelId,
            driftScore: delta.driftScore,
            notes: delta.notes,
            ts: Date.now()
        });
    }

    /**
     * Broadcast branch split creation when drift thresholds blow out
     */
    emitFork(parentChannelId, branches) {
        precogBus.publish("precog.fork.created", {
            parentChannelId,
            spawned: branches.map(b => b.id),
            forkId: branches[0]?.forkId,
            ts: Date.now()
        });
    }

    /**
     * Broadcast timelines collapsing back into unified consensus
     */
    emitMerge(forkId, mergedChannel, winningState, agreeingCount, totalCount) {
        precogBus.publish("precog.merge.completed", {
            forkId,
            mergedChannelId: mergedChannel.id,
            winningState,
            agreeingCount,
            totalCount,
            ts: Date.now()
        });
    }
}

