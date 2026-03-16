# Quick-Start: Visual Debugging Setup (5 Minutes)

## Goal
Add live text overlays to show the robot's **current state** and **perception distance** for presentation and debugging.

---

## Step 1: Add Helper Functions to DeliveryRobot (30 seconds)

In **DeliveryRobot** class, go to **Code Editor** and add these functions at the end:

```java
/**
 * Returns the human-readable name of the current active state.
 * Used by text overlay to display state name.
 */
public String getActiveState() {
    if (statechart.isStateActive(1773485639867)) {
        return "NORMAL";  // NAVIGATING state
    } else if (statechart.isStateActive(1773485642114)) {
        return "STOP";     // BLOCKED state
    } else if (statechart.isStateActive(1773485651106)) {
        return "CRAWL";    // ASSERTIVE_CRAWLING state
    }
    return "?";
}

/**
 * Returns formatted string for perception distance.
 */
public String getDistanceString() {
    return String.format(java.util.Locale.US, "%.1f m", nearestPedDist);
}

/**
 * Returns current speed.
 */
public String getSpeedString() {
    return String.format(java.util.Locale.US, "%.2f m/s", this.getSpeed());
}
```

**Note**: The numbers (1773485639867, etc.) are state IDs. If your IDs are different:
- Open **Colruyt.alp** in a text editor
- Search for `<Name><![CDATA[NAVIGATING]]></Name>` 
- Look for `<Id>XXXXX</Id>` immediately above it
- Replace the numbers in the code above

---

## Step 2: Add Text Shapes to Presentation (2 minutes)

### Part A: Open the Presentation Editor

1. **Click on DeliveryRobot** in model structure (left panel)
2. At bottom, click **Presentation** tab
3. **Double-click** on "level" to open presentation editor
4. You should see a white canvas with a lorry visual (3D model)

### Part B: Add State Display Text

1. **Right-click** on empty canvas area
2. Choose **Appearance** → **Shape** → **Text**
3. Drag to create a text box (somewhere near the robot, e.g., upper-left)

**Configure this text box:**

| Property | Value |
|----------|-------|
| **Name** | `txt_state` |
| **Position** | X: -8, Y: -25 |
| **Size** | W: 80, H: 20 |
| **Text Content** | (next section) |
| **Font Size** | 14 |
| **Font** | Bold |
| **Text Color** | White (RGB: 255,255,255) |
| **Background Color** | Dark blue with transparency |
| **Position Type** | **Relative to agent** (checkmark!) |

### Configure Text Content:

1. In the properties panel, find **"Text content"** 
2. Under **Display**, select **"Combined"**
3. In the **"Text"** field, enter:
```
"State: " + getActiveState()
```

### Part C: Add Distance Display Text

1. Right-click canvas → **Appearance** → **Shape** → **Text**
2. Position below the state text (e.g., X: -8, Y: -5)

| Property | Value |
|----------|-------|
| **Name** | `txt_distance` |
| **Text Content** | `"Ped Dist: " + getDistanceString()` |
| **Display** | Combined |
| **Position** | X: -8, Y: -5 |
| **Font Size** | 12 |
| **Relative to agent** | ✓ Yes |

### Part D: (Optional) Add Speed Display

1. Right-click canvas → **Appearance** → **Shape** → **Text**
2. Position below distance text (e.g., X: -8, Y: 10)

| Property | Value |
|----------|-------|
| **Name** | `txt_speed` |
| **Text Content** | `"Speed: " + getSpeedString()` |
| **Display** | Combined |
| **Font Size** | 11 |

---

## Step 3: Test the Visualization (1 minute)

1. **Close** the presentation editor
2. **Compile** the model (Ctrl+K or Command+K)
3. **Run** the simulation
4. **Watch the main canvas**:
   - You should see the robot moving
   - Text overlay appears above it showing:
     ```
     State: NORMAL
     Ped Dist: 30.5 m
     Speed: 1.50 m/s
     ```

5. When robot approaches pedestrians, text should change:
   ```
     State: CRAWL
     Ped Dist: 18.2 m
     Speed: 0.45 m/s
   ```

---

## Step 4: Adjust Appearance (Optional)

If text is hard to read:

1. Go back to **Presentation** editor
2. Click on any text shape
3. In properties panel:
   - **Text Color**: Try yellow (RGB: 255,255,0) or white
   - **Background**: Dark (RGB: 0,0,0) with opacity ~0.7
   - **Font**: Arial or Courier, bold

**Visual result:**

```
┌─────────────────────┐
│    [ROBOT VISUAL]   │
│  State: CRAWL       │
│  Ped Dist: 18.2 m   │
│  Speed: 0.45 m/s    │
└─────────────────────┘
```

---

## Step 5: Verify Both Behaviors Work Visually

### Test Case A: Reactive Mode

1. Set **Main parameter**: `behaviorMode = 0`
2. Run simulation
3. Watch text as robot approaches crowd:
   - Should see: **State: STOP** (frequent)
   - Robot visibly halts
   - FreezCount increments

### Test Case B: Assertive Mode

1. Change: `behaviorMode = 1`
2. Run same simulation
3. Watch text:
   - Should see: **State: CRAWL** (more frequent)
   - **State: STOP** (rarely)
   - Robot keeps moving even at close distance

---

## Troubleshooting Visual Display

| Problem | Solution |
|---------|----------|
| Text not showing | Check "Relative to agent" is **enabled** |
| Text shows "?" | State IDs don't match; check XML file for correct IDs |
| Text stuck on old value | Check that `Combined` display mode is selected |
| Text too small/big | Adjust Font Size in properties (10-14 is good) |
| Background too dark | Adjust opacity in color selector |

---

## Advanced: Change Text Style Dynamically

**If you want State text color to change based on state:**

1. Add this method to **DeliveryRobot**:

```java
public java.awt.Color getStateColor() {
    if (statechart.isStateActive(1773485639867)) {
        return new java.awt.Color(0, 255, 0);  // Green = NORMAL
    } else if (statechart.isStateActive(1773485642114)) {
        return new java.awt.Color(255, 0, 0);  // Red = STOP
    } else if (statechart.isStateActive(1773485651106)) {
        return new java.awt.Color(255, 165, 0); // Orange = CRAWL
    }
    return new java.awt.Color(255, 255, 255);  // White default
}
```

2. In presentation, set text color binding:
   - **"Text color"** → `getStateColor()`

**Result**: Text automatically changes color:
- **Green** when NORMAL
- **Red** when STOP
- **Orange** when CRAWL

---

## Next Checkpoint: Fixed Seed for Reproducibility

Once visuals are working:

1. Open **Main class** → **Code Editor**
2. In **Startup Code**, add:
```java
randomSeed(12345);
traceln(green, "✓ Seed 12345 - REPRODUCIBLE");
```

3. Run twice → should get identical pedestrian paths

---

## Final Verification Before Presentation

Checklist:

- [ ] Text displays current state (NORMAL, STOP, CRAWL)
- [ ] Text displays perception distance in real time
- [ ] Reactive mode shows frequent STOP states
- [ ] Assertive mode shows frequent CRAWL states
- [ ] Fixed seed produces identical results on re-run
- [ ] CSV file captures delivery times and freeze counts
- [ ] Animation is clear enough for non-technical audience

**Next**: See `TECHNICAL_REFERENCE.md` for detailed code snippets and fixed seed instructions.
