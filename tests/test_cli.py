import json
from pathlib import Path

from skusnap.cli import main

EX = Path(__file__).resolve().parents[1] / "examples"
CAT = str(EX / "catalog.csv")


def test_clean_order_exits_zero(tmp_path, capsys):
    order = tmp_path / "o.txt"
    order.write_text("2 cs romaine\n4 dozen eggs\n")
    assert main(["match", str(order), "--catalog", CAT]) == 0


def test_review_order_exits_one_and_json_contract(capsys):
    code = main(["match", str(EX / "orders" / "luigis-text.txt"), "--catalog", CAT, "--customer", "luigis",
                 "--aliases", str(EX / "aliases.csv"), "--history", str(EX / "history.jsonl"), "--format", "json"])
    assert code == 1
    data = json.loads(capsys.readouterr().out)
    assert data["status"] == "needs_review"
    assert data["summary"] == {"lines": 9, "ok": 6, "review": 3, "ignored": 3}
    assert {"line_no", "sku", "qty", "unit", "flags", "candidates", "match_source"} <= set(data["lines"][0])


def test_missing_file_exits_two(capsys):
    assert main(["match", "nope.txt", "--catalog", CAT]) == 2


def test_bad_catalog_exits_two(tmp_path):
    bad = tmp_path / "c.csv"
    bad.write_text("code,title\nA,B\n")
    order = tmp_path / "o.txt"
    order.write_text("1 cs a")
    assert main(["match", str(order), "--catalog", str(bad)]) == 2


def test_learn_appends_alias_once(tmp_path, capsys):
    al = tmp_path / "aliases.csv"
    args = ["learn", "--catalog", CAT, "--aliases", str(al), "--customer", "c1", "--phrase", "lox", "--sku", "SEA-SAL-SMK"]
    assert main(args) == 0 and main(args) == 0
    assert al.read_text().count("lox") == 1
    assert "already known" in capsys.readouterr().out


def test_csv_output(tmp_path):
    out = tmp_path / "o.csv"
    main(["match", str(EX / "orders" / "email-po.txt"), "--catalog", CAT, "--format", "csv", "--out", str(out)])
    head = out.read_text().splitlines()[0]
    assert head == "line_no,sku,qty,unit,name,status,flags,raw"
