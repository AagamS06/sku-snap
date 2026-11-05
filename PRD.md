# PRD: sku-snap

> Turn messy B2B orders (texts, emails, notes) into catalog-matched order lines, with a review queue and an ERP-ready CSV. Offline and explainable.

## 1. Problem statement

Restaurants and other small buyers still order from their distributors the way they always have: a text at 11pm, an email with a bulleted list, a photo of a handwritten note, a voicemail. The words don't match the distributor's catalog ("alb x3", "salmon 10", "half case lemons", "2 cajas de tomate roma"). Before the order can ship, a sales rep re-types each line into the ERP and decides, line by line, which SKU the customer meant, what unit they meant, and what to ask them about.

That re-keying is slow, it's where mistakes happen, and it depends on knowledge that lives in one rep's head (what *this* customer means by "parm", what they ordered last Friday).

## 2. Gaps this project addresses (observed, Nov 2026)

Research covered the current YC batch (**Fall 2026**, Demo Day 2 Dec 2026) and the previous one (**Summer 2026**, Demo Day 10 Sep 2026), about 470 company one-liners, with a closer look at the food-distribution, wholesale and restaurant back-office cluster.

| # | Gap / pain point | Where it was observed |
|---|---|---|
| G1 | Orders arrive as texts and handwritten notes and a rep re-enters them by hand. At one distributor, ~60 orders/day, some over 75 lines, and reps spend ~30% of their day on manual work. | **Asakana** (F26) launch coverage: "texts to ERP" |
| G2 | One word maps to many SKUs: "salmon" can be one of ten catalog items, and the right one depends on the customer's past orders and shorthand. | **Asakana** (F26) |
| G3 | Orders in Chinese, Korean, Spanish and Japanese must be matched to an English catalog. | **Asakana** (F26) |
| G4 | "I have 6 reps typing 600 lines of orders from email into the ERP every day." Orders come by email; exceptions need to go to a human and the system should learn from corrections. | **Whitespace** (S26) launch: "AI Operating System for Wholesale Distribution" |
| G5 | "Repeat last Friday's order" style requests need order history. | **Asakana** (F26) |
| G6 | Restaurants on the buying side automate purchasing and invoices; the order they send still has to be understood by the supplier. | **Marble** (S26), **Truffle** (S26) restaurant back-of-house |
| G7 | All of the above are hosted, closed products. There is no small, open, offline tool a two-person distributor (or a student, or one of these startups' own test suites) can run to see *why* a line was matched or flagged. | Not described on any of the pages reviewed |

sku-snap is a small, inspectable baseline for G1 to G5 and the supplier side of G6, and it is open source to cover G7. It is **not** affiliated with, used by, or endorsed by any company above.

## 3. Target users

- **Order-desk reps at small and mid-size food / wholesale distributors** who re-key texted and emailed orders today.
- **Small distributors without an AI vendor**, who want a free first pass and a review queue.
- **Developers** building order-intake automation who want a deterministic baseline and a test-fixture format (catalog CSV + aliases + history + expected JSON).
- **Restaurant buyers** who want to check an order against a supplier's catalog before sending it.

## 4. User stories

1. As a rep, I paste a customer's text into sku-snap and get a table: which lines are ready and which need me.
2. As a rep, when "salmon" fits three SKUs, I see the candidates; if the customer has only ever bought one of them, sku-snap picks it and tells me why.
3. As a rep, when a customer orders "48 heads romaine", it becomes 2 cases of the 24-count SKU, and I can see the conversion.
4. As a rep, when I fix a mapping once ("parm" means the wedge for Luigi's), I run `sku-snap learn` and it's right next time.
5. As a rep, I get a ready-to-send clarification message for only the lines that need the customer.
6. As an ops lead, I export a CSV I can import into the ERP, with review lines clearly marked.
7. As a developer, I get a stable JSON contract and exit codes so I can put sku-snap in a pipeline.

## 5. Core features

### MVP (v0.1.0, shipped in this repo)
- Rule-based parser for quantities (digits, fractions, "half", word numbers incl. Spanish 1 to 5), units (cs/case/caja/box, lb/#, kg, ea/heads, dz/dozen, bag, bunch, ...), leading or trailing quantities ("alb x3", "salmon 10").
- Line splitting on newlines, `;`, commas, and on "and / & / +" only when the next part starts with a quantity ("mac and cheese" stays whole).
- Matching: customer aliases → catalog aliases (any language you list) → fuzzy token scoring with shorthand prefixes ("alb" → "albacore") and typo tolerance.
- Ambiguity handling with candidates; resolved from the customer's history when exactly one candidate was ordered before.
- Unit fitting: exact conversions (dz↔ea, kg↔lb, oz→lb) and catalog pack sizes (24 ea per cs).
- "Same as last Friday" / "the usual" expansion from history.
- 14 flag rules (SS001 to SS014) with info vs review levels.
- Output as table, JSON (stable contract) or ERP-import CSV; `--clarify` draft message.
- `learn` command to store customer aliases; `rules` to list flags.
- Exit codes 0 / 1 / 2. Python 3.10+, no runtime dependencies.
- Claude Agent Skill (`skills/sku-snap/SKILL.md`).

### Later (roadmap, not built)
- Image / PDF input via OCR (handwritten notes, faxed POs).
- Optional local LLM fallback for phrases the rules can't parse, always marked as such.
- Small local web review queue (accept / fix / learn in one click), see Design.md.
- ERP export profiles (column mappings for common systems).
- Substitution suggestions for out-of-stock SKUs.
- Benchmark set of anonymised orders with expected outputs.

## 6. Non-goals

- Not an ERP, not an ordering portal, and it never places or submits orders.
- No cloud service, no account, no telemetry. Orders never leave the machine.
- No translation model: non-English names match only through aliases you provide.
- No pricing, credit or delivery-route decisions.

## 7. Success metrics

- On the bundled examples: every line lands in "ok" or "review" with a reason; zero silent guesses (enforced by tests).
- Time to first result for a new user: under 2 minutes from `pip install` (one command, no dependencies).
- Rep effort: lines needing a human are a minority of lines on real orders (to be measured with a benchmark set in Phase 2; no numbers claimed yet).
- Learning: a corrected phrase is matched by `customer-alias` on the next run (test-covered).
