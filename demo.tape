# IB Burndown — Setup Tutorial
# Run: vhs demo.tape
# Output: assets/setup-tutorial.gif

Output assets/setup-tutorial.gif

Require echo

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 600
Set Padding 20
Set Theme { "name": "EVI01", "black": "#0c0d10", "red": "#c0392b", "green": "#3a8f68", "yellow": "#e07a2f", "blue": "#2563eb", "magenta": "#7c3aed", "cyan": "#0891b2", "white": "#e8e6e1", "brightBlack": "#5c5b57", "brightRed": "#e74c3c", "brightGreen": "#4ade80", "brightYellow": "#fbbf24", "brightBlue": "#60a5fa", "brightMagenta": "#a78bfa", "brightCyan": "#22d3ee", "brightWhite": "#f5f5f4", "background": "#0c0d10", "foreground": "#e8e6e1", "selection": "#2a2b35", "cursor": "#e07a2f" }
Set TypingSpeed 50ms
Set CursorBlink false

# ── Step 1: Clone + install ──
Sleep 1s
Type "# Step 1: Clone and install"
Enter
Sleep 500ms
Type "git clone https://github.com/rpatino-cw/ib-burndown.git && cd ib-burndown && pip3 install -e ."
Enter
Sleep 4s

# ── Step 2: Just run it — drop zone appears automatically ──
Sleep 500ms
Type "# Step 2: Run it (drop zone appears if xlsx is missing)"
Enter
Sleep 500ms
Type "ib-lookup"
Enter
Sleep 3s

# Simulate dragging the xlsx file from Finder
Type "/Users/you/Downloads/EVI01 - IB Sketch.xlsx"
Enter
Sleep 3s

# Now searching — type a query
Type "ibsw-a01"
Enter
Sleep 3s

Sleep 2s
