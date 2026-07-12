// src/subsystems/precog-runtime/zoom-engine.js
// CathedralOS Native Module — Camera / Semantic Zoom / 2D Canvas Render Engine (Phase 3B: CommonJS Replay)

const Z_THRESHOLD_MACRO = 3.0;
const Z_THRESHOLD_MESSAGE = 7.0;

class ZoomEngine {
  constructor(canvas, canvasViewportControllerInstance, spatialNodeManager = null) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    this.viewport = canvasViewportControllerInstance || null;
    this.nodeManager = spatialNodeManager || null;

    this.currentState = { x: 0, y: 0, z: 4.0 };
    this.targetState = { x: 0, y: 0, z: 4.0 };

    this.lerpFactor = 0.08;
    this.isAnimating = false;

    this.selectedNodeId = null;

    // Phase 3B Temporal Replay State Properties
    this.replayMode = false;
    this.playbackCursor = null;
    this.playbackBounds = { minSequence: 0, maxSequence: 0 };
  }

  attachNodeManager(nodeManager) {
    this.nodeManager = nodeManager;
  }

  setSelectedNode(node) {
    this.selectedNodeId = node?.id || null;
    this.render();
  }

  // Phase 3B Replay Control Hooks called by Orchestrator
  setReplayMode(enabled) {
    this.replayMode = Boolean(enabled);
    this.render();
  }

  setPlaybackCursor(cursor) {
    this.playbackCursor = cursor != null ? Number(cursor) : null;
    this.render();
  }

  setPlaybackBounds(bounds = {}) {
    this.playbackBounds = {
      minSequence: Number(bounds.minSequence ?? 0),
      maxSequence: Number(bounds.maxSequence ?? 0)
    };
  }

  getLevelOfDetail(currentZ) {
    if (currentZ < Z_THRESHOLD_MACRO) return 'macro_summary';
    if (currentZ < Z_THRESHOLD_MESSAGE) return 'thematic_cluster';
    return 'raw_message';
  }

  flyTo(targetX, targetY, targetZ = this.targetState.z) {
    this.targetState = {
      x: targetX,
      y: targetY,
      z: Math.max(0.5, Math.min(25.0, targetZ))
    };

    if (!this.isAnimating) {
      this.isAnimating = true;
      this.update();
    }
  }

  focusNode(node) {
    if (!node) return;
    this.flyTo(node.x, node.y, node.targetZoom || this.targetState.z);
  }

  panBy(dx, dy) {
    this.currentState.x -= dx / this.currentState.z;
    this.currentState.y -= dy / this.currentState.z;
    this.targetState.x = this.currentState.x;
    this.targetState.y = this.currentState.y;
    this.render();
  }

  zoomAt(pointerX, pointerY, zoomFactor) {
    const prevZ = this.currentState.z;
    const nextZ = Math.max(0.5, Math.min(25.0, prevZ * zoomFactor));

    const worldBefore = this.screenToWorld(pointerX, pointerY, prevZ);

    this.currentState.z = nextZ;
    this.targetState.z = nextZ;

    const worldAfter = this.screenToWorld(pointerX, pointerY, nextZ);

    this.currentState.x += worldBefore.x - worldAfter.x;
    this.currentState.y += worldBefore.y - worldAfter.y;
    this.targetState.x = this.currentState.x;
    this.targetState.y = this.currentState.y;

    this.render();
  }

  screenToWorld(screenX, screenY, zOverride = null) {
    const z = zOverride ?? this.currentState.z;
    return {
      x: this.currentState.x + (screenX - this.canvas.width / 2) / z,
      y: this.currentState.y + (screenY - this.canvas.height / 2) / z
    };
  }

  update() {
    const dx = this.targetState.x - this.currentState.x;
    const dy = this.targetState.y - this.currentState.y;
    const zRatio = this.targetState.z / this.currentState.z;

    const closeEnough =
      Math.abs(dx) < 0.01 &&
      Math.abs(dy) < 0.01 &&
      Math.abs(zRatio - 1) < 0.001;

    if (closeEnough) {
      this.currentState = { ...this.targetState };
      this.isAnimating = false;
      this.render();
      return;
    }

    this.currentState.x += dx * this.lerpFactor;
    this.currentState.y += dy * this.lerpFactor;
    this.currentState.z *= Math.pow(zRatio, this.lerpFactor);

    this.render();
    requestAnimationFrame(() => this.update());
  }

  /**
   * Phase 3B Polymorphic Render Path
   */
  render() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.save();

    // Establish transformation camera space matrix
    ctx.translate(this.canvas.width / 2, this.canvas.height / 2);
    ctx.scale(this.currentState.z, this.currentState.z);
    ctx.translate(-this.currentState.x, -this.currentState.y);

    if (this.viewport && typeof this.viewport.drawInfiniteGrid === 'function') {
      this.viewport.drawInfiniteGrid(this.currentState);
    }

    const currentLOD = this.getLevelOfDetail(this.currentState.z);

    let visibleNodes = [];
    let visibleEdges = [];

    // Route graph filters based on the active orchestrator mode
    if (this.nodeManager) {
      visibleNodes = this.replayMode
        ? this.nodeManager.getVisibleNodesAtTime(this.currentState, this.playbackCursor)
        : this.nodeManager.getVisibleNodes(this.currentState);

      visibleEdges = this.replayMode
        ? this.nodeManager.getVisibleEdgesAtTime(this.currentState, this.playbackCursor)
        : this.nodeManager.getVisibleEdges(this.currentState);
    }

    // Pass 1: Render background relationship channels first
    this.renderEdges(visibleEdges, {
      replayMode: this.replayMode,
      playbackCursor: this.playbackCursor
    });

    // Pass 2: Overlay semantic node bounds on top
    this.renderNodes(visibleNodes, currentLOD, {
      replayMode: this.replayMode,
      playbackCursor: this.playbackCursor
    });

    ctx.restore();
  }

  renderEdges(edges = [], { replayMode = false, playbackCursor = null } = {}) {
    const ctx = this.ctx;
    const cz = this.currentState.z;

    for (const edge of edges) {
      const fromNode = edge.sourceNode;
      const toNode = edge.targetNode;
      if (!fromNode || !toNode) continue;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(fromNode.x, fromNode.y);
      ctx.lineTo(toNode.x, toNode.y);

      // Distinguish structural vs secondary paths
      if (edge.type === 'structural' || edge.type === 'parent') {
        ctx.strokeStyle = 'rgba(120, 180, 255, 0.35)';
        ctx.lineWidth = 2 / cz;
      } else {
        ctx.strokeStyle = 'rgba(180, 180, 180, 0.20)';
        ctx.lineWidth = 1 / cz;
      }

      // Pulse edge if it exactly matches the historic replay slice
      if (replayMode && playbackCursor != null && edge.sequence === playbackCursor) {
        ctx.strokeStyle = 'rgba(255, 214, 102, 0.85)';
        ctx.lineWidth = 2.5 / cz;
      }

      ctx.stroke();
      ctx.restore();
    }
  }

  renderNodes(nodes = [], lod, { replayMode = false, playbackCursor = null } = {}) {
    for (const node of nodes) {
      const isSelected = node.id === this.selectedNodeId;
      const isNewestAtCursor =
        replayMode && playbackCursor != null && node.sequence === playbackCursor;

      // Extract details dependent on metadata levels
      const nodeLevel = node.metadata?.level ?? 1;

      if (lod === 'macro_summary' && nodeLevel === 0) {
        this.drawMacroNode(node, { isSelected, isNewestAtCursor });
      } else if (lod === 'thematic_cluster' && nodeLevel <= 1) {
        this.drawThemeNode(node, { isSelected, isNewestAtCursor });
      } else if (lod === 'raw_message') {
        this.drawMessageNode(node, { isSelected, isNewestAtCursor });
      }
    }
  }

  drawMacroNode(node, flags = {}) {
    this._drawNodeShell(node, {
      fill: 'rgba(22, 119, 255, 0.25)',
      stroke: '#1677ff',
      fontSize: 14,
      font: 'sans-serif',
      ...flags
    });
  }

  drawThemeNode(node, flags = {}) {
    this._drawNodeShell(node, {
      fill: 'rgba(43, 135, 255, 0.35)',
      stroke: '#8db7ff',
      fontSize: 11,
      font: 'sans-serif',
      ...flags
    });
  }

  drawMessageNode(node, flags = {}) {
    this._drawNodeShell(node, {
      fill: '#2c2c2c',
      stroke: '#666666',
      fontSize: 9,
      font: 'monospace',
      ...flags
    });
  }

  _drawNodeShell(node, config) {
    const ctx = this.ctx;
    const cz = this.currentState.z;
    const {
      fill,
      stroke,
      fontSize,
      font,
      isSelected = false,
      isNewestAtCursor = false
    } = config;

    // Dynamic scale width boundary box based on string footprint
    const labelText = node.label || '';
    const textPadding = font === 'monospace' ? 12 : 16;
    const estimatedWidth = Math.max(node.radius * 2.5, labelText.length * (fontSize * 0.55) + textPadding);
    const boxHeight = fontSize * 2.2;

    ctx.save();
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    ctx.fillStyle = fill;
    ctx.fill();

    ctx.strokeStyle = isSelected ? '#ffd666' : stroke;
    ctx.lineWidth = (isSelected ? 2.5 : 1.5) / cz;
    ctx.stroke();

    // Chronological glow halo for the trailing temporal frame node
    if (isNewestAtCursor) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius + (5 / cz), 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(255, 214, 102, 0.9)';
      ctx.lineWidth = 2 / cz;
      ctx.stroke();
    }

    // Text label drawing bounds
    ctx.fillStyle = '#ffffff';
    ctx.font = `${fontSize / cz}px ${font}`;
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillText(labelText, node.x, node.y + node.radius + (12 / cz));
    ctx.restore();
  }
}

module.exports = ZoomEngine;

