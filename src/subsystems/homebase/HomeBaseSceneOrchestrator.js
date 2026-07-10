// src/subsystems/homebase/HomeBaseSceneOrchestrator.js
import { RodentDJMixer } from './RodentDJMixer.js';

export class HomeBaseSceneOrchestrator {
  constructor(busInstance) {
    this.bus = busInstance;
    this.sceneMode = 'idle'; // 'idle' | 'simulation' | 'performance'
    this.rodentDJ = new RodentDJMixer(busInstance);
  }

  setMode(mode) {
    this.sceneMode = mode;
    console.log(`[ORCHESTRATOR] Mode shifted to: ${mode.toUpperCase()}`);
  }

  handleNodeSelection(node) {
    if (!node) return;

    if (this.sceneMode === 'performance') {
      const label = String(node.label || node.text || '').toLowerCase();
      console.log(`[VIBE-TELEMETRY] :: Sprocket just dropped a bass-bomb on Node: ${node.text || 'Unknown'}`);

      if (label.includes('garlic')) {
        // The "Sprocket Override"
        this.rodentDJ.engageDeck('Sprocket_The_Great');
        this.rodentDJ.remixVibes('SOUL_VIBE', 'TACTICAL_CHAOS', 0.95);
        
        if (typeof this.bus.publish === 'function') {
          this.bus.publish('S_O_U_L_VIBE_REMIX', {
            operator: 'Sprocket',
            impact: 'Maximum Butter'
          });
        }
      }
    } else {
      console.log(`[LOG] Node selected standard: ${node.id || 'unknown'}`);
    }
  }

  /**
   * Translates crossfader values to full-sensory visual parameters
   */
  getVisualVibeLayers() {
    const crossfader = this.rodentDJ.crossfaderPos;
    return {
      neonStreaksOpacity: 1.0 - crossfader,
      velvetAmberOpacity: crossfader
    };
  }
}

