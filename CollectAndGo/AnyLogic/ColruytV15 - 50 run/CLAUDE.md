# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

AnyLogic simulation outputs and analysis scripts for a KU Leuven Multi-Agent Systems paper. The AnyLogic model (`ColruytV15.1_IDE.alp`) simulates robot delivery agents in a Colruyt supermarket under three routing modes (SSP, EV, EA) across varying robot counts and pedestrian crowdedness levels.

## Regenerating figures

```bash
cd "<...>/ColruytV15 - 50 run"
python3 make_figures.py
```

Reads all `summary_*.csv` files in this directory, writes `dashboard_v15_built.csv`, and outputs six paper figures to `./figs/` as both PDF and SVG.

Dependencies: `numpy`, `pandas`, `matplotlib`.

## Data layout

| File pattern | Granularity | Key columns |
|---|---|---|
| `summary_<ts>.csv` | One row per phase per run | `runId`, `phase`, `modeName`, `numRobots`, `crowdednessLevel`, `randomSeed`, `makespan`, `totalDeliveries`, `avg/min/maxTaskSec` |
| `detail_<ts>.csv` | One row per robot task | `robotId`, `taskSeq`, `pickupNode`, `destNode`, `toPickupSec`, `deliveryLegSec`, `returnSec` |
| `events_<ts>.csv` | One row per simulation event | `simTime`, `robotId`, `eventType`, `taskSeq`, `detail` |
| `dashboard_v15_built.csv` | Concatenated summary (7500 rows) | Same columns as summary, reordered by `make_figures.py` |

## Experiment design

- **50 seeds** × **5 crowdedness levels** (c=1–5) × **10 robot counts** (1–10) × **3 routing modes** = 1500 runs, 7500 phase rows total.
- Each run has 3 phases: `phase=0` (SSP), `phase=1` (EV), `phase=2` (EA). All three phases share the same seed, robot count, and crowdedness level.

## Routing modes

- **SSP** (`effectiveMode=0`): shortest-path baseline, no congestion awareness.
- **EV** (`effectiveMode=1`): routes on a static congestion-weighted graph (`dist × (1 + 0.5·w_i)`); no robot-density term.
- **EA** (`effectiveMode=2`): EV routing plus a proximity penalty that steers robots away from delivery targets already claimed by teammates.

## Robot speed model

Speed at a node depends on the static node weight `w_i` and the live pedestrian count `p_i(t)` within a 30 px radius of that node. The pedestrian count is recomputed each time a robot starts approaching a new node. Two robots approaching the same node do not directly slow each other; interaction only occurs through shared task allocation and the EA proximity penalty.

## Figures produced

| File stem | Content |
|---|---|
| `makespan_vs_robots_by_crowd` | 5-panel makespan vs. robot count (independent y-axes) |
| `makespan_vs_robots_shared_y` | Same, shared y-axis |
| `makespan_vs_robots_log_y` | Same, log y-axis |
| `relative_gain_heatmap` | (EV−SSP)/SSP and (EA−SSP)/SSP heatmaps (%) |
| `per_task_singlebot` | Avg task duration vs. crowdedness, 1 robot |
| `per_task_tenbots` | Avg task duration vs. crowdedness, 10 robots |

## Assets

- `3d/person.dae`, `bicycle.dae`, `tractor_3.dae` — 3D Collada models used in the AnyLogic scene.
- `figs/` — rendered paper figures (committed outputs).
