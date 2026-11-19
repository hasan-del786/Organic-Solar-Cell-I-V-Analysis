# Organic Solar Cell I-V Analysis

Reads voltage and current from an organic solar cell and calculates how well it turns light into electricity.

## What it gives you
- Isc, Voc, Vmp, Imp, Pmax
- Fill factor and efficiency (PCE)
- Series resistance (Rs) and shunt resistance (Rsh), as rough estimates
- I-V, P-V and combined charts
- A comparison table when you analyze several cells

## Two ways to use it
**1. Web page** (`solar-iv-analyzer.html`): open it in a browser, upload one or more CSV files, download the results. Nothing is uploaded to a server. Works on any static host, including InfinityFree.

**2. Python script** (`solar_cell_analysis.py`):
```
pip install numpy pandas matplotlib
python solar_cell_analysis.py organic_solar_cell_data.csv
python solar_cell_analysis.py cell_a.csv cell_b.csv --area 0.09
```
Results are saved in the `results` folder.

## CSV format
```
Voltage_V,Current_mA
0.00,8.0
0.30,6.6
0.60,0.0
```

## Formulas
- P = V x I
- Isc and Voc: join the two points around 0 V and 0 mA (closest point if the data does not cross them)
- FF = Pmax / (Voc x Isc)
- PCE = Pmax / (light intensity x area)
- Rs and Rsh: slope of the last 3 and first 3 points

## Limits
- The sample data is made up, not from a real device.
- Rs and Rsh need smooth, real data. Curve fitting is not included yet.
- Results are only as good as the input data.

## Folder
```
organic_solar_project/
  README.md                       this guide
  requirements.txt                Python packages
  solar_cell_analysis.py          Python analysis script
  solar-iv-analyzer.html          web tool (open in a browser or upload to your host)
  organic_solar_cell_data.csv     sample input data (illustrative, not a real device)
  results/                        results made from the sample data
```
