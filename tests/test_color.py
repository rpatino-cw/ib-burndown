"""Tests for ib_lookup.color — ANSI color helpers."""

import os
from ib_lookup.color import colorize, color_enabled, set_color, RESET, BOLD, CYAN


def test_colorize_disabled():
    os.environ["NO_COLOR"] = "1"
    from ib_lookup import color
    color._use_color = None  # reset cached value
    assert colorize("@", "@") == "@"
    del os.environ["NO_COLOR"]
    color._use_color = None


def test_colorize_symbol_at():
    set_color(True)
    result = colorize("@", "@")
    assert BOLD in result
    assert CYAN in result
    assert RESET in result
    set_color(None)


def test_colorize_no_symbol():
    set_color(True)
    result = colorize("hello")
    assert result == "hello"  # no matching symbol
    set_color(None)
