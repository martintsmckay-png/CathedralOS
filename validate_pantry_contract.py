import json
import math
from pathlib import Path


def validate_pantry_data(data):
    """Enforce flat pantry contract invariants aligned with recipe_gate.py."""
    if not isinstance(data, dict):
        raise ValueError(f"Pantry root must be a dictionary, got {type(data).__name__}.")
    if len(data) == 0:
        raise ValueError("Pantry cannot be empty.")

    for name, item in data.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Ingredient name must be a non-empty string, got {name!r}.")
        if not isinstance(item, dict):
            raise ValueError(f"Item '{name}' must be a dictionary, got {type(item).__name__}.")

        if "amount" not in item:
            raise ValueError(f"Item '{name}' is missing 'amount'.")
        if "unit" not in item:
            raise ValueError(f"Item '{name}' is missing 'unit'.")

        amount = item["amount"]
        unit = item["unit"]

        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise ValueError(f"Amount for '{name}' must be numeric (not bool), got {type(amount).__name__}.")
        if isinstance(amount, float) and not math.isfinite(amount):
            raise ValueError(f"Amount for '{name}' must be finite, got {amount!r}.")
        if amount < 0:
            raise ValueError(f"Amount for '{name}' cannot be negative, got {amount}.")
        if not isinstance(unit, str) or not unit.strip():
            raise ValueError(f"Unit for '{name}' must be a non-empty string, got {unit!r}.")


def validate_pantry_contract(data):
    """Return (valid, reason) without raising contract validation errors."""
    try:
        validate_pantry_data(data)
    except ValueError as exc:
        return False, str(exc)
    return True, "Pantry contract validation passed."


def validate_pantry(pantry_path=Path("pantry.json")):
    pantry_path = Path(pantry_path)
    if not pantry_path.exists():
        raise FileNotFoundError(f"{pantry_path} not found.")

    data = json.loads(pantry_path.read_text(encoding="utf-8"))
    validate_pantry_data(data)
    print("Flat pantry contract validation passed successfully.")


if __name__ == "__main__":
    validate_pantry()
