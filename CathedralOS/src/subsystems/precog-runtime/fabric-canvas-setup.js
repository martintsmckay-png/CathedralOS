// src/subsystems/precog-runtime/fabric-canvas-setup.js
// CathedralOS Native Module — Infinite Substrate Grid Engine

export class FabricCanvasSetup {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      throw new Error(`[CANVAS] :: Element with ID "${canvasId}" not found in document.`);
    }

    this.ctx = this.canvas.getContext('2d');
    this.zoomEngine = null;

    // Drag / interaction state
    this.isDragging = false;
    this.didDrag = false;
    this.lastPointer = { x: 0, y: 0 };

    this.initResizeHandler();
    this.initInteractionListeners();
  }

  /**
   * Bind the active ZoomEngine instance to the substrate
   */
  attachZoomEngine(zoomEngineInstance) {
    this.zoomEngine = zoomEngineInstance;
    this.resizeCanvas();
  }

  /**
   * Keep canvas dimensions synced to viewport size
   */
  initResizeHandler() {
    window.addEventListener('resize', () => this.resizeCanvas());
    this.resizeCanvas();
  }

  resizeCanvas() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;

    if (this.zoomEngine) {
      this.zoomEngine.render();
    }
  }

  /**
   * Convert screen coordinates to world coordinates using current camera state
   */
  screenToWorld(screenX, screenY) {
    if (!this.zoomEngine) {
      return { x: 0, y: 0 };
    }

    const { x, y, z } = this.zoomEngine.currentState;

    return {
      x: (screenX - this.canvas.width / 2) / z + x,
      y: (screenY - this.canvas.height / 2) / z + y
    };
  }

  /**
   * Attaches interaction event listeners for infinite canvas navigation
   */
  initInteractionListeners() {
    // --- Mouse drag panning ---
    this.canvas.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.didDrag = false;
      this.lastPointer = { x: e.clientX, y: e.clientY };
    });

    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.isDragging || !this.zoomEngine) return;

      const dx = e.clientX - this.lastPointer.x;
      const dy = e.clientY - this.lastPointer.y;

      if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
        this.didDrag = true;
      }

      this.zoomEngine.currentState.x -= dx / this.zoomEngine.currentState.z;
      this.zoomEngine.currentState.y -= dy / this.zoomEngine.currentState.z;

      // Lock target to current position so the camera does not spring back
      this.zoomEngine.targetState.x = this.zoomEngine.currentState.x;
      this.zoomEngine.targetState.y = this.zoomEngine.currentState.y;

      this.lastPointer = { x: e.clientX, y: e.clientY };
      this.zoomEngine.render();
    });

    window.addEventListener('mouseup', () => {
      this.isDragging = false;
    });

    // --- Wheel zoom ---
    this.canvas.addEventListener(
      'wheel',
      (e) => {
        if (!this.zoomEngine) return;
        e.preventDefault();

        const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
        const newZ = Math.max(
          0.5,
          Math.min(25.0, this.zoomEngine.targetState.z * zoomFactor)
        );

        this.zoomEngine.targetState.z = newZ;

        if (!this.zoomEngine.isAnimating) {
          this.zoomEngine.isAnimating = true;
          this.zoomEngine.update();
        }
      },
      { passive: false }
    );

    // --- Click-to-fly node selection ---
    this.canvas.addEventListener('click', (e) => {
      if (!this.zoomEngine || !this.zoomEngine.nodeManager) return;

      // Ignore click events that are really the tail-end of a drag
      if (this.didDrag) {
        this.didDrag = false;
        return;
      }

      const rect = this.canvas.getBoundingClientRect();
      const screenX = e.clientX - rect.left;
      const screenY = e.clientY - rect.top;

      const { z } = this.zoomEngine.currentState;
      const world = this.screenToWorld(screenX, screenY);

      const hit = this.zoomEngine.nodeManager.hitTest(world.x, world.y, z);
      if (!hit) return;

      this.zoomEngine.flyTo(hit.x, hit.y, hit.targetZoom);
    });
  }

  /**
   * Draw an infinite Cartesian grid in world space
   */
  drawInfiniteGrid(currentState) {
    const { x, y, z } = currentState;
    const ctx = this.ctx;

    ctx.save();
    ctx.strokeStyle = '#222222';
    ctx.lineWidth = 1 / z;

    // Dynamic grid density based on zoom level
    const gridSpacing = z < 3.0 ? 200 : z < 7.0 ? 100 : 50;

    const startX =
      Math.floor((x - this.canvas.width / (2 * z)) / gridSpacing) * gridSpacing;
    const endX =
      Math.ceil((x + this.canvas.width / (2 * z)) / gridSpacing) * gridSpacing;
    const startY =
      Math.floor((y - this.canvas.height / (2 * z)) / gridSpacing) * gridSpacing;
    const endY =
      Math.ceil((y + this.canvas.height / (2 * z)) / gridSpacing) * gridSpacing;

    // Vertical lines
    for (let gx = startX; gx <= endX; gx += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(gx, startY);
      ctx.lineTo(gx, endY);
      ctx.stroke();
    }

    // Horizontal lines
    for (let gy = startY; gy <= endY; gy += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(startX, gy);
      ctx.lineTo(endX, gy);
      ctx.stroke();
    }

    ctx.restore();
  }
}
