"""Traditional networking interactive CLI — search devices, connections, elevations, maps."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from collections import defaultdict

from ib_lookup.color import BOLD, DIM, RESET, CYAN, YELLOW, RED, GREEN, WHITE, MAGENTA
from ib_lookup.layouts import load_layouts, resolve_dh, normalize_layout
from ib_lookup.renderer import draw_map

_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(_DIR)


# ════════════════════════════════════════════════════════════════
#  DATA LOADING
# ════════════════════════════════════════════════════════════════

def _find_trad_data(file_arg: str | None = None) -> str | None:
    """Find trad-data.json or MASTER cutsheet xlsx."""
    if file_arg and os.path.isfile(file_arg):
        return os.path.abspath(file_arg)

    # Look for pre-exported trad-data.json
    for d in [os.getcwd(), _PROJECT_DIR, os.path.expanduser("~/dev/Network_guides")]:
        p = os.path.join(d, "trad-data.json")
        if os.path.isfile(p):
            return p

    # Look for MASTER xlsx
    import glob
    for d in [os.getcwd(), _PROJECT_DIR, os.path.expanduser("~/dev/Network_guides")]:
        for f in glob.glob(os.path.join(d, "MASTER*.xlsx")):
            if not os.path.basename(f).startswith("~$"):
                return f

    return None


def _load_trad_data(path: str) -> dict:
    """Load trad data from JSON or parse from MASTER xlsx."""
    if path.endswith(".json"):
        with open(path) as f:
            data = json.load(f)

        # Check freshness
        age_days = (time.time() - os.path.getmtime(path)) / 86400
        if age_days > 7:
            print(f"  {YELLOW}trad-data.json is {int(age_days)} days old{RESET}")

        return data

    # Parse from xlsx
    from ib_lookup.trad_parser import export_trad_data
    cache_path = os.path.join(os.path.dirname(path), "trad-data.json")
    data = export_trad_data(path, output_path=cache_path)
    return data


def _load_layouts_for_trad(data: dict) -> dict[str, dict]:
    """Load floor layouts for trad data halls."""
    all_layouts = load_layouts(extra_paths=[
        os.path.join(os.path.expanduser("~/dev/cw-node-helper"), "dh_layouts.json"),
    ])

    # Use embedded layout if present
    if data.get("layout") and data["layout"].get("columns"):
        embedded = data["layout"]
        dh_list = data.get("data_halls", [])
        # Figure out which DH the embedded layout belongs to
        if dh_list:
            key = dh_list[0]
        else:
            key = "DH2"
        result = {key: normalize_layout(embedded)}
        result[key]["label"] = result[key].get("label") or key.upper()
        return result

    # Try datahall layouts
    result = {}
    for dh in data.get("data_halls", []):
        key, layout = resolve_dh(all_layouts, dh)
        if layout:
            nl = normalize_layout(layout)
            nl["label"] = nl.get("label") or dh.upper()
            result[dh] = nl
    return result


# ════════════════════════════════════════════════════════════════
#  SEARCH
# ════════════════════════════════════════════════════════════════

def _search(data: dict, query: str) -> list[str]:
    """Search for devices matching query. Returns list of dns names."""
    q = query.strip().lower()
    if not q:
        return []

    conn_index = data.get("conn_index", {})
    devices = data.get("devices", [])

    # Exact hostname match
    for dns in conn_index:
        if dns.lower() == q:
            return [dns]

    matches = set()

    # Rack number search: r130, R130, 130
    rack_match = re.match(r'^r?(\d+)$', q, re.IGNORECASE)
    if rack_match:
        rack_num = int(rack_match.group(1))
        for d in devices:
            if d["rack"] == rack_num:
                matches.add(d["dns"])
        if matches:
            return sorted(matches)

    # Substring match on hostnames
    for dns in conn_index:
        if q in dns.lower():
            matches.add(dns)

    # Match on device role/model
    for d in devices:
        if q in d.get("role", "").lower() or q in d.get("model", "").lower():
            matches.add(d["dns"])

    return sorted(matches)


# ════════════════════════════════════════════════════════════════
#  DISPLAY
# ════════════════════════════════════════════════════════════════

def _short_dns(dns: str, site: str = "") -> str:
    """Shorten dns by stripping DH prefix and site suffix."""
    result = dns
    # Strip dhN- prefix
    m = re.match(r'^dh\d+-', result, re.IGNORECASE)
    if m:
        result = result[m.end():]
    # Strip -site suffix
    if site:
        suffix = f"-{site}"
        if result.lower().endswith(suffix.lower()):
            result = result[:-len(suffix)]
    return result


def _role_from_dns(dns: str) -> str:
    dl = dns.lower()
    for r in ["infra", "grid", "pod", "net", "con"]:
        if f"-{r}" in dl:
            return r
    m = re.match(r'.*-(t\d)', dl)
    if m:
        return m.group(1)
    if "-node-" in dl or "-r0" in dl:
        return "node"
    return "other"


def _print_device(dns: str, data: dict, site: str = "") -> list[dict]:
    """Print device info + all connections. Returns connection list."""
    device_map = {d["dns"]: d for d in data.get("devices", [])}
    conn_index = data.get("conn_index", {})
    connections = data.get("connections", [])

    dev = device_map.get(dns)
    if dev:
        print(f"\n  {CYAN}{BOLD}{dns}{RESET}")
        print(f"  {DIM}Model:{RESET} {dev['model']}  {DIM}Role:{RESET} {dev['role']}  "
              f"{DIM}Loc:{RESET} {dev['loc']}  {DIM}R{dev['rack']}:U{dev['ru']}{RESET}")
        if dev.get("mgmt_ip"):
            print(f"  {DIM}Mgmt:{RESET} {dev['mgmt_ip']}")
    else:
        print(f"\n  {CYAN}{BOLD}{dns}{RESET}  {DIM}(connection peer only){RESET}")

    indices = conn_index.get(dns, [])
    if not indices:
        print(f"  {DIM}No connections found{RESET}")
        return []

    conns = [connections[i] for i in indices if i < len(connections)]
    print(f"  {BOLD}{len(conns)} connections{RESET}\n")

    # Group by peer role
    grouped = defaultdict(list)
    for c in conns:
        if c["a_dns"].lower() == dns.lower():
            peer_dns = c["z_dns"]
        else:
            peer_dns = c["a_dns"]
        role = _role_from_dns(peer_dns)
        grouped[role].append(c)

    idx = 0
    ordered = sorted(grouped.items(), key=lambda x: (-len(x[1]), x[0]))
    for role, role_conns in ordered:
        print(f"  {MAGENTA}{BOLD}{role.upper()}{RESET} {DIM}({len(role_conns)}){RESET}")
        for c in role_conns:
            idx += 1
            if c["a_dns"].lower() == dns.lower():
                my_port, peer_dns, peer_port = c["a_port"], c["z_dns"], c["z_port"]
                peer_rack, peer_ru = c["z_rack"], c["z_ru"]
            else:
                my_port, peer_dns, peer_port = c["z_port"], c["a_dns"], c["a_port"]
                peer_rack, peer_ru = c["a_rack"], c["a_ru"]

            loc_str = f"R{peer_rack}:U{peer_ru}" if peer_rack else ""
            cable_str = f"Cable:{c['cable']}" if c.get("cable") else ""
            peer_short = _short_dns(peer_dns, site)

            print(f"    {DIM}{idx:>3}.{RESET} {WHITE}{my_port:<8}{RESET} {DIM}->{RESET} "
                  f"{YELLOW}{peer_short}{RESET} {peer_port:<8} "
                  f"{DIM}{loc_str}{RESET}  {DIM}{cable_str}{RESET}")
        print()

    return conns


def _print_conn_detail(conn: dict, data: dict):
    device_map = {d["dns"]: d for d in data.get("devices", [])}

    print(f"\n  {BOLD}Connection Detail{RESET}")
    print(f"  {DIM}{'─' * 60}{RESET}")

    a_dev = device_map.get(conn["a_dns"], {})
    print(f"  {CYAN}{BOLD}A-Side{RESET}")
    print(f"    {CYAN}{conn['a_dns']}{RESET}")
    print(f"    Port: {conn['a_port']}  {DIM}R{conn['a_rack']}:U{conn['a_ru']}{RESET}"
          f"  {DIM}Model: {a_dev.get('model', '?')}{RESET}")

    z_dev = device_map.get(conn["z_dns"], {})
    print(f"  {YELLOW}{BOLD}Z-Side{RESET}")
    print(f"    {YELLOW}{conn['z_dns']}{RESET}")
    print(f"    Port: {conn['z_port']}  {DIM}R{conn['z_rack']}:U{conn['z_ru']}{RESET}"
          f"  {DIM}Model: {z_dev.get('model', '?')}{RESET}")

    if conn.get("cable"):
        print(f"  {DIM}Cable: {conn['cable']}{RESET}")
    if conn.get("status"):
        print(f"  {DIM}Status: {conn['status']}{RESET}")
    print(f"  {DIM}{'─' * 60}{RESET}")


# ════════════════════════════════════════════════════════════════
#  ELEVATION
# ════════════════════════════════════════════════════════════════

_ANSI_RE = re.compile(r'\033\[[0-9;]*m')


def _draw_trad_elevation(rack_a: int, rack_b: int | None, data: dict,
                         highlight_dns: set[str] | None = None):
    """Draw full rack elevation using rack inventory."""
    if highlight_dns is None:
        highlight_dns = set()

    rack_inv = {int(k): v for k, v in data.get("rack_inventory", {}).items()}
    site = data.get("site", "")

    def _render_rack(rack_num: int) -> list[str]:
        inv = rack_inv.get(rack_num, [])
        if not inv:
            return [f"  {DIM}(no devices in R{rack_num}){RESET}"]

        by_ru: dict[int, list[dict]] = {}
        for d in inv:
            by_ru.setdefault(d["ru"], []).append(d)

        max_ru = max(by_ru.keys())
        min_ru = min(by_ru.keys())

        lines = [f"  {BOLD}Rack {rack_num}{RESET}  {DIM}({len(inv)} devices){RESET}"]
        lines.append(f"  {DIM}+{'=' * 58}+{RESET}")

        for ru in range(max_ru, min_ru - 1, -1):
            devs = by_ru.get(ru)
            if devs:
                for dev in devs:
                    dns = dev["dns"]
                    model = dev.get("model", "")
                    short = _short_dns(dns, site)
                    if dns in highlight_dns:
                        lines.append(
                            f"  {DIM}|{RESET} {BOLD}{ru:>2}{RESET}  "
                            f"{CYAN}{BOLD}{short:<35}{RESET} "
                            f"{WHITE}{model:<10}{RESET} "
                            f"{CYAN}{BOLD}<--{RESET}"
                        )
                    else:
                        lines.append(
                            f"  {DIM}|{RESET} {DIM}{ru:>2}{RESET}  "
                            f"{DIM}{short:<35}{RESET} "
                            f"{DIM}{model:<10}{RESET}"
                        )
            else:
                lines.append(f"  {DIM}| {ru:>2}  ·{RESET}")

        lines.append(f"  {DIM}+{'=' * 58}+{RESET}")
        return lines

    print()
    sides = [_render_rack(rack_a)]
    if rack_b and rack_b != rack_a:
        sides.append(_render_rack(rack_b))

    if len(sides) == 2:
        max_len = max(len(sides[0]), len(sides[1]))
        for s in sides:
            while len(s) < max_len:
                s.append("")
        max_w = max(len(_ANSI_RE.sub('', line)) for line in sides[0])
        pad = max(max_w + 4, 65)
        for l_line, r_line in zip(sides[0], sides[1]):
            visible_len = len(_ANSI_RE.sub('', l_line))
            spacing = pad - visible_len
            print(f"{l_line}{' ' * spacing}{r_line}")
    else:
        for line in sides[0]:
            print(line)
    print()


# ════════════════════════════════════════════════════════════════
#  TIPS
# ════════════════════════════════════════════════════════════════

_TIPS = [
    ("Find the racks", "Go to R{rack_a} ({name_a}) and R{rack_b} ({name_b})"),
    ("Check cable seating", "Reseat cable at both ends — pull fully out, inspect, push back in"),
    ("Inspect for damage", "Look for bent pins, dust, kinks, or damaged fiber ends"),
    ("Verify port LEDs", "Check link LED on both switch ports — should be green/amber, not off"),
    ("Label check", "Confirm cable label matches cutsheet for both ends"),
    ("Escalate if no fix", "Comment on the ticket and tag network engineering"),
]


# ════════════════════════════════════════════════════════════════
#  DETAIL PROMPT
# ════════════════════════════════════════════════════════════════

def _detail_prompt(conn: dict, data: dict, layouts: dict, site: str = ""):
    rack_a = conn["a_rack"]
    rack_b = conn["z_rack"]
    has_map = bool(rack_a or rack_b)
    has_elev = bool(rack_a or rack_b)

    opts = []
    if has_map:
        opts.append(f"{DIM}[m]{RESET} map")
    if has_elev:
        opts.append(f"{DIM}[e]{RESET} elevation")
    opts.append(f"{DIM}[t]{RESET} tips")
    opts.append(f"{DIM}[Enter]{RESET} back")
    hint = " ".join(opts)
    print(f"  {hint}")

    while True:
        sel = _prompt()
        if not sel:
            return
        sl = sel.lower()
        if sl in ("q", "quit", "exit"):
            raise SystemExit(0)

        if sl == "m" and has_map:
            # Use first available layout
            layout = next(iter(layouts.values()), None) if layouts else None
            if layout:
                draw_map(layout,
                         highlight_a=rack_a,
                         highlight_b=rack_b if rack_b != rack_a else None,
                         label_a=_short_dns(conn["a_dns"], site),
                         label_b=_short_dns(conn["z_dns"], site) if rack_b != rack_a else "")
            else:
                print(f"  {DIM}No floor layout available{RESET}")
            print(f"  {hint}")

        elif sl == "e" and has_elev:
            highlights = {conn["a_dns"], conn["z_dns"]}
            _draw_trad_elevation(rack_a, rack_b, data, highlight_dns=highlights)
            print(f"  {hint}")

        elif sl == "t":
            subs = {
                "rack_a": rack_a or "?",
                "rack_b": rack_b or "?",
                "name_a": _short_dns(conn["a_dns"], site),
                "name_b": _short_dns(conn["z_dns"], site),
            }
            print(f"\n  {BOLD}Steps:{RESET}")
            for i, (label, cmd) in enumerate(_TIPS, 1):
                try:
                    filled = cmd.format(**subs)
                except KeyError:
                    filled = cmd
                print(f"    {DIM}{i}.{RESET} {label}")
                print(f"       {CYAN}{filled}{RESET}")
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


def run_trad(file_arg: str | None = None):
    """Main entry point for --trad mode."""
    path = _find_trad_data(file_arg)
    if not path:
        print(f"\n  {RED}{BOLD}No traditional networking data found{RESET}")
        print(f"\n  {BOLD}Options:{RESET}")
        print(f"    1. Place trad-data.json or MASTER*.xlsx in the current directory")
        print(f"    2. Run with: {CYAN}ib-lookup --trad --file /path/to/MASTER.xlsx{RESET}")
        print(f"    3. Export from Network_guides: {CYAN}python3 export_trad.py{RESET}")
        sys.exit(1)

    _clear()
    print(f"\n  {DIM}Loading traditional networking data...{RESET}", end="", flush=True)
    data = _load_trad_data(path)
    layouts = _load_layouts_for_trad(data)
    _clear()

    site = data.get("site", "")
    devices = data.get("devices", [])
    connections = data.get("connections", [])
    device_map = {d["dns"]: d for d in devices}

    site_label = site or os.path.basename(path).replace(".json", "").replace(".xlsx", "")
    print(f"\n  {BOLD}Traditional Networking Lookup{RESET}  {DIM}{site_label}{RESET}")
    print(f"  {DIM}{len(devices)} devices · {len(connections)} connections{RESET}")
    print(f"  {DIM}Search by hostname, rack (r130), or role (infra, t0){RESET}")
    print(f"  {DIM}Type 'q' to quit{RESET}\n")

    while True:
        _flush_stdin()
        query = _prompt(f"{CYAN}search:{RESET} ")

        if not query:
            continue
        if query.lower() in ("q", "quit", "exit"):
            break

        results = _search(data, query)

        if not results:
            print(f"  {DIM}No matches for '{query}'{RESET}\n")
            continue

        if len(results) == 1:
            dns = results[0]
            conns = _print_device(dns, data, site)
            if not conns:
                continue

            while True:
                print(f"  {DIM}[1-{len(conns)}] detail  [m] map  [Enter] search{RESET}")
                sel = _prompt()
                if not sel:
                    break
                if sel.lower() in ("q", "quit", "exit"):
                    sys.exit(0)
                if sel.lower() == "m":
                    dev = device_map.get(dns)
                    rack = dev["rack"] if dev else None
                    layout = next(iter(layouts.values()), None) if layouts else None
                    if layout and rack:
                        draw_map(layout, highlight_a=rack, label_a=_short_dns(dns, site))
                    else:
                        print(f"  {DIM}No floor layout available{RESET}")
                    continue
                try:
                    idx = int(sel)
                    if 1 <= idx <= len(conns):
                        conn = conns[idx - 1]
                        _print_conn_detail(conn, data)
                        _detail_prompt(conn, data, layouts, site)
                        conns = _print_device(dns, data, site)
                    else:
                        print(f"  {DIM}Pick 1-{len(conns)}{RESET}")
                except ValueError:
                    break
            continue

        # Multiple matches
        print(f"\n  {BOLD}{len(results)} matches:{RESET}")
        for i, dns in enumerate(results, 1):
            dev = device_map.get(dns)
            if dev:
                print(f"    {DIM}{i:>3}.{RESET} {CYAN}{dns}{RESET}  "
                      f"{DIM}{dev['model']}  R{dev['rack']}:U{dev['ru']}{RESET}")
            else:
                print(f"    {DIM}{i:>3}.{RESET} {CYAN}{dns}{RESET}")
            if i >= 30:
                remaining = len(results) - 30
                if remaining > 0:
                    print(f"    {DIM}... and {remaining} more (narrow your search){RESET}")
                break

        print()
        sel = _prompt(f"{DIM}[1-{min(len(results), 30)}] or new search:{RESET} ")
        if not sel:
            continue
        if sel.lower() in ("q", "quit", "exit"):
            break

        try:
            idx = int(sel)
            if 1 <= idx <= len(results):
                dns = results[idx - 1]
                conns = _print_device(dns, data, site)
                if conns:
                    while True:
                        print(f"  {DIM}[1-{len(conns)}] detail  [m] map  [Enter] search{RESET}")
                        sel2 = _prompt()
                        if not sel2:
                            break
                        if sel2.lower() in ("q", "quit", "exit"):
                            sys.exit(0)
                        if sel2.lower() == "m":
                            dev = device_map.get(dns)
                            rack = dev["rack"] if dev else None
                            layout = next(iter(layouts.values()), None) if layouts else None
                            if layout and rack:
                                draw_map(layout, highlight_a=rack, label_a=_short_dns(dns, site))
                            continue
                        try:
                            ci = int(sel2)
                            if 1 <= ci <= len(conns):
                                conn = conns[ci - 1]
                                _print_conn_detail(conn, data)
                                _detail_prompt(conn, data, layouts, site)
                                conns = _print_device(dns, data, site)
                        except ValueError:
                            break
        except ValueError:
            results2 = _search(data, sel)
            if len(results2) == 1:
                _print_device(results2[0], data, site)
            elif results2:
                print(f"  {DIM}{len(results2)} matches — be more specific{RESET}")
