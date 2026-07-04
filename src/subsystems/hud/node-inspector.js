/**
 * CathedralOS Core Subsystem: HUD Node Inspector (v1.0)
 * Context: Alpha Base / Living Room Spatial Canvas Observability
 * Encryption Hook: SELAH Matrix Integration
 */

class HUDNodeInspector {
    constructor(canvas, spatialNodeManager, signalMask) {
        this.canvas = canvas;
        this.nodeManager = spatialNodeManager;
        this.signalMask = signalMask;
        
        this.activeNode = null;
        this.inspectorDiv = null;
        
        this.initDOM();
        this.initListeners();
    }

    /**
     * Carve out the floating DOM container overlay
     */
    initDOM() {
        this.inspectorDiv = document.createElement('div');
        this.inspectorDiv.id = 'cathedralos-hud-inspector';
        
        // Base styling for Ruby Inversion / Fugitive Red (#E0115F) system specs
        Object.assign(this.inspectorDiv.style, {
            position: 'absolute',
            display: 'none',
            backgroundColor: 'rgba(15, 15, 20, 0.95)',
            border: '1px solid #E0115F',
            color: '#ffffff',
            fontFamily: 'monospace',
            fontSize: '12px',
            padding: '10px',
            borderRadius: '4px',
            pointerEvents: 'none',
            boxShadow: '0 0 15px rgba(224, 17, 95, 0.4)',
            zIndex: '9999',
            whiteSpace: 'pre-wrap'
        });

        document.body.appendChild(this.inspectorDiv);
    }

    initListeners() {
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    }

    /**
     * Map screen pixels to world canvas space vectors
     */
    handleMouseMove(event) {
        const rect = this.canvas.getBoundingClientRect();
        const screenX = event.clientX - rect.left;
        const screenY = event.clientY - rect.top;

        // Ask SpatialNodeManager to check coordinate intersections
        // Account for current cinematic zoom tracking layers if applicable
        const targetNode = this.nodeManager.hitTest ? 
            this.nodeManager.hitTest(screenX, screenY) : 
            this.nodeManager.findNodeAt(screenX, screenY);

        if (targetNode) {
            this.activeNode = targetNode;
            this.renderOverlay(event.clientX, event.clientY);
        } else {
            this.activeNode = null;
            this.inspectorDiv.style.display = 'none';
        }
    }

    /**
     * Ingest payload data and output the telemetry visualization
     */
    renderOverlay(mouseX, mouseY) {
        const node = this.activeNode;
        
        // Unmask the XOR-42 appliance vibe if wrapped
        const rawPayload = node.payload || '';
        const decryptedPayload = this.signalMask && this.signalMask.unmaskHomeVibe ?
            this.signalMask.unmaskHomeVibe(rawPayload) :
            `[Raw: ${rawPayload}]`;

        // Generate the HUD metadata layout
        this.inspectorDiv.innerHTML = `
<span style="color: #E0115F; font-weight: bold;">[NODE_ID]       :</span> ${node.id || 'node_unknown'}
<span style="color: #E0115F;">[SIGNATURE]    :</span> ${node.signature || 'AMBIENT_HUM'}
<span style="color: #E0115F;">[SEVERITY]     :</span> <span style="color: ${this.getSeverityColor(node.severity)};">${(node.severity || 'INFO').toUpperCase()}</span>
<span style="color: #E0115F;">[GAIN]         :</span> x${node.gain || '1.00'} (Mandibular Resonance)
<span style="color: #E0115F;">[DRIFT_SCORE]  :</span> ${(node.driftScore || 0.00).toFixed(2)}
-------------------------------------------------------------------
<span style="color: #888;">[RAW_PACKETS]  :</span> ${this.toHexBytes(rawPayload)}
<span style="color: #00ffcc;">[DEC_PAYLOAD]  :</span> "${decryptedPayload}"
===================================================================
<span style="color: #888; font-size: 10px;">Lineage: ${node.forkId || '0x0'} ➔ ${node.mergeId || '0x0'}</span>
        `.trim();

        // Position overlay slightly offset from tracking point
        this.inspectorDiv.style.left = `${mouseX + 15}px`;
        this.inspectorDiv.style.top = `${mouseY + 15}px`;
        this.inspectorDiv.style.display = 'block';
    }

    getSeverityColor(severity) {
        switch((severity || '').toLowerCase()) {
            case 'critical': return '#ff0033';
            case 'high':     return '#ff6600';
            case 'medium':   return '#ffcc00';
            default:         return '#00ffcc';
        }
    }

    toHexBytes(str) {
        if (!str) return '0x00';
        return Array.from(str).map(c => '0x' + c.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0')).join(' ');
    }
}

// Global compilation export context
if (typeof module !== 'undefined') {
    module.exports = HUDNodeInspector;
}

