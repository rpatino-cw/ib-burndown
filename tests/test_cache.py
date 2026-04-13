"""Tests for ib_lookup.cache — JSON cache with auto-invalidation."""

import json
import os
from ib_lookup.cache import cache_path_for, load_cache, save_cache, CACHE_VERSION


def test_cache_path_adjacent_to_xlsx(tmp_path):
    xlsx = str(tmp_path / "test.xlsx")
    cp = cache_path_for(xlsx)
    assert os.path.dirname(cp) == str(tmp_path)
    assert cp.endswith(".ib_lookup_cache.json")


def test_save_and_load_cache(tmp_path):
    xlsx = str(tmp_path / "test.xlsx")
    # Create a dummy xlsx so mtime works
    with open(xlsx, "w") as f:
        f.write("dummy")

    conns = [{"src_name": "S1.1.1", "dest_name": "C1.1"}]
    elevs = {"S1.1.1": {"rack": 41, "ru": 38, "sku": "", "dh": "DH1", "row": ""}}

    save_cache(xlsx, conns, elevs, site="test", data_halls=["DH1"])
    result = load_cache(xlsx)

    assert result is not None
    assert len(result["connections"]) == 1
    assert "S1.1.1" in result["elevations"]
    assert result["site"] == "test"
    assert result["data_halls"] == ["DH1"]


def test_cache_invalidation_on_mtime_change(tmp_path):
    xlsx = str(tmp_path / "test.xlsx")
    with open(xlsx, "w") as f:
        f.write("v1")

    save_cache(xlsx, [{"a": 1}], {}, site="test")

    # Modify the xlsx (changes mtime)
    import time
    time.sleep(0.1)
    with open(xlsx, "w") as f:
        f.write("v2")

    result = load_cache(xlsx)
    assert result is None  # cache should be invalid


def test_cache_invalidation_on_version_change(tmp_path):
    xlsx = str(tmp_path / "test.xlsx")
    with open(xlsx, "w") as f:
        f.write("dummy")

    save_cache(xlsx, [{"a": 1}], {})

    # Tamper with version in cache
    cp = cache_path_for(xlsx)
    with open(cp) as f:
        data = json.load(f)
    data["cache_version"] = CACHE_VERSION - 1
    with open(cp, "w") as f:
        json.dump(data, f)

    result = load_cache(xlsx)
    assert result is None


def test_load_cache_missing_file(tmp_path):
    result = load_cache(str(tmp_path / "nonexistent.xlsx"))
    assert result is None
