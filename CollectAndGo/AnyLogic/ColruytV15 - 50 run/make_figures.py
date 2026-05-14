#!/usr/bin/env python3
"""
make_figures.py - regenerate figures directly from the AnyLogic V15
mode-5 sweep outputs (50 summary_*.csv files in this folder).

Place this script in the V15 sweep folder, next to the summary_*.csv
files.  It reads them, writes a combined dashboard CSV here, and
renders the six paper figures to ./figs/ (created next to this script).

Pipeline
--------
  Stage 1.  Read every summary_<timestamp>.csv in the script's own
            folder and concatenate the per-phase rows into one
            DataFrame (7500 rows = 50 seeds x 5 crowd levels x 10
            robot counts x 3 routing modes).  Also writes
            dashboard_v15_built.csv here for ad-hoc analysis.

  Stage 2.  Write the six figures used in the paper to ./figs/ as
            both PDF (for LaTeX inclusion) and SVG (for HTML / slide
            reuse).

Usage
-----
  cd "<...>/ColruytV15 - 50 run"
  python3 make_figures.py
"""
from pathlib import Path
import csv
import glob
import sys

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# All paths are resolved relative to this script's location.
HERE = Path(__file__).resolve().parent
COMBINED_CSV = HERE / "dashboard_v15_built.csv"
OUT = HERE / "figs"
OUT.mkdir(exist_ok=True)

DASH_COLS = [
    "runId", "numRobots", "phase", "effectiveMode", "modeName",
    "makespan", "totalDeliveries", "avgTaskSec", "minTaskSec",
    "maxTaskSec", "avgToPickupSec", "avgDeliveryLegSec", "avgReturnSec",
    "numOrders", "crowdednessLevel", "randomSeed",
]


def build_dataframe():
    files = sorted(glob.glob(str(HERE / "summary_*.csv")))
    if not files:
        sys.exit(f"No summary_*.csv files found in {HERE}")
    print(f"Stage 1: combining {len(files)} summary_*.csv files...")
    rows = []
    with open(COMBINED_CSV, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(DASH_COLS)
        for path in files:
            with open(path) as fh:
                for r in csv.reader(fh):
                    if not r or r[0].startswith("#") or r[0] == "runId":
                        continue
                    try:
                        int(r[7])
                    except (ValueError, IndexError):
                        continue
                    reordered = [r[0], r[4], r[1], r[2], r[3], r[8], r[9],
                                 r[10], r[11], r[12], r[13], r[14], r[15],
                                 r[5], r[6], r[7]]
                    w.writerow(reordered)
                    rows.append(reordered)
    df = pd.DataFrame(rows, columns=DASH_COLS)
    for c in ("numRobots", "phase", "effectiveMode", "makespan",
              "totalDeliveries", "avgTaskSec", "minTaskSec", "maxTaskSec",
              "avgToPickupSec", "avgDeliveryLegSec", "avgReturnSec",
              "numOrders", "crowdednessLevel", "randomSeed"):
        df[c] = pd.to_numeric(df[c])
    print(f"         -> {len(df)} phase rows (expected 7500)")
    print(f"         -> combined CSV written to {COMBINED_CSV.name}")
    return df


mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 9,
    "axes.titlesize": 9, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 200, "savefig.dpi": 300,
    "axes.linewidth": 0.8, "grid.linewidth": 0.4, "lines.linewidth": 1.3,
})

COLOR = {"SSP": "#5b6770", "EV": "#2a6f97", "EA": "#c1502e"}
MARKER = {"SSP": "o", "EV": "s", "EA": "D"}


def savefig(fig, stem):
    for ext in ("pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


def panel_makespan(df, sharey, yscale, stem):
    fig, axes = plt.subplots(1, 5, figsize=(7.2, 2.1), sharey=sharey)
    for i, c in enumerate(sorted(df["crowdednessLevel"].unique())):
        ax = axes[i]
        sub = df[df["crowdednessLevel"] == c]
        for m in ("SSP", "EV", "EA"):
            g = (sub[sub["modeName"] == m]
                 .groupby("numRobots")["makespan"]
                 .agg(["mean", "std", "count"]).reset_index())
            se = g["std"] / np.sqrt(g["count"])
            ax.errorbar(g["numRobots"], g["mean"], yerr=1.96 * se,
                        color=COLOR[m], marker=MARKER[m], markersize=3.0,
                        linewidth=1.1, capsize=1.5, label=m)
        ax.set_xticks([1, 3, 5, 7, 10])
        ax.set_xlabel("Robots")
        ax.set_title(f"Crowd $c={c}$", pad=2)
        ax.grid(alpha=0.3)
        ax.set_yscale(yscale)
        if i == 0:
            ax.set_ylabel("Makespan (s)")
            ax.legend(frameon=False, loc="upper right", handlelength=1.2)
    plt.tight_layout(pad=0.4)
    savefig(fig, stem)


def heatmap(df):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    for ax, label in zip(axes, ("EV", "EA")):
        M = np.zeros((5, 10))
        for ci, c in enumerate(sorted(df["crowdednessLevel"].unique())):
            for ri, r in enumerate(sorted(df["numRobots"].unique())):
                sub = df[(df["crowdednessLevel"] == c) & (df["numRobots"] == r)]
                p = sub.pivot_table(index="randomSeed", columns="modeName",
                                    values="makespan")
                M[ci, ri] = ((p[label] - p["SSP"]) / p["SSP"] * 100).mean()
        im = ax.imshow(M, cmap="RdBu_r", vmin=-10, vmax=10,
                       aspect="auto", origin="lower")
        ax.set_xticks(range(10), [str(r) for r in range(1, 11)])
        ax.set_yticks(range(5), [str(c) for c in range(1, 6)])
        ax.set_xlabel("Robots")
        ax.set_ylabel("Crowdedness level $c$")
        ax.set_title(f"{label} - SSP makespan (%)", pad=2)
        for ci in range(5):
            for ri in range(10):
                v = M[ci, ri]
                ax.text(ri, ci, f"{v:+.1f}", ha="center", va="center",
                        fontsize=6,
                        color="black" if abs(v) < 6 else "white")
        plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    plt.tight_layout(pad=0.4)
    savefig(fig, "relative_gain_heatmap")


def per_task(df, robots, stem, title):
    fig, ax = plt.subplots(1, 1, figsize=(3.5, 2.4))
    sub = df[df["numRobots"] == robots]
    for m in ("SSP", "EV", "EA"):
        g = (sub[sub["modeName"] == m]
             .groupby("crowdednessLevel")["avgTaskSec"]
             .agg(["mean", "std", "count"]).reset_index())
        se = g["std"] / np.sqrt(g["count"])
        ax.errorbar(g["crowdednessLevel"], g["mean"], yerr=1.96 * se,
                    color=COLOR[m], marker=MARKER[m], markersize=4,
                    linewidth=1.2, capsize=2, label=m)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xlabel("Crowdedness level $c$")
    ax.set_ylabel("Average task duration (s)")
    ax.set_title(title, pad=2)
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    plt.tight_layout(pad=0.3)
    savefig(fig, stem)


def main():
    df = build_dataframe()
    print(f"Stage 2: rendering figures to {OUT}/ ...")
    panel_makespan(df, sharey=False, yscale="linear",
                   stem="makespan_vs_robots_by_crowd")
    panel_makespan(df, sharey=True, yscale="linear",
                   stem="makespan_vs_robots_shared_y")
    panel_makespan(df, sharey=True, yscale="log",
                   stem="makespan_vs_robots_log_y")
    heatmap(df)
    per_task(df, robots=1, stem="per_task_singlebot",
             title="Single-robot regime (no fleet interaction)")
    per_task(df, robots=10, stem="per_task_tenbots",
             title="Ten-robot regime (full fleet interaction)")
    n_pdf = len(list(OUT.glob("*.pdf")))
    n_svg = len(list(OUT.glob("*.svg")))
    print(f"         -> {n_pdf} PDFs and {n_svg} SVGs")


if __name__ == "__main__":
    main()
