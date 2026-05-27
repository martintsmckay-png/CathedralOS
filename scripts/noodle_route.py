#!/usr/bin/env python3
import argparse
import json
import sys
import time

def process_tension(log_message, operational_mode):
    """Transforms structural strain into structured, elastic system data."""
    intensity = len(log_message)
    fallback_engaged = intensity > 50
    
    routing_map = {
        "marinara": "ABSORBED_BY_MARINARA_MOAT",
        "ricotta": "DIVERTED_TO_RICOTTA_UNDERTOW",
        "breadstick": "BUFFERED_VIA_BREADSTICK_FALLBACK"
    }
    
    selected_route = routing_map.get(operational_mode, "ROUTING_UNKNOWN")
    if fallback_engaged and operational_mode == "marinara":
        selected_route = routing_map["breadstick"]

    telemetry = {
        "timestamp": int(time.time()),
        "input_signature": log_message[:20] + "..." if len(log_message) > 20 else log_message,
        "assigned_vector": selected_route,
        "load_profile": {
            "initial_strain": intensity,
            "viscosity_index": round(intensity * 1.34, 2),
            "fallback_tripped": fallback_engaged
        }
    }
    return telemetry

def main():
    parser = argparse.ArgumentParser(
        description="CathedralOS Noodle Route CLI — Diverts system strain into comic infrastructure."
    )
    parser.add_argument(
        "tension_log",
        type=str,
        help="The rigid log entry or tension string to process."
    )
    parser.add_argument(
        "-m", "--mode",
        choices=["marinara", "ricotta", "breadstick"],
        default="marinara",
        help="Specify the soft-security diversion destination (default: marinara)."
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output raw structural pipeline telemetry as JSON."
    )

    args = parser.parse_args()

    try:
        telemetry = process_tension(args.tension_log, args.mode)
        
        if args.json:
            print(json.dumps(telemetry, indent=2))
        else:
            print("=== [NOODLE ROUTE INTERCEPT] ===")
            print(f"Log Hook: {telemetry['input_signature']}")
            print(f"Vector:   {telemetry['assigned_vector']}")
            print(f"Strain:   {telemetry['load_profile']['initial_strain']} units")
            
    except Exception as e:
        print(f"Routing module failure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
