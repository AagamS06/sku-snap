# sku-snap: launch video plan (Built It. Bragging About It. · Ep. 3)

**Format:** one episode made of two brag clips that merge seamlessly. 1920x1080, 30 fps, 31.5 s total, with music.
- **Clip 1: THE PROBLEM** (tone: cinematic): 0.0-13.5 s (13.5 s)
- **Clip 2: THE SOLUTION** (tone: default): 13.5-31.5 s (18.0 s)

**Angle:** clip 1 sits in the late-night texted order and every question a rep has to answer before it can ship; clip 2 reveals sku-snap next to that same message and shows the real CLI output answering those questions.

**Honesty:** every row, SKU, flag and message comes from a real `sku-snap match` run on the repo's examples (examples/orders/luigis-text.txt, fictional customer "Luigi's"). Problem statements come from the PRD (gaps observed in YC F26/S26 food-distribution and wholesale companies). No metrics, users, logos or endorsements. OCR / review queue / ERP profiles appear only under "Roadmap".

## Storyboard

### Clip 1: The problem (cinematic: letterbox bars, slow push-ins, drone, impacts)
| Time | Scene |
|---|---|
| 0.0-2.45 | Series ident: "BUILT IT. BRAGGING ABOUT IT." / "Ep. 3" (accent) / "sku-snap", underline draws in. Letterbox bars slide in from 2.2 s. |
| 2.5-6.7 | "11:48 pm. An order comes in." The customer's text appears bubble by bubble (48 heads romaine / alb x3 · salmon 10 / half case lemons, also need parm / 2 cajas de tomate roma). |
| 6.8-13.3 | The message card slides left. "Every line is a question." Four questions land one by one: which of 3 salmon SKUs? how many cases is 48 heads? they only sell whole cases; which parm, and how much? Then "Then someone re-types every line into the ERP." |

### Seam (13.0-14.0)
The questions and title clear, the letterbox bars retract, and the **same message card stays on screen** (shared element). The music lands on a downbeat at 13.5 s with a soft impact, switching from drone to plucks.

### Clip 2: The solution (default: punchy reveals, plucks + kick)
| Time | Scene |
|---|---|
| 13.5-16.9 | Reveal beside the message card: "sku-snap" / "Messy orders in. Catalog SKUs out." / "Offline CLI · flags only what needs a human". The card gets a green outline (it is being processed). |
| 17.0-22.1 | Real output table: 9 rows slide in with ok/REVIEW pills and rule ids; "6 ok · 3 need review · greetings ignored". Header: sku-snap · BUILT IT. BRAGGING ABOUT IT. · EP. 3 (poster frame at 21.3 s). |
| 22.2-26.4 | "Remembers. Converts. Asks, never guesses." Three cards: salmon → Atlantic Salmon Fillet (SS011), 48 heads → 2 cs (SS005), half case → "Round up to 1?" (SS009); "sku-snap learn". |
| 26.5-31.5 | Series end card: "BUILT IT. BRAGGING ABOUT IT. · EP. 3", "Try it on your next order.", typed pip install, chips (0 runtime deps / JSON + ERP CSV / Claude skill included), github.com/AagamS06/sku-snap, roadmap line. |

## Visual identity (from the video's CSS)
- Background: #0F1412 (subtle radial glow rgba(123,211,137,.07)); letterbox bars #070A09
- Card/surface: #18201C (border #26312B)
- Text: #ECEFE9
- Muted text: #9AA59E
- Accent: #7BD389 (review amber #F2B544, info blue #6FB7F2)
- Font family: Inter (headings/UI) + JetBrains Mono (order text, SKUs)
- Google Fonts CSS URL: https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&family=JetBrains+Mono:wght@400;600&display=swap

## Sound
- Key and mode: **A minor** (Am - F - C - G), 112 bpm, one continuous track.
- Clip 1: ident chime, low A drone, slow pad (two bars per chord), impacts on each title, muted in-key plucks under each question, riser into the seam.
- Clip 2: soft impact on the seam downbeat, pad one bar per chord, pluck arpeggio + soft kick and hat, row ticks, whooshes on scene changes, final A-minor chord.
- Peak -1 dBFS; RMS about -18 dBFS.

## Deliverables
sku-snap.mp4 (merged episode, poster as frame 0), sku-snap-clip1.mp4, sku-snap-clip2.mp4, sku-snap-cover.jpg (1280x720), sku-snap.txt, this plan. Poster still at work/poster.png, plain background at work/bg.png.
