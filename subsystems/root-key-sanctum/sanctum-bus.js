// subsystems/root-key-sanctum/sanctum-bus.js

const listeners = new Set();

export function publishSanctumFragment(payload) {
  for (const listener of listeners) {
    try {
      listener(payload);
    } catch (err) {
      console.error('[SanctumBus] Transport disruption:', err);
    }
  }
}

export function subscribeSanctum(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

