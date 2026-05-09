# Mode 5 COMPREHENSIVE — Design Spec

**Date:** 2026-05-09
**Status:** Approved
**File:** `ColruytV5.0_IDE.alp`

## Overview

Add `routingMode = 5` (COMPREHENSIVE) to the existing simulation. Builds directly on mode 4 (AUTO) by wrapping its 10-robot sweep with an outer loop over `crowdednessLevel` 1–5. Result: **150 phases per run** (5 crowd levels × 10 robot counts × 3 routing modes). The same order list is preserved across all 150 phases, isolating crowdedness as an independent variable.

## Approach

Approach A — Nested-counter. Add `autoCrowdLevel` alongside the existing `autoRobotCount`. Inner robot-count loop (mode 4 logic) is reused unchanged; outer crowd loop is handled by a new `resetForAutoNextCrowdness()` function.

---

## Section 1 — State & Initialization

### New fields on `Main`

| Field | Type | Initial value | Purpose |
|---|---|---|---|
| `autoCrowdLevel` | `int` | `0` | Current crowdedness level in the mode-5 sweep (1–5). Zero outside mode 5. |
| `baseCrowdedness` | `double[]` | size 75 | Unscaled per-node crowdedness values, captured once in `StartupCode` after manual assignment, before `crowdednessScale` multiply. |

### `StartupCode` changes

1. After the manual per-node crowdedness assignments and **before** the `crowdednessScale` multiply loop, capture base values:
   ```java
   baseCrowdedness = new double[globalNodes.size()];
   for (int i = 0; i < globalNodes.size(); i++)
       baseCrowdedness[i] = globalNodes.get(i).crowdedness;
   ```

2. Add mode 5 initialisation alongside modes 3 and 4:
   ```java
   autoCrowdLevel = (routingMode == 5) ? 1 : 0;
   if (routingMode == 5) {
       numRobots      = 1;
       crowdednessLevel = 1;
       autoRobotCount = 1;
   }
   ```
   Mode 5 always starts at `crowdednessLevel=1`, `numRobots=1`, `comparisonPhase=0`. Both sliders are ignored.

3. Add a trace line:
   ```java
   if (routingMode == 5)
       traceln("=== COMPREHENSIVE START: crowdLevel=" + autoCrowdLevel
           + " robots=" + numRobots + " ===");
   ```

---

## Section 2 — Control Flow & New Functions

### `checkAllDone` — add mode 5 branch

Insert after the existing `} else if (routingMode == 4) {` block:

```java
} else if (routingMode == 5) {
    phaseMakespan[phaseIdx] = makespan;
    writeMakespanRow(makespan);
    if (comparisonPhase < 2) {
        resetForNextPhase();
        return;
    }
    // All 3 modes done for this (crowd, robot) combination
    writeFinalComparison();
    if (autoRobotCount < 10) {
        resetForAutoNextRobot();      // inner loop — reused unchanged
        return;
    }
    // All 10 robot counts done for this crowdedness level
    if (autoCrowdLevel < 5) {
        resetForAutoNextCrowdness();  // outer loop
        return;
    }
    // Full 150-phase sweep complete
    traceln("=== COMPREHENSIVE SWEEP COMPLETE (5 crowd × 10 robots × 3 modes) ===");
    closeCsv();
}
```

`resetForAutoNextRobot()` is called **unchanged** from mode 5. It already resets `comparisonPhase=0`, `effectiveRoutingMode=0`, increments `autoRobotCount`, restores orders, and reinitialises robots.

### New function `resetForAutoNextCrowdness()`

```java
// Advance outer crowd-level counter
autoCrowdLevel++;
crowdednessLevel = autoCrowdLevel;

// Rescale per-node crowdedness weights: base × newLevel / 3.0
double newScale = crowdednessLevel / 3.0;
for (int i = 0; i < globalNodes.size(); i++)
    globalNodes.get(i).crowdedness = baseCrowdedness[i] * newScale;

// Reset robot-count inner sweep back to start
autoRobotCount = 1;
numRobots      = 1;
comparisonPhase      = 0;
effectiveRoutingMode = 0;
totalDeliveries      = 0;

// Reset phase accumulators
phaseDeliveryCount = 0;
phaseTaskTimeSum = 0; phaseOutTimeSum = 0;
phaseInTimeSum = 0;   phaseReturnTimeSum = 0;
phaseMinTaskTime = Double.MAX_VALUE; phaseMaxTaskTime = 0;
for (int i = 0; i < 10; i++) {
    phaseRobotTaskCount[i] = 0;
    phaseRobotTotalTime[i] = 0;
    robotOrders[i] = 0;
}
phaseStartSimTime = time();

// Restore original order list (savedOrderList never changes in mode 5)
orderList.clear();
claimedOrders.clear();
for (int[] t : savedOrderList) orderList.add(new int[]{t[0], t[1], t[2]});
traceln("=== COMPREHENSIVE: crowd now " + crowdednessLevel
    + " | restored " + orderList.size() + " orders ===");

writeEventLog(0, 0, time(), -1, "PHASE_START", "-", "-", -1,
    "COMPREHENSIVE crowd=" + crowdednessLevel + " robots=" + numRobots + " mode=SSP");

// Stop and clear all robots, reinitialise active ones (identical to resetForAutoNextRobot body)
int[] startNodes = {0, 7, 14, 21, 28, 35, 42, 49, 56, 63};
for (int i = 0; i < 10; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob == null) continue;
    rob.stop();
    if (rob.plannedRoute != null) rob.plannedRoute.clear();
    if (rob.routeLines   != null) rob.routeLines.clear();
    rob.clearRoute();
    rob.goalNode = rob.parStartNode = rob.parDestinationNode = null;
    rob.chainedTask = rob.deliveryComplete = rob.returnComplete = false;
}
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob == null) continue;
    int nodeIdx = startNodes[Math.min(i, startNodes.length - 1)];
    NodeLoc startLoc = globalNodes.get(nodeIdx);
    rob.setXY(startLoc.x, startLoc.y);
    rob.robotId = i;
    rob.currentPickupIdx = rob.currentDestIdx = -1;
    rob.ordersCompleted = 0;
    rob.currentState = "IDLE";
    rob.timeOrderStart = rob.timeReachedDest = 0.0;
    rob.expectedOutTime = rob.expectedInTime = 0.0;
    rob.routeHopsToStore = rob.routeHopsToDestination = rob.routeHopsReturn = 0;
    rob.localOrderList.clear();
    rob.buildLocalOrderList();
    rob.phaseReset = true;
    rob.onChange();
}
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob != null) rob.onChange();
}
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob != null) rob.onChange();
}
```

---

## Section 3 — UI Updates

### `legendModes` (in-world legend panel)

Add line 5, update closing header:

```
── ROUTING MODE ───────────────────────────
 0=SSP     shortest path (ignores crowd)
 1=EV      crowd-weighted Dijkstra
 2=EA      EV + agent-aware task selection
 3=COMPARE all 3 modes, same order list
 4=AUTO    sweep 1–10 robots × 3 modes
 5=COMPR.  sweep crowd 1–5 × 1–10 robots × 3 modes
── CURRENT RUN ────────────────────────────
```

### `routingModeGuide` (parameter selector page)

Update slider range from `[slider  0 – 4]` → `[slider  0 – 5]` and append:

```
  5 = COMPREHENSIVE  (Full 2-D Sweep)
           Sweeps crowdednessLevel 1→5, and for each level
           sweeps numRobots 1→10, running SSP→EV→EA on the
           SAME order list throughout.
           150 phases total (5 crowd × 10 robots × 3 modes).
           Both numRobots and crowdednessLevel sliders are ignored.
           All 150 results append to dashboard_performance.csv.
```

### `crowdednessLevelGuide` (parameter selector page)

Append to existing text:

```
  (ignored in COMPREHENSIVE mode — swept 1→5 automatically)
```

### `numRobotsGuide` (parameter selector page)

Update parenthetical:

```
numRobots     [slider  1 – 10]  (ignored in AUTO and COMPREHENSIVE modes)
```

### `updateStatusDisplay`

Add mode 5 branch before the `else if (routingMode == 3)` branch:

```java
if (routingMode == 5) {
    modeLabel = "COMPREHENSIVE | Crowd=" + autoCrowdLevel
        + " Robots=" + numRobots + " Phase "
        + (comparisonPhase >= 0 ? comparisonPhase : 0)
        + " [" + getModeName(effectiveRoutingMode) + "]";
} else if (routingMode == 4) {
    ...
```

### Dashboard panel

Mode 5 reuses the existing single-mode KPI `else` branch. No new panel needed — `dashboard_performance.csv` is the intended charting output.

---

## Section 4 — Logging

No schema changes. All four CSV files already include `crowdednessLevel`, so the 150 rows produced by mode 5 are naturally differentiated. Example `dashboard_performance.csv` rows:

```
runId,           numRobots, phase, effectiveMode, modeName, makespan, ..., crowdednessLevel, ...
20260509_103000, 1,         0,     0,             SSP,      42.1,    ..., 1,               ...
20260509_103000, 1,         1,     1,             EV,       38.4,    ..., 1,               ...
20260509_103000, 1,         2,     2,             EA,       35.9,    ..., 1,               ...
...
20260509_103000, 10,        2,     2,             EA,       29.1,    ..., 5,               ...
```

### `openCsv` — add mode 5 trace

```java
if (routingMode == 5)
    traceln("=== COMPREHENSIVE mode: 5 crowd × 10 robots × 3 modes = 150 phases ===");
```

### Existing guards that cover mode 5 automatically

- `initEnvironment`: `if (routingMode >= 3 && comparisonPhase > 0)` — covers mode 5 (5 ≥ 3). Order-list restore on phases 1 and 2 works with no change.
- `writeCsvRow`, `writeMakespanRow`, `writeEventLog`: all use `comparisonPhase` and `effectiveRoutingMode` which are set correctly by the sweep logic.
- `writeFinalComparison`: called at end of every 3-phase block; already writes `crowdednessLevel`. No change needed.

---

## Phase Count Summary

| Loop | Range | Count |
|---|---|---|
| Crowdedness level (outer) | 1–5 | 5 |
| Robot count (middle) | 1–10 | 10 |
| Routing mode (inner) | SSP/EV/EA | 3 |
| **Total phases** | | **150** |

## Files Changed

All changes are inside `ColruytV5.0_IDE.alp` (XML with embedded Java `CDATA` blocks):

1. `Main` variable declarations — add `autoCrowdLevel` (int), `baseCrowdedness` (double[])
2. `Main.StartupCode` — capture base crowdedness, init mode 5 vars
3. `Main.checkAllDone` — add `routingMode == 5` branch
4. `Main` — new function `resetForAutoNextCrowdness()`
5. `Main.updateStatusDisplay` — add mode 5 label branch
6. `Main.openCsv` — add mode 5 trace
7. `legendModes` text element — add line 5
8. `routingModeGuide` text element — update range + add mode 5 description
9. `crowdednessLevelGuide` text element — add ignored-in-COMPREHENSIVE note
10. `numRobotsGuide` text element — update ignored-in note
