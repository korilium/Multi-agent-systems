# Mode 5 COMPREHENSIVE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `routingMode = 5` (COMPREHENSIVE) — a 150-phase sweep (crowdedness 1–5 × robots 1–10 × SSP/EV/EA) built on top of the existing mode 4 AUTO loop.

**Architecture:** All logic lives in `ColruytV5.0_IDE.alp` as embedded Java `<![CDATA[...]]>` blocks inside XML. No separate `.java` files. Edits use exact string replacement targeting the CDATA content. A new outer crowdedness loop wraps the existing inner robot-count loop; `resetForAutoNextCrowdness()` mirrors `resetForAutoNextRobot()`. The existing `savedOrderList` is preserved across all 150 phases unchanged.

**Tech Stack:** AnyLogic 8.9.x, Java 11 (embedded), XML editing via Edit tool, no unit test framework — verification is grep + AnyLogic trace output.

---

## File Modified

- `ColruytV5.0_IDE.alp` — all 10 changes are to this single file.

---

## Task 1: Declare `autoCrowdLevel` and `baseCrowdedness` variables

**Files:**
- Modify: `ColruytV5.0_IDE.alp:615-629` (after the `autoRobotCount` variable block)

- [ ] **Step 1: Verify the variables do not yet exist**

```bash
grep -n "autoCrowdLevel\|baseCrowdedness" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Insert both variable declarations after the `autoRobotCount` block**

Find this exact string (the closing tag of the `autoRobotCount` block):
```xml
					</Properties>
				</Variable>
				<Variable Class="PlainVariable">
					<Id>1790000000004</Id>
					<Name><![CDATA[phaseStartSimTime]]></Name>
```

Replace with:
```xml
					</Properties>
				</Variable>
				<Variable Class="PlainVariable">
					<Id>1790000000201</Id>
					<Name><![CDATA[autoCrowdLevel]]></Name>
					<X>-220</X><Y>-135</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" Constant="false" AccessType="public" StaticVariable="false">
						<Type><![CDATA[int]]></Type>        
						<InitialValue Class="CodeValue">
							<Code><![CDATA[0]]></Code>
						</InitialValue>
					</Properties>
				</Variable>
				<Variable Class="PlainVariable">
					<Id>1790000000202</Id>
					<Name><![CDATA[baseCrowdedness]]></Name>
					<X>-220</X><Y>-140</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Properties SaveInSnapshot="true" Constant="false" AccessType="public" StaticVariable="false">
						<Type><![CDATA[double[]]]></Type>        
						<InitialValue Class="CodeValue">
							<Code><![CDATA[new double[0]]]></Code>
						</InitialValue>
					</Properties>
				</Variable>
				<Variable Class="PlainVariable">
					<Id>1790000000004</Id>
					<Name><![CDATA[phaseStartSimTime]]></Name>
```

- [ ] **Step 3: Verify both variables are present**

```bash
grep -n "autoCrowdLevel\|baseCrowdedness" "ColruytV5.0_IDE.alp"
```
Expected: 2 lines, each containing the variable name inside a `<Name>` tag.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: declare autoCrowdLevel and baseCrowdedness variables for mode 5"
```

---

## Task 2: Update `StartupCode` — capture base crowdedness + init mode 5

**Files:**
- Modify: `ColruytV5.0_IDE.alp:119-191` (two separate edits within `StartupCode`)

### Edit 2a — capture base crowdedness values before the scale loop

- [ ] **Step 1: Find the crowdedness scale comment line and verify `baseCrowdedness` capture is absent**

```bash
grep -n "baseCrowdedness\[i\]" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Insert base-capture block before the scale loop**

Find:
```java
// Scale all node crowdedness values by the crowdednessLevel parameter so that
// EV/EA routing actually responds to the slider (level 3 = unchanged baseline).
double crowdednessScale = crowdednessLevel / 3.0;
```

Replace with:
```java
// Capture unscaled base values before applying crowdednessLevel — needed by
// mode 5 to rescale node weights when advancing to each new crowd tier.
baseCrowdedness = new double[globalNodes.size()];
for (int i = 0; i < globalNodes.size(); i++)
    baseCrowdedness[i] = globalNodes.get(i).crowdedness;

// Scale all node crowdedness values by the crowdednessLevel parameter so that
// EV/EA routing actually responds to the slider (level 3 = unchanged baseline).
double crowdednessScale = crowdednessLevel / 3.0;
```

- [ ] **Step 3: Verify capture block is present**

```bash
grep -n "baseCrowdedness\[i\]" "ColruytV5.0_IDE.alp"
```
Expected: 1 line — the capture assignment inside the for loop.

### Edit 2b — add mode 5 init alongside mode 4

- [ ] **Step 4: Verify mode 5 init is absent**

```bash
grep -n "autoCrowdLevel =" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 5: Insert mode 5 init + extend mode 4 guards to cover mode 5**

Find:
```java
autoRobotCount       = (routingMode == 4) ? 1  : 0;
if (routingMode == 4) numRobots = 1;
```

Replace with:
```java
autoRobotCount       = (routingMode >= 4) ? 1  : 0;
if (routingMode >= 4) numRobots = 1;
autoCrowdLevel       = (routingMode == 5) ? 1  : 0;
if (routingMode == 5) crowdednessLevel = 1;
```

- [ ] **Step 6: Verify**

```bash
grep -n "autoCrowdLevel\|routingMode >= 4" "ColruytV5.0_IDE.alp"
```
Expected: lines containing `autoCrowdLevel = (routingMode == 5)` and `routingMode >= 4` (two occurrences).

- [ ] **Step 7: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: capture baseCrowdedness and init mode 5 vars in StartupCode"
```

---

## Task 3: Add `resetForAutoNextCrowdness()` function

**Files:**
- Modify: `ColruytV5.0_IDE.alp:1845` (insert new `<Function>` XML after the closing `</Function>` of `resetForAutoNextRobot`)

- [ ] **Step 1: Verify function does not yet exist**

```bash
grep -n "resetForAutoNextCrowdness" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Insert the new function after `resetForAutoNextRobot`'s closing tag**

Find the exact closing sequence of `resetForAutoNextRobot` (the last lines of its body followed by the closing XML tags):
```xml
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob != null) rob.onChange();
}]]></Body>
				</Function>
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>VOID</ReturnModificator>
					<ReturnType><![CDATA[void]]></ReturnType>
					<Id>1790000100004</Id>
					<Name><![CDATA[writeFinalComparison]]></Name>
```

Replace with:
```xml
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob != null) rob.onChange();
}]]></Body>
				</Function>
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>VOID</ReturnModificator>
					<ReturnType><![CDATA[void]]></ReturnType>
					<Id>1790000100011</Id>
					<Name><![CDATA[resetForAutoNextCrowdness]]></Name>
					<X>880</X><Y>930</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Body><![CDATA[// Advance outer crowd-level counter and rescale node weights
autoCrowdLevel++;
crowdednessLevel = autoCrowdLevel;

double newScale = crowdednessLevel / 3.0;
for (int i = 0; i < globalNodes.size(); i++)
    globalNodes.get(i).crowdedness = baseCrowdedness[i] * newScale;

// Reset inner robot-count sweep back to 1
autoRobotCount       = 1;
numRobots            = 1;
comparisonPhase      = 0;
effectiveRoutingMode = 0;
totalDeliveries      = 0;

phaseDeliveryCount = 0;
phaseTaskTimeSum = 0; phaseOutTimeSum = 0; phaseInTimeSum = 0; phaseReturnTimeSum = 0;
phaseMinTaskTime = Double.MAX_VALUE; phaseMaxTaskTime = 0;
for (int i = 0; i < 10; i++) { phaseRobotTaskCount[i] = 0; phaseRobotTotalTime[i] = 0; robotOrders[i] = 0; }
phaseStartSimTime = time();

// Restore original order list (savedOrderList never changes across all 150 phases)
orderList.clear();
claimedOrders.clear();
for (int[] t : savedOrderList) orderList.add(new int[]{t[0], t[1], t[2]});
traceln("=== COMPREHENSIVE: crowd now " + crowdednessLevel
    + " | restored " + orderList.size() + " orders ===");

writeEventLog(0, 0, time(), -1, "PHASE_START", "-", "-", -1,
    "COMPREHENSIVE crowd=" + crowdednessLevel + " robots=" + numRobots + " mode=SSP");

// Stop and clear ALL robots
int[] startNodes = {0, 7, 14, 21, 28, 35, 42, 49, 56, 63};
for (int i = 0; i < 10; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob == null) continue;
    rob.stop();
    if (rob.plannedRoute != null) rob.plannedRoute.clear();
    if (rob.routeLines   != null) rob.routeLines.clear();
    rob.clearRoute();
    rob.goalNode = null;
    rob.parStartNode = null;
    rob.parDestinationNode = null;
    rob.chainedTask = false;
    rob.deliveryComplete = false;
    rob.returnComplete = false;
}

// Fully initialise only the 1 active robot for the new phase
for (int i = 0; i < numRobots; i++) {
    Robot rob = getRobotByIndex(i);
    if (rob == null) continue;
    int nodeIdx = startNodes[Math.min(i, startNodes.length - 1)];
    NodeLoc startLoc = globalNodes.get(nodeIdx);
    rob.setXY(startLoc.x, startLoc.y);
    rob.robotId = i;
    rob.currentPickupIdx = -1;
    rob.currentDestIdx   = -1;
    rob.ordersCompleted  = 0;
    rob.currentState     = "IDLE";
    rob.timeOrderStart   = 0.0;
    rob.timeReachedDest  = 0.0;
    rob.expectedOutTime  = 0.0;
    rob.expectedInTime   = 0.0;
    rob.routeHopsToStore       = 0;
    rob.routeHopsToDestination = 0;
    rob.routeHopsReturn        = 0;
    rob.localOrderList.clear();
    rob.buildLocalOrderList();
    traceln("COMPREHENSIVE Robot" + i + " reset at node" + (nodeIdx+1)
        + " | list=" + rob.localOrderList.size());
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
}]]></Body>
				</Function>
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>VOID</ReturnModificator>
					<ReturnType><![CDATA[void]]></ReturnType>
					<Id>1790000100004</Id>
					<Name><![CDATA[writeFinalComparison]]></Name>
```

- [ ] **Step 3: Verify function was inserted**

```bash
grep -n "resetForAutoNextCrowdness" "ColruytV5.0_IDE.alp"
```
Expected: 1 line with the function name inside a `<Name>` tag.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: add resetForAutoNextCrowdness() for mode 5 outer crowd loop"
```

---

## Task 4: Add mode 5 branch in `checkAllDone`

**Files:**
- Modify: `ColruytV5.0_IDE.alp:1328-1344` (the `checkAllDone` function body)

- [ ] **Step 1: Verify mode 5 branch is absent**

```bash
grep -n "routingMode == 5" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Insert mode 5 branch after the mode 4 block**

Find the exact end of the mode 4 block and the start of the `else`:
```java
    // Full sweep 1–10 robots complete
    traceln("=== AUTO SWEEP COMPLETE (1–10 robots × 3 modes) ===");
    closeCsv();
} else {
    writeMakespanRow(makespan);
    closeCsv();
}
```

Replace with:
```java
    // Full sweep 1–10 robots complete
    traceln("=== AUTO SWEEP COMPLETE (1–10 robots × 3 modes) ===");
    closeCsv();
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
        resetForAutoNextRobot();
        return;
    }
    // All 10 robot counts done for this crowdedness level
    if (autoCrowdLevel < 5) {
        resetForAutoNextCrowdness();
        return;
    }
    // Full 150-phase sweep complete
    traceln("=== COMPREHENSIVE SWEEP COMPLETE (5 crowd × 10 robots × 3 modes) ===");
    closeCsv();
} else {
    writeMakespanRow(makespan);
    closeCsv();
}
```

- [ ] **Step 3: Verify**

```bash
grep -n "routingMode == 5\|COMPREHENSIVE SWEEP COMPLETE\|resetForAutoNextCrowdness" "ColruytV5.0_IDE.alp"
```
Expected: 3 lines — one for each of the three strings.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: add routingMode == 5 branch in checkAllDone"
```

---

## Task 5: Add mode 5 label in `updateStatusDisplay`

**Files:**
- Modify: `ColruytV5.0_IDE.alp:1887-1897` (the `updateStatusDisplay` function body)

- [ ] **Step 1: Verify mode 5 label is absent**

```bash
grep -n "COMPREHENSIVE | Crowd" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Insert mode 5 as the first branch**

Find:
```java
if (routingMode == 4) {
    modeLabel = "AUTO | Robots=" + numRobots + " Phase "
        + (comparisonPhase >= 0 ? comparisonPhase : 0)
        + " [" + getModeName(effectiveRoutingMode) + "]";
} else if (routingMode == 3) {
```

Replace with:
```java
if (routingMode == 5) {
    modeLabel = "COMPREHENSIVE | Crowd=" + autoCrowdLevel
        + " Robots=" + numRobots + " Phase "
        + (comparisonPhase >= 0 ? comparisonPhase : 0)
        + " [" + getModeName(effectiveRoutingMode) + "]";
} else if (routingMode == 4) {
    modeLabel = "AUTO | Robots=" + numRobots + " Phase "
        + (comparisonPhase >= 0 ? comparisonPhase : 0)
        + " [" + getModeName(effectiveRoutingMode) + "]";
} else if (routingMode == 3) {
```

- [ ] **Step 3: Verify**

```bash
grep -n "COMPREHENSIVE | Crowd" "ColruytV5.0_IDE.alp"
```
Expected: 1 line containing the new modeLabel string.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: add mode 5 status label in updateStatusDisplay"
```

---

## Task 6: Add mode 5 trace in `openCsv`

**Files:**
- Modify: `ColruytV5.0_IDE.alp:1405` (inside `openCsv`, after the existing traceln)

- [ ] **Step 1: Verify trace line is absent**

```bash
grep -n "150 phases" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Append mode 5 trace after the existing CSV-opened traceln**

Find:
```java
    traceln("CSV files opened: " + detailFile + " | " + eventFile + " | " + summaryFile + " | dashboard_performance.csv");
```

Replace with:
```java
    traceln("CSV files opened: " + detailFile + " | " + eventFile + " | " + summaryFile + " | dashboard_performance.csv");
    if (routingMode == 5)
        traceln("=== COMPREHENSIVE mode: 5 crowd × 10 robots × 3 modes = 150 phases ===");
```

- [ ] **Step 3: Verify**

```bash
grep -n "150 phases" "ColruytV5.0_IDE.alp"
```
Expected: 1 line.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "feat: add mode 5 phase-count trace in openCsv"
```

---

## Task 7: Update `legendModes` UI text

**Files:**
- Modify: `ColruytV5.0_IDE.alp:3180-3186` (the `legendModes` text element)

- [ ] **Step 1: Verify current text**

```bash
grep -n "4=AUTO\|5=COMPR" "ColruytV5.0_IDE.alp"
```
Expected: 1 line for `4=AUTO`, no line for `5=COMPR`.

- [ ] **Step 2: Add mode 5 line**

Find:
```
 4=AUTO    sweep 1–10 robots × 3 modes
── CURRENT RUN ────────────────────────────
```

Replace with:
```
 4=AUTO    sweep 1–10 robots × 3 modes
 5=COMPR.  crowd 1–5 × 1–10 robots × 3 modes
── CURRENT RUN ────────────────────────────
```

- [ ] **Step 3: Verify**

```bash
grep -n "5=COMPR" "ColruytV5.0_IDE.alp"
```
Expected: 1 line.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "ui: add mode 5 entry to legendModes panel"
```

---

## Task 8: Update `routingModeGuide` UI text

**Files:**
- Modify: `ColruytV5.0_IDE.alp:8094-8122` (the `routingModeGuide` text element)

- [ ] **Step 1: Verify current text**

```bash
grep -n "slider.*0 – 4\|0 – 5\|COMPREHENSIVE" "ColruytV5.0_IDE.alp"
```
Expected: 1 line for `0 – 4`, no lines for `0 – 5` or `COMPREHENSIVE`.

- [ ] **Step 2: Update slider range and append mode 5 description**

Find:
```
routingMode   [slider  0 – 4]
```

Replace with:
```
routingMode   [slider  0 – 5]
```

Then find:
```
  4 = AUTO  (Full Robot-Count Sweep)
           Automatically sweeps numRobots from 1 to 10.
           For each robot count, runs SSP → EV → EA on the SAME
           order list.  All 30 phase results (10 counts × 3 modes)
           are appended to dashboard_performance.csv for charting.
           numRobots slider is ignored — the sweep controls it.
```

Replace with:
```
  4 = AUTO  (Full Robot-Count Sweep)
           Automatically sweeps numRobots from 1 to 10.
           For each robot count, runs SSP → EV → EA on the SAME
           order list.  All 30 phase results (10 counts × 3 modes)
           are appended to dashboard_performance.csv for charting.
           numRobots slider is ignored — the sweep controls it.

  5 = COMPREHENSIVE  (Full 2-D Sweep)
           Sweeps crowdednessLevel 1→5, and for each level
           sweeps numRobots 1→10, running SSP→EV→EA on the
           SAME order list throughout.
           150 phases total (5 crowd × 10 robots × 3 modes).
           Both numRobots and crowdednessLevel sliders are ignored.
           All 150 results append to dashboard_performance.csv.
```

- [ ] **Step 3: Verify**

```bash
grep -n "0 – 5\|COMPREHENSIVE\|150 phases total" "ColruytV5.0_IDE.alp"
```
Expected: 3 lines (slider range update, COMPREHENSIVE heading, 150 phases description).

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "ui: update routingModeGuide — add mode 5 description, fix slider range to 0–5"
```

---

## Task 9: Update `crowdednessLevelGuide` UI text

**Files:**
- Modify: `ColruytV5.0_IDE.alp:8265-8276` (the `crowdednessLevelGuide` text element)

- [ ] **Step 1: Verify the note is absent**

```bash
grep -n "ignored in COMPREHENSIVE" "ColruytV5.0_IDE.alp"
```
Expected: no output.

- [ ] **Step 2: Append the ignored-in-COMPREHENSIVE note**

Find:
```
  Spatial pattern (city-centre busier than outskirts) is preserved
  via per-node crowdedness weights set in Main's startup code.
```

Replace with:
```
  Spatial pattern (city-centre busier than outskirts) is preserved
  via per-node crowdedness weights set in Main's startup code.

  (ignored in COMPREHENSIVE mode — swept 1→5 automatically)
```

- [ ] **Step 3: Verify**

```bash
grep -n "ignored in COMPREHENSIVE" "ColruytV5.0_IDE.alp"
```
Expected: 1 line.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "ui: note crowdednessLevel is ignored in COMPREHENSIVE mode"
```

---

## Task 10: Update `numRobotsGuide` UI text

**Files:**
- Modify: `ColruytV5.0_IDE.alp:8143` (the `numRobotsGuide` text element)

- [ ] **Step 1: Verify current text**

```bash
grep -n "ignored in AUTO mode\|ignored in AUTO and COMPREHENSIVE" "ColruytV5.0_IDE.alp"
```
Expected: 1 line for `ignored in AUTO mode`, no line for `AUTO and COMPREHENSIVE`.

- [ ] **Step 2: Update the parenthetical**

Find:
```
numRobots     [slider  1 – 10]  (ignored in AUTO mode)
```

Replace with:
```
numRobots     [slider  1 – 10]  (ignored in AUTO and COMPREHENSIVE modes)
```

- [ ] **Step 3: Verify**

```bash
grep -n "ignored in AUTO and COMPREHENSIVE" "ColruytV5.0_IDE.alp"
```
Expected: 1 line.

- [ ] **Step 4: Commit**

```bash
git add "ColruytV5.0_IDE.alp"
git commit -m "ui: note numRobots is also ignored in COMPREHENSIVE mode"
```

---

## Integration Verification

After all 10 tasks are committed, verify the full feature in AnyLogic:

- [ ] **Open `ColruytV5.0_IDE.alp` in AnyLogic 8.9.x**

- [ ] **Set `routingMode = 5`, `numOrders = 3`, `randomSeed = 5`. Press Run.**

Expected trace output (in order):
```
=== COMPREHENSIVE mode: 5 crowd × 10 robots × 3 modes = 150 phases ===
=== COMPREHENSIVE START: crowdLevel=1 robots=1 ===
=== SSP COMPLETE | phase=0 ...
=== EV COMPLETE  | phase=1 ...
=== EA COMPLETE  | phase=2 ...
=== AUTO: robot count now 2 ...    ← resetForAutoNextRobot called
...
=== AUTO: robot count now 10 ...
=== COMPREHENSIVE: crowd now 2 | restored 3 orders ===   ← resetForAutoNextCrowdness
...
=== COMPREHENSIVE SWEEP COMPLETE (5 crowd × 10 robots × 3 modes) ===
```

- [ ] **Check `dashboard_performance.csv` row count**

```bash
wc -l dashboard_performance.csv
```
Expected: 151 lines (1 header + 150 data rows).

- [ ] **Verify all 5 crowdedness levels appear**

```bash
awk -F',' 'NR>1 {print $NF}' dashboard_performance.csv | sort -n | uniq -c
```
Expected: 30 rows for each of crowdedness levels 1, 2, 3, 4, 5.

- [ ] **Verify the status display in AnyLogic shows the correct label format**

During the run, the status panel should show e.g.:
```
COMPREHENSIVE | Crowd=2 Robots=5 Phase 1 [EV]
```
