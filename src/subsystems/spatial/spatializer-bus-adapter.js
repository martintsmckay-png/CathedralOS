/**
 * CathedralOS Core Subsystem: Spatializer ➔ precogBus Adapter (v1.0)
 * Context: Alpha Base Infinite Canvas Mapping
 * Design Protocol: Translates data packets and timelines into structural coordinates
 */

import { precogBus } from '../broker/precog-bus.js';

export class SpatializerBusAdapter {
    constructor(spatializer) {
        this.spatializer = spatializer;

        // 1. Ingest routed transport appliance streams into grid positions
        precogBus.subscribe("transport.packet.routed", (packet) => {
            this.spatializer.ingestTransportSignature(packet.signature);
        });

        // 2. Adjust node radiance maps dynamically as reality drift increases
        precogBus.subscribe("precog.drift.detected", (event) => {
            this.spatializer.applyDriftGlow(event.channelId, event.driftScore);
        });

        // 3. Anchor speculative nodes onto the canvas when timelines split
        precogBus.subscribe("precog.fork.created", (event) => {
            this.spatializer.spawnForkNodes(event.forkId, event.spawned);
        });

        // 4. Collapse branching nodes down to a single location when states merge
        precogBus.subscribe("precog.merge.completed", (event) => {
            this.spatializer.mergeForkNodes(
                event.forkId,
                event.mergedChannelId,
                event.winningState
            );
        });
    }

    /**
     * Broadcast node hover signals from the canvas thread out to the broker
     */
    emitHover(node) {
        precogBus.publish("spatial.node.hovered", {
            nodeId: node.id,
            x: node.x,
            y: node.y,
            level: node.level,
            ts: Date.now()
        });
    }

    /**
     * Broadcast node activation events when an operator clicks an asset
     */
    emitClick(node) {
        precogBus.publish("spatial.node.clicked", {
            nodeId: node.id,
            x: node.x,
            y: node.y,
            targetZoom: node.targetZoom,
            ts: Date.now()
        });
    }
}

