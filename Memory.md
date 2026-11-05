# Memory (handoff)

**sku-snap**: offline Python CLI that turns messy B2B order texts/emails into catalog-matched lines, flags what needs a human (SS001 to SS014), drafts the clarification message, exports ERP-ready CSV. Stdlib only. v0.1.0.

## Decisions (and why)
- **Rules, not an LLM, in the core**: deterministic, explainable, offline, free. LLM is a roadmap opt-in.
- **Flag over guess**: ambiguity → SS002 with candidates; history may break a tie only when exactly one candidate was ordered before (SS011).
- **Plain files as state** (catalog.csv, aliases.csv, history.jsonl): reps can read and edit them; no DB.
- **Exit codes 0/1/2**: 1 = needs review (not an error) so pipelines can route it.
- **Multilingual via aliases only**: no translation model; honest about it.
- **Agent Skill shipped** at `skills/sku-snap/SKILL.md`, zipped as `sku-snap-skill.zip` on each release.

## Status
- **Done**: Phase 0 + Phase 1 (parser, matcher, units, history, 14 rules, table/JSON/CSV, clarify, learn, rules, 34 tests, CI, SKILL.md, release v0.1.0, launch video).
- **In progress**: nothing.
- **Next**: benchmark set + `bench` command; `check-catalog`; more number words.
- **Backlog**: web review queue, OCR extra, ERP export profiles, substitutions, PyPI.

## Open questions
- Default for bare counts ("120 eggs"): keep SS014 review, or infer pack units when qty ≥ pack size?
- Should `learn` also write history, or keep history to confirmed orders only?
- Which ERP import formats matter most to small distributors?

## Links
[PRD](PRD.md) · [Architecture](Architecture.md) · [Rules](Rules.md) · [Phases](Phases.md) · [Design](Design.md) · [README](README.md) · [Skill](skills/sku-snap/SKILL.md)
