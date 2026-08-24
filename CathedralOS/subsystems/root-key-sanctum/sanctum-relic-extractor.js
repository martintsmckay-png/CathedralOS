// subsystems/root-key-sanctum/sanctum-relic-extractor.js

export function extractRelicCommands(parsed) {
  const text = parsed.rawText || "";

  const jsSnippets = [...text.matchAll(/```(?:js|javascript)\n([\s\S]*?)```/gi)].map(m => m[1].trim());
  const htmlSnippets = [...text.matchAll(/```html\n([\s\S]*?)```/gi)].map(m => m[1].trim());

  const shellCommands = text
    .split('\n')
    .map(line => line.trim())
    .filter(line => 
      line.startsWith('$ ') || 
      line.startsWith('> ') ||
      /^node\s+/.test(line) ||
      /^npm\s+/.test(line) ||
      /^mkdir\s+/.test(line) ||
      /^nano\s+/.test(line)
    );

  return { jsSnippets, htmlSnippets, shellCommands };
}

