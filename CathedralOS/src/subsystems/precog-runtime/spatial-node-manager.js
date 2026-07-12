// src/subsystems/precog-runtime/spatial-node-manager.js
// CathedralOS Native Module – Fractal Memory Spatial Bridge (Phase 3A: CommonJS Temporal Replay)

class SpatialNodeManager {
  constructor() {
    this.nodes = new Map();
    this.edges = [];
    this.timeline = { minSequence: 0, maxSequence: 0 };
  }

  loadTopology(nodesArray = [], edgesArray = []) {
    this.nodes.clear();
    this.edges = [];

    let minSeq = Infinity;
    let maxSeq = -Infinity;

    // Load canonical nodes with integrated temporal sequence tracking
    nodesArray.forEach((node, index) => {
      if (!node.id) return;

      // Fallback to array iteration sequence if not explicitly provided
      const sequence = node.sequence !== undefined ? Number(node.sequence) : (index + 1);
      if (sequence < minSeq) minSeq = sequence;
      if (sequence > maxSeq) maxSeq = sequence;

      this.nodes.set(node.id, {
        id: node.id,
        x: node.x || 0,
        y: node.y || 0,
        label: node.label || 'Telemetry Node',
        role: node.role || 'System',
        radius: node.radius || 8,
        sequence: sequence,
        createdAt: node.createdAt || `seq:${sequence}`,
        sourceType: node.sourceType || 'message',
        metadata: {
          level: node.metadata?.level || 1,
          parentId: node.metadata?.parentId || null,
          payload: node.metadata?.payload || 'Baseline Log'
        }
      });
    });

    // Load graph structural relationships mapped chronologically
    edgesArray.forEach(edge => {
      if (this.nodes.has(edge.source) && this.nodes.has(edge.target)) {
        const sourceNode = this.nodes.get(edge.source);
        const targetNode = this.nodes.get(edge.target);

        // Edge inherits the latest structural sequence number between its target endpoints if undefined
        const edgeSeq = edge.sequence !== undefined 
          ? Number(edge.sequence) 
          : Math.max(sourceNode.sequence, targetNode.sequence);

        if (edgeSeq < minSeq) minSeq = edgeSeq;
        if (edgeSeq > maxSeq) maxSeq = edgeSeq;

        this.edges.push({
          source: edge.source,
          target: edge.target,
          type: edge.type || 'structural',
          sequence: edgeSeq,
          createdAt: edge.createdAt || `seq:${edgeSeq}`
        });
      }
    });

    this.timeline = {
      minSequence: minSeq === Infinity ? 0 : minSeq,
      maxSequence: maxSeq === -Infinity ? 0 : maxSeq
    };
  }

  getTimelineBounds() {
    return { ...this.timeline };
  }

  // Phase 1 / 2 Core Selectors
  getVisibleNodes(cameraState) {
    return Array.from(this.nodes.values());
  }

  getVisibleEdges() {
    return this.edges;
  }

  // Phase 3 Time-Slicing Window Selectors
  getVisibleNodesAtTime(cameraState, cursor) {
    const allNodes = this.getVisibleNodes(cameraState);
    if (cursor === null) return allNodes;
    return allNodes.filter(n => n.sequence <= cursor);
  }

  getVisibleEdgesAtTime(cameraState, cursor) {
    if (cursor === null) return this.getVisibleEdges();

    return this.edges
      .filter(edge => edge.sequence <= cursor)
      .map(edge => ({
        sourceNode: this.nodes.get(edge.source),
        targetNode: this.nodes.get(edge.target),
        type: edge.type
      }))
      .filter(e => e.sourceNode && e.sourceNode.sequence <= cursor && e.targetNode && e.targetNode.sequence <= cursor);
  }

  hitTest(worldX, worldY, currentZoom, options = {}) {
    const { playbackCursor = null, replayMode = false } = options;

    const visible = replayMode
      ? this.getVisibleNodesAtTime(currentZoom, playbackCursor)
      : this.getVisibleNodes(currentZoom);

    // Unpack the scalar zoom level safely whether an object or primitive is passed
    const z = typeof currentZoom === 'object' && currentZoom !== null ? currentZoom.z : currentZoom;

    for (const node of visible) {
      const dx = node.x - worldX;
      const dy = node.y - worldY;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const hitTolerance = node.radius + (2 / z);

      if (distance <= hitTolerance) {
        return node;
      }
    }
    return null;
  }
}

module.exports = SpatialNodeManager;

