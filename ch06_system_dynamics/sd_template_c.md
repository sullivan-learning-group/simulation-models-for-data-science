# SD Template C: Validation and Results

Run these checks after your model produces results. System dynamics validation is
fundamentally different from MC and DES: the model is deterministic, so there are
no confidence intervals or convergence checks. Instead, validate the structure
first, then the behavior.

**Key difference from MC and DES Template C:** Adds structural validation (does
the model have the right feedback loops?) and dimensional consistency checks.
Replaces convergence checks (not applicable, since SD models are deterministic)
with extreme condition tests. Scenario comparison uses time-series trajectories
rather than output distributions.

Template A's closure checklist hands three things to this template: the list of
parameters marked **Structural**, the expected loop dominance table, and the
reference behavior the baseline had to reproduce. Sections 4, 5, and 6 below are
where each of those gets settled.

---

## Section 1: Structural Validation

Review with a domain expert. The goal: does the model capture the feedback
dynamics that actually drive the system?

```
Are all important feedback loops represented?      [Y/N — list any missing]
Are any loops included that shouldn't be?          [Y/N — list any spurious]
Do stock definitions match real accumulations?     [Y/N]
Are delay estimates reasonable?                    [Y/N — note any contested]
Does the boundary (endogenous/exogenous/excluded)
match the expert's mental model?                   [Y/N — note any disputes]
Archetype identified in Template A still fits?     [Y/N — name the archetype]
Which constraint from Template A section 11 binds,
and for how much of the horizon?                   [name it and give the share]
Domain expert sign-off:                            [Name / Date / Notes]
```

This is the most important validation step. A model with the right loops but
wrong parameters produces the right qualitative behavior. A model with wrong
loops but perfect parameters produces misleading behavior. No amount of parameter
tuning fixes a missing feedback loop.

The binding-constraint question is worth asking explicitly. A ceiling the model
never reaches is doing no work, and a ceiling that binds from the first time step
means the system starts saturated. Both are findings the expert should hear.

---

## Section 2: Dimensional Consistency

Check every equation. Both sides must have the same units.

| Equation | Left Side Units | Right Side Units | Consistent? |
|----------|----------------|-----------------|-------------|
| | | | Y/N |
| | | | Y/N |
| | | | Y/N |

Common error: mixing stocks (units) with flows (units/time). If `acquisition_rate`
is customers/month, every term contributing to it must reduce to customers/month.

**Time-unit check.** This catches the most common SD bug: a delay constant
declared in the wrong time unit. If the model runs in months, every SMOOTH time
constant must be in months. A "6-week" word-of-mouth delay must be entered as
`6/4.33 ≈ 1.39` months, not as `6`. Make this an assertion in code, not a manual
review:

```python
assert all(p.unit == model.time_unit for p in delay_params), \
    "Delay parameter unit mismatch — convert to model time unit before solve_ivp"
```

**Initialization check.** Every delay stock starts at the equilibrium value
Template A section 13 gives it, and every stock driven toward a target starts at
that target under baseline inputs. A stock that starts away from its target moves
on its own, and that motion reads as system behavior in the output when it's an
artifact of the initial condition.

```python
assert abs(target(initial_state, baseline_params) - initial_state[stock]) < tol, \
    "Stock does not start at rest under baseline inputs — the baseline will drift"
```

---

## Section 3: Extreme Condition Tests

Set parameters to extreme values and verify the model behaves sensibly.

| Test | Parameter Setting | Expected Behavior | Observed | Pass? |
|------|------------------|-------------------|----------|-------|
| No acquisition | all acquisition terms = 0 | Stock decays toward zero | | Y/N |
| No churn | churn_fraction = 0 | Stock grows without bound | | Y/N |
| Zero delay | all delays → 0 | System reaches steady state immediately | | Y/N |
| Extreme price hike | price_change = +100% | Rapid customer loss | | Y/N |
| Infinite capacity | balancing-loop pressure = 0 | Balancing loop inactive, reinforcing loop dominates | | Y/N |

If any test fails, the model structure or equations contain an error.

Read "grows without bound" carefully. A stock can grow without bound and still
grow linearly rather than exponentially, if a balancing loop saturates and caps
the inflow while the outflow stays at zero. That's a pass, but note the shape,
because it tells you which loop is doing the limiting.

---

## Section 4: Behavioral Validation Against Reference Modes

A *reference mode* is the historical or expected behavior pattern the model
should be able to reproduce, sketched as a curve before any modeling begins.
Template A section 3 states it in numbers. Check the baseline against every row
of that table before comparing scenarios, because a baseline that misses its
reference mode invalidates everything downstream.

| Reference quantity | Required | Baseline produced | Pass? |
|--------------------|----------|-------------------|-------|
| | | | Y/N |
| | | | Y/N |

For each behavioral episode you can test against history:

```
Reference mode 1
  Pattern (sketch or describe):  [e.g., "traffic dipped sharply for 6 weeks
                                 after the March price increase, then
                                 partially recovered"]
  Triggering inputs:             [e.g., price_change = +10% at t = 0]
  Observed outcome:              [e.g., traffic dipped ~8% by June]
  Model prediction:              [e.g., customer_base drops 7.5% over 3 months]
  Qualitative match?             [Y/N — does the shape match?]
  Quantitative match?            [Y/N — within 20% of observed magnitude?]
```

Reproducing the qualitative pattern (dip-and-recover, gradual decline,
oscillation) matters more than matching exact numbers. If the model can't
reproduce a past episode, it has no business projecting the future.

If no historical reference mode is available, have a domain expert sketch the
*expected* behavior under a hypothetical scenario before they see the model
output, then compare. This anchors the validation to their independent judgment
rather than to a curve they've already been shown.

---

## Section 5: Expected vs. Observed Loop Dominance

Template A section 12 states which loop you expected to dominate in each phase.
Compare that prediction against the run. A mismatch is a finding, and often the
most interesting one in the report, so record it rather than reconciling it.

| Phase | Expected dominant loop | Observed | Match? | What the gap means |
|-------|----------------------|----------|--------|-------------------|
| | | | Y/N | |
| | | | Y/N | |

Two failure modes show up here repeatedly. A loop can be structurally present and
dynamically inert, when a policy elsewhere in the model holds its input constant.
A loop can also dominate far earlier than expected, when a ceiling binds at the
initial condition rather than partway through the run. Both are worth a paragraph
in the write-up, because both change what the decision-maker should do.

---

## Section 6: Structural Parameter Review

Template A section 9 marks some parameters **Structural**, meaning you chose them
so the model would behave the way the reference mode says it should. Each one is
a conclusion you assumed rather than derived, and each one belongs in the
limitations.

| Structural parameter | Value | What it encodes | How much the conclusion moves across its plausible range |
|---------------------|-------|-----------------|---------------------------------------------------------|
| | | | |
| | | | |

**Verdict:** [Which structural choices the conclusion actually rests on, and
which turn out not to matter. The sensitivity results in section 7 answer this
directly.]

---

## Section 7: Sensitivity Analysis

SD models support three levels of sensitivity analysis. Each answers a different
question. Start with OAT, escalate to global if interactions matter, and run
structural sensitivity whenever the model's conclusions are policy-relevant.

### 7a. One-at-a-time (OAT) parameter sensitivity

Sweep each key parameter across its plausible range with all others held
constant. Easy to interpret; misses interactions.

| Parameter | Low Value | High Value | Output @ Low | Output @ High | Swing | Rank |
|-----------|----------|-----------|-------------|--------------|-------|------|
| | | | | | | 1 |
| | | | | | | 2 |
| | | | | | | 3 |

**Key driver:** [Which parameter matters most and why]

### 7b. Global sensitivity analysis

Vary many parameters simultaneously across their plausible ranges and decompose
output variance by source. Use this when OAT shows several parameters in a
similar range, since interactions may be masking the real driver.

| Technique | When to Use | Python | Output |
|-----------|-------------|--------|--------|
| Latin Hypercube Sampling (LHS) | Quick exploration with N runs | `scipy.stats.qmc.LatinHypercube` or `SALib.sample.latin` | Regression on input → output |
| Sobol indices | Rigorous variance decomposition | `SALib.analyze.sobol` | First-order + total-order indices per parameter |
| MC wrapper (Chapter 4 pattern) | Quantify outcome uncertainty | `numpy.random` + scenario loop | Median + percentile envelope per scenario |

```
Global sensitivity method used:    [LHS / Sobol / MC wrapper]
Number of runs:                    [e.g., 1,000]
Parameters varied:                 [list]
Top drivers by total-order index:  [parameter: index value]
Any OAT top-five parameter missing
from the sampled set?              [Y/N — if Y, the global analysis is
                                   measuring the wrong thing; fix section 16
                                   of Template A and re-run]
```

Run the global analysis on more than one output. The parameter that drives the
level of a stock at the end of the horizon is often not the parameter that drives
the timing of a crossover or a payback, and the decision usually turns on the
timing.

### 7c. Structural sensitivity

Unique to SD. Test what happens when a *loop* is weaker, stronger, or absent.

| Loop | Variation | Result | Interpretation |
|------|-----------|--------|---------------|
| | Coupling × 0.5 | | |
| | Coupling × 2.0 | | |
| | Disabled (coefficient = 0) | | If qualitative behavior is unchanged, this loop isn't doing the work you thought |

**Structural finding:** [E.g., "Disabling B1 entirely lifts the 24-month endpoint
by 63 customers, confirming B1 is the active brake."]

---

## Section 8: Scenario Comparison

Compare trajectories at key time points.

| Metric | Baseline | Scenario A | Scenario B | Scenario C |
|--------|----------|------------|------------|------------|
| [Primary stock] @ 6 mo | | | | |
| [Primary stock] @ 12 mo | | | | |
| [Primary stock] @ 24 mo | | | | |
| Monthly revenue @ 24 mo | | | | |
| Cash reserves @ 24 mo | | | | |
| Investment payback month | — | | — | |
| **Equilibrium (if reached)** | | | | |

Note crossover points: when does Scenario A surpass the baseline? When does the
investment pay for itself in cumulative net cash? If a scenario never pays back
inside the horizon, say so rather than extrapolating past the last time step the
model was validated against.

**Policy resistance check.** Look for scenarios that combine two individually
sensible interventions and produce a *worse* result than either alone. This is
"policy resistance," the system absorbing or working against a well-intentioned
change through feedback. It's the most strategically important finding an SD
model can produce.

```
Does any combined scenario underperform its constituent
single-lever scenarios?            [Y/N]
If yes, which scenario, and which loop is responsible?
                                   [Confirm by disabling the suspected loop
                                   and re-running the combined scenario. If
                                   the underperformance disappears, you have
                                   your answer.]
```

---

## Section 9: Results Summary

**One-Paragraph Finding**
```
[Plain-language summary. Write for the decision-maker. Lead with
the trajectory and the decision. Use "by month X" language for
time-based outcomes. Explain delays honestly: "you won't see
results immediately."]
```

**Key Numbers**

| Metric | Value | What It Means |
|--------|-------|---------------|
| Best scenario | | |
| Payback period | | |
| Crossover point | | |
| Sensitivity risk | | |
| Policy resistance flag | Y/N | If Y, which scenario and which loop |

**Recommendation**
```
[One to three sentences. Frame as a trajectory, not a snapshot.
Address the delay: when will the decision-maker see results?
Note what happens if assumptions are wrong.]
```

**Limitations**
```
[What the model does not include, and which structural
assumptions the conclusion rests on. SD models are especially
limited by: missing feedback loops, assumed delay lengths,
parameters marked Structural in Template A section 9, and the
absence of stochastic variation.]
```
