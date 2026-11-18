# Phases

## Phase 0: Setup
**Goal:** a repo anyone can clone, install and test.
- [x] Docs: PRD, Architecture, Rules, Phases, Design, Memory, README, LICENSE
- [x] `pyproject.toml` with `sku-snap` entry point, no runtime dependencies
- [x] Package skeleton under `src/skusnap/`
- [x] pytest + GitHub Actions CI (3.10, 3.12)
- [x] Example catalog, aliases, history and orders

**Exit criteria:** `pip install .` works, `sku-snap --version` prints, tests pass in CI.

## Phase 1: MVP (v0.1.0)
**Goal:** a rep can run one command on a texted/emailed order and get ok vs review lines.
- [x] Parser: quantities (digits, fractions, word numbers), units, leading/trailing qty, safe splitting
- [x] Matcher: customer alias → catalog alias → fuzzy with shorthand + typos
- [x] Ambiguity with candidates; history tie-break (SS011)
- [x] Unit fitting with exact conversions and pack sizes
- [x] Repeat-order expansion ("same as last Friday")
- [x] Rules SS001 to SS014
- [x] Table / JSON / CSV output, `--clarify`, `learn`, `rules`
- [x] Exit codes 0 / 1 / 2
- [x] Agent Skill `skills/sku-snap/SKILL.md` + release zip

**Exit criteria:** 30+ tests green; README examples reproduce exactly; release v0.1.0 published with the skill zip.

## Phase 2: Hardening
**Goal:** trustworthy on real-world messiness.
- [x] Fictional benchmark set (orders + expected JSON, dev + held-out) and a `sku-snap bench` command (v0.2.0)
- [ ] More number/unit vocab (Spanish, Chinese, Korean, Japanese numerals via config file)
- [x] Catalog validator (`sku-snap check-catalog`): CC001 to CC008 incl. duplicate aliases, aliases colliding across SKUs, dangling customer aliases (v0.2.0)
- [ ] Configurable thresholds per catalog
- [x] Seeded fuzz / property tests: 1,000 random orders, no crash, output invariants hold (v0.2.0)
- [x] `ruff` lint in CI (v0.2.0)
- [ ] Fix the held-out benchmark misses: `qty 2` marker, "a couple"/"a few", mixed fractions (`2 1/2`), ranges (`3-4` → SS003), Spanish unit words (bolsa)

**Exit criteria:** benchmark published with per-rule precision; no crash on 1,000 fuzzed orders.

## Phase 3: Review workflow
**Goal:** fixing a flagged line takes one click.
- [ ] Local web review queue (stdlib `http.server`), styled per Design.md
- [ ] Accept / pick candidate / edit qty → writes history + aliases
- [ ] ERP export profiles (column mappings)
- [ ] Optional OCR extra for photos / PDFs (clearly marked lower confidence)
- [ ] Optional local LLM fallback for unparseable lines (opt-in, marked as such)

**Exit criteria:** a full order can be reviewed and exported without touching a terminal.

## Phase 4: Launch
**Goal:** people outside the repo can use it.
- [x] Launch video + cover in `docs/media/`
- [ ] Publish to PyPI
- [ ] Short write-up of the benchmark results
- [ ] Gather feedback from 3 real order desks (issues, not testimonials)

**Exit criteria:** `pip install sku-snap` works from PyPI; at least one external issue or PR.
