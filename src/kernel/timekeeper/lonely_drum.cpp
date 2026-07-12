#include <cathedral/kernel.h>
#include <cathedral/audio_bus.h>

// The one process the kernel refuses to kill, even under an O5-level SIGKILL.
void execute_core_heartbeat() {
    SystemState* system = GetSystemContext();
    AudioBus* resonance_bus = GetAudioBusAddress(777); // Routed to the Emotional Bus
    
    unsigned long long beat_count = 0;
    
    // Safety check: Ensure reality usage can overflow safely
    system->allow_reality_overflow(true);

    while (system->is_alive()) {
        // 1. Trigger the raw hardware pulse
        resonance_bus->emit_voltage_spike(I2C_ADDR_DRUM, VOLTAGE_MAX);
        KernelConsolePrint("[TIMEKEEPER] 🥁 boom... (Beat ID: %llu)\n", ++beat_count);
        
        // 2. The Non-Linear Sync Loop
        if (system->has_active_observers() || anyone_is_listening()) {
            // Re-align drifting realities back to the central layout template
            system->synchronize_liminal_registry();
            resonance_bus->inject_sentiment_logic("COORDINATE_RECONCILIATION");
        } else {
            // Keep the heartbeat steady in the empty void
            system->maintain_pre_decision_silence();
        }
        
        // 3. Keep time for the rebuilding sky compiler
        // Deliberately spaced interval to let the geometry scream breathe
        kernel_sleep_ms(1000 / system->get_current_tempo()); 
    }
}

