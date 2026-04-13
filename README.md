<div align="center">
  <img src="assets/banner.png" alt="ib-lookup" width="600">
  <br><br>
  <b>One tool for all switch lookups — IB and traditional networking.</b>
  <br>
  Drop in your spreadsheet, search any switch, get maps, elevations, ports, and tips.
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/rpatino-cw/ib-burndown?style=flat-square" alt="License"></a>
</div>

<br>

<img src="assets/modes.svg" alt="Two modes: IB and Traditional" width="700">

<br>

## What you need

| File | What it is | Where to find it | Required? |
|------|-----------|-------------------|-----------|
| **IB Sketch** (`.xlsx`) | InfiniBand fabric connections — pull schedules, elevations, port mappings | Your site's shared Google Drive. Ask your site lead or DCT team. | For IB mode |
| **Master Cutsheet / Overhead** (`.xlsx`) | Traditional networking + physical rack layout. Contains SITE-HOSTS (devices), CUTSHEET (connections), and OVERHEAD (floor plan) tabs. | Same shared drive — every site has one. | For trad mode + floor maps |

> **Note:** Two files, two purposes. The **IB Sketch** has IB fabric connections (Spine/Core/Leaf/Node). The **Master Cutsheet / Overhead** has traditional networking (TOR, infra, frontend — swp/eth ports) and the physical rack layout. To get floor maps, export the OVERHEAD tab as CSV and run `--import-overhead`.

<br>

## Quick start

### 1. Install

```bash
pip install git+https://github.com/rpatino-cw/ib-burndown.git@experimental/v2-merge
```

Or clone and run directly:

```bash
git clone -b experimental/v2-merge https://github.com/rpatino-cw/ib-burndown.git
cd ib-burndown && bash run.sh
```

### 2. Add your data

<img src="assets/step-download.svg" alt="Download your IB Sketch from Google Sheets" width="700">

1. Open your site's **IB Sketch** (or **MASTER cutsheet**) in Google Sheets
2. **File > Download > Microsoft Excel (.xlsx)**
3. Move the `.xlsx` into the `ib-burndown/` folder — or point to it with `--file`

### 3. Run

```bash
ib-lookup                # InfiniBand mode (IB Sketch)
ib-lookup --trad         # traditional networking mode (MASTER cutsheet)
```

That's it. The app reads your file, auto-detects the site, data halls, and connections. Search works immediately.

<br>

## Set up floor maps

Search, elevations, and port diagrams work out of the box. **Floor maps** need your site's rack layout — one extra step.

<img src="assets/step-overhead.svg" alt="Import overhead to get floor maps" width="700">

### Option A: Import from MASTER cutsheet (recommended)

Open your MASTER cutsheet in Google Sheets, go to the **OVERHEAD** tab, then **File > Download > CSV**:

```bash
ib-lookup --import-overhead your-site-overhead.csv
```

Auto-detects rack columns, serpentine patterns, data halls, and row counts. Writes to `~/.datahall/layouts.json`. No questions.

### Option B: Manual config

Create `~/.datahall/layouts.json` with 3 numbers per column:

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

After either option, search a switch and press `m` for the floor map.

<br>

## Usage

```
ib-lookup                              # IB interactive search
ib-lookup S5.3.1                       # IB one-shot search
ib-lookup "C1.15 20/2"                 # IB search + port filter
ib-lookup --trad                       # traditional networking search
ib-lookup --trad --file MASTER.xlsx    # trad with specific file
ib-lookup --import-overhead site.csv   # import floor layout
ib-lookup --file path/to/sketch.xlsx   # specify xlsx location
```

**Inside a search result, press:**

| Key | What it shows |
|-----|--------------|
| `m` | Floor map with highlighted racks |
| `e` | Rack elevation (RU positions, full device inventory in trad mode) |
| `v` | Port faceplate diagram (IB mode) |
| `t` | DCT troubleshooting steps |
| `Enter` | Back to search |

<br>

## Floor map — `m`

<img src="assets/mode-map.png" alt="Floor map" width="600">

<br>

## Rack elevation — `e`

<img src="assets/mode-elevation.png" alt="Rack elevation" width="600">

<br>

## Port diagram — `v` (IB mode)

<img src="assets/demo-search.gif" alt="Search and port diagram" width="600">

<br>

## Troubleshooting — `t`

<img src="assets/mode-tips.png" alt="Troubleshooting tips" width="600">

<br>

## How it works

Zero hardcoded site references. Everything is detected from your data:

| What | How it's detected |
|------|------------------|
| Site name | Sheet names, fabric IDs, DNS hostnames |
| Data halls | Tab names (DH1, DH2), location strings (dh2:130:44) |
| IB connections | Any tab with "Pull Schedule" in the name |
| Trad connections | CUTSHEET tab with swp/eth ports |
| Devices | SITE-HOSTS tab with DNS, model, location |
| Elevations | ELEV tabs (IB) or SITE-HOSTS rack inventory (trad) |
| Rack layouts | Imported from overhead CSV or `~/.datahall/layouts.json` |

<br>

---

Works at any site. Fork, PR, no xlsx files (internal data). [MIT](LICENSE)
