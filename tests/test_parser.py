"""Tests for ib_lookup.parser — Excel parsing for IB connections + elevations."""

from datetime import datetime
from ib_lookup.parser import (
    normalize_port, build_switch_name, parse_switch_name,
    parse_connections, parse_elevations,
)


# ── normalize_port ──

def test_normalize_port_datetime():
    """Excel corrupts 20/2 into a datetime — should convert back."""
    dt = datetime(2024, 2, 20)  # Feb 20
    assert normalize_port(dt) == "2/20"


def test_normalize_port_int():
    assert normalize_port(5) == "5"


def test_normalize_port_float_whole():
    assert normalize_port(5.0) == "5"


def test_normalize_port_string():
    assert normalize_port("20/2") == "20/2"


def test_normalize_port_none():
    assert normalize_port(None) == ""


# ── build_switch_name ──

def test_build_switch_name_spine():
    assert build_switch_name("Spine", "1.1.1", "DH1") == "S1.1.1"


def test_build_switch_name_core():
    assert build_switch_name("Core", "1.15", "") == "C1.15"


def test_build_switch_name_leaf_with_cab_and_dh():
    assert build_switch_name("Leaf", "1.2", "DH2", cab="10") == "L10.1.2-DH2"


def test_build_switch_name_leaf_no_dh():
    assert build_switch_name("Leaf", "1.1", "", cab="20") == "L20.1.1"


# ── parse_switch_name ──

def test_parse_switch_name_spine():
    r = parse_switch_name("S1.5.2")
    assert r["type"] == "Spine"
    assert r["id"] == "1.5.2"
    assert r["dh"] == ""
    assert r["cab"] == ""


def test_parse_switch_name_core():
    r = parse_switch_name("C1.15")
    assert r["type"] == "Core"
    assert r["id"] == "1.15"


def test_parse_switch_name_leaf_with_dh():
    r = parse_switch_name("L10.1.2-DH2")
    assert r["type"] == "Leaf"
    assert r["cab"] == "10"
    assert r["id"] == "1.2"
    assert r["dh"] == "DH2"


def test_parse_switch_name_empty():
    r = parse_switch_name("")
    assert r["type"] == ""
    assert r["id"] == ""


# ── parse_connections (with real xlsx fixture) ──

def test_parse_connections_count(sample_ib_xlsx):
    conns = parse_connections(sample_ib_xlsx)
    assert len(conns) == 5  # 3 core + 1 DH1 + 1 DH2


def test_parse_connections_fields(sample_ib_xlsx):
    conns = parse_connections(sample_ib_xlsx)
    c = conns[0]
    assert c["src_name"] == "S1.1.1"
    assert c["dest_name"] == "C1.1"
    assert c["src_port"] == "1/1"
    assert c["dest_port"] == "9/1"
    assert c["cable_type"] == "MTP"
    assert c["fabric_id"] == "test-site-fab01"
    assert c["status"] == "Active"


def test_parse_connections_dh_detection(sample_ib_xlsx):
    conns = parse_connections(sample_ib_xlsx)
    dh1_conns = [c for c in conns if c["data_hall"] == "DH1"]
    dh2_conns = [c for c in conns if c["data_hall"] == "DH2"]
    assert len(dh1_conns) >= 1
    assert len(dh2_conns) >= 1


def test_parse_connections_leaf_name(sample_ib_xlsx):
    conns = parse_connections(sample_ib_xlsx)
    leaf_conns = [c for c in conns if "L10" in c["src_name"] or "L20" in c["src_name"]]
    assert len(leaf_conns) >= 1


# ── parse_elevations ──

def test_parse_elevations_count(sample_ib_xlsx):
    elevs = parse_elevations(sample_ib_xlsx)
    assert len(elevs) >= 4  # S1.1.1, S1.1.2, C1.1, C1.2 minimum


def test_parse_elevations_data(sample_ib_xlsx):
    elevs = parse_elevations(sample_ib_xlsx)
    s = elevs.get("S1.1.1")
    assert s is not None
    assert s["rack"] == 41
    assert s["ru"] == 38
    assert s["dh"] == "DH1"
    assert s["sku"] == "MQM9790-NS2F"


def test_parse_elevations_dh2(sample_ib_xlsx):
    elevs = parse_elevations(sample_ib_xlsx)
    s = elevs.get("S2.1.1")
    assert s is not None
    assert s["dh"] == "DH2"
    assert s["rack"] == 10


def test_parse_elevations_missing_file():
    elevs = parse_elevations("/nonexistent/file.xlsx")
    assert elevs == {}
