/**
 * CathedralOS Core Subsystem: Transport ➔ precogBus Adapter (v1.0)
 * Context: Alpha Base / Domestic Noise Isolation Ingress
 * Design Protocol: Decouples hardware packet signatures from canvas managers
 */

import { precogBus } from '../broker/precog-bus.js';
import { DomesticSignalMask } from './domestic-signal-mask.js';
import { ResidentialRouterSentinel } from './residential-router-sentinel.js';

export class TransportBusAdapter {
    constructor(rootStream, bioHardware) {
        // Initialize the isolation masker and downstream quadrant router
        this.masker = new DomesticSignalMask(rootStream, bioHardware);
        this.router = new ResidentialRouterSentinel();
    }

    /**
     * Accept incoming raw upstream streams, apply structural masking overlays,
     * map appliance signatures, and publish metrics directly to the message spine.
     */
    ingest(packet) {
        // 1. Wrap raw packet variables inside standard household appliance noise profiles
        const masked = this.masker.maskPacket(packet);

        precogBus.publish("transport.packet.masked", {
            ...masked,
            stage: "MASKED",
            ts: Date.now()
        });

        // 2. Map appliance identifiers onto spatial system grid coordinates
        const routed = this.router.route(masked);

        precogBus.publish("transport.packet.routed", {
            ...routed,
            stage: "ROUTED",
            ts: Date.now()
        });

        return routed;
    }
}

