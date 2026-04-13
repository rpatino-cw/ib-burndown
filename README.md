<div align="center">
  <img src="assets/banner.png" alt="ib-lookup" width="600">
  <br><br>
  <b>Search any IB switch at any site from your terminal.</b>
  <br>
  Drop in your IB Sketch, get ports, cables, racks, elevations, and floor maps.
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/rpatino-cw/ib-burndown?style=flat-square" alt="License"></a>
</div>

<br>

## Get started

```bash
pip install git+https://github.com/rpatino-cw/ib-burndown.git
```

Or clone and run directly:

```bash
git clone https://github.com/rpatino-cw/ib-burndown.git && cd ib-burndown && bash run.sh
```

Place your site's IB Sketch `.xlsx` in the directory and run `ib-lookup`. It auto-detects the site, data halls, and connections.

<br>

## Set up floor maps

Floor maps need your site's rack layout. Import it from an overhead CSV:

```bash
ib-lookup --import-overhead your-overhead.csv
```

This parses the CSV, detects rack columns, serpentine patterns, and data halls, then saves the layout to `~/.datahall/layouts.json`. No questions asked — fully automatic.

<br>

## Search

<img src="assets/demo-search.gif" alt="Search for a switch" width="600">

```
ib-lookup                    # interactive mode
ib-lookup S5.3.1             # one-shot search
ib-lookup "C1.15 20/2"       # search with port filter
ib-lookup --file sketch.xlsx # specify file
```

<br>

## Floor map — `m`

<img src="assets/mode-map.png" alt="Floor map" width="600">

<br>

## Rack elevation — `e`

<img src="assets/mode-elevation.png" alt="Rack elevation" width="600">

<br>

## Troubleshooting — `t`

<img src="assets/mode-tips.png" alt="Troubleshooting tips" width="600">

<br>

## Works at any site

v2 has zero hardcoded site references. It reads whatever your Excel gives it:

- **Site name** — detected from sheet names and fabric IDs
- **Data halls** — detected from tab names (DH1, DH2, DH3, ...)
- **Rack layouts** — imported from overhead CSV or inferred from elevation data
- **Connections** — parsed from any Pull Schedule tabs
- **Elevations** — parsed from any ELEV tabs

<br>

---

Fork, PR, no xlsx files (internal data). [MIT](LICENSE)
