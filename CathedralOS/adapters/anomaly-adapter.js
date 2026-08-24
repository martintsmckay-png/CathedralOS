// src/subsystems/cathedral-core/adapters/anomaly-adapter.js
import { globalBus } from '../core-bus.js';

export function bootAnomalyAdapter() {
  if (typeof window !== 'undefined') {
    // Catch CSS, Script, and Resource Load Failures
    window.addEventListener('error', (event) => {
      if (event.target && (event.target.tagName === 'LINK' || event.target.tagName === 'SCRIPT')) {
        globalBus.publish('INTUITION_SIGNAL', {
          type: 'resource-load-error',
          payload: {
            element: event.target.tagName.toLowerCase(),
            url: event.target.src || event.target.href,
            message: 'Style/Script load error triggered reverse-entropy trace'
          }
        });
      }
    }, true);

    // Catch Unhandled Promise Rejections
    window.addEventListener('unhandledrejection', (event) => {
      globalBus.publish('INTUITION_SIGNAL', {
        type: 'runtime-exception',
        payload: {
          reason: String(event.reason),
          message: 'LostInTheSauceException // Parallel state lane execution conflict'
        }
      });
    });
  }
}

