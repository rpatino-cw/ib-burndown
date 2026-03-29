#!/bin/bash
# Full simulated demo for VHS recording — one continuous script
printf '\033[2J\033[H'

RST='\033[0m'; DIM='\033[2m'; BOLD='\033[1m'
AMBER='\033[38;5;208m'; GREEN='\033[38;5;108m'
GRAY='\033[38;5;240m'; LGRAY='\033[38;5;245m'
WHITE='\033[38;5;252m'; CYAN='\033[36m'
BORDER='\033[38;5;238m'
PS='~ ❯ '
W=54

pad() { printf "%*s" $(( (W - ${#1}) / 2 )) ""; printf "%s" "$1"; printf "%*s" $(( (W - ${#1} + 1) / 2 )) ""; }
bl() { printf "  ${BORDER}│${RST}"; eval "$@"; printf "${BORDER}│${RST}\n"; }
bk() { bl "printf '%${W}s' ''"; }
top() { printf "  ${BORDER}┌"; printf '─%.0s' $(seq 1 $W); printf "┐${RST}\n"; }
bot() { printf "  ${BORDER}└"; printf '─%.0s' $(seq 1 $W); printf "┘${RST}\n"; }

typeout() {
  printf "${PS}"
  for (( i=0; i<${#1}; i++ )); do
    printf "${1:$i:1}"
    sleep 0.04
  done
  echo ""
}

# ── Step 1: Clone + install ──
echo -e "${DIM}# Step 1 — Clone and install${RST}"
echo ""
typeout "git clone https://github.com/rpatino-cw/ib-burndown.git"
sleep 0.5
echo "Cloning into 'ib-burndown'..."
sleep 1
echo "done."
echo ""

typeout "cd ib-burndown && pip3 install -e ."
sleep 0.5
echo "Processing /Users/you/ib-burndown"
sleep 0.4
echo -e "  Installing build dependencies ... ${GREEN}done${RST}"
sleep 0.4
echo -e "  Building wheel ... ${GREEN}done${RST}"
sleep 0.3
echo -e "Successfully installed ${BOLD}ib-lookup-1.0.0${RST}"
sleep 1.5
echo ""

# ── Step 2: Run — drop zone appears ──
echo -e "${DIM}# Step 2 — Just run it${RST}"
echo ""
typeout "ib-lookup"
sleep 0.8

# Drop zone
printf '\033[2J\033[H'
echo ""
printf "  ${BOLD}${WHITE}IB Burndown${RST}  ${DIM}${LGRAY}Sketch Loader${RST}\n"
printf "  ${DIM}${GRAY}EVI01 · US-CENTRAL-07A · Elk Grove${RST}\n"
echo ""
top; bk; bk
bl "printf '${AMBER}'; pad '↑'; printf '${RST}'"
bk
bl "printf '${WHITE}${BOLD}'; pad 'Drop .xlsx here'; printf '${RST}'"
bk
bl "printf '${DIM}${LGRAY}'; pad 'drag IB Sketch from Finder into terminal'; printf '${RST}'"
bl "printf '${DIM}${GRAY}'; pad 'then press Enter'; printf '${RST}'"
bk; bk; bot
echo ""
printf "  ${DIM}${LGRAY}Source sheet:${RST}\n"
printf "  ${AMBER}https://docs.google.com/.../IB-Sketch${RST}\n"
printf "  ${DIM}${GRAY}File → Download → Microsoft Excel (.xlsx)${RST}\n"
echo ""

# Simulate user dragging file
printf "  ${AMBER}→${RST} "
sleep 1.5
for (( i=0; i<${#1}; i++ )); do printf "${1:$i:1}"; sleep 0.03; done
# Type the path
MSG="/Users/me/Downloads/EVI01 - IB Sketch.xlsx"
for (( i=0; i<${#MSG}; i++ )); do printf "${MSG:$i:1}"; sleep 0.03; done
echo ""
sleep 0.8

# Success screen
printf '\033[2J\033[H'
echo ""
printf "  ${BOLD}${WHITE}IB Burndown${RST}  ${DIM}${LGRAY}Sketch Loader${RST}\n"
printf "  ${DIM}${GRAY}EVI01 · US-CENTRAL-07A · Elk Grove${RST}\n"
echo ""
top; bk; bk
bl "printf '${GREEN}${BOLD}'; pad '✓'; printf '${RST}'"
bk
bl "printf '${GREEN}${BOLD}'; pad 'EVI01 - IB Sketch.xlsx'; printf '${RST}'"
bk
bl "printf '${LGRAY}'; pad '2.4MB → EVI01 - IB Sketch.xlsx'; printf '${RST}'"
bl "printf '${LGRAY}'; pad 'Launching...'; printf '${RST}'"
bk; bk; bot
echo ""
sleep 2

# Search UI
printf '\033[2J\033[H'
echo ""
printf "  ${GREEN}File found:${RST} EVI01 - IB Sketch.xlsx\n"
echo ""
printf "  ${BOLD}IB Lookup${RST} — ${DIM}EVI01 · US-CENTRAL-07A${RST}\n"
printf "  ${DIM}Type a switch name to search (q to quit)${RST}\n"
echo ""
printf "  ${AMBER}Search →${RST} "
sleep 1

# Type a query
QUERY="ibsw-a01"
for (( i=0; i<${#QUERY}; i++ )); do printf "${QUERY:$i:1}"; sleep 0.06; done
sleep 0.5
echo ""
echo ""

# Show result
printf "  ${BOLD}${WHITE}ibsw-a01${RST} — ${GREEN}1 match${RST}\n"
echo ""
printf "  ${CYAN}┌─ Connection ──────────────────────────────────┐${RST}\n"
printf "  ${CYAN}│${RST}  Src:  ${BOLD}IBSW-A01${RST} port 17     R0101 U38       ${CYAN}│${RST}\n"
printf "  ${CYAN}│${RST}  Dst:  ${BOLD}IBSW-L10${RST} port 3      R0205 U40       ${CYAN}│${RST}\n"
printf "  ${CYAN}│${RST}  Type: ${DIM}HDR100 → HDR100${RST}                      ${CYAN}│${RST}\n"
printf "  ${CYAN}│${RST}  Len:  ${DIM}30m${RST}                                  ${CYAN}│${RST}\n"
printf "  ${CYAN}└────────────────────────────────────────────────┘${RST}\n"
echo ""
sleep 3
