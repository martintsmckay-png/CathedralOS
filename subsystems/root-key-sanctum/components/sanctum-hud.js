// src/subsystems/root-key-sanctum/components/sanctum-hud.js
import { parseSanctumLeak } from '../sanctum-parser.js';
import { extractRelicCommands } from '../sanctum-relic-extractor.js';

export class SanctumHUD {
  constructor(parentElementId) {
    this.parent = document.getElementById(parentElementId);
    this.registry = new Map();
    this.totalRelics = 0;
    this.latestFragment = null;
    this.fractureStatus = "STABLE // 0.1% FRACTURE BALANCED";
  }

  /**
   * Process incoming raw simulation log or leak fragment
   */
  ingestStream(rawText, sourceId = "7-G_SECTOR_LEAK") {
    const parsed = parseSanctumLeak(rawText, { sourceId, timestamp: new Date().toISOString() });
    const relics = extractRelicCommands(parsed);

    // Update entity counts
    parsed.entities.forEach(entity => {
      const current = this.registry.get(entity.name) || 0;
      this.registry.set(entity.name, current + entity.occurrences);
    });

    // Update relic counters
    this.totalRelics += (relics.jsSnippets.length + relics.htmlSnippets.length + relics.shellCommands.length);
    
    // Track latest preview
    this.latestFragment = {
      source: parsed.meta.sourceId,
      preview: parsed.rawText.substring(0, 120) + "...",
      volatility: parsed.warnings.length > 0 ? "CRITICAL // VOLATILE REUSE" : "INSPECT_ONLY // READ_SAFE",
      warnings: parsed.warnings
    };

    this.render();
  }

  render() {
    if (!this.parent) return;

    const entitiesHtml = Array.from(this.registry.entries())
      .map(([name, count]) => `
        <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px dashed #222;">
          <span style="color: #ffd700;">✦ ${name}</span>
          <span style="font-weight: bold; color: #a3b8cc;">[${count} hits]</span>
        </div>
      `).join('');

    this.parent.innerHTML = `
      <div style="background-color: #0d0e12; color: #a3b8cc; font-family: 'Courier New', monospace; border: 2px solid #3a4254; padding: 15px; border-radius: 4px; max-width: 500px;">
        <div style="border-bottom: 2px solid #7f5af0; padding-bottom: 6px; margin-bottom: 12px; font-weight: bold; display: flex; justify-content: space-between;">
          <span style="color: #7f5af0;">🏛️ CATHEDRALOS // ROOT-KEY-SANCTUM</span>
          <span style="color: #2cb67d;">● ONLINE</span>
        </div>

        <div style="margin-bottom: 12px; font-size: 0.9em;">
          <strong>FRACTURE STATUS:</strong> <span style="color: #ffd700;">${this.fractureStatus}</span><br>
          <strong>RECOVERED RELICS:</strong> <span style="color: #50fa7b;">${this.totalRelics} extracted</span>
        </div>

        <div style="margin-bottom: 12px;">
          <div style="font-size: 0.8em; text-transform: uppercase; color: #6272a4; margin-bottom: 4px; font-weight: bold;">Root-Key Registry Indices:</div>
          <div style="background: #14171f; padding: 8px; border-radius: 2px; max-height: 120px; overflow-y: auto;">
            ${entitiesHtml || '<span style="color:#444;">No entities indexed yet.</span>'}
          </div>
        </div>

        ${this.latestFragment ? `
          <div style="border-top: 1px solid #3a4254; padding-top: 10px; font-size: 0.85em;">
            <div style="font-weight: bold; color: #ff5555; margin-bottom: 2px;">LATEST LEDGER FRAGMENT [${this.latestFragment.source}]:</div>
            <div style="background: #050508; padding: 6px; color: #f8f8f2; font-style: italic; margin-bottom: 6px; border-left: 2px solid #ff5555;">
              "${this.latestFragment.preview}"
            </div>
            <div><strong>VAL_METRIC:</strong> ${this.latestFragment.volatility}</div>
            ${this.latestFragment.warnings.length > 0 ? `
              <div style="color: #ff5555; margin-top: 4px; font-size: 0.9em;">
                ⚠️ <strong>WARNING:</strong> ${this.latestFragment.warnings.join(', ')}
              </div>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }
}

