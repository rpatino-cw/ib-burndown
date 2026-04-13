"""Search connections by switch name, port, or fabric ID."""

from __future__ import annotations

import re


def switch_matches(name: str, pattern: str) -> bool:
    name_up = name.upper()
    pat_up = pattern.upper()
    if name_up == pat_up:
        return True
    if "-" in name_up and "-" not in pat_up:
        base = name_up.split("-")[0]
        return base == pat_up
    return False


def auto_detect_type(raw_id: str) -> list[str]:
    """Given bare ID like '8.3.2', return candidates with type prefix."""
    parts = raw_id.split(".")
    if len(parts) == 3:
        return [f"S{raw_id}"]
    elif len(parts) == 2:
        return [f"L{raw_id}", f"C{raw_id}"]
    elif len(parts) == 1:
        return [f"C{raw_id}"]
    return [raw_id]


def parse_query(query: str) -> tuple[str, str]:
    """Split 'C1.15 20/2' into (switch_name, port_filter)."""
    q = query.strip()
    m = re.match(r'^(\S+)\s+(\d+/\d+)$', q)
    if m:
        return m.group(1), m.group(2)
    return q, ""


def search(connections: list[dict], query: str) -> list[dict]:
    q = query.strip()
    if not q:
        return []

    switch_q, port_filter = parse_query(q)

    has_prefix = bool(re.match(r'^[SCLNscln]', switch_q)) and not switch_q[0].isdigit()
    if has_prefix:
        candidates = [switch_q.upper()]
    elif re.match(r'^\d+[\.\d]*$', switch_q):
        candidates = [c.upper() for c in auto_detect_type(switch_q)]
    else:
        candidates = [switch_q.upper()]

    results = []
    seen = set()
    sq_upper = switch_q.upper()

    for conn in connections:
        conn_id = id(conn)
        if conn_id in seen:
            continue

        src_up = conn["src_name"].upper()
        dest_up = conn["dest_name"].upper()

        matched = False
        matched_side = None
        for cand in candidates:
            if switch_matches(src_up, cand):
                matched, matched_side = True, "src"
                break
            if switch_matches(dest_up, cand):
                matched, matched_side = True, "dest"
                break

        if not matched:
            if len(sq_upper) <= 4:
                pat = re.compile(re.escape(sq_upper) + r'(?=[\.\-]|$)')
                if pat.search(src_up):
                    matched, matched_side = True, "src"
                elif pat.search(dest_up):
                    matched, matched_side = True, "dest"
            else:
                if sq_upper in src_up:
                    matched, matched_side = True, "src"
                elif sq_upper in dest_up:
                    matched, matched_side = True, "dest"

        if not matched:
            if conn.get("fabric_id") and sq_upper in conn["fabric_id"].upper():
                matched = True

        if matched and port_filter:
            port_ok = False
            if matched_side == "src" and conn["src_port"] == port_filter:
                port_ok = True
            elif matched_side == "dest" and conn["dest_port"] == port_filter:
                port_ok = True
            elif matched_side is None:
                if conn["src_port"] == port_filter or conn["dest_port"] == port_filter:
                    port_ok = True
            if not port_ok:
                matched = False

        if matched:
            seen.add(conn_id)
            results.append(conn)

    return results
