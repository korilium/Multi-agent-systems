# Pedestrian Interaction & EA Fallback Re-scoring — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make actual pedestrian agents slow down robots based on proximity, and fix EA task re-scoring in the fallback path to use the full scoring function.

**Architecture:** Both fixes live entirely inside the Robot agent in `ColruytV5.0_IDE.alp`. Fix 1 adds a `computeSpeed(NodeLoc)` helper and replaces 6 `setSpeed(...)` call sites. Fix 2 adds a `scoreTaskEA(int[], NodeLoc)` helper, simplifies the primary EA selection loop, and replaces the incomplete fallback re-scoring block.

**Tech Stack:** AnyLogic 8.9.8 XML/Java (`.alp` file). All edits are inside `<![CDATA[...]]>` Java blocks in Robot's `<Functions>` and `<StatechartElement>` nodes. No separate `.java` files.

---

## File Changes

| File | What changes |
|---|---|
| `ColruytV5.0_IDE.alp` | Add `computeSpeed` and `scoreTaskEA` to Robot `<Functions>` (insert before line 7143 `</Functions>`); replace 6 `setSpeed(...)` calls; refactor primary EA loop and fallback block in `selectNextTask` |

---

## Task 1 — Add `computeSpeed(NodeLoc target)` to Robot

**Files:**
- Modify: `ColruytV5.0_IDE.alp` — insert new `<Function>` before line 7143 (`</Functions>`)

- [ ] **Step 1: Insert the `computeSpeed` function**

In `ColruytV5.0_IDE.alp`, find the exact text:
```
}]]></Body>
				</Function>
			</Functions>
			<AgentLinks>
```
(This is the end of `removeClaimedTask` closing into `</Functions>` around line 7141–7143.)

Replace it with:
```xml
}]]></Body>
				</Function>
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>RETURNS_VALUE</ReturnModificator>
					<ReturnType><![CDATA[double]]></ReturnType>
					<Id>1791000000001</Id>
					<Name><![CDATA[computeSpeed]]></Name>
					<X>50</X><Y>600</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Parameter>
						<Name><![CDATA[target]]></Name>
						<Type><![CDATA[NodeLoc]]></Type>
					</Parameter>
					<Body><![CDATA[double pedCount = 0;
for (Pedestrian p : main.pedestrians) {
    double d = Math.sqrt(Math.pow(p.getX() - target.x, 2)
                       + Math.pow(p.getY() - target.y, 2));
    if (d < 30.0) pedCount += 1.0;
}
return 10.0 / (1.0 + (target.crowdedness + pedCount * 0.5) * 0.5);]]></Body>
				</Function>
			</Functions>
			<AgentLinks>
```

- [ ] **Step 2: Replace all 6 `setSpeed(...)` call sites**

There are exactly 6 occurrences of:
```java
setSpeed(10.0 / (1.0 + goalNode.crowdedness * 0.5));
```
at lines 6040, 6142, 6278, 6324, 6398, 6504 (in `stDeliver` entry, `stGoToPickup` entry, `trDeliverReturn`, `trDeliverLoop`, `trReturnLoop`, `trDeliverLoop2`).

Use replace-all to change every occurrence to:
```java
setSpeed(computeSpeed(goalNode));
```

Verify with grep after the edit — expected result is zero matches:
```bash
grep -c "setSpeed(10.0" "ColruytV5.0_IDE.alp"
```
Expected output: `0`

- [ ] **Step 3: Verify `computeSpeed` is called in all motion contexts**

```bash
grep -n "setSpeed" "ColruytV5.0_IDE.alp"
```
Expected: 6 lines, all reading `setSpeed(computeSpeed(goalNode));`

- [ ] **Step 4: Commit**

```bash
git add ColruytV5.0_IDE.alp
git commit -m "feat: robot speed now includes real-time pedestrian proximity via computeSpeed"
```

---

## Task 2 — Add `scoreTaskEA(int[] task, NodeLoc robPos)` and refactor `selectNextTask`

**Files:**
- Modify: `ColruytV5.0_IDE.alp` — insert `scoreTaskEA` function; rewrite EA primary loop and fallback block in `selectNextTask`

- [ ] **Step 1: Insert the `scoreTaskEA` function**

In `ColruytV5.0_IDE.alp`, find (the `computeSpeed` closing tag you just added):
```
return 10.0 / (1.0 + (target.crowdedness + pedCount * 0.5) * 0.5);]]></Body>
				</Function>
			</Functions>
```

Replace it with:
```xml
return 10.0 / (1.0 + (target.crowdedness + pedCount * 0.5) * 0.5);]]></Body>
				</Function>
				<Function AccessType="default" StaticFunction="false">
					<ReturnModificator>RETURNS_VALUE</ReturnModificator>
					<ReturnType><![CDATA[double]]></ReturnType>
					<Id>1791000000002</Id>
					<Name><![CDATA[scoreTaskEA]]></Name>
					<X>50</X><Y>640</Y>
					<Label><X>10</X><Y>0</Y></Label>
					<PublicFlag>false</PublicFlag>
					<PresentationFlag>true</PresentationFlag>
					<ShowLabel>true</ShowLabel>
					<Parameter>
						<Name><![CDATA[task]]></Name>
						<Type><![CDATA[int[]]]></Type>
					</Parameter>
					<Parameter>
						<Name><![CDATA[robPos]]></Name>
						<Type><![CDATA[NodeLoc]]></Type>
					</Parameter>
					<Body><![CDATA[NodeLoc pickup = main.globalNodes.get(task[0]);
NodeLoc dest   = main.globalNodes.get(task[1]);

double score = calculateExpectedTime(robPos, pickup, 1)
             + calculateExpectedTime(pickup, dest, 1);

double minNext = Double.MAX_VALUE;
for (int[] nxt : localOrderList) {
    if (nxt == task) continue;
    double c = calculateExpectedTime(dest, main.globalNodes.get(nxt[0]), 1);
    if (c < minNext) minNext = c;
}
if (minNext == Double.MAX_VALUE)
    minNext = calculateExpectedTime(dest, main.globalNodes.get(0), 1);
score += minNext;

for (int i = 0; i < main.numRobots; i++) {
    Robot other = main.getRobotByIndex(i);
    if (other == null || other == this || other.parDestinationNode == null) continue;
    double overlap = Math.sqrt(
        Math.pow(other.parDestinationNode.x - dest.x, 2) +
        Math.pow(other.parDestinationNode.y - dest.y, 2));
    if (overlap < main.conflictRadiusThreshold)
        score += main.conflictPenaltyWeight * (1.0 - overlap / main.conflictRadiusThreshold);
}
return score;]]></Body>
				</Function>
			</Functions>
```

- [ ] **Step 2: Simplify the primary EA selection loop in `selectNextTask`**

Find this exact block (lines ~6987–7035):
```java
if (main.effectiveRoutingMode == 2) {
    // EA: expectation-aware scoring with lookahead and graduated conflict penalty
    double bestScore = Double.MAX_VALUE;
    NodeLoc robPos = findClosestNode(getX(), getY());

    for (int[] task : localOrderList) {
        NodeLoc pickup = main.globalNodes.get(task[0]);
        NodeLoc dest   = main.globalNodes.get(task[1]);

        // Travel to store + delivery leg
        double t = calculateExpectedTime(robPos, pickup, 1)
                 + calculateExpectedTime(pickup, dest, 1);

        // Lookahead: cost to nearest remaining order from destination
        double minNextCost = Double.MAX_VALUE;
        for (int[] next : localOrderList) {
            if (next == task) continue;
            NodeLoc nextPickup = main.globalNodes.get(next[0]);
            double nextCost = calculateExpectedTime(dest, nextPickup, 1);
            if (nextCost < minNextCost) minNextCost = nextCost;
        }
        // No next task — fall back to depot
        if (minNextCost == Double.MAX_VALUE) {
            minNextCost = calculateExpectedTime(dest, main.globalNodes.get(0), 1);
        }
        t += minNextCost;

        // Graduated conflict penalty
        double penalty = 0;
        for (int i = 0; i < main.numRobots; i++) {
            Robot other = main.getRobotByIndex(i);
            if (other == null || other == this) continue;
            if (other.parDestinationNode != null) {
                double overlap = Math.sqrt(
                    Math.pow(other.parDestinationNode.x - dest.x, 2) +
                    Math.pow(other.parDestinationNode.y - dest.y, 2));
                if (overlap < main.conflictRadiusThreshold) {
                    penalty += main.conflictPenaltyWeight
                             * (1.0 - overlap / main.conflictRadiusThreshold);
                }
            }
        }

        double score = t + penalty;
        if (score < bestScore) {
            bestScore = score;
            selectedTask = task;
        }
    }
} else {
```

Replace with:
```java
if (main.effectiveRoutingMode == 2) {
    // EA: expectation-aware scoring — see scoreTaskEA()
    double bestScore = Double.MAX_VALUE;
    NodeLoc robPos = findClosestNode(getX(), getY());

    for (int[] task : localOrderList) {
        double s = scoreTaskEA(task, robPos);
        if (s < bestScore) { bestScore = s; selectedTask = task; }
    }
} else {
```

- [ ] **Step 3: Fix the fallback re-scoring block**

Find this exact block (lines ~7055–7069):
```java
    // Pick next candidate (SSP/EV: first; EA: re-score remaining)
    if (main.effectiveRoutingMode == 2) {
        double bestScore2 = Double.MAX_VALUE;
        NodeLoc robPos2 = findClosestNode(getX(), getY());
        selectedTask = localOrderList.get(0);
        for (int[] task2 : localOrderList) {
            NodeLoc pickup2 = main.globalNodes.get(task2[0]);
            NodeLoc dest2   = main.globalNodes.get(task2[1]);
            double t2 = calculateExpectedTime(robPos2, pickup2, 1)
                      + calculateExpectedTime(pickup2, dest2, 1);
            if (t2 < bestScore2) { bestScore2 = t2; selectedTask = task2; }
        }
    } else {
        selectedTask = localOrderList.get(0);
    }
```

Replace with:
```java
    // Pick next candidate (SSP/EV: first; EA: full re-score with scoreTaskEA)
    if (main.effectiveRoutingMode == 2) {
        double bestScore2 = Double.MAX_VALUE;
        NodeLoc robPos2 = findClosestNode(getX(), getY());
        selectedTask = localOrderList.get(0);
        for (int[] task2 : localOrderList) {
            double s2 = scoreTaskEA(task2, robPos2);
            if (s2 < bestScore2) { bestScore2 = s2; selectedTask = task2; }
        }
    } else {
        selectedTask = localOrderList.get(0);
    }
```

- [ ] **Step 4: Verify `scoreTaskEA` is referenced exactly twice in `selectNextTask`**

```bash
grep -n "scoreTaskEA" "ColruytV5.0_IDE.alp"
```
Expected: 3 lines — the function definition (`<Name>`) and two call sites inside `selectNextTask`.

- [ ] **Step 5: Commit**

```bash
git add ColruytV5.0_IDE.alp
git commit -m "feat: extract scoreTaskEA helper; fix EA fallback to use full scoring"
```

---

## Task 3 — Verify in AnyLogic

**Files:** None changed — run-only verification

- [ ] **Step 1: Open `ColruytV5.0_IDE.alp` in AnyLogic 8.9.x and press Run**

If the IDE reports a compile error, check:
- The `<Id>` values `1791000000001` and `1791000000002` are unique (grep for them — should appear only once each)
- The CDATA blocks are properly closed (`]]></Body>`)
- No stray characters around the XML insertions

- [ ] **Step 2: Run with `routingMode=3` (COMPARE), `crowdednessLevel=3`, `numRobots=2`, `numOrders=5`**

In the AnyLogic console (traceln output), confirm:
- Simulation completes all 3 phases and writes `summary_*.csv`
- No "Robot stuck" or infinite-loop traces

- [ ] **Step 3: Confirm pedestrian effect is active**

With `crowdednessLevel=5` and a busy node (node7, crowdedness=8), watch a robot traverse that area. Its speed should be noticeably lower when pedestrians are clustered near the goal node compared to open areas.

Alternatively, temporarily add a traceln inside `computeSpeed` to log `pedCount`:
```java
traceln("computeSpeed: target=" + main.globalNodes.indexOf(target) + " crowdedness=" + target.crowdedness + " pedCount=" + pedCount);
```
Remove the traceln after confirming.

- [ ] **Step 4: Confirm EA scoring under contention**

Run with `routingMode=2` (EA), `numRobots=4`, `numOrders=20`. In the console, when a robot hits a peer-claimed task and re-scores, it should log:
```
Robot1 task claimed by peer, skipping: nodeX -> nodeY
```
followed immediately by a new `=== Robot1 claimed: ...` line — confirming the fallback selected a task (not stuck in retry).

- [ ] **Step 5: Commit verification note**

```bash
git commit --allow-empty -m "chore: verified pedestrian interaction and EA fallback in AnyLogic"
```
