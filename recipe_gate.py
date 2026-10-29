#!/usr/bin/env python3
"""CathedralOS // Sovereign Recipe Gate v3.0

Auditor-grade pantry intelligence for the Sovereign Pie deployment.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

PANTRY_FILE = Path("pantry.json")
SHOPPING_JSON = Path("shopping_list.json")
SHOPPING_CSV = Path("shopping_list.csv")
RESTOCK_LOG = Path("restock_log.jsonl")

SOVEREIGN_PIE = {
    "graham crackers": (200.0, "g"),
    "butter": (100.0, "g"),
    "peanut butter": (500.0, "g"),
    "cream cheese": (250.0, "g"),
    "whipping cream": (500.0, "ml"),
    "powdered sugar": (120.0, "g"),
}

ALIASES = {
    "creamy peanut butter": "peanut butter",
    "smooth peanut butter": "peanut butter",
    "crunchy peanut butter": "peanut butter",
    "icing sugar": "powdered sugar",
    "confectioners sugar": "powdered sugar",
    "heavy cream": "whipping cream",
    "graham crumb": "graham crackers",
    "graham crumbs": "graham crackers",
}

# Exact conversion factors. Ingredient-specific volume-to-mass values are
# deliberately approximations and should be reviewed before production baking.
CONVERSIONS = {
    ("kg", "g"): 1000.0,
    ("g", "kg"): 0.001,
    ("l", "ml"): 1000.0,
    ("ml", "l"): 0.001,
    ("cup", "tbsp"): 16.0,
    ("tbsp", "cup"): 0.0625,
    ("tbsp", "tsp"): 3.0,
    ("tsp", "tbsp"): 1 / 3,
    ("cup peanut butter", "g"): 258.0,
    ("tbsp peanut butter", "g"): 16.0,
    ("cup powdered sugar", "g"): 120.0,
    ("tbsp powdered sugar", "g"): 7.5,
    ("cup butter", "g"): 227.0,
    ("tbsp butter", "g"): 14.0,
    ("cup whipping cream", "ml"): 240.0,
    ("tbsp whipping cream", "ml"): 15.0,
    ("cup cream cheese", "g"): 225.0,
    ("tbsp cream cheese", "g"): 14.0,
    ("cup graham crackers", "g"): 100.0,
}


def normalize(text):
    return " ".join(str(text).lower().replace("-", " ").replace("_", " ").split())


def canonical_name(name):
    return ALIASES.get(normalize(name), normalize(name))


def convert(amount, from_unit, to_unit):
    from_unit, to_unit = normalize(from_unit), normalize(to_unit)
    if from_unit == to_unit:
        return float(amount)
    factor = CONVERSIONS.get((from_unit, to_unit))
    return None if factor is None else float(amount) * factor


def load_json(path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"[AUDITOR ERROR] Could not load {path}: {error}")
        return default


def save_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def load_pantry():
    raw = load_json(PANTRY_FILE, {})
    pantry = {}
    for name, value in raw.items():
        if isinstance(value, dict):
            amount, unit = value.get("amount", 0), value.get("unit", "g")
        else:
            amount, unit = value, "g"
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            print(f"[AUDITOR WARNING] Non-numeric amount for '{name}'; treated as 0.")
            amount = 0.0
        pantry[canonical_name(name)] = {"amount": amount, "unit": normalize(unit)}
    return pantry


def find_duplicates(pantry):
    warnings = []
    for name in pantry:
        canonical = ALIASES.get(normalize(name))
        if canonical and canonical != normalize(name):
            warnings.append((name, canonical))
    return warnings


def merge_duplicates(pantry):
    merged = {}
    for name, item in pantry.items():
        canonical = canonical_name(name)
        if canonical not in merged:
            merged[canonical] = dict(item)
            continue
        existing = merged[canonical]
        converted = convert(item["amount"], item["unit"], existing["unit"])
        if converted is None:
            print(
                f"[AUDITOR WARNING] Cannot merge '{name}' into '{canonical}': "
                f"no conversion from {item['unit']} to {existing['unit']}."
            )
            continue
        existing["amount"] += converted
    return merged


def audit_recipe(recipe, pantry):
    print("\n" + "=" * 52)
    print("SOVEREIGN RECIPE AUDIT")
    print("=" * 52)
    missing = []
    for ingredient, (required, unit) in recipe.items():
        available = 0.0
        if ingredient in pantry:
            item = pantry[ingredient]
            converted = convert(item["amount"], item["unit"], unit)
            if converted is None:
                print(
                    f"[AUDITOR WARNING] Cannot compare '{ingredient}': "
                    f"{item['unit']} cannot convert to {unit}."
                )
            else:
                available = converted
        status = "PASS" if available >= required else "FAIL"
        print(f"\n[{status}] {ingredient}")
        print(f"  Required : {required:.2f} {unit}")
        print(f"  Available: {available:.2f} {unit}")
        if available < required:
            missing.append({
                "ingredient": ingredient,
                "amount": round(required - available, 2),
                "unit": unit,
            })
    print("\n" + "-" * 52)
    print("DEPLOYMENT STATUS: " + ("READY" if not missing else "NOT READY"))
    return missing


def export_shopping_list(missing):
    save_json(SHOPPING_JSON, missing)
    with SHOPPING_CSV.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["ingredient", "amount", "unit"])
        writer.writeheader()
        writer.writerows(missing)
    print(f"[AUDITOR] Shopping manifest saved to {SHOPPING_JSON} and {SHOPPING_CSV}.")


def print_shopping_list(missing):
    print("\n" + "=" * 52)
    print("SHOPPING LIST")
    print("=" * 52)
    if not missing:
        print("No shopping required. The pantry has achieved readiness.")
        return
    for item in missing:
        print(f"- {item['ingredient']}: {item['amount']:.2f} {item['unit']}")


def restock(ingredient, amount, unit):
    pantry = load_pantry()
    key = canonical_name(ingredient)
    incoming = {"amount": float(amount), "unit": normalize(unit)}
    if key in pantry:
        converted = convert(incoming["amount"], incoming["unit"], pantry[key]["unit"])
        if converted is None:
            print(
                f"[AUDITOR ERROR] Unit mismatch: cannot add {unit} to "
                f"existing {pantry[key]['unit']} stock for '{key}'."
            )
            return
        pantry[key]["amount"] += converted
    else:
        pantry[key] = incoming
    save_json(PANTRY_FILE, pantry)
    entry = {
        "event": "RESTOCK",
        "ingredient": key,
        "amount": incoming["amount"],
        "unit": incoming["unit"],
        "new_amount": pantry[key]["amount"],
        "new_unit": pantry[key]["unit"],
    }
    with RESTOCK_LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry) + "\n")
    print(f"[AUDITOR] Restocked '{key}': now {pantry[key]['amount']:.2f} {pantry[key]['unit']}.")


def main():
    parser = argparse.ArgumentParser(description="CathedralOS Sovereign Recipe Gate")
    parser.add_argument("--restock", nargs=3, metavar=("INGREDIENT", "AMOUNT", "UNIT"))
    args = parser.parse_args()

    if args.restock:
        ingredient, amount, unit = args.restock
        try:
            restock(ingredient, float(amount), unit)
        except ValueError:
            parser.error("AMOUNT must be numeric.")
        return

    pantry = load_pantry()
    if not pantry:
        print("No pantry inventory found. Create pantry.json before deployment.")
        return

    print("\nDUPLICATE INSPECTION")
    print("=" * 52)
    duplicates = find_duplicates(pantry)
    if duplicates:
        for original, canonical in duplicates:
            print(f"WARNING: '{original}' -> '{canonical}'")
    else:
        print("No duplicate ingredients detected.")

    pantry = merge_duplicates(pantry)
    missing = audit_recipe(SOVEREIGN_PIE, pantry)
    print_shopping_list(missing)
    export_shopping_list(missing)

    print(
        "\n[AUDITOR]\n"
        "Inventory normalized.\n"
        "Recipe verified.\n"
        "Reality remains final authority."
    )


if __name__ == "__main__":
    main()
