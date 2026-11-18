"""Validate a catalog (and optional aliases file) before matching orders against it.

Problems here do not crash `match`; they quietly make it worse (an alias that two SKUs
share can never match exactly, an alias that points at a deleted SKU is silently
skipped). `sku-snap check-catalog` makes them visible.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .catalog import InputError, Item
from .match import norm
from .units import UNIT_ALIASES

CHECKS: dict[str, tuple[str, str]] = {
    # id: (level, title)
    "CC001": ("error", "Catalog alias shared by more than one SKU"),
    "CC002": ("warn", "Alias equals another SKU's name"),
    "CC003": ("warn", "Alias repeated on the same SKU or equal to its own name"),
    "CC004": ("error", "Customer alias points to a SKU that is not in the catalog"),
    "CC005": ("error", "Customer alias maps one phrase to two SKUs for the same customer"),
    "CC006": ("warn", "pack_size and pack_unit must be given together"),
    "CC007": ("warn", "Unit is not one sku-snap recognises (conversions will not work)"),
    "CC008": ("warn", "Two SKUs have the same name"),
}

KNOWN_UNITS = set(UNIT_ALIASES.values())


@dataclass
class Issue:
    id: str
    message: str

    @property
    def level(self) -> str:
        return CHECKS[self.id][0]


def check_catalog(catalog: dict[str, Item]) -> list[Issue]:
    issues: list[Issue] = []
    names: dict[str, str] = {}
    for item in catalog.values():
        key = norm(item.name)
        if key in names:
            issues.append(Issue("CC008", f"{names[key]} and {item.sku} are both named '{item.name}'"))
        else:
            names[key] = item.sku

    owners: dict[str, list[str]] = {}
    for item in catalog.values():
        seen: set[str] = set()
        for alias in item.aliases:
            key = norm(alias)
            if not key:
                continue
            if key in seen or key == norm(item.name):
                issues.append(Issue("CC003", f"{item.sku}: alias '{alias}' is listed twice or equals the name"))
                continue
            seen.add(key)
            owners.setdefault(key, []).append(item.sku)
            if key in names and names[key] != item.sku:
                issues.append(Issue("CC002", f"{item.sku}: alias '{alias}' is the name of {names[key]}; "
                                             "orders for that phrase become ambiguous"))
        if (item.pack_size is None) != (item.pack_unit is None):
            issues.append(Issue("CC006", f"{item.sku}: pack_size={item.pack_size} pack_unit={item.pack_unit}"))
        for label, unit in (("unit", item.unit), ("pack_unit", item.pack_unit)):
            if unit and unit not in KNOWN_UNITS:
                issues.append(Issue("CC007", f"{item.sku}: {label} '{unit}' is not a known unit"))

    for key, skus in sorted(owners.items()):
        if len(skus) > 1:
            issues.append(Issue("CC001", f"alias '{key}' is on {', '.join(skus)}; it can never match exactly"))
    return issues


def check_aliases(path: str | Path, catalog: dict[str, Item]) -> list[Issue]:
    p = Path(path)
    if not p.is_file():
        raise InputError(f"aliases file not found: {p}")
    issues: list[Issue] = []
    mapped: dict[tuple[str, str], tuple[str, int]] = {}
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        missing = {"customer", "phrase", "sku"} - {c.strip().lower() for c in (reader.fieldnames or [])}
        if missing:
            raise InputError(f"aliases {p.name} is missing columns: {', '.join(sorted(missing))}")
        for n, row in enumerate(reader, start=2):
            who = (row.get("customer") or "").strip() or "*"
            phrase = (row.get("phrase") or "").strip()
            sku = (row.get("sku") or "").strip()
            if not phrase or not sku:
                continue
            if sku not in catalog:
                issues.append(Issue("CC004", f"{p.name} line {n}: {who} '{phrase}' -> {sku}, "
                                             "which is not in the catalog (the alias is ignored)"))
                continue
            key = (who, norm(phrase))
            if key in mapped and mapped[key][0] != sku:
                issues.append(Issue("CC005", f"{p.name} line {n}: {who} '{phrase}' -> {sku}, but line "
                                             f"{mapped[key][1]} maps it to {mapped[key][0]} (the later row wins)"))
            mapped[key] = (sku, n)
    return issues


def to_text(issues: list[Issue], items: int) -> str:
    errors = sum(i.level == "error" for i in issues)
    warns = len(issues) - errors
    out = [f"{i.id}  {i.level.upper():<5}  {i.message}" for i in issues]
    if out:
        out.append("")
    out.append(f"{items} items checked: {errors} error(s), {warns} warning(s)")
    return "\n".join(out)
