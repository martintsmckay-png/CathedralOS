// src/subsystems/precog-runtime/spatial-node-manager.js
// CathedralOS Native Module — Fractal Memory Spatialize Bridge

const LEVEL_LAYOUT = {
  0: { radius: 180, label: 'session' },
  1: { radius: 420, label: 'theme' },
  2: { radius: 760, label: 'message' }
};

const LEVEL_ZOOM_TARGETS = {
  0: 1.8,
  1: 4.5,
  2: 9.0
};

function polarToCartesian(angle, radius) {
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius
  };
}

function estimateNodeSize(text = '', level = 0) {
  const normalized = String(text || '');
  const base = level === 0 ? 140 : level === 1 ? 90 : 50;
  const width = Math.max(base, Math.min(280, normalized.length * 6));
  const height = level === 2 ? 36 : 56;
  return { width, height };
}

export class SpatialNodeManager {
  constructor() {
    this.nodes = [];
    this.nodeIndex = new Map();
  }

  /**
   * Clear active coordinate memory buffers
   */
  clear() {
    this.nodes = [];
    this.nodeIndex.clear();
  }

  /**
   * Transforms hierarchical memory blocks into polar-projected spatial coordinates
   * Expected block shape:
   * { id, level, summary, content, title, parentId, lastMessageSummarizedId }
   */
  populateFromHierarchy(blocks = []) {
    this.clear();

    if (!Array.isArray(blocks) || blocks.length === 0) {
      return this.nodes;
    }

    const grouped = new Map();

    for (const block of blocks) {
      if (!block || typeof block !== 'object') continue;

      const level = Number(block.level ?? 2);
      if (!grouped.has(level)) {
        grouped.set(level, []);
      }
      grouped.get(level).push(block);
    }

    // Sort levels numerically so rendering/layout remains deterministic
    const sortedLevels = [...grouped.entries()].sort((a, b) => a[0] - b[0]);

    for (const [level, items] of sortedLevels) {
      const layout = LEVEL_LAYOUT[level] || LEVEL_LAYOUT[2];
      const count = Math.max(1, items.length);

      items.forEach((block, index) => {
        const angle = (Math.PI * 2 * index) / count;
        const jitter = level === 2 ? (index % 7) * 12 : 0;
        const radius = layout.radius + jitter;
        const pos = polarToCartesian(angle, radius);

        const text =
          block.summary ||
          block.content ||
          block.title ||
          `Node ${block.id || index}`;

        const size = estimateNodeSize(text, level);

        const node = {
          id:
            block.id ||
            block.lastMessageSummarizedId ||
            `node_${level}_${index}`,
          parentId: block.parentId || null,
          level,
          text,
          raw: block,
          x: pos.x,
          y: pos.y,
          width: size.width,
          height: size.height,
          targetZoom: LEVEL_ZOOM_TARGETS[level] || LEVEL_ZOOM_TARGETS[2]
        };

        this.nodes.push(node);
        this.nodeIndex.set(node.id, node);
      });
    }

    return this.nodes;
  }

  /**
   * Level-of-detail visibility filter aligned to ZoomEngine thresholds
   */
  getVisibleNodes(currentZ) {
    if (currentZ < 3) {
      return this.nodes.filter((n) => n.level === 0);
    }

    if (currentZ < 7) {
      return this.nodes.filter((n) => n.level <= 1);
    }

    return this.nodes;
  }

  /**
   * Hit-test a world-space coordinate against visible node bounds
   */
  hitTest(worldX, worldY, currentZ) {
    const visible = this.getVisibleNodes(currentZ);

    for (let i = visible.length - 1; i >= 0; i--) {
      const n = visible[i];
      const left = n.x - n.width / 2;
      const right = n.x + n.width / 2;
      const top = n.y - n.height / 2;
      const bottom = n.y + n.height / 2;

      if (
        worldX >= left &&
        worldX <= right &&
        worldY >= top &&
        worldY <= bottom
      ) {
        return n;
      }
    }

    return null;
  }
}
