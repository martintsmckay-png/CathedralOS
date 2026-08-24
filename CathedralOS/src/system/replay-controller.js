// src/system/replay-controller.js

import { cathedralBus } from "./core-bus.js";

export class ReplayController {
  constructor(nodeManager, zoomEngine) {
    this.nodeManager = nodeManager;
    this.zoomEngine = zoomEngine;
  }

  async replayCanvas() {
    console.log("[REPLAY] starting full system replay...");

    // reset
    this.nodeManager.clear();

    await cathedralBus.replay();

    console.log("[REPLAY] complete");
  }

  rewindAndReplay(n = 50) {
    cathedralBus.rewind(n);
    this.replayCanvas();
  }
}
