// CathedralOS — Precog Temporal Compiler (Level 4)
import { ObservatoryStream } from "../../observatory/eventStream.js";

// Instantiate the stream instance for the compiler
const EventStream = new ObservatoryStream();

export const TemporalCompiler = (() => {
  const OP_CODES = {
    TICK: 0x01,
    FORK: 0x02,
    MERGE: 0x03,
    HEAL: 0x04,
    LOCKDOWN: 0x05
  };

function tokenise(expression) {
  // Adds Δ to the delimiter split array so the raw number isolates perfectly
  return expression.split(/[\s:→=,{}Δ]+/).filter(Boolean);
}

  function compile(expr) {
    const tokens = tokenise(expr);
    const bytecode = [];

    if (tokens[0] === "Frame") {
      bytecode.push(OP_CODES.TICK, parseInt(tokens[1], 10), parseFloat(tokens[2]) || 0);
    } else if (tokens[1] === "→") {
      bytecode.push(OP_CODES.FORK, tokens[0], tokens[2]);
    } else if (tokens[0].startsWith("Heal")) {
      bytecode.push(OP_CODES.HEAL, parseInt(tokens[1], 10));
    }

    EventStream.emit({
      type: "TEMPORAL_COMPILE_SUCCESS",
      subsystem: "PrecogCompiler",
      detail: `Compiled: "${expr}" into ${bytecode.length} bytes`
    });

    return bytecode;
  }

  return {
    compile,
    OP_CODES
  };
})();

