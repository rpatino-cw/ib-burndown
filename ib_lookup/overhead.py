"""Overhead CSV parser — port of blueprint-map's 6-pass algorithm.

Reads a data center overhead CSV and extracts rack layout geometry.
Outputs layouts.json compatible with dhmap and ib-lookup.

No AI, no user questions — pure algorithmic detection.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys

from ib_lookup.color import BOLD, DIM, RESET, CYAN, YELLOW, GREEN, RED


# ════════════════════════════════════════════════════════════════
#  CSV LOADING
# ════════════════════════════════════════════════════════════════

def _load_csv(path: str) -> list[list[str]]:
    """Load CSV/TSV with delimiter auto-detection."""
    with open(path, newline='', encoding='utf-8-sig') as f:
        sample = f.read(4096)
        f.seek(0)

        # Auto-detect delimiter
        for delim in ['\t', ',', ';', '|']:
            if delim in sample:
                reader = csv.reader(f, delimiter=delim)
                return [list(row) for row in reader]

        # Fallback: comma
        reader = csv.reader(f)
        return [list(row) for row in reader]


def _cell(grid: list[list[str]], r: int, c: int) -> str:
    if r < 0 or r >= len(grid):
        return ""
    row = grid[r]
    if c < 0 or c >= len(row):
        return ""
    return (row[c] or "").replace("\n", " ").strip()


# ════════════════════════════════════════════════════════════════
#  PASS 1: CELL CLASSIFICATION
# ════════════════════════════════════════════════════════════════

_SITE_RE = re.compile(r'(?:US|GB|SE|NO|DE|FR|NL|IE|JP|SG|AU|CA)-[\w]+-?[\w]*', re.IGNORECASE)
_DH_RE = re.compile(r'DH\s*\d+', re.IGNORECASE)
_NUM_RE = re.compile(r'^\d{1,3}$')


def _classify_cell(v: str, r: int) -> str:
    if not v:
        return "empty"

    # Hall headers: site + DH pattern
    if _SITE_RE.search(v) and (_DH_RE.search(v) or re.search(r'DATA\s*HALL', v, re.IGNORECASE)):
        return "hall-header"
    if re.match(r'^DH\s*\d+$', v, re.IGNORECASE) or re.match(r'^DATA\s*HALL\s*\d+$', v, re.IGNORECASE):
        return "hall-header"
    # Standalone site header in first 3 rows
    if r < 3 and re.match(r'^[A-Z]{2,4}\d{1,2}(?:-[A-Z]+)?$', v, re.IGNORECASE) and len(v) <= 20:
        return "site-header"

    # Numbers (rack candidates)
    if _NUM_RE.match(v) and 1 <= int(v) <= 999:
        return "number"

    # Stats
    if re.search(r'node count|gpu count|total racks|rack count|cabinet count', v, re.IGNORECASE):
        return "stat"

    return "text"


def _classify_grid(grid: list[list[str]]) -> list[list[dict]]:
    classified = []
    for r, row in enumerate(grid):
        row_cls = []
        for c, val in enumerate(row):
            v = (val or "").replace("\n", " ").strip()
            kind = _classify_cell(v, r)
            row_cls.append({"value": v, "kind": kind})
        classified.append(row_cls)
    return classified


# ════════════════════════════════════════════════════════════════
#  PASS 1.5: ROW PATTERN ANALYSIS
# ════════════════════════════════════════════════════════════════

def _find_number_row_candidates(classified: list[list[dict]]) -> list[dict]:
    """Find rows dominated by number cells in a contiguous range."""
    candidates = []
    for r, row in enumerate(classified):
        num_count = 0
        total = 0
        min_c = len(row)
        max_c = 0
        for c, cell in enumerate(row):
            if cell["kind"] != "empty":
                total += 1
                if cell["kind"] == "number":
                    num_count += 1
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)
        if num_count >= 3 and total > 0 and num_count / total >= 0.5:
            candidates.append({"row": r, "num_count": num_count, "min_c": min_c, "max_c": max_c})
    return candidates


# ════════════════════════════════════════════════════════════════
#  PASS 2: RACK BLOCK DETECTION
# ════════════════════════════════════════════════════════════════

def _find_number_runs(classified: list[list[dict]], r: int) -> list[list[dict]]:
    """Find contiguous runs of 3+ numbers in a row."""
    runs = []
    current = []
    row = classified[r] if r < len(classified) else []
    for c, cell in enumerate(row):
        if cell["kind"] == "number":
            current.append({"col": c, "num": int(cell["value"])})
        else:
            if len(current) >= 3:
                runs.append(current)
            current = []
    if len(current) >= 3:
        runs.append(current)
    return runs


def _detect_blocks(grid: list[list[str]], classified: list[list[dict]]) -> list[dict]:
    """Detect rack number blocks — rows of sequential numbers."""
    blocks = []
    used_rows = set()

    for r in range(len(classified)):
        runs = _find_number_runs(classified, r)
        for run in runs:
            if len(run) < 3:
                continue

            start_col = run[0]["col"]
            end_col = run[-1]["col"]
            nums = [c["num"] for c in run]

            ascending = nums[1] > nums[0] if len(nums) > 1 else True

            # Look for row label after the run
            row_label = None
            for cc in range(end_col + 1, min(end_col + 4, len(classified[r]) if r < len(classified) else 0)):
                v = _cell(grid, r, cc)
                if re.match(r'^\d{1,2}$', v) and 1 <= int(v) <= 50:
                    row_label = int(v)
                    break

            blocks.append({
                "number_row": r,
                "start_col": start_col,
                "end_col": end_col,
                "rack_nums": nums,
                "racks_per_row": len(nums),
                "ascending": ascending,
                "serpentine": False,
                "row_label": row_label,
                "partner": None,
            })
            used_rows.add(r)

    # Sort by position
    blocks.sort(key=lambda b: (b["number_row"], b["start_col"]))

    # Detect serpentine: adjacent rows with same column range but opposite direction
    for i in range(len(blocks)):
        a = blocks[i]
        if a["serpentine"]:
            continue
        for j in range(i + 1, len(blocks)):
            b = blocks[j]
            if b["number_row"] - a["number_row"] > 6:
                break
            if (abs(a["start_col"] - b["start_col"]) <= 2 and
                    abs(a["end_col"] - b["end_col"]) <= 2 and
                    a["ascending"] != b["ascending"]):
                a["serpentine"] = True
                b["serpentine"] = True
                a["partner"] = j
                b["partner"] = i
                break

    return blocks


# ════════════════════════════════════════════════════════════════
#  PASS 3: SECTION GROUPING
# ════════════════════════════════════════════════════════════════

def _group_sections(blocks: list[dict]) -> list[dict]:
    """Group vertically aligned blocks into sections (columns)."""
    if not blocks:
        return []

    used = set()
    sections = []

    for i, block in enumerate(blocks):
        if i in used:
            continue
        section = {
            "blocks": [block],
            "start_col": block["start_col"],
            "end_col": block["end_col"],
            "min_row": block["number_row"],
            "max_row": block["number_row"],
        }
        used.add(i)

        for j in range(i + 1, len(blocks)):
            if j in used:
                continue
            b = blocks[j]
            if (abs(b["start_col"] - section["start_col"]) <= 2 and
                    abs(b["end_col"] - section["end_col"]) <= 2 and
                    b["number_row"] - section["max_row"] <= 6):
                section["blocks"].append(b)
                section["max_row"] = max(section["max_row"], b["number_row"])
                used.add(j)

        sections.append(section)

    return sections


# ════════════════════════════════════════════════════════════════
#  PASS 4: HALL ASSIGNMENT + LAYOUT EXTRACTION
# ════════════════════════════════════════════════════════════════

def _extract_hall_headers(classified: list[list[dict]]) -> list[dict]:
    """Extract hall headers and site name from classified grid."""
    headers = []
    site = ""
    for r, row in enumerate(classified):
        for c, cell in enumerate(row):
            if cell["kind"] == "hall-header":
                headers.append({"row": r, "col": c, "value": cell["value"]})
                # Extract site
                if not site:
                    sm = _SITE_RE.search(cell["value"])
                    if sm:
                        site = sm.group(0)
            elif cell["kind"] == "site-header" and not site:
                site = cell["value"].upper()
    return headers, site


def _assign_halls(sections: list[dict], hall_headers: list[dict]) -> dict[str, list[dict]]:
    """Assign sections to halls based on column proximity to hall headers."""
    hall_map: dict[str, dict] = {}

    for hh in hall_headers:
        dhm = re.search(r'DH(\d+)|DATA\s*HALL\s*(\d+)', hh["value"], re.IGNORECASE)
        name = f"DH{dhm.group(1) or dhm.group(2)}" if dhm else hh["value"][:30]

        if name not in hall_map:
            hall_map[name] = {"col_min": hh["col"], "col_max": hh["col"] + 10, "sections": []}
        else:
            hall_map[name]["col_min"] = min(hall_map[name]["col_min"], hh["col"])
            hall_map[name]["col_max"] = max(hall_map[name]["col_max"], hh["col"] + 10)

    for section in sections:
        sec_mid = (section["start_col"] + section["end_col"]) / 2
        best_hall = None
        best_dist = float("inf")

        for name, hall in hall_map.items():
            if hall["col_min"] - 3 <= sec_mid <= hall["col_max"] + 3:
                dist = abs(sec_mid - (hall["col_min"] + hall["col_max"]) / 2)
                if dist < best_dist:
                    best_dist = dist
                    best_hall = name

        # Fallback: nearest header above
        if not best_hall:
            best_row_dist = float("inf")
            for name, hall in hall_map.items():
                for hh in hall_headers:
                    row_dist = section["min_row"] - hh["row"]
                    if 0 < row_dist < best_row_dist:
                        best_row_dist = row_dist
                        best_hall = name

        if best_hall:
            hall_map[best_hall]["sections"].append(section)

    # If no hall headers detected, group everything as one
    if not hall_map and sections:
        hall_map["DH1"] = {"col_min": 0, "col_max": 999, "sections": sections}

    return hall_map


# ════════════════════════════════════════════════════════════════
#  LAYOUT GENERATION
# ════════════════════════════════════════════════════════════════

def _sections_to_layout(hall_name: str, sections: list[dict]) -> dict:
    """Convert detected sections into a dhmap-compatible layout dict."""
    if not sections:
        return None

    # Each section becomes a column in the layout
    columns = []
    all_serpentine = False

    for sec in sections:
        all_racks = []
        for block in sec["blocks"]:
            all_racks.extend(block["rack_nums"])
            if block["serpentine"]:
                all_serpentine = True

        if not all_racks:
            continue

        min_rack = min(all_racks)
        max_rack = max(all_racks)
        rpr = sec["blocks"][0]["racks_per_row"] if sec["blocks"] else 10

        # Count rows: number of blocks = number of rows
        # (each block is one row of racks in the physical layout)
        num_rows = len(sec["blocks"])

        columns.append({
            "label": f"Col{len(columns) + 1}" if len(sections) > 1 else "Main",
            "start": min_rack,
            "num_rows": num_rows,
            "racks_per_row": rpr,
        })

    if not columns:
        return None

    # Label columns Left/Right if exactly 2
    if len(columns) == 2:
        columns[0]["label"] = "Left"
        columns[1]["label"] = "Right"

    return {
        "racks_per_row": columns[0]["racks_per_row"],
        "columns": columns,
        "serpentine": all_serpentine,
    }


# ════════════════════════════════════════════════════════════════
#  PUBLIC API
# ════════════════════════════════════════════════════════════════

def parse_overhead(csv_path: str) -> dict:
    """Parse an overhead CSV and return layouts dict for all detected halls.

    Returns: {"SITE.DH1": {layout}, "SITE.DH2": {layout}, ...}
    """
    grid = _load_csv(csv_path)
    if not grid:
        return {}

    # Pass 1: Classify cells
    classified = _classify_grid(grid)

    # Pass 1.5: Row pattern analysis
    _find_number_row_candidates(classified)

    # Pass 2: Detect rack blocks
    blocks = _detect_blocks(grid, classified)

    # Pass 3: Group into sections
    sections = _group_sections(blocks)

    # Pass 4: Assign to halls
    hall_headers, site = _extract_hall_headers(classified)
    hall_map = _assign_halls(sections, hall_headers)

    # Generate layouts
    layouts = {}
    for hall_name, hall_data in hall_map.items():
        layout = _sections_to_layout(hall_name, hall_data["sections"])
        if layout:
            key = f"{site}.{hall_name}" if site else hall_name
            layouts[key] = layout

    return layouts


def import_overhead(csv_path: str, output_path: str | None = None, merge: bool = True):
    """Parse overhead CSV and write/merge into layouts.json.

    Args:
        csv_path: Path to overhead CSV/TSV file.
        output_path: Where to write layouts.json. Default: ~/.datahall/layouts.json
        merge: If True, merge with existing layouts. If False, overwrite.
    """
    if not os.path.isfile(csv_path):
        print(f"  {RED}File not found:{RESET} {csv_path}")
        return False

    print(f"  {DIM}Parsing overhead...{RESET}", end="", flush=True)
    layouts = parse_overhead(csv_path)
    print(f"\r  {GREEN}Parsed:{RESET} {len(layouts)} hall{'s' if len(layouts) != 1 else ''} detected")

    if not layouts:
        print(f"  {RED}No rack layouts detected in {os.path.basename(csv_path)}{RESET}")
        print(f"  {DIM}Expected: rows of sequential rack numbers (1, 2, 3, ... 10){RESET}")
        return False

    # Print summary
    for key, layout in layouts.items():
        total_racks = 0
        for col in layout["columns"]:
            total_racks += col["num_rows"] * col["racks_per_row"]
        cols = len(layout["columns"])
        serp = "serpentine" if layout.get("serpentine") else "linear"
        print(f"    {CYAN}{key}{RESET}: {total_racks} racks, {cols} column{'s' if cols != 1 else ''}, {serp}")

    # Write to layouts.json
    dest = output_path or os.path.expanduser("~/.datahall/layouts.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    existing = {}
    if merge and os.path.isfile(dest):
        try:
            with open(dest) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    existing.update(layouts)

    with open(dest, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\n  {GREEN}Saved:{RESET} {dest}")
    print(f"  {DIM}{len(existing)} total hall{'s' if len(existing) != 1 else ''} in config{RESET}")
    return True
