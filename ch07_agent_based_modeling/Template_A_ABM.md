# ABM Template A: Agent and Environment Spec (ODD Protocol)

Everything the model needs to know about agent types, behavioral rules, interaction mechanisms, and the environment. Fill this out before writing any Mesa code.

Unlike the Template A's in Chapters 4–6, this template is not a structure of our own design. It follows the **ODD protocol** (Overview, Design concepts, Details), the agent-based modeling community's standard for describing ABMs (Grimm et al. 2006; updated 2010 and 2020). Monte Carlo, DES, and system dynamics have no community-standard specification format, so we built our own. ABM does — hundreds of published models use it — so Template A adopts it. A spec written this way can be checked against published models, shared with practitioners who already know the format, and archived alongside models in repositories like CoMSES/OpenABM.

Two sections are book additions, not part of ODD proper, and are marked as such: Section 0 (Business Context) frames the decision for stakeholders before the formal spec begins, and Section 8 (Simulation Experiments) records the experiment design — scenarios, replications, seeds — which ODD deliberately leaves out because it describes the *model*, not the *runs*.

**Key difference from previous Template A's:** The spec defines agent behaviors and interactions rather than input distributions (MC), process flows (DES), or feedback loops (SD). The output isn't a single distribution (MC), wait-time statistics (DES), or deterministic trajectories (SD). It's a distribution of emergent outcomes across replications of an interactive system.

## Template Structure at a Glance

| Block | Element | What it answers |
|-------|---------|-----------------|
| *(book addition)* | 0. Business Context | What decision is this model for? |
| **O**verview | 1. Purpose and Patterns | Why does the model exist, and what observed patterns will tell us it's credible? |
| **O**verview | 2. Entities, State Variables, and Scales | Who and what is in the model, described by which variables, at what resolution? |
| **O**verview | 3. Process Overview and Scheduling | What happens each time step, in what order? |
| **D**esign concepts | 4. Design Concepts | The eleven-item checklist: emergence, adaptation, sensing, and so on |
| **D**etails | 5. Initialization | What does the world look like at step 0? |
| **D**etails | 6. Input Data | Does external data drive the model during the run? |
| **D**etails | 7. Submodels | The full logic and parameters of every process named in Element 3 |
| *(book addition)* | 8. Simulation Experiments | Scenarios, replications, seeds, and outputs to record |

---

## Section 0: Business Context *(book addition — not part of ODD)*

**Business Question**
```
[Write the market-level or system-level question. One or two sentences.
Good ABM questions involve competitive dynamics, emergent outcomes,
or "what happens when many actors interact?"]
```

**Decision and Decision-Maker**
```
[Who will act on this model's results, and what choice are they facing?]
```

**Scenarios to Compare**

| Scenario | Description | What Changes |
|----------|-------------|-------------|
| | | |
| | | |
| | | |

**Key Assumptions**
```
1. [Assumption]
2. [Assumption]
3. [Assumption]
```

---

## Element 1: Purpose and Patterns

**Purpose** — one or two sentences, in the form "This model was built to [answer/explain/predict] ..." The purpose is the model's contract: every entity, variable, and rule in the rest of the spec should be traceable to it. If a proposed feature doesn't serve the purpose, it doesn't go in the model.

```
[Purpose statement]
```

**Patterns** — the macro-level patterns you expect the model to reproduce. These are the model's credibility criteria: if the model can reproduce them, it is realistic enough for its purpose. Some are empirical (observed in the real system or reported in the literature); others are expected emergent outcomes (hypotheses to test, not outcomes to engineer). Every pattern listed here becomes a validation row in Template C.

| # | Pattern | Type (empirical / expected) | How We'll Check It |
|---|---------|-----------------------------|--------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

---

## Element 2: Entities, State Variables, and Scales

**Entities** — every kind of thing in the model. Typical entity kinds: agent types, spatial units (grid cells), the environment itself, and collectives (groups of agents that act as a unit, if any).

```
Agent types:     [list]
Spatial units:   [e.g., grid cells with environmental variables]
Environment:     [global variables, if any]
Collectives:     [groups that act as units, or "none"]
```

### Agent Type 1: [Name]

**Population:** [count; how the count is set]

**Attributes** (fixed at initialization):

| Attribute | Distribution / Value | Description |
|-----------|---------------------|-------------|
| | | |
| | | |

**State variables** (change during simulation):

| State Variable | Initial Value | Updated By (submodel) | Description |
|----------------|--------------|----------------------|-------------|
| | | | |
| | | | |

### Agent Type 2: [Name]

*[Repeat the same structure for each agent type]*

### Spatial Units and Environment

```
Space type:    [Grid / Network / Continuous / Abstract]
Dimensions:    [e.g., 50×50 grid]
Topology:      [e.g., toroidal wrap / bounded edges]
```

**Environmental variables** (if any):

| Variable | Spatial Pattern | Static or Dynamic | Description |
|----------|----------------|-------------------|-------------|
| | | | |

### Scales

```
One step represents:   [e.g., one day]
Run length:            [e.g., 365 steps = one year]
One grid cell spans:   [e.g., ~20 m × 20 m]
Spatial extent:        [e.g., 50×50 cells ≈ 1 km² neighborhood]
```

---

## Element 3: Process Overview and Scheduling

What happens each time step, in what order. This element is the skeleton of the model's `step()` method, and it forces decisions the previous version of this template left implicit: Does state decay before or after agents act? Do adaptive agents respond before or after the entities they respond to have moved? Ordering changes results — decide it here, not in the code.

Name each process; each named process gets a full definition in Element 7 (Submodels), and each becomes a separately named method in the generated code.

**Per-step schedule:**

```
Each step:
1. [process_name]  — [which entities, one-line description]
2. [process_name]  — [which entities, one-line description]
3. [process_name]  — [which entities, one-line description]
...
Every N steps (after step processes complete):
5. [process_name]  — [e.g., shops evaluate and adapt]
```

**Scheduling decisions:**

```
Activation order:   [Random / Simultaneous / Staged — and why]
State updates:      [Immediate (agent sees others' current-step changes)
                     or synchronous (all changes applied at step end)]
Periodic processes: [what fires on longer cycles, and at which point
                     in the step they execute]
```

---

## Element 4: Design Concepts

The ODD checklist of eleven concepts. The first seven are core for business ABMs — fill in every one. The last four are optional; "not used" is a legitimate and informative answer (it tells a reader what the model deliberately excludes). A reference table with one-line definitions of all eleven appears at the end of this template.

### Core concepts

**Emergence** — Which model outcomes emerge from agent interactions rather than being imposed by rules? (These should connect to the patterns in Element 1.)
```
[...]
```

**Adaptation** — Which agents change their behavior in response to conditions, what triggers the change, and how often?
```
[...]
```

**Objectives** — What is each agent type trying to achieve, and how is success measured inside the agent's decision rule? (For utility-based choice: what does the utility function reward and penalize, and why is that a plausible model of the real actor's goals?)
```
[...]
```

**Sensing** — What can each agent type perceive, about which other entities, over what range? What can it NOT see? Unstated sensing assumptions are one of the most common sources of unintended model behavior — if the spec doesn't say what agents know, the code generator will decide for you.
```
[...]
```

**Interaction** — How do agents affect each other? Categorize as direct (agent acts on agent), indirect (mediated through the environment or shared state), and social (information or influence transmission).

| Interaction | Type (direct/indirect/social) | From → To | Mechanism | Effect |
|-------------|-------------------------------|-----------|-----------|--------|
| | | | | |
| | | | | |

**Stochasticity** — Every use of randomness in the model, and why randomness is the right choice there (representing true variability vs. standing in for unmodeled detail).

| Random Element | Where It Occurs | Why Stochastic |
|----------------|-----------------|----------------|
| | | |
| | | |

**Observation** — What is measured, at what level, at what frequency. This is a modeling decision, not a coding detail: the observation list should be driven by the patterns in Element 1 and the business question in Section 0. It becomes the DataCollector configuration in Template B.

```
Model-level (each step):   [...]
Agent-level (each step or on demand):   [...]
End-of-run only:           [...]
```

### Optional concepts

**Basic principles** — What established theory or accepted reasoning does the model build on (discrete choice, satisficing, reinforcement, queueing intuition)? Or "none — rules are ad hoc and justified in Element 7."
```
[...]
```

**Learning** — Do agents change their decision *rules* over time based on experience (not just their state)? Or "not used."
```
[...]
```

**Prediction** — Do agents forecast future conditions when deciding? Note tacit predictions too: a rule like "cut price when revenue falls" tacitly predicts that cutting price restores revenue. Or "not used."
```
[...]
```

**Collectives** — Do agents form groups that behave as units (firms, coalitions, flocks)? Or "not used."
```
[...]
```

---

## Element 5: Initialization

What the world looks like at step 0, in enough detail that two people would build the same starting state.

```
Total agents:           [count by type]
Spatial placement:      [how agents are positioned]
Attribute assignment:   [drawn from the distributions in Element 2]
Initial state values:   [starting values for every state variable]
Varies across runs?     [Which initial values are re-drawn per replication,
                         and which are fixed across all runs]
From data?              [Is any part of initialization read from data,
                         or is it all set by assumption?]
```

---

## Element 6: Input Data

External data that drives the model *during* the run — time series of weather, demand, prices, foot traffic. This is distinct from initialization data (Element 5) and from parameter values (Element 7).

```
[Describe each input data source, its resolution, and how it enters
the model — or state "None. The model is driven entirely by its
internal rules and parameters." A "none" answer is informative: it
tells the reader every dynamic in the results was generated by the
model itself.]
```

---

## Element 7: Submodels

The full definition of every process named in Element 3. This is the longest element and the most important one to get right: the choice/decision submodel is the heart of an ABM spec. Each submodel gets a name (which becomes its method name in code), a trigger, its logic in pseudocode or equations, and a parameter table with values and justifications. If a parameter appears in a submodel but not in a parameter table, the spec is incomplete.

### Submodel: [name]

**Executed by / when:** [entity type; where it appears in the Element 3 schedule]

**Logic:**
```
[Pseudocode or equations]
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| | | | |
| | | | |

### Submodel: [name]

*[Repeat for every process in the Element 3 schedule]*

---

## Section 8: Simulation Experiments *(book addition — not part of ODD)*

ODD describes the model; this section describes how you'll run it. Scenarios here should match the table in Section 0, now expressed as concrete parameter settings.

**Scenario parameterization:**

| Parameter | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 4 |
|-----------|-----------|-----------|-----------|-----------|
| | | | | |
| | | | | |

**Run design:**

```
Steps per run:    [from Element 2 scales]
Replications:     [e.g., 30 per scenario; justify in Template C
                   convergence check]
Random seeds:     [e.g., sequential from base seed 42]
Warm-up:          [steps excluded from measurement, if any]
Outputs recorded: [reference the Observation list in Element 4]
```

---

## Reference: The Eleven ODD Design Concepts

| Concept | One-Line Definition |
|---------|---------------------|
| Basic principles | The general theories or accepted reasoning the model builds on |
| Emergence | Outcomes that arise from interactions rather than being imposed by rules |
| Adaptation | How agents change behavior in response to their state or environment |
| Objectives | What agents seek, as measured inside their decision rules |
| Learning | How agents change their decision rules themselves over time |
| Prediction | How agents estimate future conditions (explicitly or tacitly) when deciding |
| Sensing | What agents can perceive, about whom, over what range |
| Interaction | How agents affect one another, directly or through the environment |
| Stochasticity | Where and why the model uses randomness |
| Collectives | Agent groups that behave as units |
| Observation | What is measured from the model, at what level and frequency |

---

## References

- Grimm, V., et al. (2006). "A standard protocol for describing individual-based and agent-based models." *Ecological Modelling*, 198(1–2), 115–126.
- Grimm, V., et al. (2010). "The ODD protocol: A review and first update." *Ecological Modelling*, 221(23), 2760–2768.
- Grimm, V., Railsback, S. F., et al. (2020). "The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update to Improve Clarity, Replication, and Structural Realism." *Journal of Artificial Societies and Social Simulation*, 23(2), 7.

---

*This template accompanies Chapter 7 of "Simulation Models for Data Science" by Dan Sullivan, published by O'Reilly Media.*
