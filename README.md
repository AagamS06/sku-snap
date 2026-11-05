# sku-snap

**Turn messy B2B orders into clean, catalog-matched lines, and flag only what needs a human.**

[![CI](https://github.com/AagamS06/sku-snap/actions/workflows/ci.yml/badge.svg)](https://github.com/AagamS06/sku-snap/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Dependencies](https://img.shields.io/badge/runtime%20deps-0-7BD389)
![License](https://img.shields.io/badge/license-MIT-blue)
![Release](https://img.shields.io/github/v/release/AagamS06/sku-snap)

## The problem

Restaurants text their distributor "alb x3, salmon 10, half case lemons, 2 cajas de tomate roma". Someone on the order desk then re-types every line into the ERP, guessing which of ten salmon SKUs was meant, converting "48 heads" into cases, and remembering what *this* customer means by "parm". Startups in the current YC batches are attacking this from both sides (distributors' order entry, restaurants' purchasing; see [PRD.md](PRD.md)), but there was no small, open, offline tool that shows *why* each line was matched or flagged.

sku-snap is that tool. It helps **order-desk reps at small and mid-size distributors**, **developers** building order-intake automation who need a deterministic baseline, and **buyers** checking an order against a supplier catalog before sending it.

## Features

- **Parses real order text**: digits, fractions, "half", word numbers, `10#`, `x3`, trailing quantities, units like cs/case/caja/box, lb, kg, heads, dozen, bag, bunch.
- **Matches to your catalog**: customer aliases → catalog aliases (any language you list) → fuzzy scoring with shorthand ("alb" → albacore) and typo tolerance.
- **Handles ambiguity honestly**: shows candidates; breaks a tie only when the customer's history points to exactly one.
- **Fits units**: 48 ea → 2 cs from pack sizes; kg → lb; flags half cases and bare counts.
- **Repeats orders**: "same as last Friday" / "the usual" expands from history.
- **14 flag rules** (SS001 to SS014) with info vs review levels; `sku-snap rules` lists them.
- **Outputs** a table, a stable JSON contract, or an ERP-import CSV; `--clarify` drafts the message to the customer.
- **Learns**: `sku-snap learn` stores "this customer's phrase = this SKU".
- **Offline, zero runtime dependencies**, exit codes `0` clean / `1` review / `2` error.

## Launch video

_Coming with the launch commit: `docs/media/`._

## Tech stack

Python 3.10+ standard library (`csv`, `json`, `difflib`, `unicodedata`, `argparse`), pytest, GitHub Actions. Why: see [Architecture.md](Architecture.md#tech-stack).

## Getting started

```bash
pip install "git+https://github.com/AagamS06/sku-snap.git@v0.1.0"
git clone https://github.com/AagamS06/sku-snap.git && cd sku-snap   # for the examples

sku-snap match examples/orders/luigis-text.txt --catalog examples/catalog.csv \
  --customer luigis --aliases examples/aliases.csv --history examples/history.jsonl --clarify
```

```text
#   STATUS  QTY  UNIT  SKU           ITEM                       FLAGS
3   ok      2    cs    PRD-ROM-24    Romaine Hearts 24ct        SS005
4   ok      3    lb    SEA-TUN-ALB   Albacore Tuna Loin         SS012
5   ok      10   lb    PRD-ONY-JMB   Yellow Onions Jumbo        -
6   REVIEW  0.5  cs    PRD-LEM-115   Lemons 115ct               SS009
7   ok      4    dz    DRY-EGG-LG    Large Eggs                 -
8   ok      10   lb    SEA-SAL-ATL   Atlantic Salmon Fillet     SS011,SS012
9   REVIEW  -    lb    CHE-PARM-WHL  Parmigiano Reggiano Wedge  SS003
10  ok      2    cs    PRD-TOM-ROMA  Roma Tomatoes 25lb         -
11  REVIEW  1    cs    -             1 bx micro greens          SS001

9 lines, 6 ok, 3 need review, 3 ignored (chatter)  [customer: luigis]
  line 6 SS009 Quantity is not a whole selling unit: 0.5 cs is not a whole unit; round to 1?
  line 9 SS003 No quantity given: how many lb of Parmigiano Reggiano Wedge?
  line 11 SS001 Unknown item: no catalog match: nothing in the catalog looks like 'micro greens'

--- clarification draft ---
Hi luigis,
Thanks for the order. A few quick checks before we confirm:
- "half case lemons": Lemons 115ct comes in whole cs. Round up to 1?
- "also need parm": how many lb of Parmigiano Reggiano Wedge?
- "1 bx micro greens": we couldn't find this item. Can you describe it or send a photo?
Everything else is good to go.
```

More: `--format json` (contract in [Architecture.md](Architecture.md#key-apis--integrations)), `--format csv --out order.csv` for an ERP import, `sku-snap learn ...` to remember a correction. Development: `pip install -e ".[dev]" && python -m pytest -q`.

## Use it with Claude (skill)

sku-snap ships an Agent Skill so Claude (or any agent that reads skills) can run it for you and explain the result.

1. Download **`sku-snap-skill.zip`** from the [latest release](https://github.com/AagamS06/sku-snap/releases/latest) (or copy the [`skills/sku-snap/`](skills/sku-snap/SKILL.md) folder).
2. Unzip it and add the `sku-snap` folder as a skill.
3. Paste an order and say "match this against my catalog".

## Project structure

```
src/skusnap/   cli.py · parse.py · units.py · catalog.py · match.py · report.py
tests/         parser, matcher and CLI contract tests
examples/      catalog.csv · aliases.csv · history.jsonl · orders/
skills/        sku-snap/SKILL.md
docs/media/    launch video and cover
```

## Roadmap

Phase 0 setup and Phase 1 MVP are done. Next: benchmark set, catalog validator, more number words; then a local review queue, OCR extra and ERP export profiles. Details in [Phases.md](Phases.md).

## Docs

| Doc | What's in it |
|---|---|
| [PRD.md](PRD.md) | problem, observed gaps and where, users, stories, MVP vs later, metrics |
| [Architecture.md](Architecture.md) | flow diagram, modules, data model, scoring, CLI/JSON contract |
| [Rules.md](Rules.md) | conventions, AI-contributor boundaries, errors, tests, security |
| [Phases.md](Phases.md) | phases with checkboxes and exit criteria |
| [Design.md](Design.md) | palette, themes, type scale, components, accessibility |
| [Memory.md](Memory.md) | short handoff: decisions, status, open questions |
| [skills/sku-snap/SKILL.md](skills/sku-snap/SKILL.md) | Agent Skill for Claude |

## Contributing

Issues and PRs welcome. Read [Rules.md](Rules.md) first: stdlib only, flag rather than guess, a test for every change, and no real customer data in examples.

## Licence

[MIT](LICENSE) © 2026 Aagam Shah. Independent student project; not affiliated with any company mentioned in the docs.
