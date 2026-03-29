#!/bin/bash
# load.sh — Visual terminal drop zone for IB Sketch xlsx
DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$DIR/EVI01 - IB Sketch.xlsx"

# ── Colors ──
RST='\033[0m'
DIM='\033[2m'
BOLD='\033[1m'
AMBER='\033[38;5;208m'
GREEN='\033[38;5;108m'
RED='\033[38;5;167m'
GRAY='\033[38;5;240m'
LGRAY='\033[38;5;245m'
WHITE='\033[38;5;252m'
BORDER='\033[38;5;238m'

W=54  # inner width

pad() { printf "%*s" $(( (W - ${#1}) / 2 )) ""; printf "%s" "$1"; printf "%*s" $(( (W - ${#1} + 1) / 2 )) ""; }
line() { printf "${BORDER}  │${RST}"; eval "$@"; printf "${BORDER}│${RST}\n"; }
blank() { line "printf '%${W}s' ''"; }

draw_box() {
  local STATE="${1:-idle}"

  printf '\033[2J\033[H'
  echo ""

  printf "  ${BOLD}${WHITE}IB Burndown${RST}  ${DIM}${LGRAY}Sketch Loader${RST}\n"
  printf "  ${DIM}${GRAY}EVI01 · US-CENTRAL-07A · Elk Grove${RST}\n"
  echo ""

  printf "  ${BORDER}┌"
  printf '─%.0s' $(seq 1 $W)
  printf "┐${RST}\n"

  blank
  blank

  if [ "$STATE" = "idle" ]; then
    line "printf '${AMBER}'; pad '↑'; printf '${RST}'"
    blank
    line "printf '${WHITE}${BOLD}'; pad 'Drop .xlsx here'; printf '${RST}'"
    blank
    line "printf '${DIM}${LGRAY}'; pad 'drag IB Sketch from Finder into terminal'; printf '${RST}'"
    line "printf '${DIM}${GRAY}'; pad 'or pass as argument: ./load.sh file.xlsx'; printf '${RST}'"
  elif [ "$STATE" = "success" ]; then
    line "printf '${GREEN}${BOLD}'; pad '✓'; printf '${RST}'"
    blank
    line "printf '${GREEN}${BOLD}'; pad '$2'; printf '${RST}'"
    blank
    line "printf '${LGRAY}'; pad '$3'; printf '${RST}'"
    line "printf '${LGRAY}'; pad '$4'; printf '${RST}'"
  elif [ "$STATE" = "error" ]; then
    line "printf '${RED}${BOLD}'; pad '✗'; printf '${RST}'"
    blank
    line "printf '${RED}'; pad '$2'; printf '${RST}'"
    blank
    line "printf '${DIM}${GRAY}'; pad '$3'; printf '${RST}'"
  fi

  blank
  blank

  printf "  ${BORDER}└"
  printf '─%.0s' $(seq 1 $W)
  printf "┘${RST}\n"

  echo ""
}

# ── Main ──
if [ -n "$1" ]; then
  FILE="$1"
else
  draw_box "idle"

  printf "  ${DIM}${LGRAY}Source sheet:${RST}\n"
  printf "  ${AMBER}https://docs.google.com/spreadsheets/d/1U132alRVDtcrVd5kW4v534U3ME7wRZ5g3kHQMZP2LaM${RST}\n"
  printf "  ${DIM}${GRAY}File → Download → Microsoft Excel (.xlsx)${RST}\n"
  echo ""

  printf "  ${AMBER}→${RST} "
  read -r FILE
fi

# Strip quotes and trailing whitespace from Finder drag
FILE=$(echo "$FILE" | sed "s/^['\"]//;s/['\"]$//;s/[[:space:]]*$//")

if [ ! -f "$FILE" ]; then
  draw_box "error" "File not found" "Check the path and try again"
  exit 1
fi

EXT="${FILE##*.}"
if [[ "$EXT" != "xlsx" && "$EXT" != "xls" ]]; then
  draw_box "error" "Expected .xlsx, got .$EXT" "Download as: File → Download → Excel"
  exit 1
fi

# Copy to project as the expected filename
cp "$FILE" "$TARGET"
SIZE=$(ls -lh "$TARGET" | awk '{print $5}')
BASENAME=$(basename "$FILE")

draw_box "success" "$BASENAME" "$SIZE → EVI01 - IB Sketch.xlsx" "Ready to run: ib-lookup <switch>"

printf "  ${DIM}${LGRAY}Run:${RST}\n"
printf "  ${WHITE}ib-lookup ${AMBER}<switch-name>${RST}\n"
echo ""
