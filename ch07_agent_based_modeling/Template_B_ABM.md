# ABM Template B: Code Generation Prompt (ODD-Based)

Paste your completed ODD-based Template A into this prompt and hand it to your AI assistant.

**Key difference from previous Template B's:** Requests Mesa model code with agent subclasses rather than a sampling loop (MC), SimPy processes (DES), or ODE functions (SD). Must specify both model-level and agent-level data collection.

**Key difference from the pre-ODD version of this template:** The prompt no longer has to restate the model's architecture in its own words — the ODD spec already implies it. ODD elements map almost mechanically onto Mesa code, which means the prompt's job shrinks to enforcing that mapping and the spec's explicit decisions (scheduling order, sensing restrictions, parameter values) rather than describing the model a second time. Anything a spec states twice will eventually be stated inconsistently.

## The ODD → Mesa Mapping

This mapping is the reason an ODD spec generates better code than a free-form description: every element has one home in the codebase, and every part of the codebase traces back to one element.

| ODD Element | Mesa Code |
|-------------|-----------|
| 2. Entities and state variables | `mesa.Agent` subclasses; attributes and state variables become instance attributes |
| 3. Process overview and scheduling | The body of `Model.step()` — same processes, same order |
| 4. Design concepts: Sensing | What each agent method is *allowed to read* — enforce as access discipline |
| 4. Design concepts: Stochasticity | Every random draw routed through one seeded RNG per replication |
| 4. Design concepts: Observation | `DataCollector` configuration |
| 5. Initialization | `Model.__init__` |
| 6. Input data | File/config loading (or nothing) |
| 7. Submodels | Named methods — one method per submodel, same names as the spec |
| 8. Simulation experiments | `run_scenario()` replication loop and scenario configs |

---

## The Prompt

```
Generate an agent-based simulation in Python using Mesa based on the
following ODD specification.

===============================================================
ODD SPECIFICATION
===============================================================

[Paste completed ODD-based Template A here, Sections 0–8]

===============================================================
TECHNICAL REQUIREMENTS
===============================================================

Libraries: mesa, numpy, pandas, matplotlib
Python: [version]
Random seeds: as specified in Section 8 of the spec. Route ALL
randomness (agent draws, activation order, tie-breaking, event
triggers) through a single seeded RNG per replication.

===============================================================
CODE ARCHITECTURE — FOLLOW THE ODD MAPPING
===============================================================

1. One mesa.Agent subclass per agent type in Element 2. Attributes
   and state variables from Element 2 become instance attributes
   with the same names.

2. Model.step() must execute the processes in Element 3 in EXACTLY
   the order listed, including the placement of any periodic
   (every-N-steps) processes. Do not reorder for convenience.

3. Implement each submodel in Element 7 as a separately named
   method whose name matches the submodel name in the spec
   (e.g., choose_shop, adapt_strategy). One submodel = one method,
   individually callable for testing. Use the parameter values
   from the submodel parameter tables; do not invent values.

4. Enforce the Sensing restrictions in Element 4: an agent method
   may only read state the spec says that agent can perceive. If
   the spec says an agent cannot observe something, the code must
   not read it — even if the attribute is technically accessible.

5. Model.__init__ implements Element 5 (Initialization) exactly,
   including which draws are re-drawn per replication.

6. Configure mesa.DataCollector from the Observation list in
   Element 4: model-level reporters, agent-level reporters, and
   any end-of-run-only outputs.

7. run_scenario(scenario_config, n_replications, base_seed):
   outer replication loop per Section 8, one RNG per replication,
   returns per-replication DataFrames.

8. analyze_replications(results_list): cross-replication summary
   statistics and the visualizations listed below.

===============================================================
REQUIRED OUTPUTS
===============================================================

[List the per-replication outputs, cross-replication summaries, and
plots your analysis needs. Derive these from the Observation list in
Element 4 and the patterns in Element 1 — every pattern needs at
least one output that can confirm or refute it.]

===============================================================
BEFORE WRITING CODE
===============================================================

List any ambiguities, missing parameters, or contradictions you find
in the spec, and how you resolved them. Do not silently fill gaps.
```

---

## Reviewing the Generated Code

The ODD mapping gives you a review checklist for free. Walk the mapping table top to bottom:

```
[ ] One Agent subclass per Element 2 agent type; variable names match
[ ] step() order matches Element 3 exactly (including periodic processes)
[ ] One method per Element 7 submodel; names match; parameters match
    the submodel tables
[ ] No sensing leaks: search each agent method for reads the spec
    forbids (the most common AI code-generation error in ABMs —
    e.g., a shop reading a competitor's price)
[ ] All randomness flows from the per-replication seeded RNG
    (search for unseeded random / np.random module-level calls)
[ ] DataCollector matches the Element 4 Observation list
[ ] The assistant's "ambiguities" list is empty or resolved in the spec
```

Structural conformance (this checklist) belongs here at code review. Behavioral verification — do the submodels produce correct decisions, do the declared patterns emerge — belongs in Template C.

---

*This template accompanies Chapter 7 of "Simulation Models for Data Science" by Dan Sullivan, published by O'Reilly Media.*
