"""Tests for ib_lookup.overhead — CSV overhead parser for layout generation."""

import json
import os
from ib_lookup.overhead import parse_overhead, import_overhead


def test_parse_overhead_detects_hall(sample_overhead_csv):
    layouts = parse_overhead(sample_overhead_csv)
    assert len(layouts) >= 1
    # Should detect DH1 from "US-TEST01 DH1"
    keys = list(layouts.keys())
    assert any("DH1" in k or "DH" in k for k in keys)


def test_parse_overhead_serpentine(sample_overhead_csv):
    layouts = parse_overhead(sample_overhead_csv)
    for layout in layouts.values():
        assert layout.get("serpentine") is True


def test_parse_overhead_rack_count(sample_overhead_csv):
    layouts = parse_overhead(sample_overhead_csv)
    for layout in layouts.values():
        total = 0
        for col in layout["columns"]:
            total += col["num_rows"] * col["racks_per_row"]
        assert total >= 10  # should detect at least 10 racks


def test_import_overhead_writes_file(sample_overhead_csv, tmp_path):
    out = str(tmp_path / "layouts.json")
    result = import_overhead(sample_overhead_csv, output_path=out)
    assert result is True
    assert os.path.isfile(out)
    with open(out) as f:
        data = json.load(f)
    assert len(data) >= 1


def test_import_overhead_merge(sample_overhead_csv, tmp_path):
    out = str(tmp_path / "layouts.json")
    # Write existing data
    with open(out, "w") as f:
        json.dump({"EXISTING.DH1": {"columns": []}}, f)

    import_overhead(sample_overhead_csv, output_path=out, merge=True)

    with open(out) as f:
        data = json.load(f)
    assert "EXISTING.DH1" in data  # existing preserved
    assert len(data) >= 2  # new ones added


def test_import_overhead_missing_file(tmp_path):
    result = import_overhead("/nonexistent/file.csv")
    assert result is False


def test_parse_overhead_empty_csv(tmp_path):
    p = tmp_path / "empty.csv"
    p.write_text("")
    layouts = parse_overhead(str(p))
    assert layouts == {}
