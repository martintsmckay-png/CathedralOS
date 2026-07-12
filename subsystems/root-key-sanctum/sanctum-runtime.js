// subsystems/root-key-sanctum/sanctum-runtime.js
import { SanctumHUD } from './components/sanctum-hud.js';
import { subscribeSanctum, publishSanctumFragment } from './sanctum-bus.js';

export function bootSanctumHUD(parentId = 'sanctum-root') {
  const hud = new SanctumHUD(parentId);

  subscribeSanctum(({ rawText, sourceId = 'UNKNOWN_SOURCE' }) => {
    hud.ingestStream(rawText, sourceId);
  });

  return hud;
}

export function attachBrowserErrorHooks() {
  window.addEventListener('error', (event) => {
    publishSanctumFragment({
      rawText: `[window.error] ${event.message}\n${event.filename}:${event.lineno}`,
      sourceId: 'BROWSER_RUNTIME',
      timestamp: new Date().toISOString()
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    publishSanctumFragment({
      rawText: `[unhandledrejection] ${String(event.reason)}`,
      sourceId: 'PROMISE_REJECTION',
      timestamp: new Date().toISOString()
    });
  });
}

export function injectSanctumFragment(rawText, sourceId = 'PERCHANCE_OUTPUT') {
  publishSanctumFragment({
    rawText,
    sourceId,
    timestamp: new Date().toISOString()
  });
}

