from pathlib import Path

from skusnap.catalog import load_aliases, load_catalog, load_history
from skusnap.match import match_lines, score
from skusnap.parse import parse_order

EX = Path(__file__).resolve().parents[1] / "examples"


def run(text, customer=None):
    cat = load_catalog(EX / "catalog.csv")
    aliases = load_aliases(EX / "aliases.csv", customer)
    hist = load_history(EX / "history.jsonl", customer)
    lines, ignored = match_lines(parse_order(text), cat, aliases, hist)
    return lines, ignored


def ids(line):
    return {f.id for f in line.flags}


def test_score_prefers_exact_tokens():
    assert score("romaine", "Romaine Hearts 24ct") > score("romaine", "Roma Tomatoes 25lb")


def test_pack_conversion_to_cases():
    (ln,), _ = run("48 heads romaine")
    assert (ln.sku, ln.qty, ln.unit) == ("PRD-ROM-24", 2, "cs")
    assert "SS005" in ids(ln) and not ln.needs_review


def test_fractional_case_needs_review():
    (ln,), _ = run("half case lemons")
    assert "SS009" in ids(ln) and ln.needs_review


def test_ambiguous_without_history():
    (ln,), _ = run("salmon 10")
    assert ln.sku is None and "SS002" in ids(ln)
    assert {c["sku"] for c in ln.candidates} >= {"SEA-SAL-ATL", "SEA-SAL-KNG"}


def test_history_resolves_ambiguity():
    (ln,), _ = run("salmon 10", customer="luigis")
    assert ln.sku == "SEA-SAL-ATL" and "SS011" in ids(ln)


def test_customer_alias_beats_fuzzy():
    (ln,), _ = run("2 lb parm", customer="luigis")
    assert ln.sku == "CHE-PARM-WHL" and ln.source == "customer-alias"


def test_multilingual_alias():
    (ln,), _ = run("2 cajas de tomate roma")
    assert ln.sku == "PRD-TOM-ROMA" and ln.qty == 2


def test_unknown_item():
    (ln,), _ = run("1 bx micro greens")
    assert "SS001" in ids(ln)


def test_out_of_stock():
    (ln,), _ = run("1 bunch basil")
    assert "SS006" in ids(ln)


def test_pack_count_without_unit():
    (ln,), _ = run("120 eggs")
    assert "SS014" in ids(ln)


def test_chatter_is_ignored():
    lines, ignored = run("Hey Sam\n2 cs romaine\nthx - Luigi")
    assert len(lines) == 1 and len(ignored) == 2


def test_repeat_order_expands_history():
    lines, _ = run("Same as last Friday", customer="luigis")
    assert [ln.sku for ln in lines] == ["PRD-ROM-24", "PRD-TOM-ROMA", "CHE-PARM-WHL"]
    assert all("SS013" in ids(ln) for ln in lines)


def test_repeat_without_history_flags():
    (ln,), _ = run("same as last week")
    assert "SS008" in ids(ln)


def test_duplicate_sku():
    lines, _ = run("2 cs romaine\n1 cs romaine hearts")
    assert "SS007" in ids(lines[1])
