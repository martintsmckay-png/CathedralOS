# Precog Runtime Architecture Contract v1.0

## Ownership Boundaries

### 1. SpatialNodeManager
* **Responsibility:** Canonical data layer and spatial source of truth.
* **State:** Tracks all node positions, hierarchy levels, structural relationships, and relational edges.
* **Exposes:** `loadTopology()`, `getVisibleNodes()`, `getVisibleEdges()`, `hitTest()`.
* **Constraint:** Zero rendering or DOM knowledge.

### 2. ZoomEngine
* **Responsibility:** Camera transformation matrix and rendering loop authority.
* **State:** Tracks global viewport viewport camera coordinates (`x`, `y`, `z`).
* **Exposes:** `panBy()`, `zoomAt()`, `focusNode()`, `renderGrid()`, `renderNodes()`, `renderEdges()`.
* **Constraint:** Consumes data solely from `SpatialNodeManager`. Maintains no parallel node arrays.

### 3. CanvasViewportController (Migrated from FabricCanvasSetup)
* **Responsibility:** Viewport interaction layer and input translation.
* **State:** Tracks mouse down/up dragging states and pointer positions.
* **Exposes:** `initListeners()`, `resizeCanvas()`, `screenToWorld()`.
* **Constraint:** Translates browser events directly to `ZoomEngine` updates. Emits `onNodeSelected(node)`.

### 4. PrecogEngine
* **Responsibility:** Analytical ingestion and timeline state machine.
* **Exposes:** `ingest()`, `_attemptMerges()`.
* **Constraint:** Operates entirely in the background. Completely blind to UI, DOM, or canvas elements.

### 5. PrecogRuntimeOrchestrator
* **Responsibility:** System lifecycle initialization and cross-module synchronization.
* **Exposes:** `mountCanvas()`, `loadSystemTopology()`, `feedStream()`.
* **Constraint:** Orchestration only; contains zero math or drawing implementation.
