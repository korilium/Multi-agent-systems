# Design: Pedestrian Interaction & EA Fallback Re-scoring

**Date:** 2026-05-09  
**Scope:** Two targeted fixes to `ColruytV5.0_IDE.alp` (Robot agent Java blocks only)

---

## Background

Two compliance gaps identified against the conceptual note:

1. **Pedestrians are cosmetic.** Robot speed uses static node `crowdedness` only. Actual pedestrian agents in `main.pedestrians` have no effect on robot movement.
2. **EA fallback re-scoring is incomplete.** When `selectNextTask()` encounters a peer-claimed task and must re-score, it uses only travel + delivery time — omitting the lookahead and conflict penalty that define EA scoring.

---

## Fix 1 — Pedestrian Proximity → Robot Speed

### Constraint

The concept note specifies **offline planning**: routes are computed once at task selection and not revised during traversal. Pedestrian interaction is limited to **speed only** — no dynamic path replanning.

### New Function: `computeSpeed(NodeLoc target)`

Added to Robot's `<Functions>` block.

```java
double computeSpeed(NodeLoc target) {
    double pedCount = 0;
    for (Pedestrian p : main.pedestrians) {
        double d = Math.sqrt(Math.pow(p.getX() - target.x, 2)
                           + Math.pow(p.getY() - target.y, 2));
        if (d < 30.0) pedCount += 1.0;
    }
    return 10.0 / (1.0 + (target.crowdedness + pedCount * 0.5) * 0.5);
}
```

**Parameters:**
- Proximity radius: `30.0` px (= 6 m at 50 px/10 m scale)
- Per-pedestrian weight: `0.5` (each nearby pedestrian adds 0.5 to effective crowdedness; max static crowdedness is 8, so 5 peds ≈ +31% at peak zones)

**Formula consistency:** Matches the existing Dijkstra cost formula (`cost *= 1 + crowdedness * 0.5`), so the path cost estimate and the actual movement speed remain aligned.

### Call-site Replacements (4 locations in Robot)

All occurrences of:
```java
setSpeed(10.0 / (1.0 + goalNode.crowdedness * 0.5));
```
are replaced with:
```java
setSpeed(computeSpeed(goalNode));
```

| Location | State/Transition |
|---|---|
| `stGoToPickup` entry action | Moving to pickup node, first hop |
| `stDeliver` entry action | Moving to delivery node, first hop |
| `trDeliverLoop` action | Moving to delivery node, subsequent hops |
| `trDeliverReturn` action | Moving to next pickup (chained task) |

---

## Fix 2 — EA Fallback Re-scoring

### Problem

In `selectNextTask()`, after selecting the best EA task, a `while` loop removes peer-claimed tasks and re-scores. The fallback scorer (lines ~7056–7069) computes only:

```java
t2 = toPickup + delivery   // missing: lookahead + conflict penalty
```

This silently degrades EA to a weaker EV-style selector under contention.

### New Function: `scoreTaskEA(int[] task, NodeLoc robPos)`

Added to Robot's `<Functions>` block. Encapsulates the full EA scoring logic.

```java
double scoreTaskEA(int[] task, NodeLoc robPos) {
    NodeLoc pickup = main.globalNodes.get(task[0]);
    NodeLoc dest   = main.globalNodes.get(task[1]);

    // Travel + delivery leg
    double score = calculateExpectedTime(robPos, pickup, 1)
                 + calculateExpectedTime(pickup, dest, 1);

    // Lookahead: EV-weighted cost to nearest remaining task from dest
    double minNext = Double.MAX_VALUE;
    for (int[] nxt : localOrderList) {
        if (nxt == task) continue;
        double c = calculateExpectedTime(dest, main.globalNodes.get(nxt[0]), 1);
        if (c < minNext) minNext = c;
    }
    if (minNext == Double.MAX_VALUE)
        minNext = calculateExpectedTime(dest, main.globalNodes.get(0), 1);
    score += minNext;

    // Graduated conflict penalty
    for (int i = 0; i < main.numRobots; i++) {
        Robot other = main.getRobotByIndex(i);
        if (other == null || other == this || other.parDestinationNode == null) continue;
        double overlap = Math.sqrt(
            Math.pow(other.parDestinationNode.x - dest.x, 2) +
            Math.pow(other.parDestinationNode.y - dest.y, 2));
        if (overlap < main.conflictRadiusThreshold)
            score += main.conflictPenaltyWeight * (1.0 - overlap / main.conflictRadiusThreshold);
    }
    return score;
}
```

### Call-site Changes in `selectNextTask()`

**Primary EA loop** — replace inline body:
```java
// Before
double t = calculateExpectedTime(...) + calculateExpectedTime(...);
// + lookahead block
// + conflict penalty block
if (t + penalty < bestScore) { bestScore = ...; selectedTask = task; }

// After
double s = scoreTaskEA(task, robPos);
if (s < bestScore) { bestScore = s; selectedTask = task; }
```

**Fallback re-scoring loop** — replace incomplete body:
```java
// Before (incomplete)
double t2 = calculateExpectedTime(...) + calculateExpectedTime(...);
if (t2 < bestScore2) { bestScore2 = t2; selectedTask = task2; }

// After (full EA)
NodeLoc robPos2 = findClosestNode(getX(), getY());
double s2 = scoreTaskEA(task2, robPos2);
if (s2 < bestScore2) { bestScore2 = s2; selectedTask = task2; }
```

---

## Files Changed

| File | Change |
|---|---|
| `ColruytV5.0_IDE.alp` | Add `computeSpeed` and `scoreTaskEA` to Robot `<Functions>`; update 4 `setSpeed` call sites; refactor primary EA loop and fallback loop in `selectNextTask` |

No changes to `Main`, `NodeLoc`, `Pedestrian`, `Package`, or CSV logic.

---

## Out of Scope

- Dynamic path replanning based on pedestrian positions (breaks offline planning guarantee)
- Updating node `crowdedness` from real-time pedestrian counts
- SSP/EV task selection changes
