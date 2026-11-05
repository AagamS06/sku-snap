# Rules

Ground rules for anyone (human or AI) contributing to sku-snap.

## Do
- Keep every decision explainable: a line is either `ok` or carries a flag that says why.
- Prefer flagging over guessing. A wrong SKU that ships is worse than a question to the customer.
- Keep the JSON contract and exit codes stable; bump the minor version and note it in Memory.md if they change.
- Add or update a test for every parser or matcher change (parametrise parser cases in `tests/test_parse.py`).
- Keep examples realistic but fictional (no real customer names, prices or orders).

## Avoid
- Runtime dependencies. The standard library is the budget for `src/`. Discuss first if one is truly needed.
- Network calls of any kind in the core path.
- Silent fallbacks (e.g. assuming a SKU when two fit). Use SS002 / SS010 instead.
- Locale-specific magic without a test (number words, unit names).

## Approved libraries
- Runtime: Python standard library only.
- Dev: `pytest`. Optional later: `ruff` for linting.
- Roadmap features (OCR, local LLM, web UI) must be optional extras (`pip install sku-snap[ocr]`), never core.

## Coding conventions
- Python 3.10+, type hints on public functions, `from __future__ import annotations`.
- Dataclasses for records; pure functions for the pipeline.
- Names: modules lowercase, rule ids `SS###`, CLI flags kebab-case.
- Line length ~110, f-strings, no wildcard imports.
- User-facing messages are short and concrete ("0.5 cs is not a whole unit; round to 1?").

## Boundaries for AI contributors
- **May**: fix bugs, add parser cases, add rules with tests, improve docs, add examples.
- **May not** without asking: change the JSON contract, exit codes, rule ids or thresholds; add dependencies; delete files they didn't create; rewrite history (force-push).
- Never commit secrets, tokens, real customer data or real price lists.
- Ask before destructive changes (deleting files, renaming modules, migrating file formats).
- Only document features the code actually has; label everything else "roadmap".

## Error-handling procedure
1. Bad input (missing file, missing columns, duplicate SKU, invalid JSON) → raise `InputError` with file and line → CLI prints `sku-snap: error: ...` and exits **2**.
2. Order content problems are never errors: they are flags, and the CLI exits **1**.
3. Unexpected exceptions are bugs: reproduce with a test, fix, then add the case to `tests/`.

## Testing expectations
- `python -m pytest -q` must pass before every commit (CI runs 3.10 and 3.12).
- New rule → at least one test that triggers it and one that doesn't.
- Example outputs quoted in README / SKILL.md must match a real run.

## Security basics
- Orders and catalogs can contain customer data: process locally, never upload, never log to remote services.
- Treat order text as untrusted input: it is parsed, never executed or evaluated.
- Files are read as UTF-8 and written only where the user points (`--out`, `--aliases`).
