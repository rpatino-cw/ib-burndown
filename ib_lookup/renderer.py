"""Floor map, rack elevation, port faceplate, and side-by-side rendering."""

from __future__ import annotations

import re

from ib_lookup.color import (
    BOLD, DIM, RESET, CYAN, YELLOW, RED, GREEN,
    colorize, color_enabled,
)
from ib_lookup.layouts import rack_at, find_rack_position


# ════════════════════════════════════════════════════════════════
#  ANSI helpers
# ════════════════════════════════════════════════════════════════

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def _visible_len(s: str) -> int:
    return len(_ANSI_RE.sub('', s))


def _side_by_side(left: list[str], right: list[str], gap: int = 4):
    max_len = max(len(left), len(right))
    left += [''] * (max_len - len(left))
    right += [''] * (max_len - len(right))
    max_w = max((_visible_len(l) for l in left), default=0)
    pad = max_w + gap
    for l_line, r_line in zip(left, right):
        spacing = pad - _visible_len(l_line)
        print(f"{l_line}{' ' * spacing}{r_line}")


def _lines_side_by_side(left: list[str], right: list[str], gap: int = 4) -> list[str]:
    max_len = max(len(left), len(right))
    left = left + [''] * (max_len - len(left))
    right = right + [''] * (max_len - len(right))
    max_w = max((_visible_len(l) for l in left), default=0)
    pad = max_w + gap
    result = []
    for l_line, r_line in zip(left, right):
        spacing = pad - _visible_len(l_line)
        result.append(f"{l_line}{' ' * spacing}{r_line}")
    return result


# ════════════════════════════════════════════════════════════════
#  FLOOR MAP — adapted from dhmap render.py
# ════════════════════════════════════════════════════════════════

COL_GAP = "       "


def _col_width(rpr):
    return 4 + rpr * 2 - 1 + 1 + 4


def _num_width(col):
    rpr = col["rpr"]
    end = col["start"] + col["num_rows"] * rpr - 1
    return len(str(end))


def draw_map(layout: dict,
             highlight_a: int | None = None,
             highlight_b: int | None = None,
             label_a: str = "",
             label_b: str = ""):
    """Render ASCII floor map with highlighted racks."""
    serp = layout["serpentine"]
    cols = layout["columns"]
    default_rpr = layout.get("racks_per_row", 10)

    legend = []
    if highlight_a and label_a:
        legend.append(f"  {CYAN}{BOLD}@{RESET} = {label_a} {DIM}(~R{highlight_a}){RESET}")
    if highlight_b and label_b:
        legend.append(f"  {YELLOW}{BOLD}#{RESET} = {label_b} {DIM}(~R{highlight_b}){RESET}")

    label = layout.get("label", "")
    print(f"\n  {BOLD}{label} Floor Map{RESET}")
    for l in legend:
        print(l)
    print()

    hdr_parts = []
    for col in cols:
        rpr = col["rpr"]
        end_rack = col["start"] + col["num_rows"] * rpr - 1
        part = f"{col['label']} (R{col['start']}–R{end_rack})"
        cw = _col_width(rpr)
        hdr_parts.append(f"{part:<{cw}}")
    print(f"  {DIM}{COL_GAP.join(hdr_parts)}{RESET}")

    max_rows = max(col["num_rows"] for col in cols)

    def _cell(rn):
        if rn == highlight_a:
            return f"{CYAN}{BOLD}@{RESET}"
        if rn == highlight_b:
            return f"{YELLOW}{BOLD}#{RESET}"
        return f"{DIM}-{RESET}"

    for row in range(max_rows):
        col_strs = []
        for col in cols:
            rpr = col["rpr"]
            cw = _col_width(rpr)
            if row < col["num_rows"]:
                first_rack = rack_at(col["start"], row, 0, rpr, serp)
                last_rack = rack_at(col["start"], row, rpr - 1, rpr, serp)
                label_l = f"{DIM}{first_rack:>3}{RESET} "
                label_r = f" {DIM}{last_rack:<3}{RESET}"
                cells = " ".join(_cell(rack_at(col["start"], row, pos, rpr, serp))
                                 for pos in range(rpr))
                col_strs.append(label_l + cells + label_r)
            else:
                col_strs.append(" " * cw)

        print(f"  {COL_GAP.join(col_strs)}")

        if row % 2 == 1 and row < max_rows - 1:
            print()
    print()


# ════════════════════════════════════════════════════════════════
#  RACK ELEVATION
# ════════════════════════════════════════════════════════════════

def _rack_switch_map(rack_num: int, elevations: dict, dh_filter: str = "") -> dict[int, dict]:
    """Get all switches in a rack as {ru: {name, sku}}."""
    by_ru: dict[int, dict] = {}
    dh_f = dh_filter.upper()
    for sw_name, info in elevations.items():
        if info["rack"] == rack_num:
            if dh_f and sw_name.startswith("L") and info.get("dh", "").upper() != dh_f:
                continue
            by_ru[info["ru"]] = {"name": sw_name, "sku": info.get("sku", "")}
    return by_ru


def build_rack(rack_num: int, side_label: str, highlight_name: str,
               elevations: dict, dh: str = "") -> list[str]:
    """Render full rack with all RU positions, highlight a specific switch."""
    by_ru = _rack_switch_map(rack_num, elevations, dh_filter=dh)
    if not by_ru:
        return [f"  {DIM}(no elevation data for R{rack_num}){RESET}"]

    hl = highlight_name.upper()
    max_ru = max(by_ru.keys())
    min_ru = min(by_ru.keys())

    lines = [f"  {BOLD}Rack {rack_num}{RESET}  {DIM}{side_label}{RESET}"]
    lines.append(f"  {DIM}┌{'─' * 22}┐{RESET}")

    for ru in range(max_ru, min_ru - 1, -1):
        sw = by_ru.get(ru)
        if sw:
            name = sw["name"]
            if name == hl:
                lines.append(f"  {DIM}│{RESET} {BOLD}{ru:>2}{RESET}  {CYAN}{BOLD}{name}{RESET} {CYAN}{BOLD}◄{RESET}")
            else:
                lines.append(f"  {DIM}│{RESET} {DIM}{ru:>2}{RESET}  {DIM}{name}{RESET}")
        else:
            lines.append(f"  {DIM}│ {ru:>2}  ·{RESET}")

    lines.append(f"  {DIM}└{'─' * 22}┘{RESET}")
    return lines


def draw_elevation(conn: dict, elevations: dict):
    """Draw rack elevations for both sides, side by side."""
    src_name = conn["src_name"].upper()
    dest_name = conn["dest_name"].upper()

    src_elev = elevations.get(src_name)
    dest_elev = elevations.get(dest_name)

    if not src_elev and not dest_elev:
        print(f"  {DIM}No elevation data for this connection{RESET}")
        return

    print()
    sides = []
    no_elev = []
    if src_elev:
        sides.append(build_rack(src_elev["rack"], conn["src_name"],
                                conn["src_name"], elevations, dh=src_elev.get("dh", "")))
    else:
        cab = conn.get("src_cab", "")
        no_elev.append(f"{conn['src_name']}{f' (Cab{cab})' if cab else ''}")

    if dest_elev:
        if not src_elev or dest_elev["rack"] != src_elev["rack"]:
            sides.append(build_rack(dest_elev["rack"], conn["dest_name"],
                                    conn["dest_name"], elevations, dh=dest_elev.get("dh", "")))
    else:
        cab = conn.get("dest_cab", "")
        no_elev.append(f"{conn['dest_name']}{f' (Cab{cab})' if cab else ''}")

    if len(sides) == 2:
        _side_by_side(sides[0], sides[1])
    elif sides:
        for line in sides[0]:
            print(line)
    for name in no_elev:
        print(f"  {DIM}{name} — no rack elevation data{RESET}")
    print()


# ════════════════════════════════════════════════════════════════
#  PORT DIAGRAM — QM9700 faceplate with twin-port OSFP lanes
# ════════════════════════════════════════════════════════════════

def _parse_port(port_str: str) -> tuple[int, int]:
    m = re.match(r'^(\d+)/(\d+)$', port_str.strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 0


def build_faceplate(name: str, port_str: str) -> list[str]:
    """Build a 32-port QM9700 faceplate as lines."""
    port_num, lane = _parse_port(port_str)
    if port_num == 0:
        return [f"  {DIM}{name}: can't parse port '{port_str}'{RESET}"]

    top_ports = list(range(1, 32, 2))
    bot_ports = list(range(2, 33, 2))

    def _cell(p):
        if p == port_num:
            return f"{CYAN}{BOLD}{p:>2}{RESET}"
        return f"{DIM}{p:>2}{RESET}"

    def _row(ports):
        return "│".join(_cell(p) for p in ports)

    def _lane_row(ports, top: bool):
        cells = []
        for p in ports:
            if p == port_num:
                if top:
                    l1 = f"{CYAN}{BOLD}1{RESET}" if lane == 1 else f"{DIM}1{RESET}"
                    l2 = f"{CYAN}{BOLD}2{RESET}" if lane == 2 else f"{DIM}2{RESET}"
                    cells.append(f"{l1}{l2}")
                else:
                    l2 = f"{CYAN}{BOLD}2{RESET}" if lane == 2 else f"{DIM}2{RESET}"
                    l1 = f"{CYAN}{BOLD}1{RESET}" if lane == 1 else f"{DIM}1{RESET}"
                    cells.append(f"{l2}{l1}")
            else:
                cells.append(f"{DIM}··{RESET}")
        suffix = f"  {DIM}/1 /2{RESET}" if top else f"  {DIM}/2 /1{RESET}"
        return f"  │{'│'.join(cells)}│{suffix}"

    sep = "──"
    lines = [
        f"  {BOLD}{name}{RESET}  {DIM}port{RESET} {CYAN}{BOLD}{port_num}/{lane}{RESET}",
        f"  {DIM}┌{'┬'.join([sep]*16)}┐{RESET}",
        f"  │{_row(top_ports)}│",
        _lane_row(top_ports, top=True),
        f"  {DIM}├{'┼'.join([sep]*16)}┤{RESET}",
        _lane_row(bot_ports, top=False),
        f"  │{_row(bot_ports)}│",
        f"  {DIM}└{'┴'.join([sep]*16)}┘{RESET}",
    ]
    return lines


def draw_port_diagram(conn: dict):
    """Draw port diagrams for both sides, side by side."""
    left = build_faceplate(conn["src_name"], conn["src_port"])
    right = build_faceplate(conn["dest_name"], conn["dest_port"])
    print()
    _side_by_side(left, right)
    print()


def build_switch_panel(name: str, port_str: str, elevations: dict) -> list[str]:
    """Build faceplate side-by-side with rack elevation for one switch."""
    faceplate = build_faceplate(name, port_str)
    elev = elevations.get(name.upper())
    if elev:
        rack_lines = build_rack(elev["rack"], name, name, elevations, dh=elev.get("dh", ""))
        return _lines_side_by_side(faceplate, rack_lines)
    return faceplate
