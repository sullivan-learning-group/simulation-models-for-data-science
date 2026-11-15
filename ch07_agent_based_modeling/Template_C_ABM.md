# ABM Template C: Validation and Results (ODD-Based)

Run these checks after your model produces results. ABM validation operates at two levels: micro (do individual agents behave correctly?) and macro (do emergent patterns make sense?). Both are required.

**Key difference from previous Template C's:** Adds micro-level agent tracing (verify behavioral rules work as coded), macro-level emergence validation, and sensitivity to population size. Replication analysis is critical because ABM outcomes are inherently stochastic even when the model is correctly specified.

**Key difference from the pre-ODD version of this template:** The spec now does half the validation work for you. Micro-verification becomes *submodel verification* — each named submodel in Element 7 is a separately testable method, so traces map one-to-one onto spec sections. Macro-validation becomes *pattern-oriented validation* — the table below pulls its rows directly from the patterns declared in Element 1, closing the loop the spec opened: Template A declares the patterns, Template C checks them. If you find yourself validating against a pattern that isn't in Element 1, update the spec first.

## Section 1: Submodel Verification (Micro Level)

Verify each submodel in Element 7, one at a time, by tracing individual agents through multiple steps. One table (or trace set) per submodel.

### Submodel: [name]

| Step | Agent ID | Inputs Observed | Output / Action | Expected (per spec) | Matches? |
|------|----------|-----------------|-----------------|---------------------|----------|
| | | | | | Y/N |
| | | | | | Y/N |

Trace at least 3 agents with deliberately different profiles — including at least one near a decision boundary (e.g., an agent whose top two utilities are nearly tied, or an adaptive agent hovering at its trigger threshold). Boundary agents are where off-by-one and ordering bugs live.

*[Repeat for every submodel in Element 7]*

**Periodic-process timing check:** For submodels that fire every N steps, verify they fire at the correct step numbers and at the correct position within the step (per the Element 3 schedule) — not one step early or late.

---

## Section 2: Spec Conformance Checks

Structural checks that the code obeys the spec's explicit decisions. These catch a class of AI code-generation errors that behavioral traces can miss, because the model can produce plausible-looking output while quietly violating the spec.

```
Scheduling: does step() execute Element 3's processes in the
  declared order?                                        [Y/N]
Sensing: do agent methods read ONLY state the Element 4 Sensing
  section permits? (Inspect each agent method's reads; the most
  common leak is an agent reading another agent's private state.)
                                                         [Y/N]
Stochasticity: does every random draw flow from the per-replication
  seeded RNG? (Search for module-level random calls.)    [Y/N]
Reproducibility: does the same seed produce identical output twice?
                                                         [Y/N]
Parameters: do the values in code match every Element 7 parameter
  table?                                                 [Y/N]
```

---

## Section 3: Pattern-Oriented Validation (Macro Level)

Check each pattern declared in Element 1 against actual model output. Copy the pattern rows from the spec — do not rewrite them from memory.

| # | Pattern (from Element 1) | Observed? | Evidence | Notes |
|---|--------------------------|-----------|----------|-------|
| 1 | | Y/N | [Plot or metric] | |
| 2 | | Y/N | [e.g., frequency: X of 30 runs] | |
| 3 | | Y/N | | |
| 4 | | Y/N | | |

A failed pattern is a finding, not just a bug report. It means one of three things: the code doesn't implement the spec (go back to Sections 1–2), the spec's rules don't produce the behavior you expected (revise the model and re-declare the pattern), or your expectation about the real system was wrong (the most interesting outcome — write it down).

**Sanity checks:**
```
[Domain-plausibility bounds: do key quantities stay in ranges a
 person who knows the real system would accept? List 3–5 checks,
 e.g., conserved totals, plausible price/level bounds, spatial
 patterns consistent with geography.]
```

---

## Section 4: Sensitivity to Agent Parameters

Sweep key agent parameters across plausible ranges. Check whether macro-level outcomes are robust or fragile. Prioritize the parameters marked *[proposed]* or "assumption" in the Element 7 tables — those are the ones with the least empirical grounding, so the conclusions must be shown to survive variation in them.

| Parameter | Low Value | High Value | Outcome @ Low | Outcome @ High | Swing | Rank |
|-----------|----------|-----------|---------------|----------------|-------|------|
| | | | | | | 1 |
| | | | | | | 2 |
| | | | | | | 3 |

**Key driver:** [Which parameter matters most and why]

**Decision-rule sensitivity:** [Do the scenario rankings change when choice-function weights shift? A recommendation that holds only in a narrow band of an assumed weight is a fragile result — report the band.]

---

## Section 5: Sensitivity to Population and Scale

Run the model at different population sizes. Results should be qualitatively stable.

| Population | Steps | Key Metric 1 | Key Metric 2 | Qualitatively Same? |
|------------|-------|--------------|--------------|--------------------|
| [0.4×] | | | | Y/N |
| [1×] | | | | Y/N |
| [2×] | | | | Y/N |

If results change qualitatively at different scales, the model may have a threshold effect worth investigating — or a coding error.

---

## Section 6: Replication Analysis

ABM outcomes are stochastic. Single runs are anecdotes. Report distributions.

**Summary across replications:**

| Metric | Mean | Median | P10 | P90 | Std Dev |
|--------|------|--------|-----|-----|---------|
| | | | | | |
| | | | | | |

**Convergence check:** Plot cumulative mean of the headline metric vs. replication count. Verify it flattens by the replication count declared in Section 8 of the spec. If still drifting, run more replications and update Section 8.

| Replications | Cumulative Mean | Change from Previous | Stable? |
|--------------|-----------------|---------------------|---------|
| | | — | |
| | | | |
| | | | |

---

## Section 7: Scenario Comparison

| Metric | Scenario 1 | Scenario 2 | Scenario 3 | Scenario 4 |
|--------|-----------|-----------|-----------|-----------|
| Median headline metric | | | | |
| P10 (downside) | | | | |
| P90 (upside) | | | | |
| [Emergent-event frequency] | | | | |

Note any bimodal outcomes: if some replications produce one regime and others produce a different one, both findings matter. Report them separately — averaging across regimes produces a number no single run resembles.

---

## Section 8: Results Summary

**One-Paragraph Finding**
```
[Plain-language summary. Write for the decision-maker. Lead with
the range of outcomes. Use "in X% of simulations" language.
Explain emergence honestly — the outcome depends on other actors'
reactions, which are simulated, not controlled.]
```

**Key Numbers**

| Metric | Value | What It Means |
|--------|-------|---------------|
| | | |
| | | |

**Recommendation**
```
[One to three sentences. Frame as a risk profile, not a point
estimate. Compare scenarios by risk tolerance.]
```

**Limitations**
```
[What the model does not include. Start from the spec itself: the
Key Assumptions in Section 0, every "not used" entry in the Element 4
design concepts, a "none" in Element 6 (no external data driving the
model), and the [proposed]/assumption-sourced parameters in
Element 7 are your limitations list, pre-written. Two to four items.]
```

---

*This template accompanies Chapter 7 of "Simulation Models for Data Science" by Dan Sullivan, published by O'Reilly Media.*
