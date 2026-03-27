# IB Lookup — EVI01

Search any InfiniBand switch connection at US-CENTRAL-07A.

## Setup (one time)

```bash
git clone https://github.com/rpatino-cw/ib-burndown.git
cd ib-burndown
pip3 install -r requirements.txt
```

Then drop these 2 files in the folder (get from IB shared drive or ask Romeo):
- `DH1 & DH2 All_IB_Connections_Simplified_v2.xlsx`
- `EVI01 - IB Sketch.xlsx`

## Run

```bash
python3 ib_burndown.py
```

That's it. Type a switch name and hit enter.
