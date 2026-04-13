"""ANSI color helpers with TTY detection and NO_COLOR support."""

import os
import sys

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RED = "\033[31m"
GREEN = "\033[32m"
WHITE = "\033[97m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

_use_color = None


def color_enabled():
    global _use_color
    if _use_color is not None:
        return _use_color
    if os.environ.get("NO_COLOR"):
        _use_color = False
    elif not sys.stdout.isatty():
        _use_color = False
    else:
        _use_color = True
    return _use_color


def set_color(enabled):
    """Override color detection (for testing)."""
    global _use_color
    _use_color = enabled


# Map symbols for floor map rendering
SYMBOL_STYLES = {
    "@": f"{BOLD}{CYAN}",
    "#": f"{BOLD}{YELLOW}",
    "!": f"{BOLD}{RED}",
    "-": DIM,
    "|": GREEN,
    "+": GREEN,
    "=": GREEN,
}


def colorize(text, symbol=None):
    if not color_enabled():
        return text
    style = SYMBOL_STYLES.get(symbol or text)
    if style:
        return f"{style}{text}{RESET}"
    return text
