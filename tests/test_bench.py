import json
from pathlib import Path

import pytest

from skusnap.bench import run_bench, summarise
from skusnap.catalog import InputError
from skusnap.cli import main

ROOT = Path(__file__).resolve().parents[1]
CAT = (ROOT / "examples" / "catalog.csv").read_text()


def make_bench(tmp_path, cases):
    (tmp_path / "cases").mkdir()
    (tmp_path / "catalog.csv").write_text(CAT)
    for cid, (text, expected) in cases.items():
        (tmp_path / "cases" / f"{cid}.txt").write_text(text)
        (tmp_path / "cases" / f"{cid}.json").write_text(json.dumps(expected))
    return tmp_path


def line(sku, qty, unit, *flags):
    return {"sku": sku, "qty": qty, "unit": unit, "flags": list(flags)}


def test_perfect_case_scores_full(tmp_path):
    d = make_bench(tmp_path, {"a": ("2 cs romaine\n4 dozen eggs", {"lines": [
        line("PRD-ROM-24", 2, "cs"), line("DRY-EGG-LG", 4, "dz")], "ignored": 0})})
    s = summarise(run_bench(d))
    assert s["sku_accuracy"] == 1.0 and s["line_accuracy"] == 1.0
    assert s["unsafe_lines"] == 0 and s["cases_exact"] == 1


def test_wrong_ok_line_is_unsafe_and_counted_per_rule(tmp_path):
    # label says this should be reviewed as ambiguous; the tool resolves it -> unsafe
    d = make_bench(tmp_path, {"a": ("2 cs romaine", {"lines": [line(None, 2, "cs", "SS002")]})})
    s = summarise(run_bench(d))
    assert s["unsafe_lines"] == 1 and s["sku_accuracy"] == 0.0
    assert s["per_rule"]["SS002"] == {"level": "review", "tp": 0, "fp": 0, "fn": 1,
                                      "precision": None, "recall": 0.0}


def test_dropped_line_is_unsafe_without_shifting_later_lines(tmp_path):
    d = make_bench(tmp_path, {"a": ("2 cs romaine\n4 dozen eggs", {"lines": [
        line("PRD-ROM-24", 2, "cs"), line("PRD-LEM-115", 1, "cs"), line("DRY-EGG-LG", 4, "dz")]})})
    s = summarise(run_bench(d))
    assert s["missing_lines"] == 1 and s["unsafe_lines"] == 1
    assert s["sku_accuracy"] == round(2 / 3, 3)


def test_bad_expected_file_is_input_error(tmp_path):
    d = make_bench(tmp_path, {"a": ("2 cs romaine", {"lines": [line("PRD-ROM-24", 2, "cs", "SS999")]})})
    with pytest.raises(InputError, match="unknown flag ids: SS999"):
        run_bench(d)


def test_shipped_benchmark_meets_baseline(capsys):
    # guards against regressions; raise the bar as the misses listed in Memory.md get fixed
    code = main(["bench", str(ROOT / "bench"), "--min-sku-accuracy", "0.97", "--max-unsafe", "2",
                 "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["summary"]["cases"] >= 40


def test_bench_cli_threshold_and_filter(capsys):
    assert main(["bench", str(ROOT / "bench"), "--cases", "0*", "--max-unsafe", "0"]) == 0
    assert main(["bench", str(ROOT / "bench"), "--cases", "h*", "--max-unsafe", "0"]) == 1
    assert "threshold failed" in capsys.readouterr().err
    assert main(["bench", str(ROOT / "bench"), "--cases", "zzz*"]) == 2
    assert main(["bench", "no-such-dir"]) == 2
