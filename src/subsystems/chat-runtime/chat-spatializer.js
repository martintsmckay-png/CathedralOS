// src/subsystems/chat-runtime/chat-spatializer.js
// CathedralOS Native Module — Memory-to-Geometry Adapter

/**
 * Transforms the hierarchical memory blocks into spatial coordinate payloads.
 * Maps Layer 1 (Continents), Layer 2 (Regions), and Layer 3 (Streets).
 */
export function spatializeChatHierarchy(hierarchy = []) {
  const nodes = [];
  let summaryIndex = 0;

  for (const summary of hierarchy) {
    // 1. Position Continents via angular distribution field
    const angleOffset = summaryIndex * 0.8;
    const summaryX = Math.cos(angleOffset) * 1200;
    const summaryY = Math.sin(angleOffset) * 1200;
    const summaryId = `summary_${summaryIndex}`;

    nodes.push({
      id: summaryId,
      type: 'summary',
      layer: 1,
      x: summaryX,
      y: summaryY,
      zMin: 1.0,
      zMax: 3.0,
      title: summary.title || 'Macro Continent Summary',
      content: summary.text || '',
      parentId: null,
      children: []
    });

    const clusters = summary.children || [];
    clusters.forEach((cluster, clusterIndex) => {
      // 2. Position Regions orbiting their local parent Continent core
      const clusterAngle = (Math.PI * 2 * clusterIndex) / Math.max(1, clusters.length);
      const clusterX = summaryX + Math.cos(clusterAngle) * 350;
      const clusterY = summaryY + Math.sin(clusterAngle) * 350;
      const clusterId = `cluster_${summaryIndex}_${clusterIndex}`;

      nodes.push({
        id: clusterId,
        type: 'cluster',
        layer: 2,
        x: clusterX,
        y: clusterY,
        zMin: 3.0,
        zMax: 7.0,
        title: cluster.title || 'Thematic Chapter Node',
        content: cluster.text || '',
        parentId: summaryId,
        children: []
      });

      const messages = cluster.messages || [];
      messages.forEach((msg, msgIndex) => {
        // 3. Position Streets (Raw Messages) in structured, linear matrix bands below clusters
        const mx = clusterX + (msgIndex % 4) * 180 - 270;
        const my = clusterY + Math.floor(msgIndex / 4) * 90 + 100;

        nodes.push({
          id: msg.id || `msg_${summaryIndex}_${clusterIndex}_${msgIndex}`,
          type: 'message',
          layer: 3,
          x: mx,
          y: my,
          zMin: 7.0,
          zMax: Infinity,
          title: msg.name || msg.role || 'operator_terminal',
          content: msg.content || '',
          parentId: clusterId,
          children: []
        });
      });
    });

    summaryIndex++;
  }

  return nodes;
}

