// src/subsystems/root-key-sanctum/sanctum-parser.js

export function parseSanctumLeak(rawText, meta = {}) {
  const warnings = [];
  const entities = [];

  const entityPatterns = [
    { name: "Ulises", regex: /Ulises/gi },
    { name: "Gatoten", regex: /Gatoten/gi },
    { name: "Saleh", regex: /Saleh/gi },
    { name: "Paladin", regex: /Paladin/gi },
    { name: "Goblin", regex: /Goblin/gi },
    { name: "Raven", regex: /Raven/gi }
  ];

  entityPatterns.forEach(item => {
    const matches = rawText.match(item.regex);
    if (matches && matches.length > 0) {
      entities.push({
        name: item.name,
        occurrences: matches.length
      });
    }
  });

  // Blast-shield check: identify structural vulnerabilities
  const dangerPatterns = [
    { pattern: /rm\s+-rf/gi, desc: "Destructive file removal (rm -rf)" },
    { pattern: /eval\s*\(/gi, desc: "Dynamic runtime evaluation (eval)" },
    { pattern: /exec\s*\(/gi, desc: "Direct process execution shell escape" }
  ];

  dangerPatterns.forEach(item => {
    if (item.pattern.test(rawText)) {
      warnings.push(item.desc);
    }
  });

  return {
    rawText,
    meta: {
      sourceId: meta.sourceId ?? "7-G_SECTOR_LEAK",
      timestamp: meta.timestamp ?? new Date().toISOString()
    },
    entities,
    warnings
  };
}

