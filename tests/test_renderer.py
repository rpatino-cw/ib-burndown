"""Tests for ib_lookup.renderer — floor map, elevation, port diagram output."""

import os
from ib_lookup.renderer import build_faceplate, build_rack, draw_map


# ── build_faceplate ──

def test_faceplate_valid_port():
    lines = build_faceplate("S1.1.1", "21/1")
    assert len(lines) == 8  # header + top border + top row + lane + mid + lane + bot row + bot border
    # Should contain the port number highlighted
    joined = "\n".join(lines)
    assert "21" in joined
    assert "S1.1.1" in joined


def test_faceplate_invalid_port():
    lines = build_faceplate("S1.1.1", "bad")
    assert len(lines) == 1
    assert "can't parse" in lines[0]


def test_faceplate_port_zero():
    lines = build_faceplate("S1.1.1", "0/0")
    # port 0 returns (0,0) from _parse_port → error
    assert len(lines) == 1


# ── build_rack ──

def test_build_rack_with_data():
    elevations = {
        "S1.1.1": {"rack": 41, "ru": 38, "sku": "MQM9790", "dh": "DH1", "row": ""},
        "C1.1": {"rack": 41, "ru": 37, "sku": "MQM9790", "dh": "DH1", "row": ""},
    }
    lines = build_rack(41, "S1.1.1", "S1.1.1", elevations, dh="DH1")
    joined = "\n".join(lines)
    assert "Rack 41" in joined
    assert "S1.1.1" in joined


def test_build_rack_no_data():
    lines = build_rack(999, "test", "test", {}, dh="DH1")
    assert len(lines) == 1
    assert "no elevation data" in lines[0]


# ── draw_map (just verify it doesn't crash) ──

def test_draw_map_no_crash(capsys):
    layout = {
        "label": "DH1",
        "columns": [
            {"label": "Left", "start": 1, "num_rows": 3, "rpr": 5},
        ],
        "serpentine": True,
        "racks_per_row": 5,
    }
    # Should not raise
    os.environ["NO_COLOR"] = "1"
    try:
        draw_map(layout, highlight_a=3, highlight_b=10, label_a="S1", label_b="C1")
    finally:
        del os.environ["NO_COLOR"]

    captured = capsys.readouterr()
    assert "DH1" in captured.out
    assert "@" in captured.out
    assert "#" in captured.out


def test_draw_map_no_highlights(capsys):
    layout = {
        "label": "Test",
        "columns": [{"label": "Main", "start": 1, "num_rows": 2, "rpr": 5}],
        "serpentine": False,
        "racks_per_row": 5,
    }
    os.environ["NO_COLOR"] = "1"
    try:
        draw_map(layout)
    finally:
        del os.environ["NO_COLOR"]

    captured = capsys.readouterr()
    assert "Test" in captured.out
