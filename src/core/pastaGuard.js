/**
 * CathedralOS // PastaGuard Core Exception Filter
 * Hardens runtime routing against malformed chaos and undefined state injections.
 */

const PastaGuard = {
    // Standard secure fallback state when incoming data is completely corrupt
    fallbackState: {
        status: "STABLE",
        message: "PastaGuard intercepted a malformed anomaly. Framework protected.",
        timestamp: Date.now()
    },

    /**
     * Exception Filter: Validates and sanitizes incoming visitor payloads
     * @param {string|Object} rawPayload - The unchecked incoming data object
     * @returns {Object} Cleaned, safe state object
     */
    filterIncomingPayload(rawPayload) {
        try {
            // Anomaly Check 1: Empty or void payloads
            if (!rawPayload) {
                throw new ReferenceError("Null or undefined payload injection blocked.");
            }

            // Anomaly Check 2: Raw string parsing handling
            let parsed = rawPayload;
            if (typeof rawPayload === 'string') {
                parsed = JSON.parse(rawPayload);
            }

            // Anomaly Check 3: Essential structural keys verification
            if (typeof parsed !== 'object' || parsed === null) {
                throw new TypeError("Payload structural distortion: Expected Object layout.");
            }

            // Enforce clean typing boundaries on expected properties
            return {
                status: String(parsed.status || "UNKNOWN"),
                message: String(parsed.message || "No contextual text provided."),
                timestamp: Number(parsed.timestamp) || Date.now()
            };

        } catch (error) {
            // The Circuit Breaker catches the drop before it bubbles up to break the DOM
            this.logRuntimeAnomaly(error);
            return {
                ...this.fallbackState,
                errorType: error.name,
                errorDetails: error.message
            };
        }
    },

    /**
     * Explicitly records caught runtime errors without halting execution execution loop
     */
    logRuntimeAnomaly(error) {
        console.warn(`[PASTAGUARD EXCEPTION] Bypassed a crash event: ${error.name} -> ${error.message}`);
    }
};

// Export the boundary filter for layout rendering modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PastaGuard;
}

