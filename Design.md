# Design

sku-snap is a CLI today; these tokens also drive the launch video and the planned local review queue (Phase 3). The look: a calm order desk at night, a dark ledger with fresh-produce green for "ok" and amber for "needs a human".

## Colour palette

| Token | Dark (default) | Light | Use |
|---|---|---|---|
| `bg` | `#0F1412` | `#F7F6F1` | page background |
| `surface` | `#18201C` | `#FFFFFF` | cards, tables, terminal |
| `border` | `#26312B` | `#E3E1D8` | dividers, card outlines |
| `text` | `#ECEFE9` | `#17201B` | primary text |
| `muted` | `#9AA59E` | `#5D6B63` | secondary text, raw order text |
| `accent` | `#7BD389` | `#2F8F4E` | ok lines, links, primary buttons |
| `review` | `#F2B544` | `#B7791F` | review flags, the review counter |
| `error` | `#EF6F5E` | `#C2412D` | unknown item, input errors |
| `info` | `#6FB7F2` | `#2B6CB0` | info flags (conversions, history) |

Status is never shown by colour alone: every coloured state also has a word (`ok`, `REVIEW`) or a rule id.

## Themes
- **Dark** is the default for the review queue and media.
- **Light** follows `prefers-color-scheme: light`; same tokens, swapped values above.
- CLI output stays plain text (no ANSI colour in v0.1) so it pipes cleanly; colour is a roadmap option behind `--color`.

## Typography
- UI / headings: **Inter** (`https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap`)
- Order text, SKUs, CLI: **JetBrains Mono** (`https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap`)

| Step | Size / line height | Weight | Use |
|---|---|---|---|
| display | 64 / 1.05 | 800 | video titles |
| h1 | 32 / 1.2 | 700 | page title |
| h2 | 22 / 1.3 | 700 | section |
| body | 16 / 1.5 | 400 | text |
| small | 13 / 1.4 | 500 | labels, rule ids |
| mono | 14 / 1.5 | 400 | order lines, SKUs |

## Spacing
4 px base: `4, 8, 12, 16, 24, 32, 48, 64`. Card padding 24, table cell 8×12, page gutter 16 (mobile) / 32 (desktop). Radius: 6 (chips), 10 (inputs), 14 (cards).

## Components (review queue, roadmap)
- **Order line row**: raw text (mono, muted) → arrow → SKU chip + name; qty + unit right-aligned; status pill.
- **Status pill**: `ok` (accent on 12% accent tint), `REVIEW` (review on 12% tint), `UNKNOWN` (error).
- **Flag chip**: rule id + short title, tooltip with the full message.
- **Candidate picker**: up to 3 candidates with scores; picking one offers "remember for this customer" (calls `learn`).
- **Clarify panel**: the draft message, copy button.
- **Summary bar**: `9 lines · 6 ok · 3 review`.

## Accessibility
- Text contrast ≥ 4.5:1 on `bg` and `surface` in both themes (`#ECEFE9` on `#0F1412` ≈ 16:1; `#9AA59E` on `#0F1412` ≈ 7.3:1; `#5D6B63` on `#F7F6F1` ≈ 5.2:1).
- Status uses words + colour; rule ids are text, not icons only.
- Full keyboard flow in the review queue: `j/k` move, `1-3` pick candidate, `Enter` accept.
- Respect `prefers-reduced-motion`; no motion is needed to understand any state.
- Minimum touch target 44×44 px.
