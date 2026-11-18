# sku-snap benchmark

A hand-labelled set of **fictional** orders for a fictional food distributor (no real customers, prices or orders). It measures how often sku-snap gets an order line right, and how often it gets one wrong *without flagging it*, which is the number that matters for an order desk.

```bash
sku-snap bench bench                    # all 40 cases
sku-snap bench bench --cases 'h*'       # only the held-out cases
sku-snap bench bench --verbose          # list every mismatch
sku-snap bench bench --format json      # machine-readable
sku-snap bench bench --min-sku-accuracy 0.97 --max-unsafe 2   # what CI runs; exit 1 if it regresses
```

## What's in it

| File | What it is |
|---|---|
| `catalog.csv` | 33 SKUs: produce, dry goods, seafood, cheese, dairy, oil, meat; pack sizes, multilingual aliases, 2 out of stock |
| `aliases.csv` | per-customer phrases (`tavola`, `pho-saigon`) and one global alias |
| `history.jsonl` | confirmed past orders for three customers (repeat orders, tie-breaks) |
| `cases/<id>.txt` | the raw order text, as a customer would send it |
| `cases/<id>.json` | what a careful rep expects for each line: `sku` (or `null`), `qty`, `unit`, the exact flag ids, and how many chatter lines should be ignored |

**Two groups of cases, kept apart on purpose:**

- `01`–`26` (85 lines): the development set, written first. Running it found two real bugs, which v0.2.0 fixes ("fresh" made "mozzarella" silently prefer *Fresh* Mozzarella; "Could you send 2 cs romaine" was dropped as chatter).
- `h01`–`h14` (38 lines): the held-out set, written **after** those fixes and scored once. The tool was not tuned against it, so its numbers are the honest estimate.

## Metrics

Expected and predicted lines are aligned by SKU sequence, so one dropped line does not shift every later comparison.

- **sku accuracy**: the predicted SKU equals the label (`null` = "should not be matched").
- **line accuracy**: SKU, quantity, unit and the exact flag set all match.
- **status accuracy**: ok vs review agrees.
- **unsafe lines**: lines marked `ok` that are wrong or should have been reviewed, plus lines silently missing from the output. An unsafe line is an item that ships wrong (or not at all) without anyone looking.
- **per-rule precision / recall** for every flag id.

## Results (v0.2.0)

| Set | Cases | Lines | SKU acc. | Line acc. | Status acc. | Unsafe |
|---|---|---|---|---|---|---|
| Development (`01`–`26`) | 26 | 85 | 100.0% | 100.0% | 100.0% | 0 |
| Held-out (`h01`–`h14`) | 14 | 38 | 94.7% | 86.8% | 92.1% | 2 |
| **All** | 40 | 123 | 98.4% | 95.9% | 97.6% | 2 |

Every review rule that fired was right (precision 100% for SS001 to SS009 and SS014). The misses, all in the held-out set:

| Case | Order text | What happened | Planned fix |
|---|---|---|---|
| h01 | `qty 2 cs iceberg` | **dropped as chatter** (unsafe) | treat `qty`/`qty:` as a quantity marker |
| h04 | `a couple bags of rice` | **dropped as chatter** (unsafe) | "a couple", "a few" as number words |
| h02 | `2 1/2 cs lemons` | read as 2 cs, SS010 | mixed fractions |
| h03 | `3-4 cs romaine` | read as 3 cs, SS010 | ranges → SS003 "how many?" |
| h14 | `tres bolsas harina` | right SKU, but "bolsas" not a unit → SS010 | Spanish unit words (bolsa, bolsas) |

Two lessons for the next version: a line that is dropped as chatter is the worst kind of miss (there is no flag at all), and the development-set score alone would have said "100%". Keep adding held-out cases before fixing things.

## Adding a case

1. Write the order as `cases/<id>.txt` (fictional names only).
2. Write `cases/<id>.json` with what a careful rep would want, **before** running the tool:

```json
{"customer": "tavola", "ignored": 1,
 "lines": [{"sku": "PRD-ROM-24", "qty": 3, "unit": "cs", "flags": []},
           {"sku": null, "qty": 5, "unit": "lb", "flags": ["SS002"]}]}
```

3. Run `sku-snap bench bench --cases '<id>' --verbose`. If the tool disagrees, decide whether the label or the tool is wrong; only fix the label if *it* was the mistake.
