"""Tests for ib_lookup.trad_cli — traditional networking search and display."""

import json
from ib_lookup.trad_cli import _search, _short_dns, _role_from_dns


# ── _short_dns ──

def test_short_dns_strips_prefix_and_suffix():
    assert _short_dns("dh2-t0-d1-01-r001-us-central-07a", "us-central-07a") == "t0-d1-01-r001"


def test_short_dns_no_site():
    result = _short_dns("dh2-t0-d1-01-r001-us-central-07a")
    assert result == "t0-d1-01-r001-us-central-07a"  # only strips dh prefix


def test_short_dns_no_dh_prefix():
    assert _short_dns("some-host", "site") == "some-host"


# ── _role_from_dns ──

def test_role_infra():
    assert _role_from_dns("dh2-infra-d1-01-r130-us-central-07a") == "infra"


def test_role_t0():
    assert _role_from_dns("dh2-t0-d1-01-r001-us-central-07a") == "t0"


def test_role_grid():
    assert _role_from_dns("dh2-grid-agg-d-01-r130-us-central-07a") == "grid"


def test_role_other():
    assert _role_from_dns("some-unknown-host") == "other"


# ── _search ──

def _make_data():
    return {
        "devices": [
            {"dns": "dh2-t0-d1-01-r001-us-test-01", "rack": 1, "ru": 46, "model": "SN5610", "role": "t0"},
            {"dns": "dh2-infra-d1-01-r130-us-test-01", "rack": 130, "ru": 44, "model": "SN3700", "role": "infra"},
            {"dns": "dh2-net-d1-01-r001-us-test-01", "rack": 1, "ru": 44, "model": "SN2201", "role": "net"},
        ],
        "conn_index": {
            "dh2-t0-d1-01-r001-us-test-01": [0],
            "dh2-infra-d1-01-r130-us-test-01": [0],
            "dh2-net-d1-01-r001-us-test-01": [1],
        },
        "connections": [],
    }


def test_search_exact_hostname():
    data = _make_data()
    results = _search(data, "dh2-t0-d1-01-r001-us-test-01")
    assert len(results) == 1
    assert results[0] == "dh2-t0-d1-01-r001-us-test-01"


def test_search_by_rack():
    data = _make_data()
    results = _search(data, "r1")
    assert len(results) == 2  # t0 and net in rack 1


def test_search_by_rack_number_only():
    data = _make_data()
    results = _search(data, "130")
    assert len(results) == 1
    assert "r130" in results[0]


def test_search_by_role():
    data = _make_data()
    results = _search(data, "infra")
    assert len(results) >= 1


def test_search_by_model():
    data = _make_data()
    results = _search(data, "SN5610")
    assert len(results) >= 1


def test_search_substring():
    data = _make_data()
    results = _search(data, "t0-d1")
    assert len(results) >= 1


def test_search_no_match():
    data = _make_data()
    results = _search(data, "nonexistent")
    assert len(results) == 0


def test_search_empty():
    data = _make_data()
    results = _search(data, "")
    assert len(results) == 0
