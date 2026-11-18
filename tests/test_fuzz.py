"""Seeded fuzz / property tests: random order text must never crash the pipeline,
and every output line must keep its invariants. Stdlib only, deterministic."""
import random
from pathlib import Path

from skusnap.catalog import load_catalog
from skusnap.match import RULES, match_lines
from skusnap.parse import parse_order
from skusnap.report import clarify, to_csv, to_json

CAT = load_catalog(Path(__file__).resolve().parents[1] / "bench" / "catalog.csv")
VOCAB = ["2", "1/2", "½", "half", "a", "dos", "x3", "10#", "3kg", "cs", "case", "bag", "dz", "lb", "heads",
         "romaine", "salmon", "mozz", "parm", "eggs", "limes", "of", "and", "&", ",", ";", "-", ":", "pls",
         "same as last friday", "the usual", "could you send", "hi", "thanks", "é", "日本", "0", "999999",
         "1/0", "#", "x", "..", "\t", "''", "\"", "🍋"]
HISTORY = [{"customer": "c", "date": "2026-11-06", "lines": [{"sku": "PRD-ROM-24", "qty": 1, "unit": "cs"},
                                                            {"sku": "GONE", "qty": 2, "unit": "lb"}]}]


def random_order(rng):
    lines = []
    for _ in range(rng.randint(0, 6)):
        lines.append(" ".join(rng.choice(VOCAB) for _ in range(rng.randint(0, 7))))
    return rng.choice(["\n", "\r\n", ", ", "; "]).join(lines)


def test_thousand_random_orders_never_crash():
    rng = random.Random(20261118)
    for _ in range(1000):
        text = random_order(rng)
        parsed = parse_order(text)
        lines, ignored = match_lines(parsed, CAT, {"parm": "CHE-PARM-WHL"}, HISTORY)
        to_json(lines, ignored, "c")
        to_csv(lines)
        clarify(lines, "c")
        seen = {p.line_no for p in parsed}
        for ln in lines:
            assert ln.line_no in seen
            assert ln.sku is None or ln.sku in CAT
            assert ln.qty is None or ln.qty >= 0
            assert all(f.id in RULES for f in ln.flags)
            if ln.sku is None and ln.qty is not None:
                assert ln.needs_review, f"unmatched line passed as ok: {ln.raw!r}"
