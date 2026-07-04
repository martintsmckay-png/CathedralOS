/**
 * CathedralOS Core Subsystem: RitualConsole (v3.0)
 * Context: Alpha Base / Altar Liturgy Ticker & Signal Watch
 * Design Protocol: Multi-category event filtering with priority stream tracking
 */

import { precogBus } from '../broker/precog-bus.js';

export class RitualConsole {
    constructor() {
        this.el = document.getElementById("ritual-console");
        this.maxLines = 200;

        // Reactive stream filters to isolate systemic signals
        this.filters = {
            transport: true,
            precog: true,
            spatial: true,
            hud: true,
            zoom: true,
            misc: true
        };

        // Initialize user filter dashboard layout
        this.addFilterBar();

        // Subscribe to global telemetry spine
        precogBus.subscribe("*", (payload, topic) => {
            this.log(topic, payload);
        });
    }

    /**
     * Spawns clickable diagnostic toggles above the console output stream
     */
    addFilterBar() {
        if (!this.el) return;

        const bar = document.createElement("div");
        bar.className = "ritual-filter-bar";
        bar.style.cssText = `
            display: flex;
            gap: 8px;
            padding: 6px 8px;
            background: rgba(20, 20, 40, 0.9);
            border-bottom: 1px solid rgba(98, 114, 164, 0.4);
            font-family: monospace;
            font-size: 11px;
            position: sticky;
            top: 0;
            z-index: 10;
        `;

        Object.keys(this.filters).forEach(cat => {
            const btn = document.createElement("button");
            btn.textContent = `[${cat.toUpperCase()}]`;
            btn.style.cssText = `
                background: ${this.filters[cat] ? "#50fa7b" : "#44475a"};
                color: ${this.filters[cat] ? "#282a36" : "#f8f8f2"};
                border: none;
                padding: 2px 6px;
                font-family: monospace;
                font-weight: bold;
                cursor: pointer;
                border-radius: 3px;
                transition: all 0.2s ease;
            `;

            btn.onclick = () => {
                this.filters[cat] = !this.filters[cat];
                btn.style.background = this.filters[cat] ? "#50fa7b" : "#44475a";
                btn.style.color = this.filters[cat] ? "#282a36" : "#f8f8f2";
            };

            bar.appendChild(btn);
        });

        // Prepend the toolbar so it locks cleanly to the top of the buffer bounds
        this.el.insertBefore(bar, this.el.firstChild);
    }

    /**
     * Determines which tracking category a topic falls under
     */
    getCategory(topic) {
        if (topic.startsWith("transport.")) return "transport";
        if (topic.startsWith("precog.")) return "precog";
        if (topic.startsWith("spatial.")) return "spatial";
        if (topic.startsWith("hud.")) return "hud";
        if (topic.startsWith("zoom.")) return "zoom";
        return "misc";
    }

    /**
     * Intercepts, filters, parses, and logs systemic signals
     */
    log(topic, payload) {
        const category = this.getCategory(topic);
        if (!this.filters[category]) return;

        // Container references might be child logs beneath the static filter bar
        let outputContainer = this.el.querySelector(".ritual-log-container");
        if (!outputContainer) {
            outputContainer = document.createElement("div");
            outputContainer.className = "ritual-log-container";
            this.el.appendChild(outputContainer);
        }

        const ts = new Date().toISOString().split("T")[1].replace("Z", "");
        const line = document.createElement("div");
        line.className = "ritual-line";
        line.style.fontFamily = "monospace";
        line.style.fontSize = "12px";
        line.style.marginBottom = "3px";

        line.innerHTML = `
            <span class="time" style="color: #6272a4;">[${ts}]</span>
            <span class="topic" style="color: #8be9fd; font-weight: bold;"> ${topic}</span>
            <span class="payload" style="color: #f8f8f2;"> ➜ ${this.formatPayload(payload)}</span>
        `;

        outputContainer.appendChild(line);

        // Keep buffer trimmed
        while (outputContainer.children.length > this.maxLines) {
            outputContainer.removeChild(outputContainer.firstChild);
        }

        // Auto-scroll track
        this.el.scrollTop = this.el.scrollHeight;
    }

    /**
     * Flattens objects and maps ancestry linkages into clear terminal indicators
     */
    formatPayload(payload) {
        if (!payload) return "∅";
        if (typeof payload === 'string') return payload;
        
        // Ancestry-specific parsing rules
        if (payload.parentId && payload.nodeId) {
            return `GENEALOGY: parent=${payload.parentId} ➔ child=${payload.nodeId} ${payload.forkId ? '[BRANCH]' : ''}`;
        }
        
        if (payload.text) return JSON.stringify(payload.text).slice(0, 120);
        if (payload.nodeId) return `node_id=${payload.nodeId}`;
        if (payload.channelId) return `channel=${payload.channelId} drift_score=${payload.driftScore || 0}`;
        
        try {
            return JSON.stringify(payload).slice(0, 160);
        } catch (e) {
            return "[Complex Object System Structure]";
        }
    }
}

