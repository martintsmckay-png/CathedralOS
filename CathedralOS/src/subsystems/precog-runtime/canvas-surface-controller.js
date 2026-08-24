// src/subsystems/precog-runtime/canvas-surface-controller.js

export class CanvasSurfaceController {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) {
      throw new Error(`[CanvasSurface] Element "${canvasId}" not found.`);
    }

    this.ctx = this.canvas.getContext('2d');
    this.zoomEngine = null;

    this.isDragging = false;
    this.didDrag = false;
    this.lastPointer = { x: 0, y: 0 };
    this.disposers = [];

    this.bindResize();
    this.bindInteractions();
  }

  attachZoomEngine(zoomEngine) {
    this.zoomEngine = zoomEngine;
    this.resizeCanvas();
  }

  bindResize() {
    const onResize = () => this.resizeCanvas();
    window.addEventListener('resize', onResize);
    this.disposers.push(() => window.removeEventListener('resize', onResize));
    this.resizeCanvas();
  }

  resizeCanvas() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
    this.zoomEngine?.handleCanvasResize?.(this.canvas.width, this.canvas.height);
  }

  screenToWorld(screenX, screenY) {
    return this.zoomEngine?.screenToWorld?.(
      screenX,
      screenY,
      this.canvas.width,
      this.canvas.height
    ) ?? { x: 0, y: 0 };
  }

  bindInteractions() {
    const onMouseDown = (e) => {
      this.isDragging = true;
      this.didDrag = false;
      this.lastPointer = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e) => {
      if (!this.isDragging || !this.zoomEngine) return;

      const dx = e.clientX - this.lastPointer.x;
      const dy = e.clientY - this.lastPointer.y;

      if (dx !== 0 || dy !== 0) this.didDrag = true;

      this.zoomEngine.panByScreenDelta?.(dx, dy);
      this.lastPointer = { x: e.clientX, y: e.clientY };
    };

    const onMouseUp = () => {
      this.isDragging = false;
    };

    const onWheel = (e) => {
      if (!this.zoomEngine) return;
      e.preventDefault();

      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      this.zoomEngine.zoomByFactor?.(zoomFactor);
    };

    const onClick = (e) => {
      if (!this.zoomEngine?.nodeManager) return;

      if (this.didDrag) {
        this.didDrag = false;
        return;
      }

      const rect = this.canvas.getBoundingClientRect();
      const screenX = e.clientX - rect.left;
      const screenY = e.clientY - rect.top;
      const world = this.screenToWorld(screenX, screenY);

      const hit = this.zoomEngine.nodeManager.hitTest(
        world.x,
        world.y,
        this.zoomEngine.currentState.z
      );

      if (hit) {
        this.zoomEngine.flyTo(hit.x, hit.y, hit.targetZoom);
      }
    };

    this.canvas.addEventListener('mousedown', onMouseDown);
    this.canvas.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    this.canvas.addEventListener('wheel', onWheel, { passive: false });
    this.canvas.addEventListener('click', onClick);

    this.disposers.push(
      () => this.canvas.removeEventListener('mousedown', onMouseDown),
      () => this.canvas.removeEventListener('mousemove', onMouseMove),
      () => window.removeEventListener('mouseup', onMouseUp),
      () => this.canvas.removeEventListener('wheel', onWheel),
      () => this.canvas.removeEventListener('click', onClick)
    );
  }

  drawInfiniteGrid(currentState) {
    const { x, y, z } = currentState;
    const ctx = this.ctx;

    ctx.save();
    ctx.strokeStyle = '#222222';
    ctx.lineWidth = 1 / z;

    const gridSpacing = z < 3 ? 200 : z < 7 ? 100 : 50;
    const halfW = this.canvas.width / (2 * z);
    const halfH = this.canvas.height / (2 * z);

    const startX = Math.floor((x - halfW) / gridSpacing) * gridSpacing;
    const endX = Math.ceil((x + halfW) / gridSpacing) * gridSpacing;
    const startY = Math.floor((y - halfH) / gridSpacing) * gridSpacing;
    const endY = Math.ceil((y + halfH) / gridSpacing) * gridSpacing;

    for (let gx = startX; gx <= endX; gx += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(gx, startY);
      ctx.lineTo(gx, endY);
      ctx.stroke();
    }

    for (let gy = startY; gy <= endY; gy += gridSpacing) {
      ctx.beginPath();
      ctx.moveTo(startX, gy);
      ctx.lineTo(endX, gy);
      ctx.stroke();
    }

    ctx.restore();
  }

  destroy() {
    for (const dispose of this.disposers) {
      try { dispose(); } catch {}
    }
    this.disposers = [];
    this.zoomEngine = null;
  }
}
