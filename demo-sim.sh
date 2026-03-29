#!/bin/bash
# Simulated demo output for VHS recording
# Shows the ideal user experience without needing real xlsx/git

RST='\033[0m'
DIM='\033[2m'
BOLD='\033[1m'
AMBER='\033[38;5;208m'
GREEN='\033[38;5;108m'
RED='\033[38;5;167m'
GRAY='\033[38;5;240m'
LGRAY='\033[38;5;245m'
WHITE='\033[38;5;252m'
CYAN='\033[36m'
BORDER='\033[38;5;238m'

W=54

pad() { printf "%*s" $(( (W - ${#1}) / 2 )) ""; printf "%s" "$1"; printf "%*s" $(( (W - ${#1} + 1) / 2 )) ""; }
bline() { printf "  ${BORDER}│${RST}"; eval "$@"; printf "${BORDER}│${RST}\n"; }
blank() { bline "printf '%${W}s' ''"; }

case "$1" in
  clone)
    echo -e "Cloning into 'ib-burndown'..."
    sleep 1
    echo -e "done."
    ;;

  install)
    echo -e "Processing /Users/you/ib-burndown"
    sleep 0.5
    echo -e "  Installing build dependencies ... ${GREEN}done${RST}"
    sleep 0.5
    echo -e "  Getting requirements to build wheel ... ${GREEN}done${RST}"
    sleep 0.3
    echo -e "Successfully installed ib-lookup-1.0.0"
    ;;

  dropzone)
    printf '\033[2J\033[H'
    echo ""
    printf "  ${BOLD}${WHITE}IB Burndown${RST}  ${DIM}${LGRAY}Sketch Loader${RST}\n"
    printf "  ${DIM}${GRAY}EVI01 · US-CENTRAL-07A · Elk Grove${RST}\n"
    echo ""
    printf "  ${BORDER}┌"
    printf '─%.0s' $(seq 1 $W)
    printf "┐${RST}\n"
    blank; blank
    bline "printf '${AMBER}'; pad '↑'; printf '${RST}'"
    blank
    bline "printf '${WHITE}${BOLD}'; pad 'Drop .xlsx here'; printf '${RST}'"
    blank
    bline "printf '${DIM}${LGRAY}'; pad 'drag IB Sketch from Finder into terminal'; printf '${RST}'"
    bline "printf '${DIM}${GRAY}'; pad 'then press Enter'; printf '${RST}'"
    blank; blank
    printf "  ${BORDER}└"
    printf '─%.0s' $(seq 1 $W)
    printf "┘${RST}\n"
    echo ""
    printf "  ${DIM}${LGRAY}Source sheet:${RST}\n"
    printf "  ${AMBER}https://docs.google.com/.../IB-Sketch${RST}\n"
    printf "  ${DIM}${GRAY}File → Download → Microsoft Excel (.xlsx)${RST}\n"
    echo ""
    printf "  ${AMBER}→${RST} "
    read -r _INPUT
    ;;

  success)
    printf '\033[2J\033[H'
    echo ""
    printf "  ${BOLD}${WHITE}IB Burndown${RST}  ${DIM}${LGRAY}Sketch Loader${RST}\n"
    printf "  ${DIM}${GRAY}EVI01 · US-CENTRAL-07A · Elk Grove${RST}\n"
    echo ""
    printf "  ${BORDER}┌"
    printf '─%.0s' $(seq 1 $W)
    printf "┐${RST}\n"
    blank; blank
    bline "printf '${GREEN}${BOLD}'; pad '✓'; printf '${RST}'"
    blank
    bline "printf '${GREEN}${BOLD}'; pad 'EVI01 - IB Sketch.xlsx'; printf '${RST}'"
    blank
    bline "printf '${LGRAY}'; pad '2.4MB → EVI01 - IB Sketch.xlsx'; printf '${RST}'"
    bline "printf '${LGRAY}'; pad 'Launching...'; printf '${RST}'"
    blank; blank
    printf "  ${BORDER}└"
    printf '─%.0s' $(seq 1 $W)
    printf "┘${RST}\n"
    echo ""
    ;;

  search)
    echo ""
    printf "  ${GREEN}File found:${RST} EVI01 - IB Sketch.xlsx\n"
    echo ""
    printf "  ${BOLD}IB Lookup${RST} — ${DIM}EVI01 · US-CENTRAL-07A${RST}\n"
    printf "  ${DIM}Type a switch name to search (q to quit)${RST}\n"
    echo ""
    printf "  ${AMBER}Search →${RST} "
    read -r _INPUT
    echo ""
    printf "  ${BOLD}${WHITE}$_INPUT${RST} — ${GREEN}1 match${RST}\n"
    echo ""
    printf "  ${CYAN}┌─ Connection ──────────────────────────────┐${RST}\n"
    printf "  ${CYAN}│${RST}  Src:  ${BOLD}IBSW-A01${RST} port 17    R0101 U38     ${CYAN}│${RST}\n"
    printf "  ${CYAN}│${RST}  Dst:  ${BOLD}IBSW-L10${RST} port 3     R0205 U40     ${CYAN}│${RST}\n"
    printf "  ${CYAN}│${RST}  Type: ${DIM}HDR100 → HDR100${RST}                  ${CYAN}│${RST}\n"
    printf "  ${CYAN}│${RST}  Len:  ${DIM}30m${RST}                              ${CYAN}│${RST}\n"
    printf "  ${CYAN}└───────────────────────────────────────────┘${RST}\n"
    echo ""
    ;;
esac
