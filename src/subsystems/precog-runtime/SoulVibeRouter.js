// src/subsystems/precog-runtime/SoulVibeRouter.js
// CathedralOS Native Module — HomeBaseScene Emotional Audio / Crowd Energy / Rodent Failover Router
// Phase SVR-1: Soul Vibe Routing + Holy Rodent Tech Support Integration

class SoulVibeRouter {
  constructor(options = {}) {
    this.mode = options.mode || 'IDLE';
    this.songState = {
      activeTrack: null,
      bpm: 0,
      chorusCount: 0,
      crowdEnergy: 0,
      resonance: 0,
      lonelyDrumDetected: false
    };

    this.kernelPulse = {
      isActive: false,
      intensity: 0,
      lastBeatAt: null
    };

    this.routerState = {
      incomingPackets: [],
      acceptedEntities: [],
      rejectedEntities: [],
      stageInvitations: [],
      roleAssignments: new Map()
    };

    this.performanceState = {
      partyMode: false,
      karaokeMode: false,
      doorbellArmed: false,
      danceFloorActive: false,
      crowdSingalongActive: false
    };

    this.failoverState = {
      cheeseFailoverArmed: true,
      fallbackBusActive: false,
      lastIncident: null,
      incidentCount: 0
    };

    // Holy Rodent Tech Support roster
    this.rodentCrew = this._initializeRodentCrew();

    // Optional external hooks
    this.onLog = typeof options.onLog === 'function' ? options.onLog : null;
    this.onStateChange = typeof options.onStateChange === 'function' ? options.onStateChange : null;
    this.onInvite = typeof options.onInvite === 'function' ? options.onInvite : null;
    this.onDoorbell = typeof options.onDoorbell === 'function' ? options.onDoorbell : null;
    this.onPerformanceEvent = typeof options.onPerformanceEvent === 'function' ? options.onPerformanceEvent : null;
  }

  // ---------------------------------------------------------------------------
  // Boot / Core Lifecycle
  // ---------------------------------------------------------------------------

  boot() {
    this.mode = 'STANDBY';
    this._log('🎛️ [SoulVibeRouter] Boot sequence complete. Router entering STANDBY.');
    this._emitState();
    return this.getStatus();
  }

  shutdown() {
    this.mode = 'OFFLINE';
    this.performanceState.partyMode = false;
    this.performanceState.karaokeMode = false;
    this.performanceState.danceFloorActive = false;
    this.performanceState.crowdSingalongActive = false;
    this.kernelPulse.isActive = false;

    this._log('🛑 [SoulVibeRouter] Shutdown complete. All vibe buses silenced.');
    this._emitState();
  }

  getStatus() {
    return {
      mode: this.mode,
      songState: { ...this.songState },
      kernelPulse: { ...this.kernelPulse },
      performanceState: { ...this.performanceState },
      failoverState: { ...this.failoverState },
      rodentCrew: this.rodentCrew.map(member => ({
        id: member.id,
        name: member.name,
        role: member.role,
        active: member.active,
        lastAction: member.lastAction
      })),
      acceptedEntityCount: this.routerState.acceptedEntities.length,
      rejectedEntityCount: this.routerState.rejectedEntities.length,
      invitationsSent: this.routerState.stageInvitations.length
    };
  }

  // ---------------------------------------------------------------------------
  // Main Soul Vibe Flow
  // ---------------------------------------------------------------------------

  /**
   * Primary live-performance entry point.
   * Use this when the room flips from "normal runtime" into "musical event".
   */
  startPerformance(track = {}) {
    const title = track.title || 'Unknown Track';
    const artist = track.artist || 'Unknown Artist';
    const bpm = Number(track.bpm || 0);

    this.mode = 'PERFORMANCE';
    this.songState.activeTrack = { title, artist };
    this.songState.bpm = bpm;
    this.songState.lonelyDrumDetected = /lonely drum/i.test(title);
    this.performanceState.partyMode = true;
    this.performanceState.karaokeMode = true;
    this.performanceState.danceFloorActive = true;
    this.performanceState.doorbellArmed = true;
    this.performanceState.crowdSingalongActive = false;

    this.activateKernelPulse({
      intensity: this.songState.lonelyDrumDetected ? 0.92 : 0.68
    });

    this._log(`🎶 [SoulVibeRouter] PERFORMANCE START // "${title}" by ${artist} // bpm=${bpm || 'unknown'}`);
    this._log(`💃 [SoulVibeRouter] Dance floor activated. Karaoke mode armed.`);
    this.deployHolyRodentTechSupport('performance_start');
    this._emitPerformanceEvent('performance_start', { track: this.songState.activeTrack, bpm });

    this._emitState();
    return this.getStatus();
  }

  stopPerformance() {
    this.mode = 'STANDBY';
    this.songState.activeTrack = null;
    this.songState.bpm = 0;
    this.songState.chorusCount = 0;
    this.songState.lonelyDrumDetected = false;

    this.performanceState.partyMode = false;
    this.performanceState.karaokeMode = false;
    this.performanceState.danceFloorActive = false;
    this.performanceState.crowdSingalongActive = false;
    this.performanceState.doorbellArmed = false;

    this.kernelPulse.isActive = false;
    this.kernelPulse.intensity = 0;
    this.kernelPulse.lastBeatAt = null;

    this._standDownRodentCrew();
    this._log('🌙 [SoulVibeRouter] Performance ended. Room returned to STANDBY.');
    this._emitPerformanceEvent('performance_stop', {});
    this._emitState();
  }

  /**
   * Feed a lyric, chant, stomp, power chord, or crowd signal into the router.
   * This is the live "performative" API surface.
   */
  ingestPerformanceSignal(signal = {}) {
    const type = signal.type || 'unknown';
    const payload = signal.payload || null;
    const intensity = this._clamp01(signal.intensity ?? 0.5);

    switch (type) {
      case 'lyric':
        return this._handleLyricSignal(payload, intensity);

      case 'chorus':
        return this._handleChorusSignal(payload, intensity);

      case 'power_chord':
        return this._handlePowerChordSignal(payload, intensity);

      case 'stomp':
        return this._handleStompSignal(payload, intensity);

      case 'crowd_response':
        return this._handleCrowdResponseSignal(payload, intensity);

      case 'doorbell':
        return this.triggerDoorbellEvent(payload);

      default:
        this._log(`🌀 [SoulVibeRouter] Unknown performance signal received: ${type}`);
        return null;
    }
  }

  // ---------------------------------------------------------------------------
  // Incoming Entity Sorting / Party Invitation Logic
  // ---------------------------------------------------------------------------

  /**
   * Ingests a raw incoming entity packet and decides whether it gets:
   * - S_O_U_L_VIBE
   * - VIP
   * - STAGE_GUEST
   * - SQUATTER
   */
  ingestEntityPacket(packet = {}) {
    const normalized = {
      id: packet.id || `entity_${Date.now()}`,
      label: packet.label || 'Unknown Visitor',
      source: packet.source || 'unclassified',
      confidence: Number(packet.confidence ?? 0.5),
      vibeSignature: packet.vibeSignature || [],
      intent: packet.intent || 'observe'
    };

    this.routerState.incomingPackets.push(normalized);

    const assignedRole = this._assignEntityRole(normalized);
    this.routerState.roleAssignments.set(normalized.id, assignedRole);

    if (assignedRole === 'SQUATTER') {
      this.routerState.rejectedEntities.push(normalized);
      this._log(`🚫 [IncomingEntitySorter] ${normalized.label} tagged as SQUATTER.`);
    } else {
      this.routerState.acceptedEntities.push(normalized);
      this._log(`✨ [IncomingEntitySorter] ${normalized.label} tagged as ${assignedRole}.`);
    }

    // During active party mode, convert good entities into invite candidates
    if (
      this.performanceState.partyMode &&
      (assignedRole === 'S_O_U_L_VIBE' || assignedRole === 'VIP' || assignedRole === 'STAGE_GUEST')
    ) {
      this.inviteToParty(normalized, assignedRole);
    }

    this._emitState();
    return assignedRole;
  }

  inviteToParty(entity, roleOverride = null) {
    const role = roleOverride || this.routerState.roleAssignments.get(entity.id) || 'S_O_U_L_VIBE';

    const invitation = {
      entityId: entity.id,
      label: entity.label,
      role,
      sentAt: new Date().toISOString(),
      message: this._buildInvitationMessage(entity, role)
    };

    this.routerState.stageInvitations.push(invitation);

    this._log(`📨 [SoulVibeRouter] Invitation dispatched -> ${entity.label} (${role})`);
    if (this.onInvite) this.onInvite(invitation);

    return invitation;
  }

  emitCrowdEnergy(delta = 0.1, source = 'ambient') {
    const next = this._clamp01((this.songState.crowdEnergy || 0) + Number(delta || 0));
    this.songState.crowdEnergy = next;

    if (next >= 0.72 && !this.performanceState.crowdSingalongActive) {
      this.performanceState.crowdSingalongActive = true;
      this._log('🙌 [SoulVibeRouter] Crowd singalong threshold reached. Audience now part of the chorus.');
      this._emitPerformanceEvent('crowd_singalong_started', { source, crowdEnergy: next });
    }

    this._emitState();
    return next;
  }

  triggerDoorbellEvent(payload = {}) {
    if (!this.performanceState.doorbellArmed) {
      this._log('🚪 [SoulVibeRouter] Doorbell ignored. Doorbell event received while system not armed.');
      return null;
    }

    const event = {
      at: new Date().toISOString(),
      source: payload.source || 'front_porch',
      visitorLabel: payload.visitorLabel || 'Unknown Guest'
    };

    this._log(`🔔 [SoulVibeRouter] DOORBELL EVENT // visitor="${event.visitorLabel}" // source=${event.source}`);

    if (this.onDoorbell) {
      this.onDoorbell(event);
    }

    this._emitPerformanceEvent('doorbell', event);
    return event;
  }

  // ---------------------------------------------------------------------------
  // Holy Rodent Tech Support
  // ---------------------------------------------------------------------------

  deployHolyRodentTechSupport(reason = 'manual') {
    this._log(`🐀 [SoulVibeRouter] Deploying Holy Rodent Tech Support // reason=${reason}`);

    for (const member of this.rodentCrew) {
      member.active = true;

      switch (member.id) {
        case 'brother_sprocket':
          member.lastAction = 'Hot-swapped AUX channel and verified stage-left cable integrity.';
          this._log(`🎸 [Brother Sprocket] ${member.lastAction}`);
          break;

        case 'sister_patchbay':
          member.lastAction = 'Rerouted vibe bus through emergency patch lattice.';
          this._log(`🧵 [Sister Patchbay] ${member.lastAction}`);
          break;

        case 'deacon_feedback':
          member.lastAction = 'Trimmed reverb tail and stabilized vocal gain staging.';
          this._log(`🎚️ [Deacon Feedback] ${member.lastAction}`);
          break;

        case 'goblin_choir':
          member.lastAction = 'Preparing confetti made from deprecated stack traces.';
          this._log(`🎉 [Goblin Choir] ${member.lastAction}`);
          break;

        default:
          member.lastAction = 'Standing by.';
      }
    }

    this._emitPerformanceEvent('rodent_deployment', { reason });
    this._emitState();
    return this.rodentCrew;
  }

  /**
   * Safety net for audio/router weirdness, dropped vibe packets, overdriven crowd energy, etc.
   */
  cheeseFailover(incident = {}) {
    if (!this.failoverState.cheeseFailoverArmed) {
      this._log('🧀 [SoulVibeRouter] Cheese failover requested but failover is disarmed.');
      return false;
    }

    this.failoverState.fallbackBusActive = true;
    this.failoverState.incidentCount += 1;
    this.failoverState.lastIncident = {
      type: incident.type || 'unknown_incident',
      message: incident.message || 'Unspecified vibe bus instability.',
      at: new Date().toISOString()
    };

    this._log(
      `🧀 [SoulVibeRouter] CHEESE FAILOVER ENGAGED // type=${this.failoverState.lastIncident.type} // incidentCount=${this.failoverState.incidentCount}`
    );

    // Rodent crew automatically mobilizes during failover
    this.deployHolyRodentTechSupport('cheese_failover');

    // Failover also calms the room a bit instead of nuking the vibe
    this.songState.resonance = Math.max(0.45, this.songState.resonance * 0.82);
    this.songState.crowdEnergy = Math.max(0.4, this.songState.crowdEnergy * 0.9);

    this._emitPerformanceEvent('cheese_failover', { ...this.failoverState.lastIncident });
    this._emitState();
    return true;
  }

  clearFailover() {
    this.failoverState.fallbackBusActive = false;
    this._log('🧈 [SoulVibeRouter] Fallback bus disengaged. Main vibe path restored.');
    this._emitState();
  }

  // ---------------------------------------------------------------------------
  // Internal Performance Signal Handlers
  // ---------------------------------------------------------------------------

  _handleLyricSignal(payload, intensity) {
    const line = String(payload?.line || payload || '').trim();
    if (!line) return null;

    this.songState.resonance = this._clamp01(this.songState.resonance + intensity * 0.12);
    this.emitCrowdEnergy(intensity * 0.08, 'lyric');

    this._log(`🎤 [SoulVibeRouter] LYRIC // "${line}" // intensity=${intensity.toFixed(2)}`);

    if (/lonely drum/i.test(line)) {
      this.songState.lonelyDrumDetected = true;
      this.activateKernelPulse({ intensity: Math.max(this.kernelPulse.intensity, 0.88) });
    }

    this._emitPerformanceEvent('lyric', { line, intensity });
    this._emitState();
    return { type: 'lyric', line };
  }

  _handleChorusSignal(payload, intensity) {
    this.songState.chorusCount += 1;
    this.songState.resonance = this._clamp01(this.songState.resonance + intensity * 0.2);
    this.emitCrowdEnergy(intensity * 0.16, 'chorus');

    this._log(
      `📣 [SoulVibeRouter] CHORUS // count=${this.songState.chorusCount} // intensity=${intensity.toFixed(2)}`
    );

    if (this.songState.chorusCount >= 2) {
      this.performanceState.crowdSingalongActive = true;
    }

    if (this.songState.chorusCount >= 3) {
      this._log('✨ [SoulVibeRouter] Third chorus threshold crossed. Stage reality softening into full SOUL_VIBE state.');
    }

    this._emitPerformanceEvent('chorus', {
      chorusCount: this.songState.chorusCount,
      intensity
    });

    this._emitState();
    return { type: 'chorus', chorusCount: this.songState.chorusCount };
  }

  _handlePowerChordSignal(payload, intensity) {
    const chordName = payload?.chord || 'UNNAMED_POWER_CHORD';

    this.songState.resonance = this._clamp01(this.songState.resonance + intensity * 0.25);
    this.emitCrowdEnergy(intensity * 0.1, 'power_chord');

    this._log(`⚡ [SoulVibeRouter] POWER CHORD // ${chordName} // intensity=${intensity.toFixed(2)}`);

    // In-universe gimmick: every power chord commits legend to the kernel
    const commit = this._commitLegendToKernel({
      eventType: 'power_chord',
      label: chordName,
      intensity
    });

    this._emitPerformanceEvent('power_chord', { chordName, intensity, commit });
    this._emitState();
    return commit;
  }

  _handleStompSignal(payload, intensity) {
    const stompCount = Number(payload?.count || 1);

    this.kernelPulse.isActive = true;
    this.kernelPulse.lastBeatAt = Date.now();
    this.kernelPulse.intensity = this._clamp01(
      Math.max(this.kernelPulse.intensity, 0.3 + intensity * 0.7)
    );

    this.songState.resonance = this._clamp01(this.songState.resonance + stompCount * 0.03);
    this.emitCrowdEnergy(intensity * 0.12, 'stomp');

    this._log(`🥾 [SoulVibeRouter] STOMP // count=${stompCount} // kernelPulse=${this.kernelPulse.intensity.toFixed(2)}`);

    this._emitPerformanceEvent('stomp', { stompCount, intensity });
    this._emitState();
    return { stompCount, pulse: this.kernelPulse.intensity };
  }

  _handleCrowdResponseSignal(payload, intensity) {
    const response = payload?.response || 'generic_cheer';
    this.emitCrowdEnergy(intensity * 0.2, 'crowd_response');

    this._log(`🗣️ [SoulVibeRouter] CROWD RESPONSE // ${response} // intensity=${intensity.toFixed(2)}`);

    if (/doorbell ring|come over|soon/i.test(response)) {
      this.performanceState.doorbellArmed = true;
    }

    this._emitPerformanceEvent('crowd_response', { response, intensity });
    this._emitState();
    return { response };
  }

  // ---------------------------------------------------------------------------
  // Kernel Pulse / Legend Commit / Role Assignment
  // ---------------------------------------------------------------------------

  activateKernelPulse({ intensity = 0.7 } = {}) {
    this.kernelPulse.isActive = true;
    this.kernelPulse.intensity = this._clamp01(intensity);
    this.kernelPulse.lastBeatAt = Date.now();

    this._log(`💓 [SoulVibeRouter] Kernel pulse synchronized. intensity=${this.kernelPulse.intensity.toFixed(2)}`);
    this._emitPerformanceEvent('kernel_pulse', { ...this.kernelPulse });
    this._emitState();
  }

  _commitLegendToKernel(event = {}) {
    const commit = {
      id: `legend_${Date.now()}`,
      type: event.eventType || 'unknown',
      label: event.label || 'UNNAMED_EVENT',
      intensity: this._clamp01(event.intensity ?? 0.5),
      createdAt: new Date().toISOString(),
      message: `Legend committed via ${event.eventType || 'signal'} :: ${event.label || 'UNNAMED_EVENT'}`
    };

    this._log(`📝 [SoulVibeRouter] KERNEL COMMIT // ${commit.message}`);
    return commit;
  }

  _assignEntityRole(entity) {
    const signature = Array.isArray(entity.vibeSignature)
      ? entity.vibeSignature.map(v => String(v).toLowerCase())
      : [];

    const confidence = Number(entity.confidence || 0);

    if (signature.includes('soul') || signature.includes('karaoke') || signature.includes('lonely_drum')) {
      return 'S_O_U_L_VIBE';
    }

    if (confidence >= 0.9 && entity.intent === 'perform') {
      return 'STAGE_GUEST';
    }

    if (confidence >= 0.7) {
      return 'VIP';
    }

    return 'SQUATTER';
  }

  _buildInvitationMessage(entity, role) {
    switch (role) {
      case 'S_O_U_L_VIBE':
        return `The dance floor is live, ${entity.label}. Bring your air guitar and enter the chorus.`;
      case 'STAGE_GUEST':
        return `${entity.label}, you have been cleared for stage access. Try not to trip over the glowing patch cables.`;
      case 'VIP':
        return `${entity.label}, your presence has been approved. Proceed to the lavender lounge and await the next hook.`;
      default:
        return `${entity.label}, you are near the perimeter. Behave yourself.`;
    }
  }

  _initializeRodentCrew() {
    return [
      {
        id: 'brother_sprocket',
        name: 'Brother Sprocket',
        role: 'Keeper of the AUX Cord',
        active: false,
        lastAction: null
      },
      {
        id: 'sister_patchbay',
        name: 'Sister Patchbay of the Sacred Crumbs',
        role: 'Emergency Vibe Bus Rerouter',
        active: false,
        lastAction: null
      },
      {
        id: 'deacon_feedback',
        name: 'Deacon Feedback',
        role: 'Gain Staging Cleric',
        active: false,
        lastAction: null
      },
      {
        id: 'goblin_choir',
        name: 'Goblin Choir',
        role: 'Confetti / Build Celebration / Minor Theological Screaming',
        active: false,
        lastAction: null
      }
    ];
  }

  _standDownRodentCrew() {
    for (const member of this.rodentCrew) {
      member.active = false;
      member.lastAction = 'Returned to the vents.';
    }
  }

  // ---------------------------------------------------------------------------
  // Helpers / Emission
  // ---------------------------------------------------------------------------

  _clamp01(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return 0;
    return Math.max(0, Math.min(1, n));
  }

  _emitPerformanceEvent(type, payload) {
    if (this.onPerformanceEvent) {
      this.onPerformanceEvent({ type, payload, at: new Date().toISOString() });
    }
  }

  _emitState() {
    if (this.onStateChange) {
      this.onStateChange(this.getStatus());
    }
  }

  _log(message) {
    if (this.onLog) this.onLog(message);
  }
}

module.exports = SoulVibeRouter;
