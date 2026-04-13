"""JSON cache with version + mtime auto-invalidation."""

from __future__ import annotations

import json
import os

CACHE_VERSION = 4  # bump when parsing logic changes


def cache_path_for(xlsx_path: str) -> str:
    """Return cache path adjacent to the xlsx file."""
    d = os.path.dirname(os.path.abspath(xlsx_path))
    return os.path.join(d, ".ib_lookup_cache.json")


def load_cache(xlsx_path: str) -> dict | None:
    cp = cache_path_for(xlsx_path)
    if not os.path.isfile(cp):
        return None
    try:
        mtime = os.path.getmtime(xlsx_path) if os.path.isfile(xlsx_path) else 0
        with open(cp) as f:
            cache = json.load(f)
        if (cache.get("cache_version") == CACHE_VERSION
                and cache.get("sketch_mtime") == mtime
                and "elevations" in cache):
            return {
                "connections": cache["connections"],
                "elevations": cache["elevations"],
                "site": cache.get("site", ""),
                "data_halls": cache.get("data_halls", []),
            }
    except (json.JSONDecodeError, OSError, KeyError):
        pass
    return None


def save_cache(xlsx_path: str, connections: list[dict],
               elevations: dict[str, dict], site: str = "",
               data_halls: list[str] | None = None):
    cp = cache_path_for(xlsx_path)
    try:
        mtime = os.path.getmtime(xlsx_path) if os.path.isfile(xlsx_path) else 0
        with open(cp, "w") as f:
            json.dump({
                "cache_version": CACHE_VERSION,
                "sketch_mtime": mtime,
                "connections": connections,
                "elevations": elevations,
                "site": site,
                "data_halls": data_halls or [],
            }, f)
    except OSError:
        pass
