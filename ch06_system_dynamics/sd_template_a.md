# SD Template A: System Structure Spec

Template A tells you what the system is made of and what the numbers behind it
are. Fill in every section before you hand the spec to Template B. Structure
alone won't run: a stock and flow diagram with no values attached produces no
trajectory, and a code generator handed an incomplete spec invents the missing
numbers silently. Those invented numbers then decide the answer, including the
payback month, which lever wins, and whether the reinforcing loop runs away or
settles. Sections 9 through 16 exist to keep that decision in your hands, and
the closure checklist in section 17 catches the gaps before they reach code.

## 1. Business Question

State the decision the model has to inform, not the topic it covers. A question
you can answer with a number and a date is a question the model can be built
against.

**Primary:** [The decision, the quantity it turns on, and the horizon. Example
shape: "If we do X, how does that affect Y over Z months?"]

**Secondary:** [The follow-on question, usually a second lever or a combination.]

## 2. Time Horizon and Time Unit

Pick one time unit and hold every flow, delay, and rate to it. Mixed units are
the most common source of silent error in system dynamics code.

| Setting | Value | Notes |
|---------|-------|-------|
| Model time unit | [days / weeks / months / years] | Every flow is units/time unit; every delay constant is in the same unit |
| Horizon | [n time units] | Long enough for the slowest loop to close |
| Reporting interval | [n] | Integration is continuous; this is the output grid |
| Conversion factor | [e.g. 1 month = 4.33 weeks] | Apply to anything stated in another unit before it reaches the solver |
| Discontinuity times | [list every time a step, pulse, or switch lands] | The solver needs a step size small enough to resolve them |

Declaring the discontinuity times matters more than it looks. A solver with
adaptive stepping will happily step over a one-time event and miss it entirely.
Template B integrates segment by segment between these times, so list every one.

## 3. Reference Behavior

Describe what the real system has done, in numbers. The baseline scenario has to
reproduce this before any lever is worth simulating. Without a reference mode,
calibration has no target and you're just picking values that feel right.

| Observed quantity | Historical value | Source | Baseline must reproduce |
|-------------------|-----------------|--------|------------------------|
| | | | |
| | | | |
| | | | |

**Intended baseline mode:** [flat, growing, declining, oscillating, or
overshoot-and-collapse, with the bounds that would tell you the parameters are
wrong rather than the structure.]

## 4. Assumptions

[What you're holding constant, what you're taking on faith, and what the model
treats as immediate rather than delayed. Each one is a limitation waiting to be
written up in Template C.]

## 5. Model Boundary

Endogenous variables are produced by the loops. Exogenous variables are inputs
the model takes as given. Excluded variables are outside the boundary entirely,
and every one of them belongs in Template C's limitations.

| Variable / Driver | Treatment | Why |
|------------------|-----------|-----|
| | Endogenous | |
| | Exogenous | |
| | Excluded | |

## 6. Stocks

Stocks accumulate. Each one needs an initial value, and each initial value needs
a basis, because a value you measured and a value you guessed carry different
weight in the conclusion.

A stock driven toward a target deserves particular care. If its initial value
doesn't match the target its own equations imply under baseline inputs, the
stock drifts on its own, and that drift shows up in the results as system
behavior when it's really an initialization artifact.

| Stock | Initial Value | Units | Initial value basis | Description |
|-------|--------------|-------|--------------------|-------------|
| | | | | |
| | | | | |
| | | | | |

## 7. Flows

Every flow moves one stock, in one direction, in units per model time unit.

| Flow | Direction | Units | Driven By |
|------|-----------|-------|-----------|
| | Inflow to [stock] | | |
| | Outflow from [stock] | | |

## 8. Auxiliary Variables

Auxiliaries are the intermediate calculations between stocks and flows. Every
name in the **Depends On** column has to resolve somewhere else in this spec: to
another auxiliary, a stock, a parameter in section 9, or an exogenous input in
section 15. A name that resolves nowhere is a number the code generator will
invent, and the closure check in section 17 exists to catch exactly that.

| Variable | Units | Depends On | Description |
|----------|-------|-----------|-------------|
| | | | |
| | | | |
| | | | |

**Index anchoring.** Any variable on a 0 to 1 or 0 to 100 scale needs its
endpoints defined in words, or nobody can check whether 0.60 is reasonable.
State what 0 means and what the maximum means for every index in the table
above.

## 9. Parameters and Constants

This is where most of the modeling judgment actually lives. Every constant the
equations reference belongs here with four things attached: a value, units, a
basis, and a plausible range.

The **basis** column carries the most weight. Use one of four labels:

- **Measured.** You pulled it from data you have.
- **Benchmark.** Published industry figures. Cite the source.
- **Estimated.** An informed guess from someone who knows the business.
- **Structural.** You chose it so the model behaves the way the reference mode
  says it should. These are the values that need the hardest look in Template C,
  because they encode a conclusion you assumed rather than derived.

The **plausible range** column does double duty. It tells the reader how much
confidence the value carries, and it feeds the sensitivity sweeps and the
uncertainty specification in section 16 directly.

Group the parameters by subsystem so the reader can find them. Add or drop
groups to match your model.

### [Subsystem 1]

| Parameter | Value | Units | Basis | Plausible range |
|-----------|-------|-------|-------|----------------|
| | | | | |
| | | | | |

### [Subsystem 2]

| Parameter | Value | Units | Basis | Plausible range |
|-----------|-------|-------|-------|----------------|
| | | | | |
| | | | | |

## 10. Nonlinear Relationships

Any variable that saturates, ramps, or switches needs its shape written down.
"0 when wait times are negligible, 1 when wait times drive customers away" reads
fine in a diagram and tells the code generator nothing. Where does the ramp
start? How fast does it climb? Those two numbers decide whether the balancing
loop bites early or late, and that timing is usually the whole result.

Give each relationship a functional form and at least three anchor points.

| Relationship | Form | Anchor points | Basis |
|-------------|------|---------------|-------|
| | | | |
| | | | |

## 11. Constraints and Ceilings

Real systems hit walls. A model without them produces exponential growth and a
recommendation nobody can act on. Name every ceiling, floor, and hard bound.

| Constraint | Rule | Rationale |
|-----------|------|-----------|
| | | |
| | | |

Check that at least one balancing loop has a hard ceiling behind it. A ceiling
that the model never reaches inside the horizon isn't doing any work, and
Template C will find that out.

## 12. Feedback Loops

Name each loop, trace it as a closed chain back to where it started, and give it
a plain-language reading. If the chain doesn't close, it isn't a loop.

```
R1 ([name]): [variable] → [variable] → [variable] → [back to start]
   Plain language: [one sentence]

B1 ([name]): [variable] → [variable] → [variable] → [back to start]
   Plain language: [one sentence]
```

**Expected loop dominance.** State what you expect before you run the model, so
the run can surprise you. Template C compares this table against what actually
happened, and a miss here is a finding, not an embarrassment.

| Phase | Expected dominant loop | Why |
|-------|----------------------|-----|
| | | |
| | | |

## 13. Delays

Every SMOOTH becomes a state variable in the code, and every state variable
needs an initial condition. Start a smoothing stock at zero and you get a
spurious dip at the beginning of the run that has nothing to do with the system
and everything to do with the initialization. Start it at its equilibrium value
and the first period behaves.

| Delay | Type | Duration (source unit) | Duration (model unit) | Implementation | Initial value of the delay stock |
|-------|------|------------------------|-----------------------|----------------|--------------------------------|
| | Information / Material | | | SMOOTH, 1st order | |
| | | | | | |

## 14. Equations

State the model time unit once, then write every equation. Every symbol has to
resolve to a stock in section 6, an auxiliary in section 8, a parameter in
section 9, or an exogenous input in section 15.

```
[auxiliary]  = [expression]
[auxiliary]  = [expression]
[flow]       = [expression]
```

## 15. Exogenous Inputs and Policy Timing

Every lever needs a shape and a time, not just a magnitude. A one-time purchase
is a pulse; a price increase is a step; a hiring program is a ramp. The code
differs in each case, and a continuous-time solver handles a pulse only if you
tell it how wide the pulse is.

| Input | Shape | Timing | Magnitude | What it changes |
|-------|-------|--------|-----------|----------------|
| | Pulse, width [n] | | | |
| | Step, permanent | | | |
| | Ramp over [n] | | | |

**Solver note for Template B:** integrate segment by segment between the
discontinuity times listed in section 2, so every step and pulse edge lands on a
segment boundary. Inside a pulse segment, hold the maximum step size to a
fraction of the pulse width so the solver evaluates the pulse more than once.

## 16. Uncertainty Specification

Template B asks for a Monte Carlo wrapper and, when more than three parameters
are uncertain, a global sensitivity analysis. Neither one can run without
distributions. Pull these from the plausible ranges in section 9, and say which
parameters get sampled and which stay fixed.

**Sampled in the stochastic runs:**

| Parameter | Distribution | Rationale |
|-----------|-------------|-----------|
| | | |
| | | |

**Bounds for global sensitivity** (total-order indices): [list each parameter
with its low and high bound, in model units].

The sampled set has to include the parameters that actually move the answer, not
just the ones you're least sure about. Those are different questions. A
parameter you measured precisely can still dominate the output if the model is
steeply sensitive to it, and leaving it out of the global sweep hides the
strongest driver in the model.

**Held fixed and why:** [name the parameters you're not sampling and the reason.
Structural weights usually stay fixed, since sampling them tests the structure
rather than the parameters, and that's a Template C question.]

## 17. Closure Checklist

Run this before handing the spec to Template B. Every item should be a yes, and
any no is a number the code generator will otherwise invent for you.

- [ ] Every symbol in section 14 resolves to a stock, an auxiliary in section 8,
      or a parameter in section 9. No dangling references.
- [ ] Every name in the **Depends On** column of section 8 resolves the same way.
- [ ] Every parameter has a value, units, a basis, and a plausible range.
- [ ] Every 0 to 1 or 0 to 100 index has its endpoints anchored in words.
- [ ] Every saturating or threshold relationship has a functional form and three
      anchor points.
- [ ] Every delay has a duration in model time units and an initial value for its
      stock.
- [ ] Dimensional check: every flow is units per model time unit, every delay
      constant is in model time units, and both sides of every equation carry the
      same units.
- [ ] At least one balancing loop has a hard ceiling behind it, so the
      reinforcing loop can't run away.
- [ ] Every lever in the scenario table has a shape (step, pulse, ramp), a time,
      and a magnitude.
- [ ] The global sensitivity set in section 16 includes every parameter the OAT
      sweep ranks in the top five.
- [ ] The baseline scenario, run with these numbers, reproduces the reference
      behavior in section 3.
- [ ] Parameters marked **Structural** are listed for Template C, since each one
      is a conclusion you assumed rather than measured.

## 18. Scenarios

Every scenario is the baseline plus a named set of changes to section 15. The
baseline reproduces section 3; the rest are the levers you're testing.

| Scenario | [Lever 1] | [Lever 2] | Description |
|----------|-----------|-----------|-------------|
| Baseline | None | None | Current trajectory; must reproduce section 3 |
| A: [name] | | | |
| B: [name] | | | |
| C: [name] | | | |
