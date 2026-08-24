export class BootSoundscape {
    constructor() {
        // Initializing HTML5 Audio handles mapped to public asset distribution nodes
        this.hum = new Audio("audio/boot-hum.mp3");
        this.chime = new Audio("audio/boot-chime.mp3");

        // Set baseline characteristics for background loop layer
        this.hum.loop = true;
        this.hum.volume = 0.15; // Start low to allow dynamic ramping via boot-lines

        // Set execution characteristics for handoff flare layer
        this.chime.volume = 0.65;
    }

    /**
     * Start the low-frequency background oscillator wave
     */
    start() {
        this.hum.currentTime = 0;
        this.hum.play().catch(() => {
            // Catches browser security constraints if user interaction hasn't happened yet
            console.log("[WARN] Soundscape playback deferred awaiting interaction thread.");
        });
    }

    /**
     * Trigger clean auditory fade-out and handoff to the infinite canvas sound layer
     */
    stop() {
        this.fadeOut(this.hum, 800);
        // Offset chime slightly to let it puncture the dissolving hum cleanly
        setTimeout(() => {
            this.chime.play().catch(() => {});
        }, 300);
    }

    /**
     * Procedural volume step reduction utility
     */
    fadeOut(audioTrack, durationMs) {
        const stepIntervalMs = 50;
        const TotalSteps = durationMs / stepIntervalMs;
        const volumeReductionPerStep = audioTrack.volume / TotalSteps;

        const fadeTimer = setInterval(() => {
            audioTrack.volume = Math.max(0, audioTrack.volume - volumeReductionPerStep);
            
            if (audioTrack.volume <= 0) {
                clearInterval(fadeTimer);
                audioTrack.pause();
            }
        }, stepIntervalMs);
    }
}

