# Colruyt Collect&Go: Delivery Robot Behavioural Sensitivity Analysis

**Course:** Multi-Agent Systems (H02H4a) — KU Leuven, 2026  
**Platform:** AnyLogic 8.9.8+

## Scenario

This agent-based model simulates **autonomous delivery robots** (Colruyt Collect&Go) navigating a shared pedestrian street. We test the **behavioural sensitivity** of two robot intervention strategies:

- **Reactive (mode 0):** The robot uses omnidirectional detection — it stops for pedestrians approaching from *any* direction. This models the overcautious planner that leads to the *Freezing Robot Problem* (Trautman & Krause, 2010).
- **Assertive (mode 1):** The robot uses a forward-cone (±60°) detection — it only stops/slows for pedestrians *ahead*, trusting others to cooperate. This implements joint collision avoidance (Kretzschmar et al., 2016).

A secondary axis tests **coordination mode** for multi-robot scenarios:
- **Centralized (mode 0):** Leader-follower convoy managed by a MasterController.
- **Decentralized (mode 1):** Robots negotiate yield priority based on distance-to-goal.

## Agent Types

| Agent | Description | Key Parameters |
|-------|-------------|----------------|
| `DeliveryRobot` | Autonomous delivery vehicle | `behaviorMode`, `cruiseSpeed`, `crawlSpeed`, `scanRadius` |
| `PedestrianAgent` | Heterogeneous pedestrian | `speed` (0.8–1.8), `comfortDistance` (4–8), `turnRate` (0.06–0.14) |
| `MasterController` | Centralized coordinator | Leader-follower convoy logic |

## KPIs

1. **Delivery time** — Time for robot to traverse the street
2. **Freeze count** — Number of full-stop events
3. **Pedestrian deviation** — Average displacement from intended path
4. **Average pedestrian speed** — Measure of pedestrian disruption
5. **Minimum robot-pedestrian distance** — Safety metric

## How to Run

### Interactive Simulation
1. Open `AnyLogic/Colruyt.alp` in AnyLogic 8.9.8+
2. Run the **Simulation** experiment
3. Adjust `behaviorMode` (0=reactive, 1=assertive) and `numPedestrians` in the experiment parameters

### Batch Experiments
1. Run the **BehaviorSensitivity** experiment (Parameter Variation)
2. This sweeps `behaviorMode` ∈ {0, 1} × `numPedestrians` ∈ {25, 50, 100, 150, 200} × 30 replications
3. Results are logged via `traceln()` — check the AnyLogic console output

## Literature

- Trautman, P. & Krause, A. (2010). *Unfreezing the robot: Navigation in dense, interacting crowds.*
- Kretzschmar, H. et al. (2016). *Socially compliant mobile robot navigation via inverse reinforcement learning.*
- Ferrer, G. et al. (2019). *Robot social-aware navigation framework.*
- Claes, D. et al. (2017). *Decentralised online planning for multi-robot warehouse commissioning.*
- Clark, C.M. & Rock, S.M. (2004). *Dynamic robot networks.*
