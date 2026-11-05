---
name: sku-snap
description: Match a messy B2B order (a customer's text message, email, or typed-up note) against a seller's product catalog CSV and return clean order lines (SKU, quantity, selling unit) plus a review queue of lines a human must check, with a ready-to-send clarification message. Use this when someone pastes or attaches an order from a restaurant or other buyer and asks to "enter", "parse", "match", "map to SKUs", "check" or "turn into an ERP import" that order; when they ask which lines of an order are ambiguous, unknown, out of stock or in the wrong unit; when they want to repeat a customer's previous order; or when they want to teach the tool that a customer's phrase means a SKU. Runs locally with the sku-snap CLI (Python, no network).
---

# sku-snap

Turns free-text orders into catalog-matched lines and flags what needs a human. Everything runs locally; nothing is uploaded.

## 1. Install

```bash
pip install "git+https://github.com/AagamS06/sku-snap.git@v0.1.0"
sku-snap --version        # sku-snap 0.1.0
```

Requires Python 3.10+. No other dependencies. If `pip` is unavailable, clone the repo and run `PYTHONPATH=src python -m skusnap ...`.

## 2. Inputs

You need an **order** and a **catalog**. Aliases and history are optional and per customer.

**Order**: plain text, one item per line or comma-separated. Save what the user pasted to a file (or pipe it with `-`). Greetings and sign-offs are fine; they are ignored. Example (`examples/orders/luigis-text.txt` in the repo):

```text
Hey Sam, for tmrw pls:
48 heads romaine
alb x3
10# yellow onions
half case lemons
4 dozen eggs
salmon 10
also need parm
2 cajas de tomate roma
1 bx micro greens
thx - Luigi
```

**Catalog CSV**: required columns `sku,name,unit`; optional `pack_size,pack_unit,aliases,in_stock`. `unit` is the selling unit (cs, lb, dz, bag, bunch, ea...). `pack_size` + `pack_unit` say what one selling unit holds (24 ea per cs). `aliases` is `|`-separated and may be in any language. `in_stock` is yes/no.

```csv
sku,name,unit,pack_size,pack_unit,aliases,in_stock
PRD-ROM-24,Romaine Hearts 24ct,cs,24,ea,romaine|romaine hearts|lechuga romana,yes
PRD-TOM-ROMA,Roma Tomatoes 25lb,cs,25,lb,roma tomato|tomate roma|plum tomato,yes
```

**Aliases CSV** (optional): `customer,phrase,sku`; `*` means every customer.
**History JSONL** (optional): one confirmed order per line, `{"customer": "luigis", "date": "2026-10-30", "lines": [{"sku": "...", "qty": 3, "unit": "cs"}]}`.

If the user has no catalog, do not invent one; ask for it (an export from their ERP or a spreadsheet is fine).

## 3. Run

```bash
sku-snap match ORDER.txt --catalog catalog.csv \
  [--customer ID --aliases aliases.csv --history history.jsonl] \
  [--format table|json|csv] [--out FILE] [--clarify] [--min-score 0.72]

sku-snap learn --catalog catalog.csv --aliases aliases.csv --customer ID --phrase "parm" --sku CHE-PARM-WHL
sku-snap rules            # list flag ids
```

- Use `--format json` when you will read the result yourself; show the user the table or a summary.
- `--clarify` adds a draft message to the customer about review lines (stdout for table, stderr for json/csv).
- `--customer` turns on that customer's aliases and history (tie-breaks and "same as last Friday").
- **Exit codes**: `0` every line ok · `1` at least one line needs review (normal, not a failure) · `2` usage or input error (message on stderr).

**JSON contract**: `{tool, version, customer, status: "clean"|"needs_review", summary: {lines, ok, review, ignored}, lines: [{line_no, raw, sku, name, qty, unit, score, match_source, status, flags: [{id, level, message}], candidates: [{sku, name, score}]}], ignored: [{line_no, raw}]}`.

**CSV** (ERP import): `line_no,sku,qty,unit,name,status,flags,raw`.

Real output for the example above with `--customer luigis --aliases examples/aliases.csv --history examples/history.jsonl`:

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
```

## 4. Explain the result

Lead with the summary (`6 ok, 3 need review`), then list each review line with its reason in plain words, then offer the clarification draft. Explain info flags only if asked or if they change a quantity (SS005).

| id | level | meaning | what to tell the user |
|---|---|---|---|
| SS001 | review | no catalog match | item not in catalog; ask the customer or add it |
| SS002 | review | several SKUs fit | list `candidates`; ask which one |
| SS003 | review | no quantity | ask how many (unit shown) |
| SS004 | review | unit not sold for this SKU | say the selling unit |
| SS005 | info | unit converted (e.g. 48 ea → 2 cs) | mention the conversion |
| SS006 | review | out of stock | ask to skip or substitute |
| SS007 | review | SKU on two lines | ask to combine |
| SS008 | review | repeat requested, no history | ask for the item list |
| SS009 | review | not a whole selling unit (0.5 cs) | ask to round |
| SS010 | review | low-confidence match | confirm the SKU |
| SS011 | info | ambiguity resolved from history | say which SKU and why |
| SS012 | info | no unit, selling unit assumed | mention if relevant |
| SS013 | info | line copied from a previous order | name the order date |
| SS014 | review | bare count looks like pack units ("120 eggs") | ask which unit was meant |

`match_source` says how a SKU was chosen: `customer-alias`, `catalog-alias`, `fuzzy` (see `score`, 0 to 1), or `history`. When the user confirms a correction, offer to run `sku-snap learn` so it sticks for that customer.

## 5. Boundaries

- Never place, submit or send an order or message; only prepare them for a person to send.
- Never pick a SKU for an SS002/SS010 line yourself; present the candidates.
- Do not invent catalog rows, prices, stock levels or customer history.
- Keep order and catalog data local; do not paste it into web tools or other services.
- No pricing, credit, delivery or legal advice; that is out of scope.
- Roadmap only (not available yet): photo/PDF/OCR input, web review queue, ERP export profiles, substitutions, LLM fallback. Say so if asked.
