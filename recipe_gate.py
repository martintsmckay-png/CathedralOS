#!/usr/bin/env python3
"""CathedralOS // Sovereign Recipe Gate v3.0

Auditor-grade pantry intelligence for the Sovereign Pie deployment.
"""

import argparse
import csv
import json
import math
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

PANTRY_FILE = Path("pantry.json")
SHOPPING_JSON = Path("shopping_list.json")
SHOPPING_CSV = Path("shopping_list.csv")
RESTOCK_LOG = Path("restock_log.jsonl")


class DirectorySyncError(OSError):
    """The file was replaced, but directory durability was not confirmed."""

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
    """Write JSON through a same-directory temporary file and atomic replace."""
    path = Path(path)
    temporary_name = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_name = file.name
            json.dump(data, file, indent=2, allow_nan=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_name, path)
        temporary_name = None

        # Replacement has succeeded. A directory-sync failure must not
        # be reported as though the inventory file was never replaced.
        try:
            directory_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as error:
            raise DirectorySyncError(
                f"{path} was replaced, but directory sync failed: {error}"
            ) from error

    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def load_pantry(strict=False):
    """Load pantry data; strict mode refuses damaged or invalid inventory."""
    if strict:
        if not PANTRY_FILE.exists():
            return {}
        try:
            with PANTRY_FILE.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Cannot safely load pantry: {error}") from error

        if not isinstance(raw, dict):
            raise ValueError("Pantry root must be a JSON object.")
    else:
        raw = load_json(PANTRY_FILE, {})

    pantry = {}
    for name, value in raw.items():
        if not isinstance(name, str) or not normalize(name):
            if strict:
                raise ValueError("Pantry contains an invalid ingredient name.")
            continue

        if isinstance(value, dict):
            amount, unit = value.get("amount", 0), value.get("unit", "g")
        else:
            amount, unit = value, "g"

        try:
            if isinstance(amount, bool):
                raise ValueError("Boolean is not a valid quantity.")
            amount = float(amount)
        except (TypeError, ValueError) as error:
            if strict:
                raise ValueError(
                    f"Invalid quantity for '{name}'."
                ) from error
            print(f"[AUDITOR WARNING] Non-numeric amount for '{name}'; treated as 0.")
            amount = 0.0

        if strict and (not math.isfinite(amount) or amount < 0):
            raise ValueError(
                f"Invalid quantity for '{name}': must be finite and non-negative."
            )

        if not isinstance(unit, str) or not normalize(unit):
            if strict:
                raise ValueError(f"Invalid unit for '{name}'.")
            unit = "g"

        pantry[canonical_name(name)] = {
            "amount": amount,
            "unit": normalize(unit),
        }

    return pantry


def append_ledger_event(event):
    """Append one durable JSONL event."""
    with RESTOCK_LOG.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, allow_nan=False) + "\n")
        file.flush()
        os.fsync(file.fileno())


def unresolved_transactions():
    """Return PREPARED transactions without a matching COMMITTED event."""
    prepared = {}
    committed = set()

    if not RESTOCK_LOG.exists():
        return []

    with RESTOCK_LOG.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid ledger JSON on line {line_number}."
                ) from error

            if not isinstance(event, dict):
                raise ValueError(
                    f"Invalid ledger record on line {line_number}."
                )

            transaction_id = event.get("transaction_id")
            if event.get("event") == "PREPARED" and transaction_id:
                prepared[transaction_id] = event
            elif event.get("event") == "COMMITTED" and transaction_id:
                committed.add(transaction_id)

    return [
        event for transaction_id, event in prepared.items()
        if transaction_id not in committed
    ]


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
    """Validate, prepare, and commit a restock with auditable transaction events."""
    if not isinstance(ingredient, str) or not normalize(ingredient):
        raise ValueError("Ingredient name must not be empty.")

    if isinstance(amount, bool):
        raise ValueError("Restock amount must be a finite, non-negative number.")

    try:
        quantity = float(amount)
    except (TypeError, ValueError) as error:
        raise ValueError("Restock amount must be numeric.") from error

    if not math.isfinite(quantity) or quantity < 0:
        raise ValueError("Restock amount must be finite and non-negative.")

    if not isinstance(unit, str) or not normalize(unit):
        raise ValueError("Unit must not be empty.")

    key = canonical_name(ingredient)
    incoming_unit = normalize(unit)

    # Refuse new writes until earlier transactions are reconciled.
    pending = unresolved_transactions()
    if pending:
        pending_ids = ", ".join(
            str(event["transaction_id"]) for event in pending
        )
        raise RuntimeError(
            "Cannot restock while unresolved restock transaction(s) exist: "
            f"{pending_ids}. Reconcile the ledger first."
        )

    # Strict loading prevents damaged inventory from being treated as empty.
    pantry = load_pantry(strict=True)

    if key in pantry:
        converted = convert(quantity, incoming_unit, pantry[key]["unit"])
        if converted is None:
            raise ValueError(
                f"Unit mismatch: cannot add {unit} to "
                f"existing {pantry[key]['unit']} stock for '{key}'."
            )
        if not math.isfinite(converted):
            raise ValueError("Converted restock amount is not finite.")
        new_amount = pantry[key]["amount"] + converted
        new_unit = pantry[key]["unit"]
    else:
        new_amount = quantity
        new_unit = incoming_unit

    if not math.isfinite(new_amount):
        raise ValueError("Resulting inventory balance is not finite.")

    updated_pantry = dict(pantry)
    updated_pantry[key] = {"amount": new_amount, "unit": new_unit}

    transaction_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    prepared = {
        "event": "PREPARED",
        "transaction_id": transaction_id,
        "timestamp": timestamp,
        "ingredient": key,
        "amount": quantity,
        "unit": incoming_unit,
        "new_amount": new_amount,
        "new_unit": new_unit,
    }

    # If this fails, inventory has not yet been changed.
    append_ledger_event(prepared)

    try:
        save_json(PANTRY_FILE, updated_pantry)
    except DirectorySyncError as error:
        raise RuntimeError(
            f"Inventory was replaced for transaction {transaction_id}, "
            "but directory durability confirmation failed. "
            "The PREPARED ledger event remains unresolved; inspect "
            "unresolved_transactions() before further reconciliation."
        ) from error
    except OSError as error:
        raise RuntimeError(
            f"Inventory commit failed for transaction {transaction_id}; "
            "the PREPARED ledger event remains unresolved."
        ) from error

    committed = {
        "event": "COMMITTED",
        "transaction_id": transaction_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ingredient": key,
        "new_amount": new_amount,
        "new_unit": new_unit,
    }

    try:
        append_ledger_event(committed)
    except OSError as error:
        raise RuntimeError(
            f"Inventory was committed for transaction {transaction_id}, "
            "but the COMMITTED ledger event could not be written. "
            "Inspect unresolved_transactions() before further reconciliation."
        ) from error

    print(f"[AUDITOR] Restocked '{key}': now {new_amount:.2f} {new_unit}.")
    return True


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
