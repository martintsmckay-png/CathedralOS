#!/usr/bin/env python3
import argparse
import json
import sys
import time

def stabilize_input(chaos_string, stability_factor):
    """Converts unrefined input turbulence into structure."""
    entropy_score = len(set(chaos_string)) / max(len(chaos_string), 1)
    adjusted_stability = min(1.0, stability_factor + (1.0 - entropy_score) * 0.1)
    
    output_data = {
        "timestamp": int(time.time()),
        "status": "STABILIZED" if adjusted_stability > 0.85 else "TURBULENT",
        "metrics": {
            "input_len": len(chaos_string),
            "calculated_entropy": round(entropy_score, 4),
            "final_stability": round(adjusted_stability, 4)
        },
        "output_backbone": f"STRUCTURAL_BEAM::{hash(chaos_string) & 0xFFFFFFFF:X}"
    }
    return output_data

def main():
    parser = argparse.ArgumentParser(
        description="CathedralOS Amber Core Stabilizer — Converts chaos into architecture."
    )
    parser.add_argument(
        "chaos", 
        type=str, 
        help="The unrefined, high-entropy string input to process."
    )
    parser.add_argument(
        "-s", "--stability", 
        type=float, 
        default=0.92, 
        help="Override the baseline stability factor (default: 0.92)."
    )
    parser.add_argument(
        "-j", "--json", 
        action="store_true", 
        help="Output the telemetry data as raw JSON."
    )

    args = parser.parse_args()

    try:
        telemetry = stabilize_input(args.chaos, args.stability)
        
        if args.json:
            print(json.dumps(telemetry, indent=2))
        else:
            print(f"=== [AMBER CORE DIAGNOSTIC] ===")
            print(f"Status:    {telemetry['status']}")
            print(f"Stability: {telemetry['metrics']['final_stability']}")
            print(f"Backbone:  {telemetry['output_backbone']}")
            
    except Exception as e:
        print(f"Core execution failure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
