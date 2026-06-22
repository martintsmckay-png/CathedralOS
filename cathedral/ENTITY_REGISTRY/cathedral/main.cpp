#include <iostream>
#include <string>
#include <cstdlib>

// ============================================================================
// 1. IDENTITY & STATE LAYER
// ============================================================================
enum class SceneType {
    HOMEBASE,
    FIELD,
    OBSERVATORY,
    LAB
};

struct SystemState {
    std::string name = "Martin Kessler";
    std::string callsign = "Steward Pilot";
    std::string version = "1.0";
    std::string entityClass = "Human Operator";
    std::string registryID = "SP-001";
    std::string primaryDomain = "Cathedral Engine";
    std::string verdict = "STABLE";
    int loopDepth = 0;
    std::string driftLevel = "LOW";
};

// ============================================================================
// 2. UNIFIED SURFACE LAYER (TEXT-MODE CONSOLE)
// ============================================================================
class StewardConsole {
public:
    StewardConsole() = default;

    void Render(const SystemState& state, SceneType currentScene) {
        // Clear the Termux screen and home the cursor using standard ANSI codes
        std::cout << "\033[2J\033[1;1H";

        // Draw Frame Border
        std::cout << "==================================================\n";
        std::cout << "       CATHEDRAL ENGINE v1.0 // TERMINAL CONSOLE  \n";
        std::cout << "==================================================\n\n";

        // Panel One: Identity
        std::cout << " [HOME BASE CONSOLE] \n";
        std::cout << " ----------------------------------\n";
        std::cout << "  Operator : " << state.name << "\n";
        std::cout << "  Callsign : " << state.callsign << "\n";
        std::cout << "  Domain   : " << state.primaryDomain << "\n";
        // ANSI escape for green text if STABLE
        if (state.verdict == "STABLE") {
            std::cout << "  Verdict  : \033[32m" << state.verdict << "\033[0m\n\n";
        } else {
            std::cout << "  Verdict  : \033[31m" << state.verdict << "\033[0m\n\n";
        }

        // Panel Two: Entity Registry
        std::cout << " [ACTIVE REGISTRY] \n";
        std::cout << " ----------------------------------\n";
        std::cout << "  [+] Steward Pilot\n";
        std::cout << "  [+] Auditor Raven\n";
        std::cout << "  [+] Debugging Kitten\n";
        std::cout << "  [+] Chaos Goblin\n\n";

        // Panel Three: System Overlay
        std::cout << " [ENGINE STATUS] \n";
        std::cout << " ----------------------------------\n";
        std::cout << "  Scene    : " << SceneName(currentScene) << "\n";
        std::cout << "  FPS      : \033[32m60 (Fixed Text Mode)\033[0m\n";
        std::cout << "  Depth    : " << state.loopDepth << "\n";
        std::cout << "  Quests   : 3 Active\n\n";

        // Panel Four: Navigation Router
        std::cout << " [NAVIGATION ROUTER] \n";
        std::cout << " ----------------------------------\n";
        std::cout << "  [1] Home Base\n";
        std::cout << "  [2] Field Router\n";
        std::cout << "  [3] Observatory\n";
        std::cout << "  [4] Laboratory\n";
        std::cout << "  [q] Shutdown Core Console\n";
        std::cout << "==================================================\n";
    }

private:
    std::string SceneName(SceneType type) {
        switch (type) {
            case SceneType::HOMEBASE:    return "\033[36mHOME_BASE\033[0m";
            case SceneType::FIELD:       return "\033[32mFIELD_ZONE\033[0m";
            case SceneType::OBSERVATORY: return "\033[34mOBSERVATORY\033[0m";
            case SceneType::LAB:         return "\033[31mLABORATORY\033[0m";
            default:                     return "UNKNOWN_NODE";
        }
    }
};

// ============================================================================
// 3. MAIN RUNTIME EXECUTION
// ============================================================================
int main() {
    SystemState systemState;
    StewardConsole console;
    SceneType currentScene = SceneType::HOMEBASE;
    char input = ' ';

    while (input != 'q' && input != 'Q') {
        // Draw the console based on the current state
        console.Render(systemState, currentScene);
        
        // Quiet validation marker at the bottom prompt
        std::cout << "\n[SYSTEM SAFE] Select route (1-4) or 'q' to exit: ";
        std::cin >> input;

        // Route evaluation
        switch (input) {
            case '1': currentScene = SceneType::HOMEBASE; break;
            case '2': currentScene = SceneType::FIELD; break;
            case '3': currentScene = SceneType::OBSERVATORY; break;
            case '4': currentScene = SceneType::LAB; break;
            default:  break; // Ignore any other input keystrokes gently
        }
    }

    // Clean terminal exit behavior
    std::cout << "\nConsole connection closed. Core remains anchored.\n";
    return 0;
}

