"""Render matched lines as a table, JSON, ERP-import CSV, or a clarification draft."""

from __future__ import annotations

import csv
import io
import json

from . import __version__
from .match import RULES, Line, _fmt


def to_dict(lines: list[Line], ignored: list[dict], customer: str | None) -> dict:
    review = sum(1 for ln in lines if ln.needs_review)
    return {
        "tool": "sku-snap",
        "version": __version__,
        "customer": customer,
        "status": "needs_review" if review else "clean",
        "summary": {"lines": len(lines), "ok": len(lines) - review, "review": review, "ignored": len(ignored)},
        "lines": [
            {
                "line_no": ln.line_no,
                "raw": ln.raw,
                "sku": ln.sku,
                "name": ln.name,
                "qty": ln.qty,
                "unit": ln.unit,
                "score": ln.score,
                "match_source": ln.source,
                "status": "review" if ln.needs_review else "ok",
                "flags": [{"id": f.id, "level": f.level, "message": f.message} for f in ln.flags],
                "candidates": ln.candidates,
            }
            for ln in lines
        ],
        "ignored": ignored,
    }


def to_json(lines: list[Line], ignored: list[dict], customer: str | None) -> str:
    return json.dumps(to_dict(lines, ignored, customer), indent=2, ensure_ascii=False)


def to_csv(lines: list[Line]) -> str:
    """ERP-import style CSV: one row per line, review rows marked."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["line_no", "sku", "qty", "unit", "name", "status", "flags", "raw"])
    for ln in lines:
        w.writerow([ln.line_no, ln.sku or "", "" if ln.qty is None else _fmt(ln.qty), ln.unit or "",
                    ln.name or "", "review" if ln.needs_review else "ok",
                    " ".join(f.id for f in ln.flags), ln.raw])
    return buf.getvalue()


def to_table(lines: list[Line], ignored: list[dict], customer: str | None) -> str:
    rows = [("#", "STATUS", "QTY", "UNIT", "SKU", "ITEM", "FLAGS")]
    for ln in lines:
        rows.append((str(ln.line_no), "REVIEW" if ln.needs_review else "ok",
                     "-" if ln.qty is None else _fmt(ln.qty), ln.unit or "-", ln.sku or "-",
                     (ln.name or ln.raw)[:34], ",".join(f.id for f in ln.flags) or "-"))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    out = ["  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows]
    review = [ln for ln in lines if ln.needs_review]
    out.append("")
    out.append(f"{len(lines)} lines, {len(lines) - len(review)} ok, {len(review)} need review"
               + (f", {len(ignored)} ignored (chatter)" if ignored else "")
               + (f"  [customer: {customer}]" if customer else ""))
    for ln in lines:
        for f in ln.flags:
            if f.level == "review":
                out.append(f"  line {ln.line_no} {f.id} {RULES[f.id][1]}: {f.message}")
    return "\n".join(out)


def clarify(lines: list[Line], customer: str | None) -> str:
    """Draft a short message asking the customer about the lines that need review."""
    asks = []
    for ln in lines:
        ids = {f.id for f in ln.flags}
        q = None
        if "SS002" in ids:
            opts = " or ".join(c["name"] for c in ln.candidates[:3]) or "which item"
            q = f'"{ln.raw}": did you mean {opts}?'
        elif "SS001" in ids:
            q = f'"{ln.raw}": we couldn\'t find this item. Can you describe it or send a photo?'
        elif "SS003" in ids:
            q = f'"{ln.raw}": how many {ln.unit or "units"} of {ln.name}?'
        elif "SS009" in ids:
            q = f'"{ln.raw}": {ln.name} comes in whole {ln.unit}. Round up to {int(ln.qty) + 1}?'
        elif "SS004" in ids:
            msg = next(f.message for f in ln.flags if f.id == "SS004")
            q = f'"{ln.raw}": {msg}. How many should we send?'
        elif "SS006" in ids:
            q = f'"{ln.raw}": {ln.name} is out of stock. OK to skip or substitute?'
        elif "SS008" in ids:
            q = f'"{ln.raw}": we couldn\'t find that earlier order. Could you list the items?'
        elif "SS014" in ids:
            msg = next(f.message for f in ln.flags if f.id == "SS014")
            q = f'"{ln.raw}": {msg}'
        elif "SS010" in ids:
            q = f'"{ln.raw}": just checking, is this {ln.name}?'
        elif "SS007" in ids:
            q = f'"{ln.raw}": {ln.name} is on your order twice. Combine them?'
        if q:
            asks.append(f"- {q}")
    if not asks:
        return "Order looks complete. No questions."
    hello = f"Hi {customer}," if customer else "Hi,"
    return "\n".join([hello, "Thanks for the order. A few quick checks before we confirm:", *asks,
                      "Everything else is good to go."])
