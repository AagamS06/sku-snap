import json
from pathlib import Path

from skusnap.catalog import load_catalog
from skusnap.check import check_aliases, check_catalog
from skusnap.cli import main

EX = Path(__file__).resolve().parents[1] / "examples"

BAD = """sku,name,unit,pack_size,pack_unit,aliases,in_stock
A1,Romaine Hearts,cs,24,ea,romaine|lettuce|romaine,yes
A2,Iceberg Lettuce,cs,24,,lettuce|romaine hearts,yes
A3,Iceberg Lettuce,crate,,,iceberg,yes
"""


def ids(issues):
    return sorted(i.id for i in issues)


def test_example_catalog_is_clean():
    assert check_catalog(load_catalog(EX / "catalog.csv")) == []
    assert check_aliases(EX / "aliases.csv", load_catalog(EX / "catalog.csv")) == []


def test_finds_catalog_problems(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text(BAD)
    got = ids(check_catalog(load_catalog(p)))
    # CC001 lettuce on A1+A2, CC002 A2 alias = A1 name, CC003 romaine twice on A1,
    # CC006 A2 pack_size without pack_unit, CC007 'crate', CC008 A2/A3 same name
    assert got == ["CC001", "CC002", "CC003", "CC006", "CC007", "CC008"]


def test_finds_alias_file_problems(tmp_path):
    al = tmp_path / "a.csv"
    al.write_text("customer,phrase,sku\nc1,parm,CHE-PARM-WHL\nc1,Parm,CHE-PARM-GRT\nc2,lox,GONE-123\n")
    got = check_aliases(al, load_catalog(EX / "catalog.csv"))
    assert ids(got) == ["CC004", "CC005"]
    assert "line 4" in next(i.message for i in got if i.id == "CC004")


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["check-catalog", "--catalog", str(EX / "catalog.csv"), "--aliases", str(EX / "aliases.csv")]) == 0
    capsys.readouterr()
    p = tmp_path / "c.csv"
    p.write_text(BAD)
    assert main(["check-catalog", "--catalog", str(p), "--format", "json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["errors"] == 1 and data["warnings"] == 5
    warn_only = tmp_path / "w.csv"
    warn_only.write_text("sku,name,unit\nB1,Thing,crate\n")
    assert main(["check-catalog", "--catalog", str(warn_only)]) == 0
    assert main(["check-catalog", "--catalog", str(warn_only), "--strict"]) == 1
    assert main(["check-catalog", "--catalog", str(EX / "catalog.csv"), "--aliases", "missing.csv"]) == 2
