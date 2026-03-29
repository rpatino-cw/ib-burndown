<div align="center">
  <img src="assets/banner.png" alt="ib-burndown" width="600">

  <br>

  **For you CLI lovers who'd rather grep a switch than open a spreadsheet.**

  Search any InfiniBand connection at EVI01. Type a switch name, get the port, cable, rack, RU, and a floor map. All from your terminal.

  [![License](https://img.shields.io/github/license/rpatino-cw/ib-burndown?style=flat-square)](LICENSE)
  [![Issues](https://img.shields.io/github/issues/rpatino-cw/ib-burndown?style=flat-square)](https://github.com/rpatino-cw/ib-burndown/issues)
</div>

---

## Install

```bash
git clone https://github.com/rpatino-cw/ib-burndown.git
cd ib-burndown
pip3 install -r requirements.txt
```

Then drop the IB Sketch in the folder (get from IB shared drive or ask Romeo):

- `EVI01 - IB Sketch.xlsx`

---

## Use it

```bash
python3 ib_burndown.py
```

Type a switch name and hit enter. That's it.

<img src="assets/demo-search.gif" alt="Searching for a switch connection" width="600">

Non-interactive mode for scripting:

```
python3 ib_burndown.py "L10"
python3 ib_burndown.py "S5.3.1 20/2"
python3 ib_burndown.py "C1.15"
```

---

## Four modes

### Search &mdash; *"L10"*

Type any switch name, port, or fabric ID. Results show source, destination, tier, and port in one line. Pick a number for the detail view with cable metadata, rack location, and RU position.

### Floor Map &mdash; *"[m] where is it?"*

Press `m` from the detail view. Get an ASCII floor map with both racks highlighted -- `@` for source, `#` for destination. Cross-hall connections render maps for both DH1 and DH2.

<img src="assets/mode-map.png" alt="Floor map mode" width="600">

### Rack Elevation &mdash; *"[e] which RU?"*

Press `e` to see the full rack with every switch and its RU position. Highlighted switches get a `◄` marker so you know exactly where to look.

<img src="assets/mode-elevation.png" alt="Rack elevation mode" width="600">

### Troubleshooting &mdash; *"[t] what do I check?"*

Press `t` for step-by-step DCT troubleshooting. Context-aware -- it knows the cable type, optic, port numbers, and rack locations, so the steps are specific to the connection you're looking at.

<img src="assets/mode-tips.png" alt="Troubleshooting tips" width="600">

---

## Contributing

Fork, PR, no connection data (the Excel files are internal). Keep it simple.

[MIT](LICENSE)
