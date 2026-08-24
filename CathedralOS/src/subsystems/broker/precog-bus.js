/**
 * CathedralOS Core Subsystem: precogBus Central Spine (v3.0)
 * Context: Alpha Base System Nervous System Axis
 * Design Protocol: Event-driven pub/sub architecture with bounded historical logging
 */

// Global timeline buffer tracking all operational vectors
export const precogTimeline = [];

class PrecogBus {
    constructor() {
        this.subscriptions = new Map();
    }

    /**
     * Subscribes an entry callback handle to a topic string or wildcard string '*'
     */
    subscribe(topic, callback) {
        if (!this.subscriptions.has(topic)) {
            this.subscriptions.set(topic, []);
        }
        this.subscriptions.get(topic).push(callback);
    }

    /**
     * Publishes payload packages down the spine and records them to the history array
     */
    publish(topic, payload) {
        // Record transaction to the timeline cache before processing distribution
        this.recordEvent(topic, payload);

        // 1. Process explicit topic channel distribution
        if (this.subscriptions.has(topic)) {
            this.subscriptions.get(topic).forEach(callback => {
                try { callback(payload, topic); } catch (e) { console.error(e); }
            });
        }

        // 2. Process systemic wildcard '*' listener configurations
        if (this.subscriptions.has("*")) {
            this.subscriptions.get("*").forEach(callback => {
                try { callback(payload, topic); } catch (e) { console.error(e); }
            });
        }
    }

    /**
     * Encapsulates events inside a time-stamped framework frame
     */
    recordEvent(topic, payload) {
        precogTimeline.push({
            topic,
            payload,
            ts: performance.now()
        });

        // Enforce boundary caps to avoid memory leak scenarios over prolonged sessions
        if (precogTimeline.length > 5000) {
            precogTimeline.shift();
        }
    }
}

export const precogBus = new PrecogBus();

