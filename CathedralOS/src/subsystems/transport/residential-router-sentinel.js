/**
 * @file residential-router-sentinel.js
 * @subsystem Network_Demuxer / Spatial_Layout
 * @protocol CATHEDRALOS-PRIME-0x42
 * @status OPERATIONAL
 * 
 * "We are mapping the layout of the kingdom based on appliance telemetry. 
 *  Microwaves to the North-West, laundry to the depths."
 */

export class ResidentialRouterSentinel {
  /**
   * @param {Object} spatialNodeManager - The engine responsible for assigning grid coordinates.
   * @param {Object} zoomEngine - The ZUI camera engine for triggering fly-tos on high-priority anomalies.
   */
  constructor(spatialNodeManager, zoomEngine) {
    this.spatialManager = spatialNodeManager;
    this.zoomEngine = zoomEngine;
    
    // Sector map assigning signature profiles to explicit spatial territories
    this.sectorMap = {
      'MICROWAVE_HUM_2_4GHZ':      { x: -5000, y: 5000,  sector: 'KITCHEN_HEAVY_RF' },
      'SMART_FRIDGE_RECIPE_PING': { x: -2500, y: 2500,  sector: 'KITCHEN_LOGISTICS' },
      'BABY_MONITOR_STATIC_LOOP':  { x: 5000,  y: -5000, sector: 'NURSERY_DMZ' },
      'LAUNDRY_LOAD_BALANCER_VIBE': { x: 0,     y: -10000, sector: 'BASEMENT_CORE' }
    };
  }

  /**
   * Ingests a masked packet from the precog bus and routes it spatially.
   * @param {Object} maskedPacket - The packet produced by DomesticSignalMask.
   */
  routeIncomingPacket(maskedPacket) {
    const signature = maskedPacket.signature || 'MICROWAVE_HUM_2_4GHZ';
    const mapping = this.sectorMap[signature] || { x: 0, y: 0, sector: 'UNKNOWN_HALLWAY' };

    // Apply hardware gain modifier to the node's visual scale or radius
    const nodeRadius = 15 * (maskedPacket.gain || 1.0);

    // Inject into the spatial layout engine
    const node = this.spatialManager.createNode({
      id: `node_${maskedPacket.timestamp}_${Math.floor(Math.random() * 1000)}`,
      targetX: mapping.x + (Math.random() * 200 - 100), // Add minor variance to avoid stacking
      targetY: mapping.y + (Math.random() * 200 - 100),
      radius: nodeRadius,
      metadata: {
        signature: signature,
        sector: mapping.sector,
        timestamp: maskedPacket.timestamp,
        obfuscated: true
      }
    });

    // If it's a high-severity packet, force the Zoom Engine to snap to the sector immediately
    if (maskedPacket.severity === 'critical' || maskedPacket.severity === 'high') {
      this.zoomEngine.flyTo({
        x: mapping.x,
        y: mapping.y,
        duration: 800, // Fast frame interpolation
        reason: `CRITICAL_DOMESTIC_ANOMALY_IN_${mapping.sector}`
      });
    }

    return node;
  }
}

