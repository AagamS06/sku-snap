import pytest

from skusnap.parse import parse_order, parse_segment


@pytest.mark.parametrize("text,qty,unit,phrase", [
    ("2 cs romaine", 2, "cs", "romaine"),
    ("alb x3", 3, None, "alb"),
    ("10# yellow onions", 10, "lb", "yellow onions"),
    ("half case lemons", 0.5, "cs", "lemons"),
    ("4 dozen eggs", 4, "dz", "eggs"),
    ("salmon 10", 10, None, "salmon"),
    ("2 cajas de tomate roma", 2, "cs", "tomate roma"),
    ("- Romaine hearts x 2 cs", 2, "cs", "Romaine hearts"),
    ("also need parm", None, None, "parm"),
    ("3 kg yellow onions", 3, "kg", "yellow onions"),
    ("1/2 cs lemons", 0.5, "cs", "lemons"),
])
def test_parse_segment(text, qty, unit, phrase):
    q, u, p = parse_segment(text)
    assert q == qty
    assert u == unit
    assert p == phrase


def test_splits_lines_commas_and_quantities():
    lines = parse_order("Hi Sam, 2 cs romaine and 1 case lemons\n3 lb basil")
    phrases = [ln.phrase for ln in lines]
    assert phrases == ["Hi Sam", "romaine", "lemons", "basil"]


def test_keeps_and_inside_item_names():
    lines = parse_order("2 cs mac and cheese")
    assert [ln.phrase for ln in lines] == ["mac and cheese"]


def test_detects_repeat_with_weekday():
    lines = parse_order("Same as last Friday please")
    assert lines[0].repeat == {"weekday": "friday"}
