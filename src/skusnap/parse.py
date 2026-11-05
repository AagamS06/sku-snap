"""Turn free-text order messages into candidate order lines.

The parser is deliberately rule-based and explainable: every line keeps
its raw text, and nothing is guessed silently. Quantity and unit are
pulled out; whatever is left is the item phrase that the matcher scores.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .units import normalise_unit

WORD_NUMBERS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "fifteen": 15, "twenty": 20, "half": 0.5, "couple": 2,
    "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
}
UNICODE_FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75}

REPEAT_PATTERNS = [
    re.compile(r"\b(same as|repeat|copy)\b.*\b(last|previous|usual)\b", re.I),
    re.compile(r"\bthe usual\b", re.I),
    re.compile(r"\busual order\b", re.I),
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_NUM = r"(?:\d+(?:\.\d+)?(?:/\d+)?|[½¼¾])"
_LEAD = re.compile(rf"^(?P<x>x\s*)?(?P<qty>{_NUM})\s*(?P<x2>x\b)?\s*(?P<rest>.*)$", re.I)
_TRAIL = re.compile(rf"^(?P<rest>.*?)\s*(?:x\s*|-\s*|:\s*)?(?P<qty>{_NUM})\s*(?P<unit>[a-z#]+)?\s*$", re.I)
_SPLIT = re.compile(r"[\n;]+")
_SUBSPLIT = re.compile(r"\s*(?:,|\band\b|&|\+)\s*(?=(?:\d|[½¼¾]|a\s|an\s|one\s|two\s|three\s|half\s|x\d))", re.I)
_FILLER = re.compile(r"^(?:also|plus|pls|please|and|i need|we need|need|can i get|can we get|get|send|add)\b[\s,:]*", re.I)


@dataclass
class ParsedLine:
    line_no: int
    raw: str
    qty: float | None
    unit: str | None
    phrase: str
    repeat: dict | None = None  # {"weekday": "friday"} or {} for "last order"
    notes: list[str] = field(default_factory=list)


def _to_number(tok: str) -> float | None:
    tok = tok.strip().lower()
    if tok in UNICODE_FRACTIONS:
        return UNICODE_FRACTIONS[tok]
    if tok in WORD_NUMBERS:
        return float(WORD_NUMBERS[tok])
    try:
        if "/" in tok:
            a, b = tok.split("/", 1)
            return float(a) / float(b)
        return float(tok)
    except (ValueError, ZeroDivisionError):
        return None


def _strip_filler(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _FILLER.sub("", text).strip()
    return text


def parse_segment(segment: str) -> tuple[float | None, str | None, str]:
    """Return (qty, unit, phrase) for one order segment."""
    text = _strip_filler(segment.strip(" -*•\t:.,"))
    text = re.sub(r"(\d)#", r"\1 #", text)          # "10#" -> "10 #"
    text = re.sub(r"(\d)([a-z]{2,})\b", r"\1 \2", text, flags=re.I)  # "2cs" -> "2 cs"
    words = text.split()
    if not words:
        return None, None, ""

    qty: float | None = None
    unit: str | None = None

    # word-number lead ("two cases", "half case", "a dozen")
    first = words[0].lower()
    if first in WORD_NUMBERS or first in UNICODE_FRACTIONS:
        if not (first in ("a", "an") and len(words) > 1 and normalise_unit(words[1]) is None):
            qty = _to_number(first)
            words = words[1:]
    else:
        m = _LEAD.match(text)
        if m and _to_number(m.group("qty")) is not None:
            qty = _to_number(m.group("qty"))
            words = m.group("rest").split()

    if qty is not None and words:
        u = normalise_unit(words[0])
        if u:
            unit, words = u, words[1:]
            if words and words[0].lower() in ("of", "de", "del"):
                words = words[1:]
        elif len(words) > 1 and words[0].lower() == "x":
            words = words[1:]

    if qty is None:
        # trailing quantity: "salmon 2", "alb x3", "lemons - 2 cs"
        m = _TRAIL.match(" ".join(words))
        if m and _to_number(m.group("qty")) is not None and m.group("rest").strip():
            u = normalise_unit(m.group("unit")) if m.group("unit") else None
            if m.group("unit") is None or u:
                qty = _to_number(m.group("qty"))
                unit = u
                words = m.group("rest").split()

    phrase = " ".join(words).strip(" -:,.x")
    # "dozen eggs" with qty -> unit dz
    if unit is None and phrase.lower().startswith("dozen "):
        unit, phrase = "dz", phrase[6:]
    return qty, unit, phrase


def detect_repeat(text: str) -> dict | None:
    for pat in REPEAT_PATTERNS:
        if pat.search(text):
            low = text.lower()
            for day in WEEKDAYS:
                if day in low:
                    return {"weekday": day}
            return {}
    return None


def parse_order(text: str) -> list[ParsedLine]:
    """Split a message into ParsedLines (line numbers are 1-based segments)."""
    out: list[ParsedLine] = []
    n = 0
    for chunk in _SPLIT.split(text):
        chunk = chunk.strip()
        if not chunk:
            continue
        for seg in _split_commas(chunk):
            seg = seg.strip()
            if not seg:
                continue
            n += 1
            rep = detect_repeat(seg)
            if rep is not None:
                out.append(ParsedLine(n, seg, None, None, "", repeat=rep))
                continue
            qty, unit, phrase = parse_segment(seg)
            out.append(ParsedLine(n, seg, qty, unit, phrase))
    return out


def _split_commas(chunk: str) -> list[str]:
    # split on commas always (greetings like "Hey Sam, for tmrw:" become chatter),
    # and on and/&/+ only when the next part starts with a quantity
    parts: list[str] = []
    for piece in chunk.split(","):
        parts.extend(_SUBSPLIT.split(piece))
    return parts
