import { OrchestrationLayer } from "../subsystems/precog-runtime/precog-orchestration-layer.js";

export const EventStream = {
  emit: OrchestrationLayer.emit,
  subscribe: OrchestrationLayer.subscribe
};
