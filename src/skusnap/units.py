"""Unit vocabulary and conversions.

Units are normalised to short codes. Only conversions that are exact by
definition live here (dz -> ea, kg -> lb, ...). Pack-size conversions
(for example "24 ea per cs") come from the catalog, not from this table.
"""

from __future__ import annotations

UNIT_ALIASES: dict[str, str] = {
    # cases / boxes
    "cs": "cs", "case": "cs", "cases": "cs", "cse": "cs", "caja": "cs", "cajas": "cs",
    "box": "cs", "boxes": "cs", "bx": "cs", "ctn": "cs", "carton": "cs", "cartons": "cs",
    # weight
    "lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb", "#": "lb",
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg",
    "oz": "oz",
    # count
    "ea": "ea", "each": "ea", "pc": "ea", "pcs": "ea", "piece": "ea", "pieces": "ea",
    "ct": "ea", "count": "ea", "head": "ea", "heads": "ea", "unit": "ea", "units": "ea",
    "dz": "dz", "doz": "dz", "dozen": "dz", "dozens": "dz",
    # containers
    "bag": "bag", "bags": "bag", "sack": "bag", "sacks": "bag",
    "gal": "gal", "gallon": "gal", "gallons": "gal",
    "btl": "btl", "bottle": "btl", "bottles": "btl",
    "tub": "tub", "tubs": "tub",
    "bunch": "bunch", "bunches": "bunch", "bn": "bunch",
    "tray": "tray", "trays": "tray", "flat": "tray", "flats": "tray",
}

# exact conversions: (from, to) -> factor
CONVERSIONS: dict[tuple[str, str], float] = {
    ("dz", "ea"): 12.0,
    ("ea", "dz"): 1 / 12,
    ("kg", "lb"): 2.20462,
    ("lb", "kg"): 1 / 2.20462,
    ("oz", "lb"): 1 / 16,
    ("lb", "oz"): 16.0,
}


def normalise_unit(token: str | None) -> str | None:
    """Map a raw unit token to its short code, or None if it is not a unit."""
    if not token:
        return None
    return UNIT_ALIASES.get(token.lower().strip("."))


def convert(qty: float, src: str, dst: str) -> float | None:
    """Convert qty from src to dst using exact conversions only."""
    if src == dst:
        return qty
    factor = CONVERSIONS.get((src, dst))
    return None if factor is None else qty * factor
