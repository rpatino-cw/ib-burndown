"""Tests for ib_lookup.search — switch name matching and query parsing."""

from ib_lookup.search import switch_matches, auto_detect_type, parse_query, search


# ── switch_matches ──

def test_exact_match():
    assert switch_matches("S1.1.1", "S1.1.1") is True


def test_case_insensitive():
    assert switch_matches("s1.1.1", "S1.1.1") is True


def test_dh_suffix_stripped():
    """L10.1.1-DH2 should match L10.1.1 (without DH suffix)."""
    assert switch_matches("L10.1.1-DH2", "L10.1.1") is True


def test_no_match():
    assert switch_matches("S1.1.1", "S2.2.2") is False


def test_partial_no_match():
    assert switch_matches("S1.1.1", "S1.1") is False


# ── auto_detect_type ──

def test_auto_detect_3_parts():
    assert auto_detect_type("8.3.2") == ["S8.3.2"]


def test_auto_detect_2_parts():
    assert auto_detect_type("8.3") == ["L8.3", "C8.3"]


def test_auto_detect_1_part():
    assert auto_detect_type("8") == ["C8"]


# ── parse_query ──

def test_parse_query_with_port():
    name, port = parse_query("C1.15 20/2")
    assert name == "C1.15"
    assert port == "20/2"


def test_parse_query_no_port():
    name, port = parse_query("S5.3.1")
    assert name == "S5.3.1"
    assert port == ""


def test_parse_query_extra_spaces():
    name, port = parse_query("  C1.15  20/2  ")
    assert name == "C1.15"
    assert port == "20/2"


# ── search (integration with connection data) ──

_SAMPLE_CONNS = [
    {"src_name": "S1.1.1", "dest_name": "C1.1", "src_port": "1/1", "dest_port": "9/1",
     "fabric_id": "test-fab01", "data_hall": "DH1", "src_type": "Spine", "dest_type": "Core"},
    {"src_name": "S1.1.1", "dest_name": "C1.2", "src_port": "1/2", "dest_port": "9/1",
     "fabric_id": "test-fab01", "data_hall": "DH1", "src_type": "Spine", "dest_type": "Core"},
    {"src_name": "L10.1.1-DH2", "dest_name": "S1.1.1", "src_port": "25/1", "dest_port": "17/1",
     "fabric_id": "test-fab01", "data_hall": "DH2", "src_type": "Leaf", "dest_type": "Spine"},
]


def test_search_exact():
    results = search(_SAMPLE_CONNS, "S1.1.1")
    assert len(results) == 3  # appears in all 3 connections


def test_search_with_port_filter():
    results = search(_SAMPLE_CONNS, "S1.1.1 1/1")
    assert len(results) == 1
    assert results[0]["src_port"] == "1/1"


def test_search_leaf():
    results = search(_SAMPLE_CONNS, "L10.1.1")
    assert len(results) == 1
    assert "L10" in results[0]["src_name"]


def test_search_bare_id_auto_detect():
    """Searching '1.1.1' should auto-detect as spine and match S1.1.1."""
    results = search(_SAMPLE_CONNS, "1.1.1")
    assert len(results) >= 1


def test_search_fabric_id():
    results = search(_SAMPLE_CONNS, "test-fab01")
    assert len(results) == 3


def test_search_no_results():
    results = search(_SAMPLE_CONNS, "ZZZZZ")
    assert len(results) == 0


def test_search_empty():
    results = search(_SAMPLE_CONNS, "")
    assert len(results) == 0


def test_search_substring_short():
    """Short query 'L10' should match with word boundary."""
    results = search(_SAMPLE_CONNS, "L10")
    assert len(results) >= 1


def test_search_case_insensitive():
    results = search(_SAMPLE_CONNS, "s1.1.1")
    assert len(results) == 3
