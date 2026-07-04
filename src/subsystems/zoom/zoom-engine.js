/**
 * CathedralOS Core Subsystem: ZoomEngine Renderer (v3.0)
 * Context: Alpha Base Infinite Canvas Viewport Axis
 * Design Protocol: Structural vector pipelines with integrated lineage vector traces
 */

export class ZoomEngine {
    constructor(canvas, fabricSetup, spatializer) {
        this.canvas = canvas;
        this.ctx = canvas.getContext("2d");
        this.fabric = fabricSetup;
        this.spatializer = spatializer;

        this.currentState = {
            x: 0,
            y: 0,
            z: 1.0, 
            globalDriftGlow: 0.0
        };
    }

    /**
     * Refreshes the underlying canvas buffer through hierarchical draw passes
     */
    render() {
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        ctx.save();
        ctx.translate(this.canvas.width / 2, this.canvas.height / 2);
        ctx.scale(this.currentState.z, this.currentState.z);
        ctx.translate(-this.currentState.x, -this.currentState.y);

        // 1. Grid matrix structural layout pass
        this.drawBackgroundGrid();

        // 2. Base quadrant activation tracking map
        this.renderQuadrantGlows();

        // 3. Structural Node Lineage & Ancestry Pass (drawn behind nodes)
        this.renderAncestryLines();

        // 4. Temporal timeline anomaly auroras
        this.renderTemporalHalos();

        // 5. Hard physical node entities
        this.renderNodes();

        ctx.restore();
    }

    /**
     * Traverses node connectivity trees to render genealogical vector maps
     */
    renderAncestryLines() {
        if (!this.spatializer || !this.spatializer.ancestry) return;

        const ctx = this.ctx;

        for (const [nodeId, entry] of this.spatializer.ancestry.entries()) {
            const intensity = this.spatializer.getAncestryLineIntensity(nodeId);
            if (intensity <= 0) continue;

            const child = this.spatializer.getNode(nodeId);
            const parent = this.spatializer.getNode(entry.parentId);
            if (!child || !parent) continue;

            ctx.save();
            const alpha = intensity * 0.55;
            
            // Scaled stroke weight matches zoom configuration ratio
            let width = 2.5 / this.currentState.z;
            let color = `rgba(180, 180, 255, ${alpha})`; // Baseline parent-child tie

            // Adjust parameters based on fork branching or convergence status
            if (entry.forkId) color = `rgba(120, 180, 255, ${alpha})`;
            if (entry.mergeId) color = `rgba(255, 255, 255, ${alpha})`;

            // Override color matrix if this segment resides inside the inspected golden path
            if (this.spatializer.highlightedChain && this.spatializer.highlightedChain.has(entry.parentId)) {
                color = `rgba(255, 200, 80, ${intensity * 0.85})`;
                width = 4.0 / this.currentState.z;
            }

            ctx.beginPath();
            ctx.moveTo(parent.x, parent.y);
            ctx.lineTo(child.x, child.y);

            ctx.strokeStyle = color;
            ctx.lineWidth = width;

            const blurPx = Math.max(1, 6 / this.currentState.z);
            ctx.filter = `blur(${blurPx}px)`;
            ctx.stroke();
            ctx.restore();
        }
    }

    renderQuadrantGlows() {
        const q = this.spatializer.activeQuadrant;
        if (!q) return;

        const ctx = this.ctx;
        ctx.save();
        ctx.fillStyle = "rgba(120, 200, 255, 0.12)";

        const w = this.canvas.width / this.currentState.z;
        const h = this.canvas.height / this.currentState.z;

        if (q === "Q1") ctx.fillRect(this.currentState.x - w, this.currentState.y - h, w, h);
        if (q === "Q2") ctx.fillRect(this.currentState.x, this.currentState.y - h, w, h);
        if (q === "Q3") ctx.fillRect(this.currentState.x - w, this.currentState.y, w, h);
        if (q === "Q4") ctx.fillRect(this.currentState.x, this.currentState.y, w, h);

        ctx.restore();
    }

    renderTemporalHalos() {
        const ctx = this.ctx;

        // FORK HALOS (Speculative Branches)
        for (const [forkId, halo] of this.spatializer.forkHalos.entries()) {
            const intensity = this.spatializer.getForkHaloIntensity(forkId);
            if (intensity <= 0) continue;

            for (const nodeId of halo.nodes) {
                const node = this.spatializer.getNode(nodeId);
                if (!node) continue;

                ctx.save();
                const radius = Math.max(node.width || 40, node.height || 40) * 1.1;
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(120, 180, 255, ${intensity * 0.45})`;
                ctx.lineWidth = 4 / this.currentState.z;
                ctx.filter = `blur(${Math.max(1, 10 / this.currentState.z)}px)`;
                ctx.stroke();
                ctx.restore();
            }
        }

        // MERGE COLLAPSE HALOS (Consensus Stabilization Flashes)
        for (const [forkId, halo] of this.spatializer.mergeHalos.entries()) {
            const intensity = this.spatializer.getMergeHaloIntensity(forkId);
            if (intensity <= 0) continue;

            const node = this.spatializer.getNode(halo.nodeId);
            if (!node) continue;

            ctx.save();
            const radius = Math.max(node.width || 40, node.height || 40) * (1.2 - intensity * 0.4);
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(255, 255, 255, ${intensity * 0.6})`;
            ctx.filter = `blur(${Math.max(1, 14 / this.currentState.z)}px)`;
            ctx.fill();
            ctx.restore();
        }
    }

    renderNodes() {
        for (const node of this.spatializer.nodes) {
            this.drawNodeGlow(node);
            this.drawNodeCore(node);
        }
    }

    drawNodeGlow(node) {
        const glow = this.spatializer.getDriftGlow(node);
        const ctx = this.ctx;

        if (glow > 0) {
            const radius = Math.max(node.width || 40, node.height || 40) * 0.9;
            ctx.save();
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);

            let color = `rgba(120, 255, 120, ${glow * 0.65})`;
            if (glow > 0.20) color = `rgba(255, 220, 60, ${glow * 0.65})`;
            if (glow > 0.45) color = `rgba(255, 160, 60, ${glow * 0.65})`;
            if (glow > 0.75) color = `rgba(255, 60, 60, ${glow * 0.65})`;

            ctx.fillStyle = color;
            ctx.filter = `blur(${Math.max(1, 12 / this.currentState.z)}px)`;
            ctx.fill();
            ctx.restore();
        }

        if (node.raw?.forkId && this.spatializer.forkHalos.has(node.raw.forkId)) {
            ctx.save();
            const radius = Math.max(node.width || 40, node.height || 40) * 0.75;
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
            ctx.strokeStyle = "rgba(255, 200, 80, 0.65)";
            ctx.lineWidth = 3 / this.currentState.z;
            ctx.filter = `blur(${Math.max(1, 6 / this.currentState.z)}px)`;
            ctx.stroke();
            ctx.restore();
        }
    }

    drawNodeCore(node) {
        const ctx = this.ctx;
        ctx.save();
        ctx.fillStyle = "#282a36";
        ctx.strokeStyle = "#6272a4";
        ctx.lineWidth = 2;

        const w = node.width || 40;
        const h = node.height || 40;
        ctx.fillRect(node.x - w / 2, node.y - h / 2, w, h);
        ctx.strokeRect(node.x - w / 2, node.y - h / 2, w, h);
        ctx.restore();
    }

    drawBackgroundGrid() {
        if (this.fabric && typeof this.fabric.drawInfiniteGrid === 'function') {
            this.fabric.drawInfiniteGrid(this.currentState);
        }
    }

    update() {
        if (this.spatializer.nodes.length > 0) {
            this.currentState.globalDriftGlow = Math.max(
                ...this.spatializer.nodes.map(n => this.spatializer.getDriftGlow(n))
            );
        }
        this.render();
    }

    flyTo(targetX, targetY, targetZoom) {
        this.currentState.x = targetX;
        this.currentState.y = targetY;
        this.currentState.z = targetZoom;
        this.render();
    }
}

