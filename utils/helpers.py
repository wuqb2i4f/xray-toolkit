from typing import Dict, Any, List
from utils.validators import validators_map


def validate_object(obj: Dict[str, Any], fields_config: Dict[str, Any]) -> bool:
    """Validate object fields using config (general for any protocol)."""
    for field, field_def in fields_config.items():
        if field not in obj:
            if field_def.get("required", False):
                return False
            continue

        value = obj[field]
        if not validate_field(value, field_def):
            return False

    return True


def validate_field(value: Any, field_def: Dict[str, Any]) -> bool:
    """Validate field value based on config (delegates to small checkers)."""
    field_type = field_def.get("type", "string")

    # Type check
    if not check_type(value, field_type):
        return False

    # Range check (for ints)
    if "range" in field_def and field_type == "int":
        if not check_range(value, field_def["range"]):
            return False

    # Allowed values check
    if "allowed" in field_def:
        if not check_allowed(value, field_def["allowed"]):
            return False

    # Validators list
    validators = field_def.get("validators", [])
    if not apply_validators(value, validators):
        return False

    return True


def check_type(value: Any, field_type: str) -> bool:
    """Check if value matches the field type."""
    if field_type == "int" and not isinstance(value, int):
        return False
    elif field_type == "string" and not isinstance(value, str):
        return False
    elif field_type == "dict" and not isinstance(value, dict):
        return False
    return True


def check_range(value: int, range_def: List[int]) -> bool:
    """Check if int value is in range [min, max]."""
    min_val, max_val = range_def
    return min_val <= value <= max_val


def check_allowed(value: Any, allowed_list: List[Any]) -> bool:
    """Check if value is in the allowed list."""
    return value in allowed_list


def apply_validators(value: str, validators: List[str]) -> bool:
    """Apply validators from config: Returns True if ANY matches (OR logic), or if empty list (no checks)."""
    if not validators:
        return True

    for validator in validators:
        if validator in validators_map:
            if validators_map[validator](value):
                return True
        else:
            print(
                f"Unknown validator '{validator}' in config - skipping (add to validators_map)."
            )

    return False
