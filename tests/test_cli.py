"""Tests for ib_lookup.cli — CLI entry point, file finding, data loading."""

import os
import subprocess
import sys


def test_version_flag():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "--version"],
        capture_output=True, text=True,
        cwd=os.path.expanduser("~/dev/ib-burndown"),
    )
    assert result.returncode == 0
    assert "2.0.0" in result.stdout


def test_help_flag():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "--help"],
        capture_output=True, text=True,
        cwd=os.path.expanduser("~/dev/ib-burndown"),
    )
    assert result.returncode == 0
    assert "--trad" in result.stdout
    assert "--import-overhead" in result.stdout
    assert "--file" in result.stdout


def test_oneshot_search():
    """Test non-interactive one-shot search with real EVI01 data."""
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "S5.3.1"],
        capture_output=True, text=True,
        cwd=os.path.expanduser("~/dev/ib-burndown"),
        timeout=30,
    )
    assert result.returncode == 0
    assert "S5.3.1" in result.stdout
    assert "match" in result.stdout.lower()


def test_oneshot_search_with_port():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "C1.15 20/2"],
        capture_output=True, text=True,
        cwd=os.path.expanduser("~/dev/ib-burndown"),
        timeout=30,
    )
    assert result.returncode == 0
    assert "1 match" in result.stdout.lower()


def test_oneshot_no_match():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "ZZZZNONEXISTENT"],
        capture_output=True, text=True,
        cwd=os.path.expanduser("~/dev/ib-burndown"),
        timeout=30,
    )
    assert result.returncode == 0
    assert "No matches" in result.stdout


def test_missing_file_flag():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "--file", "/nonexistent/file.xlsx"],
        capture_output=True, text=True,
        cwd="/tmp",
        timeout=10,
    )
    assert result.returncode != 0


def test_import_overhead_missing():
    result = subprocess.run(
        [sys.executable, "-m", "ib_lookup", "--import-overhead", "/nonexistent/file.csv"],
        capture_output=True, text=True,
        timeout=10,
    )
    assert result.returncode != 0
