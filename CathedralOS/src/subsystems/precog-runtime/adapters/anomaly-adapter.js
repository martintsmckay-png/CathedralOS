// src/subsystems/precog-runtime/adapters/anomaly-adapter.js
import { precogBus } from '../core-bus.js';


const DEFAULT_SOURCE = 'LOCAL_RUNTIME';
const DEFAULT_SEVERITY = 'info';

function inferSeverity(raw = {}) {
  const text = [
    raw.message,
    raw.error?.message,
    raw.stack,
    raw.type
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

  if (/fatal|panic|crash|uncaught|unhandled/.test(text)) return 'critical';
  if (/error|failed|failure|exception/.test(text)) return 'high';
  if (/warn|warning/.test(text)) return 'medium';
  return DEFAULT_SEVERITY;
}

function inferSignalType(raw = {}) {
  const text = [
    raw.type,
    raw.message,
    raw.error?.message
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

  if (/css|stylesheet|style load/.test(text)) return 'RESOURCE_FAILURE';
  if (/network|fetch|xhr|timeout/.test(text)) return 'NETWORK_ANOMALY';
  if (/render|webgl|canvas/.test(text)) return 'RENDER_FAILURE';
  if (/uncaught|exception|error|panic|crash/.test(text)) return 'RUNTIME_FAILURE';
  return 'ANOMALY_SIGNAL';
}

function buildSummary(raw = {}, signalType) {
  return (
    raw.message ||
    raw.error?.message ||
    raw.detail ||
    raw.type ||
    signalType
  );
}

export function normalizeAnomaly(raw = {}, overrides = {}) {
  const signalType = overrides.signalType || inferSignalType(raw);
  const severity = overrides.severity || inferSeverity(raw);

  return {
    signalType,
    severity,
    source: overrides.source || raw.source || DEFAULT_SOURCE,
    summary: buildSummary(raw, signalType),
    stack: raw.stack || raw.error?.stack || null,
    metadata: {
      filename: raw.filename || null,
      lineno: raw.lineno ?? null,
      colno: raw.colno ?? null,
      code: raw.code || null,
      context: raw.context || null,
      originalType: raw.type || null,
      ...raw.metadata
    },
    raw,
    ts: new Date().toISOString()
  };
}

/**
 * Attach browser-side listeners and route them into the bus.
 * Safe to call in browser contexts; no-op in non-browser environments.
 */
export function attachGlobalAnomalyListeners(bus, options = {}) {
  if (typeof window === 'undefined' || !bus) return () => {};

  const unbinders = [];

  const onError = (event) => {
    const normalized = normalizeAnomaly({
      type: 'window.error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error,
      stack: event.error?.stack,
      source: options.source || 'WINDOW'
    });

    bus.publish('anomaly', normalized);
  };

  const onUnhandledRejection = (event) => {
    const reason = event.reason || {};
    const normalized = normalizeAnomaly({
      type: 'unhandledrejection',
      message: reason.message || String(reason),
      error: reason,
      stack: reason.stack,
      source: options.source || 'PROMISE'
    });

    bus.publish('anomaly', normalized);
  };

  window.addEventListener('error', onError);
  window.addEventListener('unhandledrejection', onUnhandledRejection);

  unbinders.push(() => window.removeEventListener('error', onError));
  unbinders.push(() => window.removeEventListener('unhandledrejection', onUnhandledRejection));

  return () => {
    unbinders.forEach(fn => fn());
  };
}
