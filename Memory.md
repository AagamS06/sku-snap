# Memory (handoff)

**sku-snap**: offline Python CLI that turns messy B2B order texts/emails into catalog-matched lines, flags what needs a human (SS001 to SS014), drafts the clarification message, exports ERP-ready CSV. Stdlib only. v0.2.0.

## Decisions (and why)
- **Rules, not an LLM, in the core**: deterministic, explainable, offline, free. LLM is a roadmap opt-in.
- **Flag over guess**: ambiguity → SS002 with candidates; history may break a tie only when exactly one candidate was ordered before (SS011).
- **Plain files as state** (catalog.csv, aliases.csv, history.jsonl): reps can read and edit them; no DB.
- **Exit codes 0/1/2**: 1 = needs review (not an error) so pipelines can route it.
- **Multilingual via aliases only**: no translation model; honest about it.
- **Benchmark with a held-out split** (`bench/`): dev cases 01-26 may drive fixes; held-out h01-h14 were written after the v0.2.0 fixes and must not be tuned against. Report both. "Unsafe lines" (ok-but-wrong + silently dropped) is the headline metric.
- **"fresh" is a soft word, not a stopword** (v0.2.0): it was hiding the difference between Fresh and Shredded Mozzarella. In a phrase it only counts if the target has it.
- **Catalog checks are a separate id space** (CC001-CC008, error|warn) so the SS rule ids and JSON contract of `match` stay unchanged.
- **Agent Skill shipped** at `skills/sku-snap/SKILL.md`, zipped as `sku-snap-skill.zip` on each release.

## Status
- **Done**: Phase 0 + Phase 1 (v0.1.0). v0.2.0 (build session 2026-11-18): `bench` command + 40-case fictional benchmark (all 98.4% SKU acc., held-out 94.7%, 2 unsafe), `check-catalog` (CC001-CC008), polite-request filler fix ("could you send ..."), soft-word scoring fix (fresh), seeded fuzz test (1,000 orders), ruff in CI, CI runs check-catalog + bench gate (`--min-sku-accuracy 0.97 --max-unsafe 2`). 52 tests.
- **In progress**: nothing.
- **Next**: fix held-out misses (h01 `qty 2 cs iceberg` and h04 `a couple bags of rice` are dropped as chatter = unsafe; h02 mixed fraction; h03 range; h14 "bolsas"), then write a NEW held-out batch before claiming better numbers; tighten the CI gate to `--max-unsafe 0`. Then configurable thresholds per catalog.
- **Backlog**: web review queue, OCR extra, ERP export profiles, substitutions, PyPI.

## Open questions
- Default for bare counts ("120 eggs"): keep SS014 review, or infer pack units when qty ≥ pack size?
- Should `learn` also write history, or keep history to confirmed orders only?
- Which ERP import formats matter most to small distributors?

## Links
[PRD](PRD.md) · [Architecture](Architecture.md) · [Rules](Rules.md) · [Phases](Phases.md) · [Design](Design.md) · [README](README.md) · [Skill](skills/sku-snap/SKILL.md)
