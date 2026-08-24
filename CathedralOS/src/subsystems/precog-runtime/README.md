# Precog Runtime

A speculative runtime subsystem for CathedralOS-style anomaly handling and fork/merge state exploration.

## Modules

- `core-bus.js`
  - Minimal event bus for anomaly signals.

- `adapters/anomaly-adapter.js`
  - Normalizes browser/runtime anomalies into a consistent event shape.

- `moonwalk-core.js`
  - Pure channel creation, fork, and merge logic.

- `precog-engine.js`
  - Runtime orchestrator that evaluates anomalies and manages speculative lanes.

- `precog-sanctum-bridge.js`
  - Mounts `PrecogEngine` to `SanctumHUD`.

- `test-events.js`
  - Browser-side test injector for runtime verification.

## Event shape

Precog runtime emits structured ledger entries:

```js
{
  source: 'PRECOG_RUNTIME',
  type: 'FORK_TRIGGERED',
  severity: 'high',
  summary: 'Fork triggered on phi_0',
  details: {
    channelId: 'phi_0',
    childId: 'phi_0::alt',
    driftScore: 0.88
  },
  ts: '2026-07-02T...'
}
