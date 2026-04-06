# Technical Reference: Exact Code Snippets & Visual Debugging Setup

## Part A: How to Add Text Display Elements (Visual Debugging)

### Section A.1: Add Text for Current State

**Steps in AnyLogic IDE:**

1. **Open DeliveryRobot class** → **Presentation** tab (bottom of screen)
2. **Double-click "level"** to edit the presentation
3. **Right-click in canvas** → **Appearance** → **Shape** → **Text**
4. Drag the Text shape somewhere above/beside the robot visual (e.g., X: -5, Y: -15)
5. **Name it**: `txt_state`

**Configure the Text Element:**

- **Text content** (property panel on right):
  - Display: **Combined**
  - Enter text: `"State: " + getActiveState()`
  
- **Position relative to agent**: Check **"Relative to agent"**
- **Font**: 12pt, bold, white color (RGB: 255,255,255)
- **Background**: Dark semi-transparent (for contrast)

**Add this helper method to DeliveryRobot:**

```java
public String getActiveState() {
    if (statechart.isStateActive("1773485639867")) {  // NAVIGATING
        return "NORMAL";
    } else if (statechart.isStateActive("1773485642114")) {  // BLOCKED
        return "STOP";
    } else if (statechart.isStateActive("1773485651106")) {  // ASSERTIVE_CRAWLING
        return "CRAWL";
    }
    return "?";
}
```

(Note: The numbers are the state IDs from your XML. If different in your file, replace with your actual IDs.)

---

### Section A.2: Add Text for Perception Distance

**Steps:**

1. Add another **Text shape** in the same Presentation level
2. **Name it**: `txt_distance`
3. Position below the state display (e.g., X: -5, Y: 0)

**Configure:**

- **Text content**:
  - Enter: `"Dist: " + (int)nearestPedDist + "m"`
  
- **Position relative to agent**: Yes
- **Font**: 10pt, white
- **Update rate**: Every frame (automatic)

**Visual Result on Screen:**
```
┌─────────────────┐
│ [ROBOT VISUAL]  │
│ State: NORMAL   │
│ Dist: 28m       │
└─────────────────┘
```

---

### Section A.3: Add Speed Display (Optional)

For extra transparency:

1. Add **Text shape**: `txt_speed`
2. **Text content**: `String.format("%.1f m/s", this.getSpeed())`
3. Position below distance display

**Visual Result:**
```
State: CRAWL
Dist: 18m
Speed: 0.3 m/s
```

---

## Part B: Statechart Condition & Action Code

### Section B.1: Transition Conditions (Copy-Paste Ready)

**Transition: NAVIGATING → BLOCKED**

- **Trigger**: Condition
- **Condition**:
```java
behaviorMode == 0 && nearestPedDist < 35
```

---

**Transition: NAVIGATING → ASSERTIVE_CRAWLING**

- **Trigger**: Condition
- **Condition**:
```java
behaviorMode == 1 && nearestPedDist < 35
```

---

**Transition: BLOCKED → NAVIGATING**

- **Trigger**: Condition
- **Condition**:
```java
nearestPedDist >= 35
```

---

**Transition: ASSERTIVE_CRAWLING → NAVIGATING**

- **Trigger**: Condition
- **Condition**:
```java
nearestPedDist >= 35
```

---

**Transition: ASSERTIVE_CRAWLING → BLOCKED** (Safety fallback)

- **Trigger**: Condition
- **Condition**:
```java
nearestPedDist < 20
```

---

### Section B.2: State Entry Actions (On Enter)

**State: NAVIGATING**

```java
// Optional: Log state entry
int logLevel = blue;  // AnyLogic color constant
traceln(logLevel, "[t=" + String.format("%.1f", time()) + 
    "s] Robot NAVIGATING at " + 
    String.format("%.1f", cruiseSpeed) + " m/s");
```

---

**State: BLOCKED** (Reactive baseline only)

```java
freezeCount++;
int logLevel = red;
traceln(logLevel, "[t=" + String.format("%.1f", time()) + 
    "s] Robot STOPPED! Pedestrian at " + 
    String.format("%.1f", nearestPedDist) + "m. Freeze #" + freezeCount);
```

---

**State: ASSERTIVE_CRAWLING**

```java
int logLevel = blue;
traceln(logLevel, "[t=" + String.format("%.1f", time()) + 
    "s] Robot CRAWLING. Obstacle at " + 
    String.format("%.1f", nearestPedDist) + "m. " +
    "Continuing forward at " + 
    String.format("%.1f", crawlSpeed) + " m/s");
```

---

## Part C: Perception Event Code (Full Implementation)

### Section C.1: Complete Cyclic Event Action

**Event**: `event` (cyclic, every 0.05 seconds)

**Action Code:**

```java
// ========================================
// SECTION A: PERCEPTION LOGIC
// ========================================
// Skip if robot is loading/unloading
if (time() < loadingPauseUntil) return;

// Scan 1: FORWARD CONE (±60° from heading)
double nearestFwdDist = scanRadius;
double nearestFwdAngle = 0;

// Scan 2: OMNIDIRECTIONAL (all directions)
double nearestAnyDist = scanRadius;
double nearestAnyAngle = 0;

for (PedestrianAgent ped : main.pedestrians) {
    double dx = ped.getX() - getX();
    double dy = ped.getY() - getY();
    double rawDist = Math.sqrt(dx * dx + dy * dy);
    
    if (rawDist < scanRadius) {
        double pedAngle = Math.atan2(dy, dx);
        
        // Update omnidirectional scan
        if (rawDist < nearestAnyDist) {
            nearestAnyDist = rawDist;
            nearestAnyAngle = pedAngle;
        }
        
        // Check if pedestrian is in forward cone (±60°)
        double relAngle = pedAngle - heading;
        // Normalize to [-π, π]
        while (relAngle > Math.PI) relAngle -= 2 * Math.PI;
        while (relAngle < -Math.PI) relAngle += 2 * Math.PI;
        
        if (Math.abs(relAngle) < Math.PI / 3.0) {  // ±60°
            if (rawDist < nearestFwdDist) {
                nearestFwdDist = rawDist;
                nearestFwdAngle = pedAngle;
            }
        }
    }
}

// UPDATE STATE TRANSITION VARIABLE:
// Reactive: uses omnidirectional; Assertive: uses forward-cone
if (behaviorMode == 0) {
    this.nearestPedDist = nearestAnyDist;
} else {
    this.nearestPedDist = nearestFwdDist;
}


// ========================================
// SECTION B: SPEED DECISION
// ========================================
double currentSpeed = cruiseSpeed;
double stopDist = 20.0;   // Threshold for full stop
double slowDist = 35.0;   // Threshold for gradual slowdown

if (behaviorMode == 0) {
    // REACTIVE MODE: Respond to ALL pedestrians (omnidirectional)
    if (nearestAnyDist < stopDist) {
        currentSpeed = 0.0;  // FULL STOP
    } else if (nearestAnyDist < slowDist) {
        // Gradual slowdown between stop and slow thresholds
        double progress = (nearestAnyDist - stopDist) / 
                         (slowDist - stopDist);  // 0 to 1
        currentSpeed = crawlSpeed + 
                      (cruiseSpeed - crawlSpeed) * progress;
    }
    // else: maintain cruiseSpeed
} else {
    // ASSERTIVE MODE: Respond only to forward-cone pedestrians
    if (nearestFwdDist < stopDist) {
        currentSpeed = crawlSpeed;  // Crawl, NOT stop
    } else if (nearestFwdDist < slowDist) {
        // Gradual slowdown
        double progress = (nearestFwdDist - stopDist) / 
                         (slowDist - stopDist);
        currentSpeed = crawlSpeed + 
                      (cruiseSpeed - crawlSpeed) * progress;
    }
    // else: maintain cruiseSpeed
}


// ========================================
// SECTION C: MOVEMENT KINEMATICS
// ========================================

// Calculate desired heading (toward delivery target)
double desired = Math.atan2(
    targetY - getY(), 
    targetX - getX()
);

// Wall avoidance: nudge away from street edges
double distTop = getY() - main.streetY;
double distBot = (main.streetY + main.streetWidth) - getY();
if (distTop < 5) desired += 0.3;  // nudge away from top wall
if (distBot < 5) desired -= 0.3;  // nudge away from bottom wall

// Lateral avoidance: dodge perpendicular to world-frame goal
// (not turn backward; sidestep instead)
if (nearestFwdDist < slowDist) {
    double obstRelative = nearestFwdAngle - desired;
    // Which side is the obstacle on relative to the goal direction?
    double dodgeSign = (Math.sin(obstRelative) >= 0) ? -1 : 1;
    
    // Magnitude: closer obstacle = larger dodge
    double proximity = 1.0 - (nearestFwdDist / slowDist);
    
    // Max dodge angle: aggressive in reactive, gentle in assertive
    double maxDodge = (behaviorMode == 1) ? 
                      Math.PI / 8 :   // 22.5° for assertive
                      Math.PI / 5;    // 36° for reactive
    
    desired = desired + dodgeSign * maxDodge * proximity;
}

// Smooth heading update (max turn rate constraint)
double diff = desired - heading;
// Normalize diff to [-π, π]
while (diff > Math.PI) diff -= 2 * Math.PI;
while (diff < -Math.PI) diff += 2 * Math.PI;

double maxTurn = 0.08;  // radians per 0.05s time step
heading += Math.max(-maxTurn, Math.min(maxTurn, diff));

// Compute candidate position using current speed
double dt = 0.05;  // time step (seconds)
double candidateX = getX() + currentSpeed * dt * Math.cos(heading);
double candidateY = getY() + currentSpeed * dt * Math.sin(heading);

// Clamp to street bounds (avoid going outside walls)
candidateY = Math.max(main.streetY + 3,
    Math.min(main.streetY + main.streetWidth - 3, candidateY));


// ========================================
// SECTION D: COLLISION CLAMP
// ========================================
// Safety net: Check if moving to candidate position would
// collide with ANY pedestrian (omnidirectional check).
// This prevents the robot from moving into anyone even if
// the forward-cone perception missed them.

double clampRadius = 16.0;  // exclusion zone around robot
boolean canMove = true;

for (PedestrianAgent ped : main.pedestrians) {
    double px = candidateX - ped.getX();
    double py = candidateY - ped.getY();
    double dist = Math.sqrt(px * px + py * py);
    if (dist < clampRadius) {
        canMove = false;
        break;  // No need to check further
    }
}

if (canMove) {
    setXY(candidateX, candidateY);
} else {
    // Don't move, but heading WAS updated above
    // so next tick the robot may steer around the obstacle
}


// ========================================
// SECTION E: DELIVERY WORKFLOW
// ========================================
// Check if robot has reached its destination

boolean hasArrived = 
    (!isReturning && getX() >= targetX - 10) || 
    (isReturning && getX() <= targetX + 10);

if (hasArrived) {
    if (!isReturning) {
        // DELIVERY COMPLETED (reached customer location)
        double deliveryTime = time() - startTime;
        
        // Log metrics
        main.deliveryTimeData.add(deliveryTime);
        main.freezeCountData.add(freezeCount);
        main.completedOrders++;
        
        traceln(green, "✓ Delivery completed! Time: " +
            String.format("%.1f", deliveryTime) + "s, " +
            "Freezes: " + freezeCount + ", " +
            "Total deliveries: " + main.completedOrders);
        
        // Write to CSV
        try (java.io.PrintWriter out = 
             new java.io.PrintWriter(
                new java.io.FileWriter(
                    "experiment_results.csv", true))) {
            out.println(String.format(
                java.util.Locale.US,
                "%.1f,%d,%d,%d,%d,%.1f",
                time(), 
                behaviorMode, 
                main.numPedestrians, 
                main.completedOrders,
                freezeCount, 
                deliveryTime
            ));
        } catch (java.io.IOException e) {
            traceln(red, "CSV write error: " + e.getMessage());
        }
        
        // Begin return trip
        isReturning = true;
        targetX = 5;
        heading = Math.PI;  // Face left
        freezeCount = 0;
        loadingPauseUntil = time() + 15.0;  // Unload 15s
        traceln("Unloading pause (15s)...");
        
    } else {
        // RETURN TRIP COMPLETE (picked up new order)
        isReturning = false;
        targetX = main.streetLength - 5;  // Right edge
        heading = 0;  // Face right
        freezeCount = 0;
        startTime = time() + 30.0;  // Timer starts after loading
        loadingPauseUntil = time() + 30.0;  // Load 30s
        traceln("Loading pause (30s)...");
    }
}
```

---

## Part D: How to Configure Fixed Random Seed

### Method 1: Via GUI (Experiment Settings)

1. **In AnyLogic IDE**, go to **Simulation** menu → **Multiple Runs Configuration**
2. **Under "Advanced" tab:**
   - Find "Random seed" parameter
   - Change from **`<<auto>>`** to **`12345`** (or any fixed integer)
3. **Click OK** and run simulation

**Effect**: Every run of this experiment will produce identical pedestrian trajectories because the random number generator starts at the same seed.

---

### Method 2: Programmatically (In Main Startup Code)

Add this to the **Main class** startup code:

```java
// Fix random seed for reproducibility
randomSeed(12345);
traceln(green, "========================================");
traceln(green, "FIXED RANDOM SEED: 12345");
traceln(green, "Simulation is REPRODUCIBLE.");
traceln(green, "========================================");
```

---

### Method 3: Batch Runs with Multiple Seeds

**For Monte Carlo analysis:**

1. Open **Simulation** → **Multiple Runs Configuration**
2. **Replication settings**:
   - Number of replications: `10`
   - Random seed: **`<<auto>>`** (let AnyLogic vary it)
3. This will run 10 times with seeds: 0, 1, 2, ..., 9

**Results**: Each replication is different (good statistics), but run #5 of condition A will always differ from run #5 of condition B (different design).

---

### Verification Checklist

- [ ] Run simulation twice with same seed
- [ ] Compare output files: `experiment_results.csv` should be identical
- [ ] (Optional) Print first 5 pedestrian positions at t=1.0s; should match exactly

---

## Part E: How to Setup Multiple Runs (Batch Experiment)

### Create a Batch Experiment

1. **Right-click in Model structure** (left panel) → **Add** → **Experiment**
2. **Type**: Batch (or Simulation with multiple runs)
3. **Name**: `exp_batch`

### Configure the Sweep

**Parameters to vary:**

| Parameter | Baseline | Intervention | Values |
|-----------|----------|--------------|--------|
| `behaviorMode` | 0 | 1 | {0, 1} |
| `numPedestrians` | (fixed) | (fixed) | {100} |

**Replications**: 10 per condition

### Data Collection

AnyLogic will automatically:
- Run 10 times with `behaviorMode=0`, seeds 0-9
- Run 10 times with `behaviorMode=1`, seeds 0-9
- Collect metrics in `deliveryTimeData`, `freezeCountData`
- Append to `experiment_results.csv`

---

## Part F: Example Output Format (experiment_results.csv)

**Expected headers** (add this line manually to the CSV file first):
```
time,behaviorMode,numPedestrians,completedOrders,freezeCount,deliveryTime
```

**Example data rows:**
```
123.5,0,100,1,3,123.5
156.2,0,100,2,1,32.7
185.1,0,100,3,5,29.9
203.8,1,100,1,0,203.8
220.5,1,100,2,0,16.7
232.1,1,100,3,1,11.6
```

### Interpretation
- **behaviorMode=0** (Reactive): Higher freezeCount (3, 1, 5)
- **behaviorMode=1** (Assertive): Lower freezeCount (0, 0, 1)
- Suggests Assertive mode reduces deadlock situations ✓

---

## Part G: Common Configuration Issues & Solutions

### Issue 1: Robot Doesn't Change Speed

**Symptom**: Robot always moves at `cruiseSpeed`, states never transition.

**Diagnosis**:
```java
// Check: is perception event firing?
traceln("nearestPedDist = " + nearestPedDist);  // Add to event
```

**Solution**:
- Verify event is **cyclic** at 0.05s interval
- Verify event code is saved and compiled (no red X markers)
- Check that **Pedestrian Library is imported** (might need extension install)

---

### Issue 2: Pedestrians Walk Through Robot

**Symptom**: Robot visual and pedestrians occupy same space.

**Diagnosis**:
- Robot's physical dimensions may be 0

**Solution**:
  In **DeliveryRobot** → **Properties** → **Agent Properties**:
  ```
  Physical Length: 1 meter
  Physical Width: 1 meter
  ```

---

### Issue 3: CSV File Not Updating

**Symptom**: `experiment_results.csv` stays empty or isn't created.

**Diagnosis**:
- File path may be wrong
- I/O permissions issue

**Solution**:
  Update file path in event code:
  ```java
  // Absolute path (Windows)
  String filePath = "C:\\Colruyt\\experiment_results.csv";
  
  // Absolute path (macOS)
  String filePath = System.getProperty("user.home") + 
                     "/Desktop/experiment_results.csv";
  
  try (java.io.PrintWriter out = 
       new java.io.PrintWriter(new java.io.FileWriter(filePath, true))) {
      // ... write line
  }
  ```

---

### Issue 4: Text Overlay Not Showing

**Symptom**: State and distance text not visible.

**Diagnosis**:
- Text binding expression may be wrong
- Text position may be off-screen

**Solution**:
1. **Edit text shape**:
   - Double-click in Presentation
   - Under **"Text content"** section:
   - Try simple text first: `"TEST"`
   - Verify it appears
2. Then switch to binding:
   - **Display**: `Combined`
   - **Text**: `"State: " + getActiveState()`

---

## Part H: Performance Tuning

### If Simulation Runs Slow

1. **Reduce pedestrian count**: `numPedestrians = 50` (test mode)
2. **Increase scan interval**: Change cyclic event to `0.1s` instead of `0.05s`
3. **Reduce scan radius**: `scanRadius = 20.0` (less agents to check each tick)

### If You Need Real-Time Data

- Use **data collection** (automatic in AnyLogic)
- Export to CSV at end of run (not every tick)
- Use **buffered I/O** for large batches

---

## Part I: Debugging Checklist

Before running full experiment:

- [ ] Open **Simulation** → **Trace** window
- [ ] Set **Trace level** to "Everything"
- [ ] Run one short simulation (e.g., 5 seconds)
- [ ] Verify trace output shows:
  - `"[t=0.1s] Robot NAVIGATING..."`
  - `"[t=0.15s] Robot CRAWLING. Obstacle at 25.3m."`
  - `"✓ Delivery completed! Time: 150.2s, ..."`

- [ ] Verify `experiment_results.csv` has one line (one delivery)

If trace shows nothing:
- Check event is enabled (checkbox should be checked)
- Check no compile errors (red X in model structure)
- Restart AnyLogic

---

## Summary Checklist: Ready for Presentation?

- [ ] Model compiles (no red errors)
- [ ] Two behavior modes runnable (`behaviorMode = 0 and 1`)
- [ ] Text overlay shows current state and perception distance
- [ ] Fixed seed set (e.g., `randomSeed(12345)`)
- [ ] CSV file generated with delivery metrics
- [ ] Batch experiment configured (10 runs per condition)
- [ ] Statistics computed (mean, std dev of delivery times, freezes)
- [ ] Trace output explains robot decisions
- [ ] Animation visually shows difference between behaviors

**You're ready! ✓**
