// src/subsystems/homebase/RodentDJMixer.js
// CathedralOS Native Module — Rodent-Driven Audio Modulation
// Turns the Rodent Crew into a live remix engine.

class RodentDJMixer {
  constructor(soulVibeRouter) {
    this.router = soulVibeRouter;
    this.currentDeck = 'S_O_U_L_VIBE';
    this.crossfaderPos = 0.5; // 0: Pure Soul, 1: Pure Grit
    this.activeStems = [];
  }

  /**
   * Triggered when the Rodent Crew takes over the board.
   * @param {string} rodentId - The name of the rodent currently on the decks.
   */
  engageDeck(rodentId) {
    this.router.routeEvent('RODENT_DJ_ENGAGED', {
      dj: rodentId,
      status: 'SCRATCHING_THE_KERNEL',
      message: 'Hold tight, humans. Sprocket is in the mix.'
    });
  }

/**
 * Mixes two vibe states into a hybrid resonance.
 */
remixVibes(vibeA, vibeB, intensity) {
  const hybridTag = `${vibeA}_${vibeB}`;
  this.crossfaderPos = Math.max(0, Math.min(1, intensity));

  this.router.routeEvent('VIBE_FUSION', {
    hybridTag,
    intensity: this.crossfaderPos,
    crossfader: this.crossfaderPos
  });
}

  syncToStomp(stompCount) {
    // Every stomp shifts the crossfader by 0.1
    this.crossfaderPos = Math.min(1, this.crossfaderPos + 0.1);
    this.router.routeEvent('CROSSFADER_SHIFT', {
      position: this.crossfaderPos,
      source: 'STOMP_SENSORS'
    });
  }
}

module.exports = RodentDJMixer;
