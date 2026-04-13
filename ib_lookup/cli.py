"""Interactive CLI — site-agnostic IB Lookup."""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import openpyxl

from ib_lookup import __version__
from ib_lookup.color import BOLD, DIM, RESET, CYAN, YELLOW, RED, GREEN, c
from ib_lookup.parser import parse_connections, parse_elevations, detect_site
from ib_lookup.cache import load_cache, save_cache
from ib_lookup.layouts import (
    load_layouts, resolve_dh, normalize_layout, infer_layout_from_elevations,
)
from ib_lookup.search import search
from ib_lookup.renderer import (
    draw_map, draw_elevation, draw_port_diagram,
    build_switch_panel,
)

_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_DIR)
_TIPS_PATH = os.path.join(_PROJECT_DIR, "tips.json")


# ════════════════════════════════════════════════════════════════
#  DATA LOADING
# ════════════════════════════════════════════════════════════════

def _find_xlsx(file_arg: str | None = None) -> str | None:
    """Find the IB Sketch xlsx. Priority: --file arg > cwd > project dir."""
    if file_arg:
        if os.path.isfile(file_arg):
            return os.path.abspath(file_arg)
        print(f"  {c(RED, 'File not found:')} {file_arg}")
        return None

    # Search current dir then project dir
    for d in [os.getcwd(), _PROJECT_DIR]:
        matches = glob.glob(os.path.join(d, "*.xlsx"))
        # Filter out temp files
        matches = [m for m in matches if not os.path.basename(m).startswith("~$")]
        if matches:
            if len(matches) == 1:
                return matches[0]
            # Prefer files with "IB" or "Sketch" in name
            for m in matches:
                bn = os.path.basename(m).lower()
                if "ib" in bn or "sketch" in bn:
                    return m
            return matches[0]

    return None


def _load_data(xlsx_path: str) -> tuple[list[dict], dict[str, dict], str, list[str]]:
    """Load connections + elevations, using cache if valid.

    Returns (connections, elevations, site_name, data_halls).
    """
    cached = load_cache(xlsx_path)
    if cached is not None:
        return (cached["connections"], cached["elevations"],
                cached.get("site", ""), cached.get("data_halls", []))

    connections = parse_connections(xlsx_path)
    elevations = parse_elevations(xlsx_path)

    # Auto-detect site
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    site, data_halls = detect_site(wb)
    wb.close()

    # Also detect site from fabric IDs
    if not site and connections:
        fab_ids = {c.get("fabric_id", "") for c in connections if c.get("fabric_id")}
        for fid in fab_ids:
            # Pattern: us-central-07a-fab52 → us-central-07a
            parts = fid.rsplit("-", 1)
            if len(parts) == 2 and parts[1].startswith("fab"):
                site = parts[0]
                break

    if connections:
        save_cache(xlsx_path, connections, elevations, site, data_halls)

    return connections, elevations, site, data_halls


def _load_layouts_for_halls(data_halls: list[str], elevations: dict) -> dict[str, dict]:
    """Load or infer layouts for each data hall. Returns {DH_key: normalized_layout}."""
    all_layouts = load_layouts(extra_paths=[
        os.path.join(os.path.expanduser("~/dev/cw-node-helper"), "dh_layouts.json"),
    ])

    result = {}
    for dh in data_halls:
        key, layout = resolve_dh(all_layouts, dh)
        if layout:
            nl = normalize_layout(layout)
            nl["label"] = nl.get("label") or dh
            result[dh] = nl
        else:
            # Try to infer from elevation data
            inferred = infer_layout_from_elevations(elevations, dh)
            if inferred:
                result[dh] = inferred

    return result


# ════════════════════════════════════════════════════════════════
#  TIPS
# ════════════════════════════════════════════════════════════════

def _load_tips() -> list[dict]:
    if os.path.isfile(_TIPS_PATH):
        try:
            with open(_TIPS_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _get_tips(conn: dict, elevations: dict) -> list[tuple[str, str]]:
    tips = _load_tips()
    if not tips:
        return []

    rack_a = _extract_rack(conn.get("src_name", ""), elevations)
    rack_b = _extract_rack(conn.get("dest_name", ""), elevations)
    subs = {
        "src_name": conn.get("src_name", ""),
        "dest_name": conn.get("dest_name", ""),
        "src_port": conn.get("src_port", ""),
        "dest_port": conn.get("dest_port", ""),
        "rack_a": rack_a or "?",
        "rack_b": rack_b or "?",
    }
    filled = []
    for tip in tips:
        try:
            filled.append((tip["label"], tip["cmd"].format(**subs)))
        except KeyError:
            filled.append((tip["label"], tip["cmd"]))
    return filled


# ════════════════════════════════════════════════════════════════
#  RACK + MAP HELPERS
# ════════════════════════════════════════════════════════════════

def _extract_rack(switch_name: str, elevations: dict) -> int | None:
    if not switch_name:
        return None
    elev = elevations.get(switch_name.upper())
    if elev:
        return elev["rack"]
    m = re.match(r'^L(\d+)\.', switch_name)
    if m:
        return int(m[1])
    return None


def _map_halls(conn: dict, elevations: dict) -> list[str]:
    """Return list of DH keys to render maps for."""
    src_elev = elevations.get(conn["src_name"].upper())
    dest_elev = elevations.get(conn["dest_name"].upper())
    src_dh = src_elev["dh"] if src_elev and src_elev.get("dh") else None
    dest_dh = dest_elev["dh"] if dest_elev and dest_elev.get("dh") else None

    halls = set()
    for dh_val, name in [(src_dh, conn.get("src_name", "")),
                         (dest_dh, conn.get("dest_name", ""))]:
        if dh_val:
            halls.add(dh_val)
        else:
            dh_m = re.search(r'(DH\d+)', name, re.IGNORECASE)
            if dh_m:
                halls.add(dh_m.group(1).upper())

    if not halls:
        dh = conn.get("data_hall", "")
        return [dh] if dh else []

    return sorted(halls)


# ════════════════════════════════════════════════════════════════
#  DISPLAY
# ════════════════════════════════════════════════════════════════

def _tier_label(conn: dict) -> str:
    s = conn.get("src_type", "")
    d = conn.get("dest_type", "")
    return f"{s}→{d}" if s and d else ""


def _cab_label(conn: dict, side: str) -> str:
    cab = conn.get(f"{side}_cab", "")
    return f"Cab{cab}" if cab else ""


def _short_fabric(fabric_id: str) -> str:
    if not fabric_id:
        return ""
    return fabric_id.rsplit("-", 1)[-1]


def _print_result(conn: dict, idx: int):
    num = c(BOLD, f"{idx:>3}.")
    tier = c(DIM, _tier_label(conn))
    line = (f"{c(CYAN, conn['src_name'])} {conn['src_port']} "
            f"{c(DIM, '→')} "
            f"{c(YELLOW, conn['dest_name'])} {conn['dest_port']}")
    print(f"  {num} {line}  {tier}")


def _print_detail(conn: dict, elevations: dict):
    tier = _tier_label(conn)

    line = (f"{c(CYAN+BOLD, conn['src_name'])} {conn['src_port']} "
            f"{c(DIM, '→')} "
            f"{c(YELLOW+BOLD, conn['dest_name'])} {conn['dest_port']}"
            f"  {c(DIM, tier)}")
    print(f"\n  {line}")

    meta = []
    if conn.get("status"):
        meta.append(conn["status"])
    if conn.get("cable_type"):
        meta.append(conn["cable_type"])
    if conn.get("cable_length") and conn["cable_length"] != "??":
        meta.append(conn["cable_length"])
    if conn.get("optic_type"):
        meta.append(conn["optic_type"])
    fab = _short_fabric(conn.get("fabric_id", ""))
    if fab:
        meta.append(fab)
    if meta:
        print(f"  {c(DIM, ' · '.join(meta))}")

    rack_a = _extract_rack(conn["src_name"], elevations)
    rack_b = _extract_rack(conn["dest_name"], elevations)
    src_cab = _cab_label(conn, "src")
    dest_cab = _cab_label(conn, "dest")

    def _loc(rack, name, cab):
        parts = [c(BOLD, f"R{rack}")] if rack else []
        elev = elevations.get(name.upper())
        if elev:
            parts.append(f"RU{elev['ru']}")
        if cab:
            parts.append(cab)
        label = " ".join(parts) if parts else ""
        return f"{label} {c(DIM, f'({name})')}" if label else c(DIM, f"({name})")

    if rack_a or rack_b or src_cab or dest_cab:
        print(f"  {_loc(rack_a, conn['src_name'], src_cab)} → {_loc(rack_b, conn['dest_name'], dest_cab)}")


def _show_connection_detail(conn: dict, elevations: dict, layouts: dict):
    """Auto-expand full detail: faceplate + elevation for each switch, then map."""
    _print_detail(conn, elevations)

    has_ports = conn.get("src_port") or conn.get("dest_port")
    src_elev = elevations.get(conn["src_name"].upper())
    dest_elev = elevations.get(conn["dest_name"].upper())

    if has_ports or src_elev or dest_elev:
        if has_ports:
            src_panel = build_switch_panel(conn["src_name"], conn["src_port"], elevations)
            dest_panel = build_switch_panel(conn["dest_name"], conn["dest_port"], elevations)
            print()
            for line in src_panel:
                print(line)
            print()
            for line in dest_panel:
                print(line)
        elif src_elev or dest_elev:
            draw_elevation(conn, elevations)
        print()

    # Floor map
    dh = conn.get("data_hall", "")
    rack_a = _extract_rack(conn["src_name"], elevations)
    rack_b = _extract_rack(conn["dest_name"], elevations)
    if rack_a or rack_b:
        halls = _map_halls(conn, elevations)
        src_dh = src_elev["dh"] if src_elev and src_elev.get("dh") else None
        dest_dh = dest_elev["dh"] if dest_elev and dest_elev.get("dh") else None
        for lk in halls:
            layout = layouts.get(lk)
            if not layout:
                print(f"  {c(DIM, f'No floor layout for {lk} — add it to ~/.datahall/layouts.json')}")
                continue
            ha = rack_a if (src_dh == lk or src_dh is None) else None
            hb = rack_b if (dest_dh == lk or dest_dh is None) else None
            la = conn["src_name"] if ha else ""
            lb = conn["dest_name"] if hb else ""
            draw_map(layout, highlight_a=ha, highlight_b=hb, label_a=la, label_b=lb)


def _detail_prompt(conn: dict, elevations: dict, layouts: dict):
    """Handle [m]/[t]/[e]/[v] sub-prompt."""
    dh = conn.get("data_hall", "")
    rack_a = _extract_rack(conn["src_name"], elevations)
    rack_b = _extract_rack(conn["dest_name"], elevations)
    has_map = bool(rack_a or rack_b)
    has_elev = bool(
        elevations.get(conn["src_name"].upper())
        or elevations.get(conn["dest_name"].upper())
    )
    has_ports = bool(conn.get("src_port") or conn.get("dest_port"))

    opts = []
    if has_map:
        opts.append(f"{c(DIM, '[m]')} map")
    if has_elev:
        opts.append(f"{c(DIM, '[e]')} elevation")
    if has_ports:
        opts.append(f"{c(DIM, '[v]')} ports")
    opts.append(f"{c(DIM, '[t]')} tips")
    opts.append(f"{c(DIM, '[Enter]')} back")
    hint = " ".join(opts)
    print(f"  {hint}")

    while True:
        sel = _prompt()
        if not sel:
            return
        sl = sel.lower()
        if sl in ("q", "quit", "exit"):
            raise SystemExit(0)
        if sl == "v" and has_ports:
            draw_port_diagram(conn)
            print(f"  {hint}")
        elif sl == "m" and has_map:
            halls = _map_halls(conn, elevations)
            src_elev = elevations.get(conn["src_name"].upper())
            dest_elev = elevations.get(conn["dest_name"].upper())
            src_dh = src_elev["dh"] if src_elev and src_elev.get("dh") else None
            dest_dh = dest_elev["dh"] if dest_elev and dest_elev.get("dh") else None
            for lk in halls:
                layout = layouts.get(lk)
                if not layout:
                    print(f"  {c(DIM, f'No layout for {lk}')}")
                    continue
                ha = rack_a if (src_dh == lk or src_dh is None) else None
                hb = rack_b if (dest_dh == lk or dest_dh is None) else None
                la = conn["src_name"] if ha else ""
                lb = conn["dest_name"] if hb else ""
                draw_map(layout, highlight_a=ha, highlight_b=hb, label_a=la, label_b=lb)
            print(f"  {hint}")
        elif sl == "e" and has_elev:
            draw_elevation(conn, elevations)
            print(f"  {hint}")
        elif sl == "t":
            tips = _get_tips(conn, elevations)
            if tips:
                print(f"\n  {c(BOLD, 'Steps:')}")
                for i, (label, cmd) in enumerate(tips, 1):
                    print(f"    {c(DIM, f'{i}.')} {label}")
                    print(f"       {c(CYAN, cmd)}")
                print()
            print(f"  {hint}")
        else:
            return


# ════════════════════════════════════════════════════════════════
#  INTERACTIVE LOOP
# ════════════════════════════════════════════════════════════════

def _flush_stdin():
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except (ImportError, termios.error, ValueError):
        pass


def _prompt(hint: str = "> ") -> str:
    try:
        return input(f"  {hint}").strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _clear():
    os.system("clear" if os.name != "nt" else "cls")


def _run(xlsx_path: str):
    _clear()
    print(f"\n  {c(DIM, 'Loading data...')}", end="", flush=True)
    connections, elevations, site, data_halls = _load_data(xlsx_path)
    layouts = _load_layouts_for_halls(data_halls, elevations)
    _clear()

    site_label = site or os.path.basename(xlsx_path).replace(".xlsx", "")
    missing_layouts = [dh for dh in data_halls if dh not in layouts]

    print(f"\n  {c(BOLD, 'IB Lookup')}  {c(DIM, f'{site_label} · {len(connections):,} connections · {len(data_halls)} halls')}")
    if missing_layouts:
        print(f"  {c(YELLOW, 'Missing floor layouts:')} {', '.join(missing_layouts)}")
        print(f"  {c(DIM, 'Add them to ~/.datahall/layouts.json or run the datahall-map-creator skill')}")
    print(f"  {c(DIM, 'Search any switch — example: S5.3.1, L10, C1.15 20/2')}\n")

    while True:
        query = _prompt(f"{c(BOLD, 'Search:')} ")

        if query in ("q", "quit", "exit"):
            break
        if query == "?":
            print(f"\n  {c(BOLD, 'Examples:')}")
            print(f"    S5.3.1       {c(DIM, '— spine switch')}")
            print(f"    L10          {c(DIM, '— all leaf switches in cab 10')}")
            print(f"    C1.15 20/2   {c(DIM, '— core switch + specific port')}")
            print(f"    8.3.2        {c(DIM, '— auto-detects type')}")
            print(f"    q            {c(DIM, '— quit')}\n")
            continue
        if not query:
            continue

        results = search(connections, query)
        if not results:
            print(f"  {c(DIM, 'No matches for ' + repr(query))}\n")
            continue

        print(f"\n  {c(BOLD, query)} — {len(results)} match{'es' if len(results) != 1 else ''}\n")
        for idx, conn in enumerate(results, 1):
            _print_result(conn, idx)

        if len(results) == 1:
            _show_connection_detail(results[0], elevations, layouts)
            _detail_prompt(results[0], elevations, layouts)
            _flush_stdin()
            continue

        print(f"\n  {c(DIM, 'Enter a number for details, or just search again')}")
        sel = _prompt()
        if sel in ("q", "quit", "exit"):
            break
        if sel.isdigit():
            n = int(sel) - 1
            if 0 <= n < len(results):
                _show_connection_detail(results[n], elevations, layouts)
                _detail_prompt(results[n], elevations, layouts)
                _flush_stdin()
            else:
                print(f"  {c(DIM, f'Pick 1–{len(results)}')}")


# ════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ════════════════════════════════════════════════════════════════

def main():
    # Auto-detect trad mode when invoked as 'trad-lookup'
    invoked_as_trad = os.path.basename(sys.argv[0]).startswith("trad")

    parser = argparse.ArgumentParser(
        prog="trad-lookup" if invoked_as_trad else "ib-lookup",
        description="Switch Lookup — search IB and traditional networking connections at any site",
    )
    parser.add_argument("query", nargs="?", default=None,
                        help="Switch name to search (e.g. L10, S5.3, C1.4)")
    parser.add_argument("--file", "-f", default=None,
                        help="Path to .xlsx file")
    parser.add_argument("--trad", action="store_true", default=invoked_as_trad,
                        help="Traditional networking mode (MASTER cutsheet)")
    parser.add_argument("--import-overhead", metavar="CSV",
                        help="Import overhead CSV to generate floor layouts")
    parser.add_argument("--version", "-V", action="version",
                        version=f"ib-lookup {__version__}")
    args = parser.parse_args()

    # Handle --import-overhead
    if args.import_overhead:
        from ib_lookup.overhead import import_overhead
        success = import_overhead(args.import_overhead)
        sys.exit(0 if success else 1)

    # Handle --trad (or trad-lookup invocation)
    if args.trad:
        from ib_lookup.trad_cli import run_trad
        run_trad(file_arg=args.file)
        return

    xlsx_path = _find_xlsx(args.file)
    if not xlsx_path:
        print(f"\n  {c(RED+BOLD, 'No IB Sketch .xlsx found')}")
        print(f"\n  {c(BOLD, 'Options:')}")
        print(f"    1. Place your IB Sketch .xlsx in the current directory")
        print(f"    2. Run with: {c(CYAN, 'ib-lookup --file /path/to/sketch.xlsx')}")
        print(f"    3. Import a floor layout: {c(CYAN, 'ib-lookup --import-overhead overhead.csv')}")
        print(f"\n  {c(DIM, 'The file should have Pull Schedule and ELEV tabs.')}")
        sys.exit(1)

    if args.query:
        # One-shot mode — silent, just results
        connections, elevations, site, data_halls = _load_data(xlsx_path)
        results = search(connections, args.query)
        if not results:
            print(f"  {c(DIM, 'No matches for ' + repr(args.query))}")
            return
        print(f"\n  {c(BOLD, args.query)} — {len(results)} matches\n")
        for idx, conn in enumerate(results, 1):
            _print_result(conn, idx)
        if len(results) == 1:
            _print_detail(results[0], elevations)
        print()
        return

    print(f"  {c(GREEN, 'Found:')} {os.path.basename(xlsx_path)}")
    _run(xlsx_path)


if __name__ == "__main__":
    main()
