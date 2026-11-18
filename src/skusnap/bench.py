"""Score sku-snap against a labelled benchmark set.

A benchmark directory holds a catalog plus hand-labelled orders:

    bench/
      catalog.csv            required
      aliases.csv            optional (customer,phrase,sku)
      history.jsonl          optional
      cases/<id>.txt         the raw order text
      cases/<id>.json        what a careful rep expects:
                             {"customer": "tavola" | null,
                              "lines": [{"sku": "PRD-ROM-24" | null, "qty": 3 | null,
                                         "unit": "cs" | null, "flags": ["SS012"]}],
                              "ignored": 3}

Expected lines are compared with predicted lines in order. The headline numbers:

- sku accuracy:   predicted SKU equals the expected SKU (null == null counts)
- line accuracy:  SKU, quantity, unit and the exact flag set all match
- status accuracy: ok vs review agrees
- unsafe lines:   predicted "ok" although the expected SKU differs or the line should be
                  reviewed. This is the number that matters most: an unsafe line is a wrong
                  item that would ship without anyone looking at it.
- per-rule precision / recall over flag ids.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from .catalog import InputError, load_aliases, load_catalog, load_history
from .match import RULES, Line, match_lines
from .parse import parse_order


@dataclass
class LineResult:
    case: str
    index: int
    raw: str
    expected: dict | None
    got: dict | None
    sku_ok: bool
    qty_ok: bool
    unit_ok: bool
    flags_ok: bool
    status_ok: bool
    unsafe: bool

    @property
    def exact(self) -> bool:
        return self.sku_ok and self.qty_ok and self.unit_ok and self.flags_ok


@dataclass
class CaseResult:
    case: str
    customer: str | None
    lines: list[LineResult] = field(default_factory=list)
    expected_lines: int = 0
    got_lines: int = 0
    expected_ignored: int | None = None
    got_ignored: int = 0

    @property
    def exact(self) -> bool:
        return (self.expected_lines == self.got_lines and all(r.exact for r in self.lines)
                and (self.expected_ignored is None or self.expected_ignored == self.got_ignored))


def _qty_equal(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= max(0.01, 0.005 * abs(a))


def _expected_review(flags: list[str]) -> bool:
    return any(RULES.get(f, ("info",))[0] == "review" for f in flags)


def _align(exp: list, got: list) -> list[tuple[int | None, int | None]]:
    """Pair expected and predicted lines by SKU sequence, so one dropped line does not
    shift every later comparison. Unpaired lines come back with None on one side."""
    pairs: list[tuple[int | None, int | None]] = []
    sm = SequenceMatcher(None, exp, got, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            pairs += list(zip(range(i1, i2), range(j1, j2), strict=True))
        elif op == "delete":
            pairs += [(i, None) for i in range(i1, i2)]
        elif op == "insert":
            pairs += [(None, j) for j in range(j1, j2)]
        else:   # replace: pair positionally, leftovers are missing / extra
            k = min(i2 - i1, j2 - j1)
            pairs += [(i1 + t, j1 + t) for t in range(k)]
            pairs += [(i, None) for i in range(i1 + k, i2)]
            pairs += [(None, j) for j in range(j1 + k, j2)]
    return pairs


def _line_dict(ln: Line) -> dict:
    return {"sku": ln.sku, "qty": ln.qty, "unit": ln.unit, "flags": [f.id for f in ln.flags],
            "status": "review" if ln.needs_review else "ok"}


def _load_case(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"{path.name}: not valid JSON ({exc.msg}, line {exc.lineno})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("lines"), list):
        raise InputError(f"{path.name}: expected an object with a 'lines' list")
    for i, ln in enumerate(data["lines"], start=1):
        if not isinstance(ln, dict) or "sku" not in ln:
            raise InputError(f"{path.name}: line {i} needs at least a 'sku' key (null for no match)")
        unknown = [f for f in ln.get("flags", []) if f not in RULES]
        if unknown:
            raise InputError(f"{path.name}: line {i} has unknown flag ids: {', '.join(unknown)}")
    return data


def run_case(case_id: str, text: str, expected: dict, catalog, aliases_path, history_path) -> CaseResult:
    customer = expected.get("customer")
    aliases = load_aliases(aliases_path, customer)
    history = load_history(history_path, customer)
    lines, ignored = match_lines(parse_order(text), catalog, aliases, history)
    exp_lines = expected["lines"]
    res = CaseResult(case_id, customer, expected_lines=len(exp_lines), got_lines=len(lines),
                     expected_ignored=expected.get("ignored"), got_ignored=len(ignored))
    got_dicts = [_line_dict(ln) for ln in lines]
    for n, (ei, gi) in enumerate(_align([e["sku"] for e in exp_lines], [g["sku"] for g in got_dicts]), start=1):
        exp = exp_lines[ei] if ei is not None else None
        got = got_dicts[gi] if gi is not None else None
        raw = lines[gi].raw if gi is not None else ""
        if exp is None or got is None:
            # a missing line is unsafe (an item silently dropped); an extra "ok" line is unsafe too
            unsafe = exp is not None or (got is not None and got["status"] == "ok")
            res.lines.append(LineResult(case_id, n, raw, exp, got, False, False, False, False, False, unsafe))
            continue
        exp_flags = sorted(exp.get("flags", []))
        exp_review = _expected_review(exp_flags)
        sku_ok = exp["sku"] == got["sku"]
        status_ok = exp_review == (got["status"] == "review")
        unsafe = got["status"] == "ok" and (not sku_ok or exp_review)
        res.lines.append(LineResult(
            case_id, n, raw, exp, got, sku_ok,
            _qty_equal(exp.get("qty"), got["qty"]),
            exp.get("unit") == got["unit"],
            exp_flags == sorted(got["flags"]),
            status_ok, unsafe))
    return res


def run_bench(directory: str | Path) -> list[CaseResult]:
    d = Path(directory)
    if not d.is_dir():
        raise InputError(f"benchmark directory not found: {d}")
    catalog = load_catalog(d / "catalog.csv")
    aliases_path = d / "aliases.csv" if (d / "aliases.csv").is_file() else None
    history_path = d / "history.jsonl" if (d / "history.jsonl").is_file() else None
    cases_dir = d / "cases"
    texts = sorted(cases_dir.glob("*.txt")) if cases_dir.is_dir() else []
    if not texts:
        raise InputError(f"no cases found in {cases_dir} (expected <id>.txt + <id>.json pairs)")
    results = []
    for txt in texts:
        exp_path = txt.with_suffix(".json")
        if not exp_path.is_file():
            raise InputError(f"case {txt.stem} has no expected file {exp_path.name}")
        expected = _load_case(exp_path)
        results.append(run_case(txt.stem, txt.read_text(encoding="utf-8"), expected, catalog,
                                aliases_path, history_path))
    return results


def _ratio(n: int, d: int) -> float | None:
    return round(n / d, 3) if d else None


def summarise(results: list[CaseResult]) -> dict:
    rows = [r for c in results for r in c.lines]
    paired = [r for r in rows if r.expected is not None and r.got is not None]
    total = len(rows)
    per_rule: dict[str, dict] = {}
    for rid in RULES:
        tp = fp = fn = 0
        for r in paired:
            e, g = rid in r.expected.get("flags", []), rid in r.got["flags"]
            tp += e and g
            fp += g and not e
            fn += e and not g
        if tp or fp or fn:
            per_rule[rid] = {"level": RULES[rid][0], "tp": tp, "fp": fp, "fn": fn,
                             "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn)}
    return {
        "cases": len(results),
        "cases_exact": sum(c.exact for c in results),
        "lines": total,
        "sku_accuracy": _ratio(sum(r.sku_ok for r in rows), total),
        "line_accuracy": _ratio(sum(r.exact for r in rows), total),
        "status_accuracy": _ratio(sum(r.status_ok for r in rows), total),
        "unsafe_lines": sum(r.unsafe for r in rows),
        "missing_lines": sum(1 for r in rows if r.got is None),
        "extra_lines": sum(1 for r in rows if r.expected is None),
        "chatter_mismatches": sum(1 for c in results
                                  if c.expected_ignored is not None and c.expected_ignored != c.got_ignored),
        "per_rule": per_rule,
    }


def mismatches(results: list[CaseResult]) -> list[dict]:
    out = []
    for c in results:
        for r in c.lines:
            if not r.exact:
                out.append({"case": r.case, "line": r.index, "raw": r.raw, "unsafe": r.unsafe,
                            "expected": r.expected, "got": r.got})
        if c.expected_ignored is not None and c.expected_ignored != c.got_ignored:
            out.append({"case": c.case, "line": None, "raw": "(chatter)", "unsafe": False,
                        "expected": {"ignored": c.expected_ignored}, "got": {"ignored": c.got_ignored}})
    return out


def _pct(x: float | None) -> str:
    return "-" if x is None else f"{x * 100:.1f}%"


def _brief(d: dict | None) -> str:
    if d is None:
        return "(none)"
    if "ignored" in d:
        return f"ignored={d['ignored']}"
    qty = "-" if d.get("qty") is None else f"{d['qty']:g}"
    return f"{d.get('sku') or '-'} {qty} {d.get('unit') or '-'} [{' '.join(d.get('flags', [])) or '-'}]"


def to_text(summary: dict, misses: list[dict], verbose: bool = False) -> str:
    s = summary
    out = [
        f"sku-snap bench: {s['cases']} cases, {s['lines']} lines",
        f"  sku accuracy     {_pct(s['sku_accuracy'])}",
        f"  line accuracy    {_pct(s['line_accuracy'])}   (sku + qty + unit + exact flags)",
        f"  status accuracy  {_pct(s['status_accuracy'])}   (ok vs review)",
        f"  unsafe lines     {s['unsafe_lines']}        (marked ok but wrong or should be reviewed)",
        f"  exact cases      {s['cases_exact']}/{s['cases']}",
    ]
    if s["missing_lines"] or s["extra_lines"] or s["chatter_mismatches"]:
        out.append(f"  missing {s['missing_lines']} · extra {s['extra_lines']} · "
                   f"chatter mismatches {s['chatter_mismatches']}")
    out += ["", "RULE   LEVEL   TP  FP  FN  PRECISION  RECALL"]
    for rid, m in s["per_rule"].items():
        out.append(f"{rid}  {m['level']:<6}  {m['tp']:>2}  {m['fp']:>2}  {m['fn']:>2}  "
                   f"{_pct(m['precision']):>9}  {_pct(m['recall']):>6}")
    if misses:
        out.append("")
        shown = misses if verbose else [m for m in misses if m["unsafe"]]
        label = "mismatches" if verbose else "unsafe lines (use --verbose for every mismatch)"
        out.append(f"{len(misses)} mismatch(es); {label}:" if shown else
                   f"{len(misses)} mismatch(es), none unsafe (use --verbose to list them)")
        for m in shown:
            where = f"{m['case']}#{m['line']}" if m["line"] else m["case"]
            raw = f'"{m["raw"]}"' if m["raw"] else "(line missing from the output)"
            out.append(f"  {'UNSAFE ' if m['unsafe'] else ''}{where} {raw}")
            out.append(f"      expected {_brief(m['expected'])}")
            out.append(f"      got      {_brief(m['got'])}")
    return "\n".join(out)
