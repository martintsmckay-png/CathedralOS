/**
 * CathedralOS Core Subsystem: SpatialNodeManager (v3.0)
 * Context: Alpha Base / Spatial Quadrant Lineage Axis
 * Design Protocol: Structural coordinate registers with real-time geometric ancestry indexes
 */

export class SpatialNodeManager {
    constructor() {
        this.nodes = [];                   // Flat collection of rendering node instances
        this.nodeIndex = new Map();         // Fast lookup cache: nodeId -> node reference
        this.activeQuadrant = null;        // Highlighted visual boundary context
        this.highlightedChain = new Set(); // Gold tracking targets for HUD inspection
        
        // Temporal Topology Registries
        this.forkHalos = new Map();        // forkId -> { nodes: [nodeIds], intensity, ts }
        this.mergeHalos = new Map();       // forkId -> { nodeId, intensity, ts }
        this.ancestry = new Map();         // nodeId -> { parentId, forkId, mergeId, ts }
    }

    getNode(nodeId) {
        return this.nodeIndex.get(nodeId);
    }

    /**
     * Registers connection joints between parents, branches, and timeline merges
     */
    registerAncestry(nodeId, parentId, forkId = null, mergeId = null) {
        this.ancestry.set(nodeId, { 
            parentId, 
            forkId, 
            mergeId,
            ts: performance.now()
        });
    }

    /**
     * Calculates temporal decay for parent-child structural strings (4 seconds)
     */
    getAncestryLineIntensity(nodeId) {
        const entry = this.ancestry.get(nodeId);
        if (!entry) return 0;
        const elapsed = (performance.now() - entry.ts) / 4000;
        return Math.max(0, 1 - elapsed);
    }

    ingestTransportSignature(signature) {
        const quadrant = this.getQuadrantForSignature(signature);
        if (quadrant) {
            this.highlightQuadrant(quadrant.id);
        }
    }

    getQuadrantForSignature(signature) {
        if (window.CATHEDRAL_ROUTER && typeof window.CATHEDRAL_ROUTER.getQuadrantForSignature === 'function') {
            return window.CATHEDRAL_ROUTER.getQuadrantForSignature(signature);
        }
        switch (signature) {
            case "MICROWAVEHUM2_4GHZ": return { id: "Q1", x: -800, y: -600, zoom: 4.5 };
            case "SMARTFRIDGERECIPE_PING": return { id: "Q2", x: 800, y: -600, zoom: 4.5 };
            case "BABYMONITORSTATIC_LOOP": return { id: "Q3", x: -800, y: 600, zoom: 4.5 };
            case "LAUNDRYLOADBALANCER_VIBE": return { id: "Q4", x: 800, y: 600, zoom: 4.5 };
            default: return null;
        }
    }

    highlightQuadrant(quadrantId) {
        this.activeQuadrant = quadrantId;
    }

    highlightChain(chainArray) {
        this.highlightedChain = new Set(chainArray);
    }

    applyDriftGlow(channelId, driftScore) {
        const node = this.getNode(channelId);
        if (!node) return;
        node.driftGlow = {
            driftIntensity: Math.min(1, Math.max(0, driftScore)),
            lastUpdate: performance.now()
        };
    }

    getDriftGlow(node) {
        if (!node || !node.driftGlow) return 0;
        const elapsed = (performance.now() - node.driftGlow.lastUpdate) / 1000;
        return Math.max(0, node.driftGlow.driftIntensity - elapsed / 3);
    }

    spawnForkNodes(forkId, spawnedIds) {
        this.forkHalos.set(forkId, { nodes: spawnedIds, intensity: 1.0, ts: performance.now() });
    }

    mergeForkNodes(forkId, mergedId, winningState) {
        this.mergeHalos.set(forkId, { nodeId: mergedId, intensity: 1.0, ts: performance.now() });
        this.forkHalos.delete(forkId);
    }

    getForkHaloIntensity(forkId) {
        const halo = this.forkHalos.get(forkId);
        if (!halo) return 0;
        return Math.max(0, halo.intensity - (performance.now() - halo.ts) / 2000);
    }

    getMergeHaloIntensity(forkId) {
        const halo = this.mergeHalos.get(forkId);
        if (!halo) return 0;
        return Math.max(0, halo.intensity - (performance.now() - halo.ts) / 1500);
    }
}

