/**
 * CathedralOS Core Subsystem: HUD Inspector ➔ precogBus Adapter (v1.0)
 * Context: Alpha Base Sensory Cortex & Real-Time Diagnostics
 * Design Protocol: Feeds all internal timelines and unmasked telemetry to the HUD overlay
 */

import { precogBus } from '../broker/precog-bus.js';

export class HudBusAdapter {
    constructor(hudInspector) {
        this.hud = hudInspector;

        // 1. Pipe masked packet streams into the inspector HUD viewport
        precogBus.subscribe("transport.packet.masked", (packet) => {
            this.hud.ingestMaskedPacket ? this.hud.ingestMaskedPacket(packet) : null;
        });

        // 2. Map routed appliance signatures directly to HUD telemetry rows
        precogBus.subscribe("transport.packet.routed", (packet) => {
            this.hud.ingestRoutedPacket ? this.hud.ingestRoutedPacket(packet) : null;
        });

        // 3. Output historical ledger text fragments directly to the console ticker
        precogBus.subscribe("precog.ledger.fragment", (fragment) => {
            this.hud.ingestLedgerFragment ? this.hud.ingestLedgerFragment(fragment) : null;
        });

        // 4. Update HUD delta indicators when variance drift is reported
        precogBus.subscribe("precog.drift.detected", (event) => {
            this.hud.ingestDriftEvent ? this.hud.ingestDriftEvent(event) : null;
        });

        // 5. Track timeline fork lineage and display speculative structural flags
        precogBus.subscribe("precog.fork.created", (event) => {
            this.hud.ingestForkEvent ? this.hud.ingestForkEvent(event) : null;
        });

        // 6. Clear speculative flags when timelines merge back to stability
        precogBus.subscribe("precog.merge.completed", (event) => {
            this.hud.ingestMergeEvent ? this.hud.ingestMergeEvent(event) : null;
        });

        // 7. Track mouseover triggers to update floating canvas node previews
        precogBus.subscribe("spatial.node.hovered", (event) => {
            this.hud.showNodePreview ? this.hud.showNodePreview(event.nodeId) : null;
        });

        // 8. Capture active canvas node selection to trigger deep diagnostic matrices
        precogBus.subscribe("spatial.node.clicked", (event) => {
            this.hud.inspectNode ? this.hud.inspectNode(event.nodeId) : null;
        });
    }

    /**
     * Broadcast a deep inspection request down the spine when an asset is queried
     */
    requestInspection(nodeId) {
        precogBus.publish("hud.node.inspect.requested", {
            nodeId,
            ts: Date.now()
        });
    }
}

