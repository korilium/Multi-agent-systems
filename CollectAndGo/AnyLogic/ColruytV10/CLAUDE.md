# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAPD-EA — Multi-Agent Pickup and Delivery with External Agents. An AnyLogic 8.9.8 simulation modelling autonomous grocery delivery robots navigating a crowded urban environment inspired by Colruyt's Leuven pilot. The single project file is [ColruytV5.0_IDE.alp](ColruytV5.0_IDE.alp) (XML, AnyLogic 8.9.x format, Java package `colruytv2`). All logic lives inside that file as `<![CDATA[...]]>` Java blocks — there are no separate `.java` source files.

**Research goal:** Compare three routing strategies (SSP, EV, EA) on makespan under varying pedestrian density. Each simulation run executes all three phases sequentially within one session.

## Running the Model

Open `ColruytV5.0_IDE.alp` in **AnyLogic 8.9.x** (Personal Learning Edition or higher). Press Run. There is no build/compile step — the IDE compiles embedded Java on run.

Batch experiments (parameter variation runs) are configured inside AnyLogic via the Experiments panel.

## Architecture

### Agent Classes (inside the `.alp` XML)

| Class | Role |
|---|---|
| `Main` | Environment root: builds the road graph, spawns pedestrians and robots, owns the global order list, manages CSV logging |
| `Robot` | Delivery agent with a statechart (Init → GoToPickup → Deliver → Return → NextTask) |
| `Pedestrian` | External agent (non-cooperative); moves through the space creating congestion |
| `NodeLoc` (Java class) | Graph node: holds `(x, y)`, a crowdedness weight, an adjacency `edges` list, and `nodeIndex` |

### Road Graph

75 `NodeLoc` nodes on a circular city-centre layout. Built in `Main.StartupCode`:
1. Coordinates read from AnyLogic Point Markup objects (`node1`–`node75`).
2. Edges added between nodes within `maxEdgeDist=100` px, filtered for wall intersection using 12 `Wall` objects.
3. Per-node `crowdedness` values (1–8) set manually, reflecting ring-road vs. cross-road vs. outer-ring zones.

### Routing Strategies (`routingMode` / `phase` column 0–2)

| Value | Name | Path algorithm | Task selection |
|---|---|---|---|
| `0` | SSP | Standard Dijkstra (distance only) | Greedy nearest pickup |
| `1` | EV | Crowd-weighted Dijkstra (`cost = dist × (1 + crowdedness × 0.5)`) | Greedy nearest pickup |
| `2` | EA | Crowd-weighted Dijkstra | Lookahead scoring + graduated inter-robot conflict penalty |
| `3` | COMPARE | Runs SSP → EV → EA sequentially on identical orders | — |
| `4` | AUTO | Sweeps `numRobots` 1→10, running SSP→EV→EA at each count | — |

Mode 3 runs all three phases in one session; the `phase` column (0/1/2) identifies which. Mode 4 additionally sweeps robot counts automatically — `numRobots` slider is overridden and the full 30-phase result (10 counts × 3 modes) accumulates into `dashboard_performance.csv`.

`calculatePath(start, end, mode)` in `Robot` runs Dijkstra. Robot speed per segment: `10 / (1 + crowdedness × 0.3)`.

### Task Assignment

- `Main.initEnvironment()` generates `numOrders` pickup→delivery pairs stored in `Main.orderList`.
- `Robot.buildLocalOrderList()` copies and sorts the global list by Dijkstra distance from current position.
- `Robot.selectNextTask()` applies mode-specific scoring, then broadcasts a claim via `removeClaimedTask()`. `Main.claimedOrders` (`HashSet<String>`) prevents double-claiming.
- EA mode penalises tasks whose delivery node is within `conflictRadiusThreshold` px of another robot's current destination, weighted by `conflictPenaltyWeight`.

### Key Parameters

| Parameter | Default | Range | Effect |
|---|---|---|---|
| `routingMode` | 0 | 0–2 | Active routing strategy (overridden sequentially per phase) |
| `crowdednessLevel` | 3 | 1–5 | Scales pedestrian arrival rate |
| `numRobots` | 2 | 1–10 | Number of active delivery robots |
| `numOrders` | 10 | 1–1000 | Delivery tasks per run |
| `conflictRadiusThreshold` | 40 | — | EA: radius for conflict detection (px) |
| `conflictPenaltyWeight` | 30 | — | EA: penalty magnitude |
| `randomSeed` | 5 | — | RNG seed for reproducibility |

### CSV Output (three files per run, named `*_<timestamp>.csv`)

**`detail_*.csv`** — one row per completed task delivery:
```
runId, phase, effectiveMode, modeName, robotId, taskSeq,
pickupNode, destNode, taskStartSim, toPickupSec, deliveryLegSec,
returnSec, totalSec, expOutSec, expInSec,
hopsToStore, hopsToDest, hopsReturn,
crowdednessLevel, numRobots, numOrders, randomSeed
```

**`summary_*.csv`** — one row per phase, written when all tasks complete:
```
runId, phase, effectiveMode, modeName, numRobots, numOrders,
crowdednessLevel, randomSeed, makespan, totalDeliveries,
avgTaskSec, minTaskSec, maxTaskSec, avgToPickupSec,
avgDeliveryLegSec, avgReturnSec,
robot0Tasks … robot3Tasks, robot0TotalSec … robot3TotalSec
```

**`dashboard_performance.csv`** — cross-run accumulation file for charting (opened in **append** mode, no timestamp). One row per phase per run:
```
runId, numRobots, phase, effectiveMode, modeName, makespan, totalDeliveries,
avgTaskSec, minTaskSec, maxTaskSec, avgToPickupSec, avgDeliveryLegSec, avgReturnSec,
numOrders, crowdednessLevel, randomSeed
```
Use routingMode=4 (AUTO) to fill this file automatically in a single run (30 rows: 10 robot counts × 3 modes). Alternatively, run multiple times with routingMode=3 at different robot counts — rows append.

**`events_*.csv`** — fine-grained event log per robot action:
```
runId, phase, effectiveMode, modeName, simTime, robotId,
eventType, pickupNode, destNode, taskSeq, detail
```
Event types include `TASK_CLAIMED`, `DEPART_TO_PICKUP`, `ARRIVED_PICKUP`, `DEPART_TO_DEST`, `ARRIVED_DEST`, `RETURN_STARTED`, `RETURN_COMPLETE`.

CSV helpers in `Main`: `openCsv()`, `writeCsvRow()`, `writeMakespanRow()`, `writeEventRow()`, `closeCsv()`. File opened at simulation start, closed in `Main.DestroyCode`.

## Editing Conventions

All logic is in the `.alp` XML:
- **Robot statechart actions** → `<StatechartElement>` nodes under the `Robot` `<ActiveObjectClass>`.
- **Main utility functions** → `<Function>` elements in the `Main` class.
- **`NodeLoc`** → standalone `<JavaClass>` near the bottom of the file — edit it there, not inline.

Model time unit: **seconds**. Distance scale: 50 px = 10 m.

### 3D Assets (`3d/`)
`tractor_3.dae` (robot), `person.dae` (pedestrian), `bicycle.dae`.
