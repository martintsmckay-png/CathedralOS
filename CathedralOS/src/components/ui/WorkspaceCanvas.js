// src/components/ui/WorkspaceCanvas.js
import React, { useEffect, useRef } from 'react';

export const WorkspaceCanvas = ({ onCanvasReady, activeTool }) => {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const fabricInstance = useRef(null);

  useEffect(() => {
    const initWidth = containerRef.current.clientWidth;
    const initHeight = containerRef.current.clientHeight;
    const fabricContext = window.fabric || require('fabric').fabric;

    // Initialize clean canvas axis
    const canvas = new fabricContext.Canvas(canvasRef.current, {
      width: initWidth,
      height: initHeight,
      selection: true,
      backgroundColor: '#0a0a0c'
    });

    fabricInstance.current = canvas;

    // Infinite Wheel Zooming Engine
    canvas.on('mouse:wheel', (opt) => {
      const delta = opt.e.deltaY;
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** delta;
      if (zoom > 20) zoom = 20;
      if (zoom < 0.05) zoom = 0.05;
      
      canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    });

    // Infinite Vector Panning Engine
    let isPanning = false;
    let lastX, lastY;

    canvas.on('mouse:down', (opt) => {
      const evt = opt.e;
      if (evt.spaceKey === true || evt.button === 1 || activeTool === 'pan') {
        isPanning = true;
        canvas.selection = false;
        lastX = evt.clientX;
        lastY = evt.clientY;
      }
    });

    canvas.on('mouse:move', (opt) => {
      if (!isPanning) return;
      const e = opt.e;
      const vpt = canvas.viewportTransform;
      vpt[4] += e.clientX - lastX;
      vpt[5] += e.clientY - lastY;
      canvas.requestRenderAll();
      lastX = e.clientX;
      lastY = e.clientY;
    });

    canvas.on('mouse:up', () => {
      canvas.setViewportTransform(canvas.viewportTransform);
      isPanning = false;
      if (activeTool === 'select') canvas.selection = true;
    });

    const handleResize = () => {
      if (!containerRef.current || !fabricInstance.current) return;
      fabricInstance.current.setDimensions({
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight
      });
    };
    window.addEventListener('resize', handleResize);

    if (onCanvasReady) onCanvasReady(canvas);

    return () => {
      window.removeEventListener('resize', handleResize);
      canvas.dispose();
    };
  }, [onCanvasReady]);

  // Handle live tool toggles
  useEffect(() => {
    const canvas = fabricInstance.current;
    if (!canvas) return;

    if (activeTool === 'select') {
      canvas.isDrawingMode = false;
      canvas.selection = true;
      canvas.forEachObject(obj => obj.selectable = true);
    } else if (activeTool === 'pan') {
      canvas.isDrawingMode = false;
      canvas.selection = false;
      canvas.forEachObject(obj => obj.selectable = false);
    }
  }, [activeTool]);

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden bg-zinc-950">
      <canvas ref={canvasRef} id="cathedral-infinite-axis" />
    </div>
  );
};

