// subsystems/root-key-sanctum/sanctum-parser.js

const DEFAULT_ENTITY_PATTERNS = [
  { name: 'Ulises', regex: /\bUlises\b/gi },
  { name: 'Gatoten', regex: /\bGatoten\b/gi },
  { name: 'Saleh', regex: /\bSaleh\b/gi },
  { name: 'Paladin', regex: /\bPaladin\b/gi },
  { name: 'Goblin', regex: /\bGoblins?\b/gi },
  { name: 'Raven', regex: /\bRaven\b/gi },
  { name: 'CathedralOS', regex: /\bCathedralOS\b/gi }
];

const DEFAULT_WARNING_PATTERNS = [
  { regex: /\brm\s+-rf\b/gi, desc: 'Destructive file removal (rm -rf)' },
  { regex: /\beval\s*\(/gi, desc: 'Dynamic runtime evaluation (eval)' },
  { regex: /\bexec\s*\(/gi, desc: 'Direct process execution shell escape' }
];

export function parseSanctumLeak(rawText, meta = {}) {
  const warnings = [];
  const entities = [];
  const safeText = typeof rawText === 'string' ? rawText : String(rawText ?? '');

  DEFAULT_ENTITY_PATTERNS.forEach(item => {
    const matches = safeText.match(item.regex);
    if (matches && matches.length > 0) {
      entities.push({ name: item.name, occurrences: matches.length });
    }
  });

  DEFAULT_WARNING_PATTERNS.forEach(item => {
    if (item.regex.test(safeText)) {
      warnings.push(item.desc);
    }
  });

  return {
    rawText: safeText,
    meta: {
      sourceId: meta.sourceId ?? '7-G_SECTOR_LEAK',
      timestamp: meta.timestamp ?? new Date().toISOString()
    },
    entities,
    warnings
  };
}

