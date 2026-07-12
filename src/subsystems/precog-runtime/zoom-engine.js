// src/subsystems/precog-runtime/zoom-engine.js
// CathedralOS Native Module — Camera / Semantic Zoom / Node Render Engine

const Z_THRESHOLD_MACRO = 3.0;
const Z_THRESHOLD_MESSAGE = 7.0;

class ZoomEngine {
  constructor(canvas, fabricCanvasSetupInstance, spatialNodeManager = null) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // Rendering substrate / infinite grid provider
    this.fabricCanvas = fabricCanvasSetupInstance || null;

    // Hierarchical node bridge (SpatialNodeManager)
    this.nodeManager = spatialNodeManager || null;

    // Camera state (Live Simulation Owned)
    this.currentState = { x: 0, y: 0, z: 4.0 };
    this.targetState = { x: 0, y: 0, z: 4.0 };

    // ISOLATED: Replay state layers to prevent simulation plane corruption
    this.replayFrame = null;
    this.replayMode = false;

    // Animation tuning
    this.lerpFactor = 0.08;
    this.isAnimating = false;
  }

  /**
   * Optional late binding if the node manager is created after the engine
   */
  attachNodeManager(nodeManager) {
    this.nodeManager = nodeManager;
  }

  /**
   * Semantic zoom / LOD resolver
   */
  getLevelOfDetail(currentZ) {
    if (currentZ < Z_THRESHOLD_MACRO) {
      return 'macro_summary';
    }

    if (currentZ < Z_THRESHOLD_MESSAGE) {
      return 'thematic_cluster';
    }

    return 'raw_message';
  }

  /**
   * Camera fly-to target setter
   */
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

  /**
   * Main camera interpolation loop
   */
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

    // Position interpolation
    this.currentState.x += dx * this.lerpFactor;
    this.currentState.y += dy * this.lerpFactor;

    // Exponential zoom interpolation
    this.currentState.z *= Math.pow(zRatio, this.lerpFactor);

    this.render();
    requestAnimationFrame(() => this.update());
  }

  /**
   * FIXED: State Layering Hook
   * Isolates the playback snapshot instead of mutating runtime truth mid-frame
   */
  setReplayFrame(frame) {
    this.replayFrame = frame;
    if (frame && (frame.camera || frame.nodes)) {
      this.replayMode = true;
    } else {
      this.replayMode = false;
    }
    this.render();
  }

  /**
   * Restores regular simulation perspective rendering
   */
  clearReplayMode() {
    this.replayMode = false;
    this.replayFrame = null;
    this.render();
  }

  /**
   * Full render pass
   */
  render() {
    const ctx = this.ctx;

    // FIXED: Select render state source non-destructively
    const renderCamera = (this.replayMode && this.replayFrame?.camera)
      ? this.replayFrame.camera
      : this.currentState;

    const { x, y, z } = renderCamera;

    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.save();

    // 1) Move origin to canvas center
    ctx.translate(this.canvas.width / 2, this.canvas.height / 2);

    // 2) Apply zoom
    ctx.scale(z, z);

    // 3) Apply camera translation in world space
    ctx.translate(-x, -y);

    const currentLOD = this.getLevelOfDetail(z);

    // Draw substrate grid beneath nodes
    if (this.fabricCanvas) {
      this.fabricCanvas.drawInfiniteGrid(renderCamera);
    }

    // FIXED: Render spatial nodes from the isolated replay history or live context
    let visibleNodes = [];
    if (this.replayMode && this.replayFrame?.nodes) {
      visibleNodes = this.replayFrame.nodes;
    } else if (this.nodeManager) {
      visibleNodes = this.nodeManager.getVisibleNodes(z);
    }

    for (const node of visibleNodes) {
      this.drawNode(node, currentLOD, renderCamera);
    }

    ctx.restore();
  }

  /**
   * Node renderer for each semantic zoom layer
   */
  drawNode(node, lod, renderCamera) {
    if (lod === 'macro_summary' && node.level === 0) {
      this.drawMacroNode(node, renderCamera.z);
      return;
    }

    if (lod === 'thematic_cluster' && node.level <= 1) {
      this.drawThemeNode(node, renderCamera.z);
      return;
    }

    if (lod === 'raw_message') {
      this.drawMessageNode(node, renderCamera.z);
    }
  }

  /**
   * Level 0: session / continent layer
   */
  drawMacroNode(node, currentZ) {
    const ctx = this.ctx;
    const width = node.width || 160;
    const height = node.height || 56;
    const radius = 18;

    ctx.fillStyle = 'rgba(22, 119, 255, 0.22)';
    ctx.strokeStyle = '#1677ff';
    ctx.lineWidth = 2 / currentZ;

    this.drawRoundedRect(
      node.x - width / 2,
      node.y - height / 2,
      width,
      height,
      radius
    );

    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = `${14 / currentZ}px sans-serif`;
    ctx.textBaseline = 'middle';

    const label = this.truncateText(node.text || 'Macro Core', 36);
    ctx.fillText(label, node.x - width / 2 + 12, node.y);
  }

  /**
   * Level 1: theme / region layer
   */
  drawThemeNode(node, currentZ) {
    const ctx = this.ctx;
    const width = node.width || 120;
    const height = node.height || 48;
    const radius = 14;

    ctx.fillStyle = 'rgba(43, 135, 255, 0.32)';
    ctx.strokeStyle = '#8db7ff';
    ctx.lineWidth = 1.5 / currentZ;

    this.drawRoundedRect(
      node.x - width / 2,
      node.y - height / 2,
      width,
      height,
      radius
    );

    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = `${11 / currentZ}px sans-serif`;
    ctx.textBaseline = 'middle';

    const label = this.truncateText(node.text || 'Thematic Cluster', 42);
    ctx.fillText(label, node.x - width / 2 + 8, node.y);
  }

  /**
   * Level 2+: raw message / street layer
   */
  drawMessageNode(node, currentZ) {
    const ctx = this.ctx;
    const width = node.width || 180;
    const height = node.height || 36;
    const radius = 10;

    ctx.fillStyle = '#2c2c2c';
    ctx.strokeStyle = '#666666';
    ctx.lineWidth = 1 / currentZ;

    this.drawRoundedRect(
      node.x - width / 2,
      node.y - height / 2,
      width,
      height,
      radius
    );

    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = `${9 / currentZ}px monospace`;
    ctx.textBaseline = 'middle';

    const label = this.truncateText(node.text || 'Message Node', 60);
    ctx.fillText(label, node.x - width / 2 + 6, node.y);
  }

  /**
   * Rounded rectangle helper with canvas fallback safety
   */
  drawRoundedRect(x, y, width, height, radius) {
    const ctx = this.ctx;

    if (typeof ctx.roundRect === 'function') {
      ctx.beginPath();
      ctx.roundRect(x, y, width, height, radius);
      return;
    }

    const r = Math.min(radius, width / 2, height / 2);

    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
  }


  
 /**
   * Prevent labels from blowing out node bounds
   */
truncateText(text, maxLength) {
  if (typeof text !== 'string') {
    return '';
  }

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.slice(0, maxLength - 3)}...`;
}

} // <-- closes class ZoomEngine

module.exports = ZoomEngine;
