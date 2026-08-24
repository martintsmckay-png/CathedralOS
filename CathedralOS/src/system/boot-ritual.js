import { BootLines } from "./boot-lines.js";
import { BootSoundscape } from "./boot-soundscape.js";

/**
 * Orchestrates the full-screen startup ceremony, binding diagnostics,
 * soundscapes, and the instant-bypass mercy valve.
 * 
 * @param {Function} onComplete Callback execution thread to initialize the main runtime.
 */
export function runBootRitual(onComplete) {
    const overlay = document.getElementById("cathedral-boot");
    const sound = new BootSoundscape();
    const linesGen = new BootLines();

    // Graceful pass-through fallback if the overlay node is physically missing from the DOM
    if (!overlay) {
        if (onComplete) onComplete();
        return;
    }

    // Wake up the low-frequency ambient loop
    sound.start();
    let ritualActive = true;

    /**
     * Cleanly dismantles the ritual layout and commands a safe handoff to main.js
     */
    function finishRitual() {
        if (!ritualActive) return;
        ritualActive = false;

        // Cease audio loops and fire the completion chime
        sound.stop();
        
        // Dissolve the visual interface wrapper
        overlay.style.transition = "opacity 800ms ease";
        overlay.style.opacity = "0";

        setTimeout(() => {
            overlay.remove();
            if (onComplete) onComplete();
        }, 800);
    }

    /**
     * Mercy Valve: Triggers instantaneous bypass sequence when any key is pressed
     */
    function skipBoot() {
        finishRitual();
        window.removeEventListener("keydown", skipBoot);
    }
    window.addEventListener("keydown", skipBoot);

    // Grab existing static line containers in the DOM markup to inject text into
    const staticLines = Array.from(overlay.querySelectorAll(".boot-line"));
    let lineIndex = 0;

    // Asynchronous diagnostic loop execution
    (async () => {
        for await (const lineState of linesGen.generate()) {
            if (!ritualActive) return;

            // If we run out of physical line container structures, break out
            const el = staticLines[lineIndex];
            if (!el) break;

            // Update DOM text string content
            el.textContent = `[ INIT ] ${lineState.text}`;
            el.className = "boot-line visible"; // Ensure transition styling fires
            
            // Apply dynamic visual indicator styling classes based on step status
            if (lineState.status === "READY") {
                el.classList.add("ready");
            } else if (lineState.status === "DELAYED") {
                el.classList.add("delayed");
            }

            // Execute dynamic volume ramping step as the liturgy progresses
            if (sound.hum && lineState.status === "PENDING") {
                sound.hum.volume = Math.min(0.6, sound.hum.volume + 0.04);
            }

            // Only advance line layout indices when moving past an un-mutated base state
            if (lineState.status !== "PENDING") {
                lineIndex++;
                await new Promise(resolve => setTimeout(resolve, 250));
            }
        }
        
        // Finalize state execution cleanly after breathing room
        setTimeout(finishRitual, 500);
    })();
}

