"""Layout loading + rack math — from dhmap, adapted for ib-lookup."""

from __future__ import annotations

import json
import os
import sys

LAYOUT_PATHS = [
    os.path.expanduser("~/.datahall/layouts.json"),
    os.path.join(os.getcwd(), "dh_layouts.json"),
]


def load_layouts(extra_paths: list[str] | None = None) -> dict | None:
    """Load layouts from default locations or extra paths."""
    paths = list(extra_paths or []) + LAYOUT_PATHS
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
    return None


def resolve_dh(layouts: dict | None, dh_key: str) -> tuple[str, dict | None]:
    """Find layout matching a DH key like 'DH2'.

    Searches for exact key, then tries SITE.DHx pattern.
    Returns (full_key, layout_dict) or (dh_key, None).
    """
    if not layouts:
        return dh_key, None

    # Exact match
    if dh_key in layouts:
        return dh_key, layouts[dh_key]

    # Case-insensitive exact match
    for key in layouts:
        if key.lower() == dh_key.lower():
            return key, layouts[key]

    # Match by DH suffix: "US-CENTRAL-07A.DH2" matches "DH2"
    dh_upper = dh_key.upper()
    for key in layouts:
        if key.upper().endswith(f".{dh_upper}"):
            return key, layouts[key]

    # Match by DH substring
    for key in layouts:
        if dh_upper in key.upper():
            return key, layouts[key]

    return dh_key, None


def normalize_layout(layout: dict) -> dict:
    """Normalize a dhmap layout to the internal format used by the renderer.

    Ensures each column has 'rpr' (racks per row) set.
    """
    default_rpr = layout.get("racks_per_row", 10)
    columns = []
    for c in layout.get("columns", []):
        columns.append({
            "label": c.get("label", ""),
            "start": c["start"],
            "num_rows": c["num_rows"],
            "rpr": c.get("racks_per_row", c.get("rpr", default_rpr)),
        })
    return {
        "label": layout.get("label", ""),
        "columns": columns,
        "serpentine": layout.get("serpentine", True),
        "racks_per_row": default_rpr,
    }


def rack_at(col_start: int, row: int, pos: int,
            racks_per_row: int, serpentine: bool) -> int:
    """Return the rack number at a given row and position within a column."""
    if serpentine and row % 2 == 1:
        return col_start + (row + 1) * racks_per_row - 1 - pos
    return col_start + row * racks_per_row + pos


def find_rack_position(rack_num: int, columns: list[dict],
                       default_rpr: int, serpentine: bool) -> dict | None:
    """Find which column, row, and position a rack number falls in."""
    for col_idx, col in enumerate(columns):
        rpr = col.get("rpr", col.get("racks_per_row", default_rpr))
        col_end = col["start"] + col["num_rows"] * rpr - 1
        if col["start"] <= rack_num <= col_end:
            offset = rack_num - col["start"]
            row = offset // rpr
            pos = offset % rpr
            if serpentine and row % 2 == 1:
                pos = rpr - 1 - pos
            return {
                "col_idx": col_idx,
                "col_label": col["label"],
                "row": row,
                "pos": pos,
            }
    return None


def infer_layout_from_elevations(elevations: dict, dh: str) -> dict | None:
    """Try to infer a basic layout from elevation data.

    Counts racks in a DH and builds a simple 2-column layout.
    Returns None if not enough data.
    """
    racks = set()
    for info in elevations.values():
        if info.get("dh", "").upper() == dh.upper():
            racks.add(info["rack"])

    if len(racks) < 4:
        return None

    min_rack = min(racks)
    max_rack = max(racks)
    total = max_rack - min_rack + 1
    rpr = 10  # assume 10 racks per row

    # Heuristic: if total > 120, split into 2 columns
    if total > 120:
        mid = min_rack + total // 2
        left_rows = (mid - min_rack) // rpr
        right_rows = (max_rack - mid + 1) // rpr + 1
        return {
            "label": dh,
            "columns": [
                {"label": "Left", "start": min_rack, "num_rows": left_rows, "rpr": rpr},
                {"label": "Right", "start": mid, "num_rows": right_rows, "rpr": rpr},
            ],
            "serpentine": True,
            "racks_per_row": rpr,
        }
    else:
        rows = total // rpr + (1 if total % rpr else 0)
        return {
            "label": dh,
            "columns": [
                {"label": "Main", "start": min_rack, "num_rows": rows, "rpr": rpr},
            ],
            "serpentine": True,
            "racks_per_row": rpr,
        }
