// src/subsystems/precog-runtime/canvas-viewport-controller.js
// CathedralOS Native Module — Viewport View Input & Coordinate Pointer Interaction Bridge (Phase 3C: Replay)

class CanvasViewportController {
  constructor(canvasElement, zoomEngineInstance) {
    if (!canvasElement || !zoomEngineInstance) {
      throw new Error("CanvasViewportController requires valid canvas and zoomEngine instances.");
    }

    this.canvas = canvasElement;
    this.zoomEngine = zoomEngineInstance;

    // Operational Tracking State
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.accumulatedDragDistance = 0;
    this.clickThreshold = 4; // Max pixels allowed to travel before transforming click into pan

    // Extensible Event Callbacks for Orchestrator Observation
    this.onNodeSelected = null;
    this.onReplayCursorChanged = null;

    this.initEventListeners();
  }

  initEventListeners() {
    // Mouse Wheel Zoom Capture
    this.canvas.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });

    // Pointer Drag / Click Lifecycle Orchestration
    this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
    this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    this.canvas.addEventListener('mouseleave', () => { this.isDragging = false; });
  }

  /**
   * Binds an external DOM slider element directly to the internal temporal engine playback timeline
   * @param {HTMLInputElement} sliderElement - Standard UI Input Range Control Type
   */
  bindReplaySlider(sliderElement) {
    if (!sliderElement) return;

    const syncHandler = () => {
      const cursor = Number(sliderElement.value);
      
      // Update the structural renderer state mapping bounds
      this.zoomEngine.setPlaybackCursor(cursor);

      // Notify the higher-level monitoring engine context
      if (typeof this.onReplayCursorChanged === 'function') {
        this.onReplayCursorChanged(cursor);
      }
    };

    sliderElement.addEventListener('input', syncHandler);
    sliderElement.addEventListener('change', syncHandler);
  }

  handleWheel(e) {
    e.preventDefault();
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Continuous dynamic zoom calculation
    const zoomFactor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
    this.zoomEngine.zoomAt(mouseX, mouseY, zoomFactor);
  }

  handleMouseDown(e) {
    if (e.button !== 0) return; // Restrict capture strictly to left clicks
    this.isDragging = true;
    this.dragStart = { x: e.clientX, y: e.clientY };
    this.accumulatedDragDistance = 0;
  }

  handleMouseMove(e) {
    if (!this.isDragging) return;

    const dx = e.clientX - this.dragStart.x;
    const dy = e.clientY - this.dragStart.y;
    
    this.accumulatedDragDistance += Math.sqrt(dx * dx + dy * dy);

    // Command ZoomEngine camera matrix offset translate shifts
    this.zoomEngine.panBy(dx, dy);

    // Shift vector base context frame
    this.dragStart = { x: e.clientX, y: e.clientY };
  }

  handleMouseUp(e) {
    if (!this.isDragging) return;
    this.isDragging = false;

    // Process evaluation: Is this gesture an intentional camera pan or a precise target click selection?
    if (this.accumulatedDragDistance <= this.clickThreshold) {
      this.processViewportClick(e);
    }
  }

  processViewportClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;

    // Convert client rendering system vectors straight into world space coordinates
    const worldCoords = this.zoomEngine.screenToWorld(screenX, screenY);

    if (!this.zoomEngine.nodeManager) return;

    // Replay-Aware Trace Testing Execution
    const hitNode = this.zoomEngine.nodeManager.hitTest(
      worldCoords.x,
      worldCoords.y,
      this.zoomEngine.currentState, // Passes current polymorphic state object seamlessly
      {
        replayMode: this.zoomEngine.replayMode,
        playbackCursor: this.zoomEngine.playbackCursor
      }
    );

    if (hitNode) {
      // Focus internal render selection maps
      this.zoomEngine.setSelectedNode(hitNode);
      this.zoomEngine.focusNode(hitNode);

      // Bubble up information structure notification to tracking interfaces
      if (typeof this.onNodeSelected === 'function') {
        this.onNodeSelected(hitNode);
      }
    } else {
      // Reset selected context if empty space is clicked
      this.zoomEngine.setSelectedNode(null);
      if (typeof this.onNodeSelected === 'function') {
        this.onNodeSelected(null);
      }
    }
  }

  /**
   * Renders basic background structure grids onto the targeted 2D frame drawing zone
   */
  drawInfiniteGrid(cameraState) {
    const ctx = this.zoomEngine.ctx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const z = cameraState.z;

    ctx.save();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1 / z;

    // Grid tracking intervals scale organically relative to internal camera elevation metrics
    const gridSize = z > 6 ? 40 : z > 2 ? 100 : 250;

    const startX = Math.floor((cameraState.x - width / (2 * z)) / gridSize) * gridSize;
    const endX = Math.ceil((cameraState.x + width / (2 * z)) / gridSize) * gridSize;
    const startY = Math.floor((cameraState.y - height / (2 * z)) / gridSize) * gridSize;
    const endY = Math.ceil((cameraState.y + height / (2 * z)) / gridSize) * gridSize;

    for (let x = startX; x <= endX; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, startY);
      ctx.lineTo(x, endY);
      ctx.stroke();
    }

    for (let y = startY; y <= endY; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(startX, y);
      ctx.lineTo(endX, y);
      ctx.stroke();
    }

    ctx.restore();
  }
}

module.exports = CanvasViewportController;

