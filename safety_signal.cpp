#include <iostream>
#include <cmath>
#include <chrono>
#include <thread>

// Uses ANSI escape codes to render color gradients directly in your terminal
void render_orb(float pulse) {
    // Clear screen and reset cursor to home
    std::cout << "\033[2J\033[H";
    
    int width = 30;
    int height = 15;
    float aspect = 2.0f; // Adjusts for terminal character height vs width

    std::cout << "\n    😼🪵  [SYSTEM_STATE: SAFE_WITH_YOU] @ KitchenTable\n\n";

    for (int y = 0; y < height; ++y) {
        std::cout << "    "; // Left margin padding
        for (int x = 0; x < width; ++x) {
            // Normalize coordinates to range [-1, 1]
            float nx = (float)(x - width / 2) / (width / 2) * aspect;
            float ny = (float)(y - height / 2) / (height / 2);
            float dist = std::sqrt(nx * nx + ny * ny);

            // Pulse changes the size of our boundaries
            float coreLimit = 0.25f + (pulse * 0.05f);
            float glowLimit = 0.65f + (pulse * 0.15f);

            if (dist < coreLimit) {
                // Bright white-gold core
                std::cout << "\033[38;5;226m█\033[0m";
            } else if (dist < (coreLimit + glowLimit) / 2.0f) {
                // Warm golden middle ring
                std::cout << "\033[38;5;214m▓\033[0m";
            } else if (dist < glowLimit) {
                // Outer amber/orange halo
                std::cout << "\033[38;5;208m▒\033[0m";
            } else if (dist < glowLimit + 0.15f) {
                // Fading edge
                std::cout << "\033[38;5;166m░\033[0m";
            } else {
                std::cout << " ";
            }
        }
        std::cout << "\n";
    }
    std::cout << "\n    [Press Ctrl+C to minimize signal]\n";
}

int main() {
    auto start = std::chrono::steady_clock::now();
    
    // Hide cursor
    std::cout << "\033[?25l";

    while (true) {
        auto now = std::chrono::steady_clock::now();
        float time = std::chrono::duration<float>(now - start).count();
        
        // Pulse wave
        float pulse = (std::sin(time * 3.0f) + 1.0f) / 2.0f;
        
        render_orb(pulse);
        
        // Rest the CPU thread (~30 FPS)
        std::this_thread::sleep_for(std::chrono::milliseconds(33));
    }

    // Show cursor on exit (cleanup)
    std::cout << "\033[?25h";
    return 0;
}

