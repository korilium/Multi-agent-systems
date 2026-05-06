# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AnyLogic 8.9.8 multi-agent simulation (MAPD-EA — Multi-Agent Pickup and Delivery with External Agents) modelling autonomous grocery delivery robots navigating a crowded urban environment inspired by Colruyt's Leuven pilot. The single project file is [ColruytV5.0_IDE.alp](ColruytV5.0_IDE.alp) (XML format). All logic is embedded in that file; there are no separate Java source files.

**Research context:** The simulation tests three routing strategies to measure makespan under varying pedestrian density. Results are logged to CSV for statistical analysis.

## Running the Model

Open `ColruytV5.0_IDE.alp` in **AnyLogic 8.9.x** (Personal Learning Edition or higher). Press Run. There is no build/compile step outside AnyLogic — the IDE compiles embedded Java code on run.

Batch experiments (parameter variation runs) are configured inside AnyLogic via the Experiments panel.

## Architecture

### Agent Classes (inside the `.alp` XML)

| Class | Role |
|---|---|
| `Main` | Environment root: builds the road graph, spawns pedestrians and robots, owns the global order list, manages CSV logging |
| `Robot` | Delivery agent with a 4-state statechart (Init → GoToPickup → Deliver → Return → NextTask) |
| `Pedestrian` | External agent (non-cooperative); moves through the space creating congestion |
| `NodeLoc` (Java class) | Graph node: holds `(x, y)`, a crowdedness weight, an adjacency `edges` list, and `nodeIndex` |

### Road Graph

75 `NodeLoc` nodes placed on a circular city-centre layout. Built at startup in `Main.StartupCode`:
1. Coordinates read from AnyLogic Point Markup objects (`node1`–`node75`).
2. Edges added between nodes within `maxEdgeDist=100` px, filtered for wall intersection using 12 `Wall` objects.
3. Per-node `crowdedness` values (1–8) set manually, reflecting ring-road vs. cross-road vs. outer-ring zones.

### Routing Strategies (`routingMode` parameter, 0–2)

| Value | Name | Path algorithm | Task selection |
|---|---|---|---|
| `0` | SSP | Standard Dijkstra (distance only) | Greedy nearest pickup |
| `1` | EV | Crowd-weighted Dijkstra (`cost = dist * (1 + crowdedness)`) | Greedy nearest pickup |
| `2` | EA | Crowd-weighted Dijkstra | Lookahead scoring + graduated inter-robot conflict penalty |

`calculatePath(start, end, mode)` in `Robot` runs Dijkstra. `calculateExpectedTime(s, e, mode)` returns estimated travel time (`path_length / 10.0`). Robot speed along each segment is `10 / (1 + crowdedness * 0.3)`.

### Task Assignment

- `Main.initEnvironment()` generates `numOrders` pickup→delivery pairs and stores them in `Main.orderList`.
- Each `Robot.buildLocalOrderList()` copies and sorts the global list by Dijkstra distance from the robot's current position.
- `Robot.selectNextTask()` applies the routing-mode-specific scoring, then broadcasts a claim to peer robots via `removeClaimedTask()`. `Main.claimedOrders` (a `HashSet<String>`) prevents double-claiming.
- EA mode additionally penalises tasks whose delivery node is within `conflictRadiusThreshold` (default 40 px) of another robot's current destination, weighted by `conflictPenaltyWeight` (default 30).

### Key Parameters (set in AnyLogic UI or experiment sweeps)

| Parameter | Default | Range | Effect |
|---|---|---|---|
| `routingMode` | 0 | 0–2 | Routing strategy (SSP/EV/EA) |
| `crowdednessLevel` | 3 | 1–5 | Scales pedestrian arrival rate |
| `numRobots` | 2 | 1–4 | Number of active delivery robots |
| `numOrders` | 6 | 1–20 | Delivery tasks per run |
| `conflictRadiusThreshold` | 40 | — | EA: radius for conflict detection |
| `conflictPenaltyWeight` | 30 | — | EA: penalty magnitude |
| `randomSeed` | 5 | — | RNG seed for reproducibility |

### CSV Output

`openCsv()` / `writeCsvRow()` / `writeMakespanRow()` / `closeCsv()` in `Main` write two kinds of rows:

- **Per-task row:** `runId, robotId, taskId, routingMode, numRobots, numOrders, pickupNode, destNode, taskStartTime, deliveryTime, returnTime, totalTime, expOutTime, expInTime`
- **Makespan row:** `runId, routingMode, numRobots, numOrders, crowdednessLevel, makespan`

The file is opened at simulation start and closed in `Main.DestroyCode`.

### 3D Assets

`3d/tractor_3.dae` (robot), `3d/person.dae` (pedestrian), `3d/bicycle.dae` — referenced as AnyLogic model resources.

## Editing Conventions

All logic lives inside the `.alp` XML as `<![CDATA[...]]>` Java code blocks. When editing:
- **Robot statechart actions** are in `<StatechartElement>` nodes under the `Robot` `ActiveObjectClass`.
- **Main utility functions** (`initEnvironment`, `assignNextTask`, `checkAllDone`, CSV helpers) are `<Function>` elements in the `Main` class.
- **`NodeLoc`** is a standalone `<JavaClass>` at the bottom of the file — edit it there, not inline.
- AnyLogic model time unit is **seconds**; distances are in px where 50 px = 10 m (scale ruler).
