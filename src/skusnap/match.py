"""Match parsed order lines to catalog SKUs and raise review flags."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .catalog import Item
from .parse import ParsedLine
from .units import convert

RULES: dict[str, tuple[str, str]] = {
    # id: (level, title)
    "SS001": ("review", "Unknown item: no catalog match"),
    "SS002": ("review", "Ambiguous item: several SKUs fit"),
    "SS003": ("review", "No quantity given"),
    "SS004": ("review", "Unit not sold for this SKU"),
    "SS005": ("info", "Unit converted to the selling unit"),
    "SS006": ("review", "SKU is out of stock"),
    "SS007": ("review", "Same SKU ordered on more than one line"),
    "SS008": ("review", "Repeat order requested but no matching history"),
    "SS009": ("review", "Quantity is not a whole selling unit"),
    "SS010": ("review", "Low-confidence match"),
    "SS011": ("info", "Ambiguity resolved from this customer's order history"),
    "SS012": ("info", "No unit given; assumed the selling unit"),
    "SS013": ("info", "Line expanded from a previous order"),
    "SS014": ("review", "No unit given and the quantity looks like a pack count"),
}

STOPWORDS = {"of", "the", "some", "de", "del", "la", "el", "los", "las", "for", "pls", "please", "fresh"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def tokens(text: str) -> list[str]:
    out = []
    for t in norm(text).split():
        if t in STOPWORDS or t.isdigit():
            continue
        if len(t) > 4 and t.endswith("es") and not t.endswith("ses"):
            t = t[:-2] if t[-3] in "hox" else t[:-1]
        elif len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]
        out.append(t)
    return out


def _tok_sim(q: str, c: str) -> float:
    if q == c:
        return 1.0
    if len(q) >= 3 and c.startswith(q):
        return 0.9                      # shorthand: "alb" -> "albacore"
    r = SequenceMatcher(None, q, c).ratio()
    return r if r >= 0.8 else 0.0       # typo tolerance: "romain" -> "romaine"


def score(phrase: str, target: str) -> float:
    q, c = tokens(phrase), tokens(target)
    if not q or not c:
        return 0.0
    coverage = sum(max(_tok_sim(t, u) for u in c) for t in q) / len(q)
    precision = sum(max(_tok_sim(u, t) for t in q) for u in c) / len(c)
    seq = SequenceMatcher(None, " ".join(q), " ".join(c)).ratio()
    return round(0.6 * coverage + 0.15 * precision + 0.25 * seq, 3)


@dataclass
class Flag:
    id: str
    message: str

    @property
    def level(self) -> str:
        return RULES[self.id][0]


@dataclass
class Line:
    line_no: int
    raw: str
    qty: float | None
    unit: str | None
    sku: str | None = None
    name: str | None = None
    score: float = 0.0
    source: str = "none"   # customer-alias | catalog-alias | fuzzy | history
    candidates: list[dict] = field(default_factory=list)
    flags: list[Flag] = field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return any(f.level == "review" for f in self.flags)


@dataclass
class Settings:
    min_score: float = 0.72
    low_score: float = 0.5
    margin: float = 0.06
    chatter_score: float = 0.6


def rank(phrase: str, catalog: dict[str, Item]) -> list[tuple[float, Item]]:
    ranked = []
    for item in catalog.values():
        best = max([score(phrase, item.name)] + [score(phrase, a) for a in item.aliases])
        ranked.append((best, item))
    ranked.sort(key=lambda x: (-x[0], x[1].sku))
    return ranked


def _history_skus(history: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for order in history:
        for ln in order.get("lines", []):
            counts[ln.get("sku")] = counts.get(ln.get("sku"), 0) + 1
    return counts


def _pick_history(history: list[dict], rep: dict) -> dict | None:
    if not history:
        return None
    if rep.get("weekday"):
        want = rep["weekday"]
        for order in reversed(history):
            try:
                d = dt.date.fromisoformat(order.get("date", ""))
            except ValueError:
                continue
            if d.strftime("%A").lower() == want:
                return order
        return None
    return history[-1]


def resolve_unit(line: Line, item: Item) -> None:
    """Fit the ordered quantity/unit to the item's selling unit."""
    if line.qty is None:
        return
    if line.unit is None:
        line.unit = item.unit
        line.flags.append(Flag("SS012", f"assumed {item.unit}"))
        if item.pack_size and item.pack_unit and line.qty >= item.pack_size:
            alt = line.qty / item.pack_size
            line.flags.append(Flag("SS014", f"{_fmt(line.qty)} {item.unit} assumed; did you mean "
                                   f"{_fmt(line.qty)} {item.pack_unit} (= {_fmt(round(alt, 2))} {item.unit})?"))
            return
    elif line.unit != item.unit:
        qty, src = line.qty, line.unit
        converted = convert(qty, src, item.unit)
        if converted is None and item.pack_size and item.pack_unit:
            in_pack = convert(qty, src, item.pack_unit)
            if in_pack is not None:
                converted = in_pack / item.pack_size
        if converted is None:
            line.flags.append(Flag("SS004", f"ordered in {src}; {item.sku} is sold per {item.unit}"))
            return
        line.qty, line.unit = round(converted, 3), item.unit
        line.flags.append(Flag("SS005", f"{_fmt(qty)} {src} -> {_fmt(line.qty)} {item.unit}"))
    if item.unit in ("cs", "bag", "tray", "btl", "tub", "bunch", "ea", "dz") and line.qty != int(line.qty):
        up = int(line.qty) + 1
        line.flags.append(Flag("SS009", f"{_fmt(line.qty)} {item.unit} is not a whole unit; round to {up}?"))


def _fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else f"{x:g}"


def match_lines(parsed: list[ParsedLine], catalog: dict[str, Item], aliases: dict[str, str],
                history: list[dict], settings: Settings | None = None) -> tuple[list[Line], list[dict]]:
    """Return (order lines, ignored chatter lines)."""
    s = settings or Settings()
    norm_aliases = {norm(k): v for k, v in aliases.items() if v in catalog}
    hist_counts = _history_skus(history)
    lines: list[Line] = []
    ignored: list[dict] = []

    for p in parsed:
        if p.repeat is not None:
            order = _pick_history(history, p.repeat)
            if order is None:
                ln = Line(p.line_no, p.raw, None, None)
                ln.flags.append(Flag("SS008", "no earlier order found for this customer"
                                     + (f" on a {p.repeat['weekday'].title()}" if p.repeat.get("weekday") else "")))
                lines.append(ln)
                continue
            for h in order.get("lines", []):
                item = catalog.get(h.get("sku"))
                ln = Line(p.line_no, p.raw, float(h.get("qty", 1)), h.get("unit") or (item.unit if item else None))
                ln.source, ln.score = "history", 1.0
                if item is None:
                    ln.flags.append(Flag("SS001", f"history SKU {h.get('sku')} is no longer in the catalog"))
                else:
                    ln.sku, ln.name = item.sku, item.name
                    ln.flags.append(Flag("SS013", f"from order dated {order.get('date', '?')}"))
                    if not item.in_stock:
                        ln.flags.append(Flag("SS006", f"{item.sku} is marked out of stock"))
                lines.append(ln)
            continue

        phrase = p.phrase
        if not phrase:
            ignored.append({"line_no": p.line_no, "raw": p.raw})
            continue
        ln = Line(p.line_no, p.raw, p.qty, p.unit)
        key = norm(phrase)
        item: Item | None = None
        if key in norm_aliases:
            item, ln.score, ln.source = catalog[norm_aliases[key]], 1.0, "customer-alias"
        else:
            exact = [it for it in catalog.values() if key in {norm(a) for a in it.aliases} or key == norm(it.name)]
            if len(exact) == 1:
                item, ln.score, ln.source = exact[0], 0.97, "catalog-alias"
        if item is None:
            ranked = rank(phrase, catalog)
            top_score, top = ranked[0]
            if p.qty is None and top_score < s.chatter_score:
                ignored.append({"line_no": p.line_no, "raw": p.raw})   # greeting / sign-off
                continue
            ln.candidates = [{"sku": it.sku, "name": it.name, "score": sc} for sc, it in ranked[:3] if sc >= s.low_score]
            close = [(sc, it) for sc, it in ranked if sc >= s.low_score and top_score - sc <= s.margin]
            if top_score < s.low_score:
                ln.flags.append(Flag("SS001", f"nothing in the catalog looks like '{phrase}'"))
                ln.candidates = [{"sku": it.sku, "name": it.name, "score": sc} for sc, it in ranked[:3]]
                lines.append(ln)
                continue
            if len(close) > 1:
                known = [(sc, it) for sc, it in close if it.sku in hist_counts]
                if len(known) == 1:
                    item, ln.score, ln.source = known[0][1], known[0][0], "history"
                    ln.flags.append(Flag("SS011", f"{len(close)} SKUs fit; customer has ordered {item.sku} before"))
                else:
                    ln.flags.append(Flag("SS002", f"{len(close)} SKUs fit '{phrase}': "
                                         + ", ".join(it.sku for _, it in close[:4])))
                    lines.append(ln)
                    continue
            else:
                item, ln.score, ln.source = top, top_score, "fuzzy"
                if top_score < s.min_score:
                    ln.flags.append(Flag("SS010", f"best match {top.sku} scored {top_score:.2f}"))
        ln.sku, ln.name = item.sku, item.name
        if p.qty is None:
            ln.unit = item.unit
            ln.flags.append(Flag("SS003", f"how many {item.unit} of {item.name}?"))
        else:
            resolve_unit(ln, item)
        if not item.in_stock:
            ln.flags.append(Flag("SS006", f"{item.sku} is marked out of stock"))
        lines.append(ln)

    seen: dict[str, int] = {}
    for ln in lines:
        if ln.sku:
            if ln.sku in seen and ln.source != "history":
                ln.flags.append(Flag("SS007", f"also on line {seen[ln.sku]}"))
            seen.setdefault(ln.sku, ln.line_no)
    return lines, ignored
