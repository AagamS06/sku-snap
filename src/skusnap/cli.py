"""sku-snap command line.

Exit codes: 0 = every line matched cleanly, 1 = at least one line needs review,
2 = usage or input error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .catalog import InputError, append_alias, load_aliases, load_catalog, load_history
from .match import RULES, Settings, match_lines
from .parse import parse_order
from .report import clarify, to_csv, to_json, to_table


def _read_order(arg: str) -> str:
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg)
    if not p.is_file():
        raise InputError(f"order file not found: {p}")
    return p.read_text(encoding="utf-8")


def cmd_match(a: argparse.Namespace) -> int:
    catalog = load_catalog(a.catalog)
    if a.customer is None and a.history:
        print("note: --history is only used with --customer", file=sys.stderr)
    aliases = load_aliases(a.aliases, a.customer)
    history = load_history(a.history, a.customer)
    text = _read_order(a.order)
    settings = Settings(min_score=a.min_score)
    lines, ignored = match_lines(parse_order(text), catalog, aliases, history, settings)
    if a.format == "json":
        out = to_json(lines, ignored, a.customer)
    elif a.format == "csv":
        out = to_csv(lines)
    else:
        out = to_table(lines, ignored, a.customer)
    if a.out:
        Path(a.out).write_text(out + ("" if out.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(out)
    if a.clarify:
        print("\n--- clarification draft ---", file=sys.stderr if a.out is None and a.format != "table" else sys.stdout)
        print(clarify(lines, a.customer), file=sys.stderr if a.out is None and a.format != "table" else sys.stdout)
    return 1 if any(ln.needs_review for ln in lines) else 0


def cmd_learn(a: argparse.Namespace) -> int:
    catalog = load_catalog(a.catalog)
    if a.sku not in catalog:
        raise InputError(f"sku {a.sku} is not in {a.catalog}")
    added = append_alias(a.aliases, a.customer, a.phrase, a.sku)
    print(("learned" if added else "already known") + f": {a.customer} '{a.phrase}' -> {a.sku} ({catalog[a.sku].name})")
    return 0


def cmd_rules(_: argparse.Namespace) -> int:
    for rid, (level, title) in RULES.items():
        print(f"{rid}  {level:<6}  {title}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="sku-snap", description="Match messy B2B orders (texts, emails, notes) to catalog SKUs.")
    ap.add_argument("--version", action="version", version=f"sku-snap {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="match an order message against a catalog")
    m.add_argument("order", help="order text file, or - for stdin")
    m.add_argument("--catalog", required=True, help="catalog CSV (sku,name,unit[,pack_size,pack_unit,aliases,in_stock])")
    m.add_argument("--customer", help="customer id (enables aliases and history for that customer)")
    m.add_argument("--aliases", help="aliases CSV (customer,phrase,sku)")
    m.add_argument("--history", help="order history JSONL (one confirmed order per line)")
    m.add_argument("--format", choices=["table", "json", "csv"], default="table")
    m.add_argument("--out", help="write the result to this file instead of stdout")
    m.add_argument("--clarify", action="store_true", help="also print a draft message asking about review lines")
    m.add_argument("--min-score", type=float, default=0.72, help="fuzzy score needed for a confident match (default 0.72)")
    m.set_defaults(func=cmd_match)

    le = sub.add_parser("learn", help="remember that a customer's phrase means a SKU")
    le.add_argument("--catalog", required=True)
    le.add_argument("--aliases", required=True)
    le.add_argument("--customer", required=True)
    le.add_argument("--phrase", required=True)
    le.add_argument("--sku", required=True)
    le.set_defaults(func=cmd_learn)

    r = sub.add_parser("rules", help="list flag ids")
    r.set_defaults(func=cmd_rules)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    try:
        return a.func(a)
    except InputError as exc:
        print(f"sku-snap: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
