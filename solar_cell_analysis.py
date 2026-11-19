"""
Organic Solar Cell Analysis, version 2
I-V curve, maximum power point, fill factor, efficiency, Rs and Rsh.

Usage:
    python solar_cell_analysis.py                    # uses organic_solar_cell_data.csv
    python solar_cell_analysis.py a.csv b.csv        # several cells, adds a comparison
    python solar_cell_analysis.py a.csv --area 0.09 --pin 100 --unit A --flip

Options:
    --area   active area in cm2 (default 1)
    --pin    light intensity in mW/cm2 (default 100, AM1.5G)
    --unit   current unit in your file: mA, A or uA (default mA)
    --flip   use this if your photocurrent is negative
    --out    output folder (default: results)

NOTE: organic_solar_cell_data.csv is ILLUSTRATIVE sample data, not a real device.
Needs: numpy, pandas, matplotlib
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

UNIT = {"mA": 1.0, "A": 1000.0, "uA": 0.001}
KEYS = ["Isc (mA)", "Voc (V)", "Vmp (V)", "Imp (mA)", "Pmax (mW)",
        "Fill factor (%)", "Jsc (mA/cm2)", "PCE (%) [assumed area & intensity]",
        "Rs (ohm)", "Rsh (ohm)"]


def read_cell(path, unit="mA", flip=False):
    """Read a CSV, find the voltage and current columns, return a sorted table."""
    df = pd.read_csv(path, sep=None, engine="python")
    low = {c: str(c).lower() for c in df.columns}
    vc = next((c for c, l in low.items() if "volt" in l or l.split("_")[0] == "v"), None)
    ic = next((c for c, l in low.items() if "curr" in l or l.split("_")[0] in ("i", "j")), None)
    if vc is None or ic is None:
        num = df.select_dtypes("number").columns.tolist()
        if len(num) < 2:
            raise ValueError(f"{path}: could not find voltage and current columns")
        vc, ic = num[-2], num[-1]
    out = pd.DataFrame({"Voltage_V": df[vc],
                        "Current_mA": df[ic] * UNIT[unit] * (-1 if flip else 1)})
    out = out.dropna().sort_values("Voltage_V").reset_index(drop=True)
    if len(out) < 3:
        raise ValueError(f"{path}: need at least 3 data points")
    out["Power_mW"] = out["Voltage_V"] * out["Current_mA"]
    return out


def analyze(df, area=1.0, pin=100.0):
    V, I, P = (df[c].to_numpy() for c in ("Voltage_V", "Current_mA", "Power_mW"))
    k = int(np.argmax(P))
    Vmp, Imp, Pmax = V[k], I[k], P[k]
    notes = []

    # Isc: join the two points around 0 V, else use the closest point
    Isc, isc_ok = I[np.argmin(np.abs(V))], False
    for j in range(len(V) - 1):
        if V[j] <= 0 <= V[j + 1] and V[j + 1] != V[j]:
            Isc, isc_ok = float(np.interp(0, V[j:j + 2], I[j:j + 2])), True
            break
    # Voc: join the two points around 0 mA (highest crossing), else closest point
    Voc, voc_ok = V[np.argmin(np.abs(I))], False
    for j in range(len(V) - 2, -1, -1):
        if I[j] >= 0 >= I[j + 1] and I[j] != I[j + 1]:
            Voc, voc_ok = float(np.interp(0, [I[j + 1], I[j]], [V[j + 1], V[j]])), True
            break
    if not isc_ok:
        notes.append("Data does not cross 0 V: Isc taken from the closest point.")
    if not voc_ok:
        notes.append("Data does not cross 0 mA: Voc taken from the closest point.")

    FF = Pmax / (Voc * Isc) * 100 if Voc * Isc > 0 else np.nan
    PCE = Pmax / (pin * area) * 100 if pin * area > 0 else np.nan
    Jsc = Isc / area if area > 0 else np.nan

    # Rs and Rsh: slope of the last 3 and first 3 points (rough estimates)
    s_hi = np.polyfit(V[-3:], I[-3:], 1)[0]
    s_lo = np.polyfit(V[:3], I[:3], 1)[0]
    Rs = -1000 / s_hi if s_hi < 0 else np.nan
    Rsh = -1000 / s_lo if s_lo < 0 else np.nan
    notes.append("Rs and Rsh are rough estimates. They need smooth, real data.")

    rises = int(np.sum(np.diff(I) > 0.02 * np.max(np.abs(I))))
    if rises:
        notes.append(f"Current goes up with voltage at {rises} point(s). "
                     "A real I-V curve normally falls steadily. Check your data.")

    vals = [Isc, Voc, Vmp, Imp, Pmax, FF, Jsc, PCE, Rs, Rsh]
    return dict(zip(KEYS, map(float, vals))), notes


def make_plots(df, res, name, outdir):
    V, I, P = (df[c].to_numpy() for c in ("Voltage_V", "Current_mA", "Power_mW"))
    Vmp, Imp, Pmax = res["Vmp (V)"], res["Imp (mA)"], res["Pmax (mW)"]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(V, I, "o-", color="tab:blue", label="I-V curve")
    ax.plot(Vmp, Imp, "r*", markersize=15, label=f"MPP ({Vmp:.2f} V, {Imp:.2f} mA)")
    ax.set(xlabel="Voltage (V)", ylabel="Current (mA)", title=f"I-V curve: {name}")
    ax.grid(True, alpha=0.4); ax.legend()
    fig.tight_layout(); fig.savefig(outdir / f"{name}_iv_curve.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(V, P, "s--", color="tab:green", label="P-V curve")
    ax.plot(Vmp, Pmax, "r*", markersize=15, label=f"Pmax = {Pmax:.3f} mW")
    ax.set(xlabel="Voltage (V)", ylabel="Power (mW)", title=f"Power-voltage curve: {name}")
    ax.grid(True, alpha=0.4); ax.legend()
    fig.tight_layout(); fig.savefig(outdir / f"{name}_pv_curve.png", dpi=200); plt.close(fig)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(V, I, "o-", color="tab:blue", label="Current")
    ax1.set_xlabel("Voltage (V)"); ax1.set_ylabel("Current (mA)", color="tab:blue")
    ax1.grid(True, alpha=0.4)
    ax2 = ax1.twinx()
    ax2.plot(V, P, "s--", color="tab:green", label="Power")
    ax2.set_ylabel("Power (mW)", color="tab:green")
    ax1.axvline(Vmp, color="red", ls=":", label="Vmp")
    ax1.set_title(f"I-V and P-V curves: {name}"); ax1.legend(loc="lower left")
    fig.tight_layout(); fig.savefig(outdir / f"{name}_combined_iv_pv.png", dpi=200); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="Organic solar cell I-V analysis")
    ap.add_argument("files", nargs="*", default=["organic_solar_cell_data.csv"])
    ap.add_argument("--area", type=float, default=1.0)
    ap.add_argument("--pin", type=float, default=100.0)
    ap.add_argument("--unit", choices=UNIT, default="mA")
    ap.add_argument("--flip", action="store_true")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()

    outdir = Path(a.out); outdir.mkdir(exist_ok=True)
    rows, cells = [], []
    for f in a.files:
        name = Path(f).stem
        df = read_cell(f, a.unit, a.flip)
        res, notes = analyze(df, a.area, a.pin)
        print(f"\n== {name} ==")
        for k, v in res.items():
            print(f"{k:38s}: {v:.4f}")
        for n in notes:
            print("Note:", n)
        df.to_csv(outdir / f"{name}_results.csv", index=False)
        pd.Series(res, name="Value").to_csv(outdir / f"{name}_summary.csv")
        make_plots(df, res, name, outdir)
        rows.append({"File": name, **res}); cells.append((name, df))

    pd.DataFrame(rows).to_csv(outdir / "comparison.csv", index=False)
    if len(cells) > 1:
        fig, ax = plt.subplots(figsize=(8, 5))
        for name, df in cells:
            ax.plot(df["Voltage_V"], df["Current_mA"], "o-", label=name)
        ax.set(xlabel="Voltage (V)", ylabel="Current (mA)", title="I-V curves of all cells")
        ax.grid(True, alpha=0.4); ax.legend()
        fig.tight_layout(); fig.savefig(outdir / "all_cells_iv.png", dpi=200); plt.close(fig)
    print(f"\nSaved everything in the '{outdir}' folder.")


if __name__ == "__main__":
    main()
