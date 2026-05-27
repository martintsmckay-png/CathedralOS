#!/usr/bin/env python3
import argparse
import json
import sys
import time
import math

def calculate_metrics(runtime_seconds, intensity_level):
    """Calculates operational velocity and tracks the 412Hz resonance variance."""
    base_frequency = 412.0
    # Create a localized wave shift based on operational intensity
    variance = math.sin(runtime_seconds * 0.05) * (intensity_level * 1.85)
    target_resonance = round(base_frequency + variance, 2)
    
    efficiency = max(10.0, 100.0 - (intensity_level * 4.2))
    stability_offset = "OPTIMAL_PURR" if 405.0 <= target_resonance <= 419.0 else "ATTENUATED_PULSE"

    telemetry = {
        "timestamp": int(time.time()),
        "subsystem": "USB-Kitten Daemon Node",
        "telemetry_stream": {
            "monitored_velocity": round(intensity_level * 12.34, 2),
            "resonance_hz": target_resonance,
            "profile": stability_offset
        },
        "system_efficiency_pct": round(efficiency, 1)
    }
    return telemetry

def main():
    parser = argparse.ArgumentParser(
        description="CathedralOS Kitten Metrics Engine — Calculates processing velocity and 412Hz purr profiles."
    )
    parser.add_parser.add_argument(
        "-t", "--time",
        type=int,
        default=120,
        help="Simulated elapsed process runtime in seconds (default: 120)."
    )
    parser.add_parser.add_argument(
        "-v", "--velocity",
        type=int,
        choices=range(1, 11),
        default=5,
        help="Current workspace emotional or technical velocity scale 1-10 (default: 5)."
    )
    parser.add_parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output raw telemetric stream as JSON."
    )

    args = parser.parse_args()

    try:
        telemetry = calculate_metrics(args.time, args.velocity)
        
        if args.json:
            print(json.dumps(telemetry, indent=2))
        else:
            print("=== [DAEMON KITTEN METRICS] ===")
            print(f"Node Status: {telemetry['telemetry_stream']['profile']}")
            print(f"Frequency:   {telemetry['telemetry_stream']['resonance_hz']} Hz")
            print(f"Efficiency:  {telemetry['system_efficiency_pct']}%")
            
    except Exception as e:
        print(f"Metrics engine fault: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
