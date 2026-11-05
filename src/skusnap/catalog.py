"""Load the seller's catalog, per-customer aliases and order history."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from .units import normalise_unit

REQUIRED_COLUMNS = {"sku", "name", "unit"}


class InputError(Exception):
    """Bad or missing input file. The CLI maps this to exit code 2."""


@dataclass
class Item:
    sku: str
    name: str
    unit: str                     # selling unit, e.g. cs, lb, dz
    pack_size: float | None = None
    pack_unit: str | None = None  # what one selling unit contains, e.g. 24 ea
    aliases: list[str] = field(default_factory=list)
    in_stock: bool = True


def load_catalog(path: str | Path) -> dict[str, Item]:
    p = Path(path)
    if not p.is_file():
        raise InputError(f"catalog not found: {p}")
    with p.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        cols = {c.strip().lower() for c in (reader.fieldnames or [])}
        missing = REQUIRED_COLUMNS - cols
        if missing:
            raise InputError(f"catalog {p.name} is missing columns: {', '.join(sorted(missing))}")
        items: dict[str, Item] = {}
        for i, row in enumerate(reader, start=2):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            sku = row["sku"]
            if not sku:
                continue
            unit = normalise_unit(row["unit"]) or row["unit"].lower()
            pack_size = None
            if row.get("pack_size"):
                try:
                    pack_size = float(row["pack_size"])
                except ValueError as exc:
                    raise InputError(f"{p.name} line {i}: pack_size must be a number") from exc
            pack_unit = normalise_unit(row.get("pack_unit")) or (row.get("pack_unit") or None)
            aliases = [a.strip() for a in row.get("aliases", "").split("|") if a.strip()]
            in_stock = row.get("in_stock", "yes").lower() not in ("no", "n", "false", "0", "out")
            if sku in items:
                raise InputError(f"{p.name} line {i}: duplicate sku {sku}")
            items[sku] = Item(sku, row["name"], unit, pack_size, pack_unit, aliases, in_stock)
    if not items:
        raise InputError(f"catalog {p.name} has no items")
    return items


def load_aliases(path: str | Path | None, customer: str | None) -> dict[str, str]:
    """phrase -> sku for one customer (rows with customer '*' apply to everyone)."""
    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    with p.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            who = (row.get("customer") or "").strip()
            if who in ("*", "") or (customer and who == customer):
                phrase = (row.get("phrase") or "").strip()
                sku = (row.get("sku") or "").strip()
                if phrase and sku:
                    out[phrase] = sku
    return out


def load_history(path: str | Path | None, customer: str | None) -> list[dict]:
    """Past confirmed orders for one customer, oldest first."""
    if not path or not customer:
        return []
    p = Path(path)
    if not p.is_file():
        return []
    orders = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"{p.name} line {n}: not valid JSON") from exc
        if rec.get("customer") == customer:
            orders.append(rec)
    return sorted(orders, key=lambda r: r.get("date", ""))


def append_alias(path: str | Path, customer: str, phrase: str, sku: str) -> bool:
    """Add a customer alias row. Returns False if it already existed."""
    p = Path(path)
    exists = p.is_file()
    if exists:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                if (row.get("customer"), row.get("phrase"), row.get("sku")) == (customer, phrase, sku):
                    return False
    with p.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if not exists:
            w.writerow(["customer", "phrase", "sku"])
        w.writerow([customer, phrase, sku])
    return True
