# sku-snap launch video plan

**Angle:** the late-night texted order every distributor rep re-types, and the tool that turns it into SKU lines while flagging only what needs a human.
**Hook (0-4.6s):** a real-looking customer text ("48 heads romaine", "alb x3 · salmon 10", "half case lemons, also need parm", "2 cajas de tomate roma") with "Someone has to re-type it into the ERP."
**Highlights:** (1) the real `sku-snap match` output on examples/orders/luigis-text.txt, rows appearing one by one with ok/REVIEW pills and rule ids; (2) history tie-break (SS011), unit fitting (SS005), drafted question (SS009).
**Punchline:** "Try it on your next order." + install command, 0 runtime deps / JSON + ERP CSV / Claude skill included, repo URL, roadmap labelled as roadmap.
**Tone:** default. **Format:** 1920x1080, 30 fps, 21.0 s, with music.
**Honesty:** all table rows, SKUs, flags and messages come from a real run of the CLI on the repo's example files. "Luigi's" is the fictional example customer from examples/. No metrics, users, logos or endorsements. OCR/review queue/ERP profiles shown only under "Roadmap".

## Storyboard
| # | Time | Scene |
|---|---|---|
| 1 | 0.0-4.6s | Hook: "Your customer texted an order." + 4 message bubbles pop in + "Someone has to re-type it into the ERP." |
| 2 | 4.7-8.0s | Reveal: "sku-snap" wordmark, "Messy orders in. Catalog SKUs out.", "Offline CLI · flags only what needs a human" |
| 3 | 8.1-13.1s | "Every line: matched or flagged." 9 real output rows slide in, summary "6 ok · 3 need review · greetings ignored" (poster frame at 12.6s) |
| 4 | 13.2-17.0s | "Remembers. Converts. Asks, never guesses." 3 cards: salmon (SS011), romaine (SS005), lemons (SS009) + "sku-snap learn" |
| 5 | 17.1-21.0s | "Try it on your next order." typed pip install, chips, github.com/AagamS06/sku-snap, roadmap line |
Transitions: 0.3s fade out to background, 0.1s gap, 0.35s fade in (dip, no crossfade).

## Visual identity (used in the video's CSS)
- Background: #0F1412 (with a subtle radial accent glow, rgba(123,211,137,.07))
- Card/surface: #18201C (border #26312B)
- Text: #ECEFE9
- Muted text: #9AA59E
- Accent: #7BD389 (review amber #F2B544, info blue #6FB7F2)
- Font family: Inter (headings/UI) + JetBrains Mono (order text, SKUs)
- Google Fonts CSS URL: https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@400;600&display=swap

## Sound
- Key and mode: **A minor** (progression Am - F - C - G, 112 bpm)
- Soft detuned pad throughout; pluck arpeggio + soft kick from the reveal; in-key blips for message bubbles and table rows; quiet whooshes at scene changes; final A-minor chord ring. Peak -1 dBFS, RMS about -16.6 dBFS.

## Deliverables
sku-snap.mp4 (poster baked in as frame 0), sku-snap-cover.jpg (1280x720), sku-snap.txt (YouTube title/description), this plan. Poster still kept at work/poster.png; plain background at work/bg.png.
