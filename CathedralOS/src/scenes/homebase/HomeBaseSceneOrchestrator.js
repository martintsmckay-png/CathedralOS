// src/scenes/homebase/HomeBaseSceneOrchestrator.js
// CathedralOS Native Module — HomeBase Scene Runtime Conductor
// Binds PrecogRuntimeOrchestrator + SoulVibeRouter into one live scene system.

const PrecogRuntimeOrchestrator = require('../../subsystems/precog-runtime/precog-orchestrator');
const SoulVibeRouter = require('../../subsystems/soul-vibe/SoulVibeRouter');
const RodentDJMixer = require('../../subsystems/homebase/RodentDJMixer');

class HomeBaseSceneOrchestrator {
  constructor(options = {}) {
    // -------------------------------------------------------------------------
    // Core Runtime Modules
    // -------------------------------------------------------------------------
    this.precog = new PrecogRuntimeOrchestrator();
    this.soulVibe = new SoulVibeRouter(options.soulVibeConfig || {});
    this.rodentDJ = new RodentDJMixer(); // Initializing Sprocket's workspace

    // -------------------------------------------------------------------------
    // Scene Runtime State
    // -------------------------------------------------------------------------
    this.isMounted = false;
    this.isRunning = false;

    this.canvas = null;
    this.replaySlider = null;

    this.sceneState = {
      mode: 'IDLE', // IDLE | LIVE_SHOW | REPLAY | AMBIENT | PERFORMANCE
      activeNodeId: null,
      playbackCursor: null,
      timelineBounds: { minSequence: 0, maxSequence: 0 },
      lastSoulEvent: null,
      soulStats: {
        totalEvents: 0,
        lastRoute: null
      }
    };

    // -------------------------------------------------------------------------
    // Optional external UI / telemetry hooks
    // -------------------------------------------------------------------------
    this.onInspectorUpdate = null;
    this.onTimelineUpdate = null;
    this.onSceneLog = null;
    this.onSoulTelemetry = null;
    this.onModeChanged = null;
  }

  // ===========================================================================
  // MOUNT / BOOTSTRAP
  // ===========================================================================

  mount(config = {}) {
    const {
      canvas,
      replaySlider = null,
      onInspectorUpdate = null,
      onTimelineUpdate = null,
      onSceneLog = null,
      onSoulTelemetry = null,
      onModeChanged = null
    } = config;

    if (!canvas) {
      throw new Error('HomeBaseSceneOrchestrator.mount requires a valid canvas element.');
    }

    this.canvas = canvas;
    this.replaySlider = replaySlider || null;

    this.onInspectorUpdate = typeof onInspectorUpdate === 'function' ? onInspectorUpdate : null;
    this.onTimelineUpdate = typeof onTimelineUpdate === 'function' ? onTimelineUpdate : null;
    this.onSceneLog = typeof onSceneLog === 'function' ? onSceneLog : null;
    this.onSoulTelemetry = typeof onSoulTelemetry === 'function' ? onSoulTelemetry : null;
    this.onModeChanged = typeof onModeChanged === 'function' ? onModeChanged : null;

    // Mount Precog canvas runtime
    this.precog.mountCanvas(canvas);

    // Inspector callback: when a node is selected in the spatializer
    this.precog.registerInspectorListener((node) => {
      this.sceneState.activeNodeId = node?.id || null;

      this._log(
        node
          ? `🎯 [HOMEBASE] Inspector focus -> ${node.id} (${node.label || 'Unnamed Node'})`
          : '🎯 [HOMEBASE] Inspector cleared'
      );

      if (this.onInspectorUpdate) {
        this.onInspectorUpdate(node);
      }

      // -----------------------------------------------------------------------
      // THE SPROCKET OVERRIDE (Vibe-Telemetry Bypass Mode)
      // -----------------------------------------------------------------------
      if (node && this.sceneState.mode === 'PERFORMANCE') {
        const label = String(node.label || '').toLowerCase();
        
        this._log(`🎛️ [VIBE-TELEMETRY] :: Sprocket just dropped a bass-bomb on Node: ${node.id}`);

        if (label.includes('garlic')) {
          this.rodentDJ.engageDeck('Sprocket_The_Great');
          this.rodentDJ.remixVibes('SOUL_VIBE', 'TACTICAL_CHAOS', 0.95);
          
          this._routeSoulEvent({
            type: 'S_O_U_L_VIBE_REMIX',
            payload: {
              operator: 'Sprocket',
              impact: 'Maximum Butter',
              crossfader: this.rodentDJ.crossfaderPos
            },
            source: 'SprocketBridge'
          });

          // Actively map fader values onto the canvas context renderer layout layers
          this.syncVisualVibeLayers();
        }
      } else if (node) {
        // Fallback standard routing
        this._routeSoulEvent({
          type: 'NODE_SELECTED',
          payload: {
            nodeId: node.id,
            label: node.label || null,
            metadata: node.metadata || {},
            sequence: node.sequence ?? null
          },
          source: 'PrecogRuntime'
        });
      }
    });

    // Timeline callback: replay cursor changed by slider or external control
    this.precog.registerTimelineListener((cursor) => {
      this.sceneState.playbackCursor = cursor;
      this._log(`⏱️ [HOMEBASE] Playback cursor -> ${cursor}`);

      if (this.onTimelineUpdate) {
        this.onTimelineUpdate({
          cursor,
          bounds: { ...this.sceneState.timelineBounds }
        });
      }

      this._routeSoulEvent({
        type: 'TIMELINE_CURSOR_CHANGED',
        payload: {
          cursor,
          bounds: { ...this.sceneState.timelineBounds }
        },
        source: 'PrecogRuntime'
      });
    });

    if (this.replaySlider) {
      this.precog.bindReplaySlider(this.replaySlider);
    }

    this.isMounted = true;
    this._log('🏠 [HOMEBASE] Scene mounted. Precog + SoulVibe handshake complete.');
  }

  // ===========================================================================
  // SENSORY METRIC FEEDBACK INTERFACE
  // ===========================================================================

  /**
   * Translates crossfader thresholds into visual canvas rendering alphas
   */
  syncVisualVibeLayers() {
    if (!this.precog.zoomEngine) return;
    
    const crossfader = this.rodentDJ.crossfaderPos || 0.0;
    
    // Bind directly to zoomEngine's context layering configurations
    this.precog.zoomEngine.neonStreaksOpacity = 1.0 - crossfader;
    this.precog.zoomEngine.velvetAmberOpacity = crossfader;
  }

  // ===========================================================================
  // TOPOLOGY / DATA LOADING
  // ===========================================================================

  loadSceneTopology(nodesArray = [], edgesArray = []) {
    this._assertMounted();
    this.precog.loadSystemTopology(nodesArray, edgesArray);

    const bounds = this.precog.getTimelineBounds();
    this.sceneState.timelineBounds = { ...bounds };

    if (this.replaySlider) {
      this.replaySlider.min = String(bounds.minSequence);
      this.replaySlider.max = String(bounds.maxSequence);
      this.replaySlider.step = '1';

      const initialCursor =
        this.precog.zoomEngine?.playbackCursor != null
          ? this.precog.zoomEngine.playbackCursor
          : bounds.maxSequence;

      this.replaySlider.value = String(initialCursor);
    }

    this.sceneState.playbackCursor =
      this.precog.zoomEngine?.playbackCursor != null
        ? this.precog.zoomEngine.playbackCursor
        : bounds.maxSequence;

    this._log(`🧭 [HOMEBASE] Topology loaded. timeline=${bounds.minSequence}..${bounds.maxSequence}`);

    this._routeSoulEvent({
      type: 'TOPOLOGY_LOADED',
      payload: {
        nodeCount: Array.isArray(nodesArray) ? nodesArray.length : 0,
        edgeCount: Array.isArray(edgesArray) ? edgesArray.length : 0,
        timelineBounds: { ...bounds }
      },
      source: 'HomeBaseScene'
    });

    if (this.onTimelineUpdate) {
      this.onTimelineUpdate({
        cursor: this.sceneState.playbackCursor,
        bounds: { ...bounds }
      });
    }
  }

  // ===========================================================================
  // LIFECYCLE
  // ===========================================================================

  start() {
    this._assertMounted();
    if (this.isRunning) return;

    this.isRunning = true;
    this.sceneState.mode = 'LIVE_SHOW';

    this.precog.start();
    this._log('🚀 [HOMEBASE] Scene runtime started.');
    this._emitModeChanged();

    this._routeSoulEvent({
      type: 'SCENE_STARTED',
      payload: { mode: this.sceneState.mode },
      source: 'HomeBaseScene'
    });
  }

  stop() {
    if (!this.isMounted || !this.isRunning) return;

    this.precog.stop();
    this.isRunning = false;
    this.sceneState.mode = 'IDLE';

    this._log('🛑 [HOMEBASE] Scene runtime stopped.');
    this._emitModeChanged();

    this._routeSoulEvent({
      type: 'SCENE_STOPPED',
      payload: { mode: this.sceneState.mode },
      source: 'HomeBaseScene'
    });
  }

  // ===========================================================================
  // REPLAY CONTROLS
  // ===========================================================================

  setReplayMode(enabled) {
    this._assertMounted();

    const replayEnabled = Boolean(enabled);
    this.precog.setReplayMode(replayEnabled);
    this.sceneState.mode = replayEnabled ? 'REPLAY' : 'LIVE_SHOW';

    this._log(`🕰️ [HOMEBASE] Replay mode -> ${replayEnabled ? 'ON' : 'OFF'}`);
    this._emitModeChanged();

    this._routeSoulEvent({
      type: replayEnabled ? 'REPLAY_ENABLED' : 'REPLAY_DISABLED',
      payload: {
        cursor: this.precog.zoomEngine?.playbackCursor ?? null,
        bounds: { ...this.sceneState.timelineBounds }
      },
      source: 'HomeBaseScene'
    });
  }

  setPlaybackCursor(cursor) {
    this._assertMounted();

    const normalized = Number(cursor);
    if (!Number.isFinite(normalized)) return;

    this.precog.setPlaybackCursor(normalized);
    this.sceneState.playbackCursor = normalized;

    if (this.replaySlider) {
      this.replaySlider.value = String(normalized);
    }

    this._log(`🎞️ [HOMEBASE] Playback cursor set -> ${normalized}`);

    if (this.onTimelineUpdate) {
      this.onTimelineUpdate({
        cursor: normalized,
        bounds: { ...this.sceneState.timelineBounds }
      });
    }

    this._routeSoulEvent({
      type: 'TIMELINE_CURSOR_SET',
      payload: {
        cursor: normalized,
        bounds: { ...this.sceneState.timelineBounds }
      },
      source: 'HomeBaseScene'
    });
  }

  focusNodeById(nodeId) {
    this._assertMounted();
    this.precog.focusNodeById(nodeId);
  }

  // ===========================================================================
  // SCENE EVENT INGESTION
  // ===========================================================================

  ingestSceneEvent(event = {}) {
    if (!event || typeof event !== 'object') return;

    const normalized = {
      type: event.type || 'UNKNOWN_EVENT',
      payload: event.payload || {},
      source: event.source || 'ExternalSceneSource',
      timestamp: Date.now()
    };

    this._log(`🎛️ [HOMEBASE] ingestSceneEvent -> ${normalized.type}`);
    this._applySceneEventSideEffects(normalized);
    this._routeSoulEvent(normalized);
  }

  emitPerformancePulse(kind, payload = {}) {
    this.ingestSceneEvent({
      type: 'PERFORMANCE_PULSE',
      payload: { kind, ...payload },
      source: 'PerformanceLayer'
    });
  }

  dispatchRodentAction(actor, action, payload = {}) {
    this.ingestSceneEvent({
      type: 'RODENT_ACTION',
      payload: { actor, action, ...payload },
      source: 'RodentCrew'
    });
  }

  dispatchEntityPing(entity = {}) {
    this.ingestSceneEvent({
      type: 'ENTITY_PING',
      payload: entity,
      source: 'IncomingEntitySorter'
    });
  }

  // ===========================================================================
  // INTERNAL SOULVIBE ROUTING
  // ===========================================================================

  _routeSoulEvent(event) {
    if (!this.soulVibe || typeof this.soulVibe.route !== 'function') {
      return null;
    }

    const result = this.soulVibe.route({
      ...event,
      sceneContext: {
        mode: this.sceneState.mode,
        activeNodeId: this.sceneState.activeNodeId,
        playbackCursor: this.sceneState.playbackCursor,
        timelineBounds: { ...this.sceneState.timelineBounds }
      }
    });

    this.sceneState.lastSoulEvent = {
      type: event.type,
      source: event.source || 'unknown',
      timestamp: Date.now()
    };

    this.sceneState.soulStats.totalEvents += 1;
    this.sceneState.soulStats.lastRoute = result?.route || result?.channel || event.type;

    if (this.onSoulTelemetry) {
      this.onSoulTelemetry({
        input: event,
        output: result,
        sceneState: this.getSceneState()
      });
    }

    return result;
  }

  _applySceneEventSideEffects(event) {
    switch (event.type) {
      case 'AMBIENT_MODE_SET': {
        const nextMode = event.payload?.mode;
        if (typeof nextMode === 'string' && nextMode.trim()) {
          this.sceneState.mode = nextMode.trim().toUpperCase();
          this._emitModeChanged();
        }
        break;
      }

      case 'FOCUS_NODE': {
        const nodeId = event.payload?.nodeId;
        if (nodeId) {
          this.focusNodeById(nodeId);
        }
        break;
      }

      case 'SET_REPLAY_CURSOR': {
        if (event.payload?.cursor != null) {
          this.setPlaybackCursor(event.payload.cursor);
        }
        break;
      }

      case 'SET_REPLAY_MODE': {
        this.setReplayMode(Boolean(event.payload?.enabled));
        break;
      }

      default:
        break;
    }
  }

  // ===========================================================================
  // READ-ONLY STATE SURFACE
  // ===========================================================================

  getSceneState() {
    return {
      isMounted: this.isMounted,
      isRunning: this.isRunning,
      canvasMounted: Boolean(this.canvas),
      replaySliderBound: Boolean(this.replaySlider),
      ...this.sceneState
    };
  }

  getPrecogRuntime() {
    return this.precog;
  }

  getSoulVibeRouter() {
    return this.soulVibe;
  }

  // ===========================================================================
  // INTERNAL UTILITIES
  // ===========================================================================

  _emitModeChanged() {
    if (this.onModeChanged) {
      this.onModeChanged(this.sceneState.mode, this.getSceneState());
    }
  }

  _log(message) {
    if (typeof this.onSceneLog === 'function') {
      this.onSceneLog(message);
    }
  }

  _assertMounted() {
    if (!this.isMounted) {
      throw new Error('HomeBaseSceneOrchestrator must be mounted before invoking runtime operations.');
    }
  }
}

module.exports = HomeBaseSceneOrchestrator;

