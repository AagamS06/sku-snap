# Architecture

## App flow

```mermaid
flowchart LR
    A[Order text<br/>file or stdin] --> B[parse.py<br/>split lines, qty, unit, phrase]
    B --> C{repeat request?}
    C -- yes --> H[history.jsonl<br/>pick last / weekday order]
    C -- no --> D[match.py<br/>customer alias → catalog alias → fuzzy]
    H --> F
    D --> E{ambiguous?}
    E -- one candidate in history --> F[resolve unit<br/>units.py + pack size]
    E -- several --> R[flag SS002 + candidates]
    E -- no --> F
    F --> G[flags SS001 to SS014]
    R --> G
    G --> O[report.py<br/>table / JSON / CSV / clarify]
    O --> X[exit 0 clean · 1 review · 2 error]
    O -. learn command .-> L[aliases.csv]
    L -.-> D
```

## System architecture

A single-process Python CLI. No network, no database, no background service. All state is in three plain files the user owns:

| File | Role |
|---|---|
| `catalog.csv` | The seller's catalog: `sku,name,unit[,pack_size,pack_unit,aliases,in_stock]` |
| `aliases.csv` | Learned phrases: `customer,phrase,sku` (`*` = every customer) |
| `history.jsonl` | Confirmed past orders, one JSON object per line |

The pipeline is pure functions (`parse_order` → `match_lines` → renderers), so it is easy to test and to embed in another program.

## Folder and file structure

```
sku-snap/
├── src/skusnap/
│   ├── __init__.py      # version
│   ├── __main__.py      # python -m skusnap
│   ├── cli.py           # argparse: match, learn, rules; exit codes
│   ├── parse.py         # message → ParsedLine (qty, unit, phrase, repeat)
│   ├── units.py         # unit vocabulary + exact conversions
│   ├── catalog.py       # CSV / JSONL loaders, InputError, append_alias
│   ├── match.py         # scoring, ambiguity, unit fitting, RULES
│   ├── report.py        # table, JSON, CSV, clarification draft
│   ├── check.py         # check-catalog: CC001..CC008 catalog + alias checks
│   └── bench.py         # bench: score against labelled cases, unsafe lines, per-rule P/R
├── tests/               # pytest: parser, matcher, CLI contract, checks, bench, seeded fuzz
├── bench/               # labelled benchmark (fictional): catalog, aliases, history, cases/
├── examples/            # catalog.csv, aliases.csv, history.jsonl, orders/*.txt
├── skills/sku-snap/SKILL.md   # Agent Skill for Claude
├── docs/media/          # launch video, cover
├── .github/workflows/ci.yml
└── PRD.md Architecture.md Rules.md Phases.md Design.md Memory.md
```

## Tech stack

| Choice | Why |
|---|---|
| Python 3.10+ | Runs anywhere a rep's laptop does; same language as most data tooling. |
| Standard library only (`csv`, `json`, `difflib`, `unicodedata`, `argparse`) | `pip install` in seconds, nothing to audit, works offline. |
| `difflib.SequenceMatcher` + token scoring | Good enough for shorthand and typos, deterministic, explainable scores. |
| pytest (dev only) | Fast tests, parametrised parser cases. |
| GitHub Actions | Runs ruff, the tests, check-catalog and the benchmark gate on 3.10 and 3.12. |

## Data model

```text
ParsedLine  line_no, raw, qty?, unit?, phrase, repeat?        (parse.py)
Item        sku, name, unit, pack_size?, pack_unit?, aliases[], in_stock   (catalog.py)
Line        line_no, raw, qty?, unit?, sku?, name?, score, source,
            candidates[{sku,name,score}], flags[Flag]          (match.py)
Flag        id (SS001..SS014), message, level (info|review)
```

`source` is one of `customer-alias`, `catalog-alias`, `fuzzy`, `history`, `none`.

### Matching score

For a phrase `q` and a catalog name or alias `c` (both tokenised, stopwords and digits dropped, plurals trimmed; the soft word "fresh" counts in a phrase only when the target has it too):

```
score = 0.60 · coverage(q in c) + 0.15 · precision(c in q) + 0.25 · sequence_ratio
```

Token similarity is 1.0 for equal tokens, 0.9 when `c` starts with a 3+ letter `q` (shorthand), the `difflib` ratio when ≥ 0.8 (typos), else 0. Thresholds: confident ≥ 0.72 (`--min-score`), candidate ≥ 0.5, ambiguity margin 0.06, chatter (no quantity) < 0.6.

## Key APIs / integrations

- **CLI contract**: `sku-snap match ORDER --catalog CSV [--customer ID --aliases CSV --history JSONL] [--format table|json|csv] [--out FILE] [--clarify] [--min-score N]`.
- **JSON output**: `{tool, version, customer, status, summary{lines,ok,review,ignored}, lines[...], ignored[...]}`.
- **check-catalog**: `sku-snap check-catalog --catalog CSV [--aliases CSV] [--format table|json] [--strict]`; JSON `{tool, version, items, errors, warnings, issues[{id, level, message}]}`; exit 0 no errors / 1 errors / 2 bad input.
- **bench**: `sku-snap bench DIR [--cases GLOB] [--verbose] [--format table|json] [--min-sku-accuracy N] [--max-unsafe N]`; JSON `{tool, version, summary{cases, cases_exact, lines, sku_accuracy, line_accuracy, status_accuracy, unsafe_lines, missing_lines, extra_lines, chatter_mismatches, per_rule{...}}, mismatches[...]}`; exit 1 only when a threshold fails.
- **CSV output**: `line_no,sku,qty,unit,name,status,flags,raw`, ready to map into an ERP import.
- **Python API**: `parse_order(text)`, `match_lines(parsed, catalog, aliases, history)`, `to_json(...)`.
- **Agent Skill**: `skills/sku-snap/SKILL.md` lets Claude run the CLI and explain results.
- No ERP API integrations in v0.1 (roadmap).
