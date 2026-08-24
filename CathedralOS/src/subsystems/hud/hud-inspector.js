/**
 * CathedralOS Core Subsystem: HudInspector (v3.0)
 * Context: Alpha Base / Viewport Diagnostics Glass Overlay
 * Design Protocol: Lineage highlight traversals and visual mode switching states
 */

import { DomesticSignalMask } from '../transport/domestic-signal-mask.js';

export class HudInspector {
    constructor() {
        this.masker = new DomesticSignalMask(null, { mandibularPlating: true });
        this.hoverPanel = document.getElementById("hud-hover-panel");
        this.inspectPanel = document.getElementById("hud-inspect-panel");
    }

    /**
     * Triggered via HudBusAdapter when a spatial.node.hovered event is published.
     */
    showNodePreview(nodeId) {
        if (!window.CATHEDRAL_SPATIALIZER || typeof window.CATHEDRAL_SPATIALIZER.getNode !== 'function') {
            return;
        }

        const node = window.CATHEDRAL_SPATIALIZER.getNode(nodeId);
        if (!node) return;

        const masked = node.raw?.payload;
        let decrypted = null;

        if (masked) {
            decrypted = this.masker.decryptWithHomeVibe(masked);
        }

        this.renderHoverPanel({
            id: nodeId,
            signature: node.raw?.signature,
            maskedPayload: masked,
            decryptedPayload: decrypted,
            severity: node.raw?.severity,
            level: node.level
        });
    }

    /**
     * Formats binary hex streams and writes structural elements into the HTML string
     */
    renderHoverPanel(data) {
        if (!this.hoverPanel) return;

        const maskedHex = data.maskedPayload
            ? Array.from(data.maskedPayload).map(b => b.toString(16).padStart(2, "0")).join(" ")
            : "—";

        const decryptedText = data.decryptedPayload
            ? new TextDecoder().decode(data.decryptedPayload)
            : "—";

        this.hoverPanel.innerHTML = `
            <div class="hud-hover-title" style="font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 4px; margin-bottom: 6px;">Node Asset: ${data.id}</div>
            <div><strong>Signature:</strong> <span style="color: #8be9fd;">${data.signature || "UNKNOWN"}</span></div>
            <div><strong>Severity:</strong> <span style="color: #ff5555;">${data.severity || "info"}</span></div>
            <div><strong>Level Depth:</strong> ${data.level}</div>
            <div style="margin-top: 6px; font-size: 10px; color: #aaa; word-break: break-all;"><strong>Masked Hex:</strong> ${maskedHex}</div>
            <div style="margin-top: 4px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 4px; color: #50fa7b;"><strong>Decrypted Output:</strong> ${decryptedText}</div>
        `;
    }

    /**
     * Traverses upward through the lineage registry to isolate parent ancestors
     */
    highlightAncestry(nodeId) {
        if (!window.CATHEDRAL_SPATIALIZER || !window.CATHEDRAL_SPATIALIZER.ancestry) return;

        const chain = [];
        let current = nodeId;

        while (current) {
            const entry = window.CATHEDRAL_SPATIALIZER.ancestry.get(current);
            if (!entry || !entry.parentId) break;
            chain.push(entry.parentId);
            current = entry.parentId; // Step up one generation link
        }

        // Send down the structural set to the spatializer matrix
        window.CATHEDRAL_SPATIALIZER.highlightChain(chain);
    }

    inspectNode(nodeId) {
        console.log(`[HudInspector] Inspecting node link line: ${nodeId}`);
    }

    /**
     * Switches viewport context boundaries visually into a dedicated purple matrix
     */
    enterReplayMode() {
        document.body.classList.add("replay-mode");
    }

    /**
     * Restores screen styles to normal operational parameters
     */
    exitReplayMode() {
        document.body.classList.remove("replay-mode");
    }
}

