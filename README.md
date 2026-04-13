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

## What you need

| File | What it is | Where to find it | Required? |
|------|-----------|-------------------|-----------|
| **IB Sketch** (`.xlsx`) | InfiniBand connection list — pull schedules, elevations, port mappings | Your site's shared Google Drive. Ask your site lead or DCT team. Download as **File > Download > Microsoft Excel (.xlsx)** | Yes |
| **Overhead** (`.csv`) | Physical rack layout — rack numbers, positions, data hall structure | Your site's shared Google Drive. Same place as the IB Sketch — it's the floor plan view. Download as **File > Download > CSV** | Only for floor maps |

> **Note:** The IB Sketch and Overhead are two different sheets. They look similar — both have rack numbers and switch names — but they serve different purposes. The IB Sketch has **IB fabric connections** (source/destination/port/cable). The Overhead has the **physical rack layout** (which rack sits where on the floor). The Overhead is also used for traditional networking connections, not just IB.

<br>

## Quick start (3 steps)

### 1. Install

```bash
pip install git+https://github.com/rpatino-cw/ib-burndown.git@experimental/v2-merge
```

Or clone and run directly:

```bash
git clone -b experimental/v2-merge https://github.com/rpatino-cw/ib-burndown.git
cd ib-burndown && bash run.sh
```

### 2. Add your site's IB Sketch

Download your site's IB Sketch as `.xlsx` from Google Sheets:

1. Open your site's IB Sketch in Google Sheets
2. **File > Download > Microsoft Excel (.xlsx)**
3. Move the file into the `ib-burndown/` folder (or anywhere — you can point to it with `--file`)

The file needs **Pull Schedule** tabs (connections) and **ELEV** tabs (rack positions). Most IB Sketches already have these.

### 3. Run

```bash
ib-lookup
```

That's it. The app reads your `.xlsx`, auto-detects the site name, data halls, and all connections. Search works immediately — type any switch name.

<br>

## Set up floor maps (optional but recommended)

Search, elevations, and port diagrams work out of the box. **Floor maps** need one extra step — your site's rack layout.

### Option A: Import from overhead CSV (recommended)

If your site has an overhead document (the spreadsheet with the physical rack layout), export it as CSV and run:

```bash
ib-lookup --import-overhead your-site-overhead.csv
```

The parser auto-detects:
- Rack number rows and column groupings
- Serpentine vs linear rack ordering
- Data hall boundaries (DH1, DH2, etc.)
- Multi-column layouts (Left/Right splits)

It writes the result to `~/.datahall/layouts.json`. No questions, no manual input.

**Where to get the overhead CSV:**
- Google Sheets: open the overhead > **File > Download > CSV**
- Ask your site lead or DCT team — most sites have one in the shared drive

### Option B: Manual config (if no overhead exists)

Create `~/.datahall/layouts.json` with your hall dimensions:

```json
{
  "YOUR-SITE.DH1": {
    "racks_per_row": 10,
    "columns": [
      {"label": "Left",  "start": 1,   "num_rows": 14},
      {"label": "Right", "start": 141, "num_rows": 17}
    ],
    "serpentine": true
  }
}
```

You need three numbers per column: **start rack**, **number of rows**, and **racks per row**. Ask anyone who knows the hall layout.

### Verify it works

After either option, run `ib-lookup`, search a switch, and press `m` for the floor map.

<br>

## Usage

```
ib-lookup                           # interactive search
ib-lookup S5.3.1                    # one-shot search
ib-lookup "C1.15 20/2"              # search + port filter
ib-lookup --file path/to/sketch.xlsx  # specify xlsx location
ib-lookup --import-overhead site.csv  # import floor layout from CSV
```

**Inside a search result, press:**

| Key | What it shows |
|-----|--------------|
| `m` | Floor map with highlighted racks |
| `e` | Rack elevation (RU positions) |
| `v` | Port faceplate diagram |
| `t` | DCT troubleshooting steps |
| `Enter` | Back to search |

<br>

## Floor map — `m`

<img src="assets/mode-map.png" alt="Floor map" width="600">

<br>

## Rack elevation — `e`

<img src="assets/mode-elevation.png" alt="Rack elevation" width="600">

<br>

## Port diagram — `v`

<img src="assets/demo-search.gif" alt="Search and port diagram" width="600">

<br>

## Troubleshooting — `t`

<img src="assets/mode-tips.png" alt="Troubleshooting tips" width="600">

<br>

## How it works

The app has zero hardcoded site references. Everything is detected from your data:

| What | How it's detected |
|------|------------------|
| Site name | Sheet names, fabric IDs in the Excel |
| Data halls | Tab names containing DH1, DH2, etc. |
| Connections | Any tab with "Pull Schedule" in the name |
| Elevations | Any tab with "ELEV" in the name + Leaf Pull Schedule tabs |
| Rack layouts | Imported from overhead CSV or `~/.datahall/layouts.json` |

<br>

---

Fork, PR, no xlsx files (internal data). [MIT](LICENSE)
