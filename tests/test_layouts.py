"""Tests for ib_lookup.layouts — layout loading, rack math, DH resolution."""

import json
import os
from ib_lookup.layouts import (
    rack_at, find_rack_position, resolve_dh, normalize_layout,
    load_layouts, infer_layout_from_elevations,
)


# ── rack_at ──

def test_rack_at_linear():
    assert rack_at(1, 0, 0, 10, False) == 1
    assert rack_at(1, 0, 9, 10, False) == 10
    assert rack_at(1, 1, 0, 10, False) == 11


def test_rack_at_serpentine_even_row():
    """Even rows go left-to-right (same as linear)."""
    assert rack_at(1, 0, 0, 10, True) == 1
    assert rack_at(1, 0, 9, 10, True) == 10


def test_rack_at_serpentine_odd_row():
    """Odd rows go right-to-left."""
    assert rack_at(1, 1, 0, 10, True) == 20  # rightmost
    assert rack_at(1, 1, 9, 10, True) == 11  # leftmost


def test_rack_at_offset_start():
    """Column starting at rack 141."""
    assert rack_at(141, 0, 0, 10, True) == 141
    assert rack_at(141, 1, 0, 10, True) == 160


# ── find_rack_position ──

def test_find_rack_position_found():
    columns = [
        {"label": "Left", "start": 1, "num_rows": 5, "rpr": 10, "racks_per_row": 10},
        {"label": "Right", "start": 51, "num_rows": 5, "rpr": 10, "racks_per_row": 10},
    ]
    pos = find_rack_position(15, columns, 10, True)
    assert pos is not None
    assert pos["col_idx"] == 0
    assert pos["col_label"] == "Left"


def test_find_rack_position_right_col():
    columns = [
        {"label": "Left", "start": 1, "num_rows": 5, "rpr": 10, "racks_per_row": 10},
        {"label": "Right", "start": 51, "num_rows": 5, "rpr": 10, "racks_per_row": 10},
    ]
    pos = find_rack_position(55, columns, 10, True)
    assert pos is not None
    assert pos["col_idx"] == 1
    assert pos["col_label"] == "Right"


def test_find_rack_position_not_found():
    columns = [{"label": "Left", "start": 1, "num_rows": 5, "rpr": 10, "racks_per_row": 10}]
    pos = find_rack_position(999, columns, 10, True)
    assert pos is None


# ── resolve_dh ──

def test_resolve_dh_exact():
    layouts = {"DH1": {"columns": []}, "DH2": {"columns": []}}
    key, layout = resolve_dh(layouts, "DH1")
    assert key == "DH1"
    assert layout is not None


def test_resolve_dh_with_site_prefix():
    """'DH2' should match 'US-CENTRAL-07A.DH2'."""
    layouts = {"US-CENTRAL-07A.DH2": {"columns": []}}
    key, layout = resolve_dh(layouts, "DH2")
    assert layout is not None
    assert "DH2" in key


def test_resolve_dh_case_insensitive():
    layouts = {"DH1": {"columns": []}}
    key, layout = resolve_dh(layouts, "dh1")
    assert layout is not None


def test_resolve_dh_not_found():
    layouts = {"DH1": {"columns": []}}
    key, layout = resolve_dh(layouts, "DH99")
    assert layout is None


def test_resolve_dh_none_layouts():
    key, layout = resolve_dh(None, "DH1")
    assert layout is None


# ── normalize_layout ──

def test_normalize_layout_sets_rpr():
    layout = {
        "racks_per_row": 10,
        "columns": [{"label": "Left", "start": 1, "num_rows": 5}],
        "serpentine": True,
    }
    norm = normalize_layout(layout)
    assert norm["columns"][0]["rpr"] == 10
    assert norm["serpentine"] is True


# ── infer_layout_from_elevations ──

def test_infer_layout_enough_data():
    elevs = {}
    for i in range(1, 150):
        elevs[f"SW{i}"] = {"rack": i, "ru": 38, "dh": "DH1"}
    layout = infer_layout_from_elevations(elevs, "DH1")
    assert layout is not None
    assert len(layout["columns"]) == 2  # should split into 2 columns


def test_infer_layout_small_hall():
    elevs = {}
    for i in range(1, 50):
        elevs[f"SW{i}"] = {"rack": i, "ru": 38, "dh": "DH1"}
    layout = infer_layout_from_elevations(elevs, "DH1")
    assert layout is not None
    assert len(layout["columns"]) == 1  # single column


def test_infer_layout_not_enough_data():
    elevs = {"SW1": {"rack": 1, "ru": 38, "dh": "DH1"}}
    layout = infer_layout_from_elevations(elevs, "DH1")
    assert layout is None  # < 4 racks


# ── load_layouts ──

def test_load_layouts_from_file(tmp_path):
    data = {"TEST.DH1": {"columns": [{"label": "Left", "start": 1, "num_rows": 5}]}}
    p = tmp_path / "layouts.json"
    with open(p, "w") as f:
        json.dump(data, f)
    result = load_layouts(extra_paths=[str(p)])
    assert result is not None
    assert "TEST.DH1" in result


def test_load_layouts_missing():
    result = load_layouts(extra_paths=["/nonexistent/layouts.json"])
    # May return None or find default paths — depends on system state
    # Just verify it doesn't crash
    assert result is None or isinstance(result, dict)
