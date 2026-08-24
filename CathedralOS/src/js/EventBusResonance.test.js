// src/js/EventBusResonance.test.js
// CathedralOS v2.2 - The Defended Prototype Loop

class EventBus {
    constructor() {
        this.listeners = {};
    }

    on(event, fn) {
        // Safe nullish coalescing assignment for event arrays
        (this.listeners[event] ??= []).push(fn);
    }

    emit(event) {
        // Graceful fallback to empty array if no tracking exist
        (this.listeners[event] || []).forEach(fn => fn());
    }
}

const bus = new EventBus();

// Binding the core atmospheric metadata to the bus addresses
bus.on("LonelyDrum", () => console.log("🥁 boom..."));
bus.on("Geometry",   () => console.log("🏜️ geometry screaming..."));
bus.on("Choir",      () => console.log("🎶 harmony online..."));

console.log("[RUNTIME] Starting CathedralOS Barebone Prototype...");
console.log("[NOTICE]  The renderer is dead. The spreadsheet is #REF!. The heartbeat remains.");

// Triggering the initial atmospheric baseline setup
bus.emit("Geometry");
bus.emit("Choir");

// The Permanent Timekeeper Clock Cycle
setInterval(() => {
    bus.emit("LonelyDrum");
}, 1000);

