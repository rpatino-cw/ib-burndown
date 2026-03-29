<div align="center">
  <img src="assets/banner.png" alt="ib-lookup" width="600">
  <br><br>
  <b>Search any IB switch at EVI01 from your terminal.</b>
  <br>
  Type a name, get the port, cable, rack, and floor map.
  <br><br>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/rpatino-cw/ib-burndown?style=flat-square" alt="License"></a>
</div>

<br>

## Get started

**3 steps. That's it.**

```bash
git clone https://github.com/rpatino-cw/ib-burndown.git && cd ib-burndown && pip3 install -e .
```

Download the [IB Sketch](https://docs.google.com/spreadsheets/d/1U132alRVDtcrVd5kW4v534U3ME7wRZ5g3kHQMZP2LaM/edit?gid=1992819001#gid=1992819001) (File > Download > .xlsx) and drop it in the folder.

```bash
ib-lookup
```

> Also works with `python3 ib_burndown.py` if you skip the install.

<br>

## Search

<img src="assets/demo-search.gif" alt="Search for a switch" width="600">

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

---

Fork, PR, no xlsx files (internal data). [MIT](LICENSE)
