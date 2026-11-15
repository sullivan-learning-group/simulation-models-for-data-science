# Monte Carlo Simulation Specification Template

> **How to use this template:** Fill in every bracketed section `[...]` to define your simulation. Once complete, this document serves two purposes: (1) a human-readable specification documenting your design decisions, and (2) a structured prompt you can paste directly into an LLM to generate Python simulation code. For a completed example using this template, see the Coffee Shop Daily Revenue specification in Chapter 4.

---

## 1. Problem Definition

### Business Question

[State the specific question this simulation will answer. The question should be precise, measurable, and tied to a decision. Avoid vague questions like "simulate X" — instead frame it as a probability or threshold question. Example format: "What is the probability that [output variable] falls below/above [threshold value] over [time horizon]?"]

### Decision Context

```
Decision to be made: [What action or choice depends on the simulation results?]
How results will be used: [Describe the decision rule. Under what conditions will
  the decision maker choose option A vs. option B? Include specific thresholds
  if applicable.]
Note: [Any additional context about how the threshold or decision criteria
  were determined.]
```

### Output Variable

```
Name: [variable_name — use snake_case, this will become a column in the results]
Units: [unit of measure, e.g., USD per day, hours, defects per batch]
Each iteration represents: [what one simulation run models, e.g., one day of
  operations, one project timeline, one production batch]
```

### Key Assumptions

```
[List the simplifying assumptions that define the scope of this model. These
should state what is true within the simulation, even if reality is more
complex. Number each assumption. Common assumptions include:]
1. [The equation relating inputs to outputs]
2. [Independence or dependence assumptions between variables]
3. [Stationarity assumptions — are distributions constant over time?]
4. [Boundary assumptions — what is included in the model scope?]
5. [Add more as needed]
```

### What This Simulation Excludes

```
[List factors deliberately left out of the model. This documents scope
boundaries and prevents reviewers from asking "did you consider X?"
Include factors such as: trends over time, external shocks, rare events,
variables with negligible impact, second-order effects, and any factors
where data is unavailable.]
```

---

## 2. Input Variables

> Repeat this block for each uncertain input variable. Most simulations have 2–6 input variables. For each variable, you must specify a distribution and its parameters. If a variable depends on another variable (e.g., its parameters change based on a categorical condition), note that here and provide full details in Section 3.

### Variable 1: [Descriptive Name]

```
Name: [variable_name — use snake_case]
Description: [One sentence explaining what this variable represents]
Distribution: [Distribution type, e.g., Normal, Lognormal, Categorical,
  Uniform, Poisson, Exponential, Beta, Triangular. If conditional on
  another variable, note that here, e.g., "Normal (conditional on weather)"]
Parameters: [List all distribution parameters. For conditional distributions,
  list parameters for each condition. Examples:
  - Normal: mean=100, std_dev=15
  - Lognormal: mu=1.5, sigma=0.3 (underlying normal parameters)
  - Categorical: category_a=0.40, category_b=0.35, category_c=0.25
  - Uniform: low=10, high=50
  - Triangular: low=5, mode=10, high=20]
Units: [unit of measure]
Constraints: [Any restrictions on valid values, e.g., integer, minimum=0,
  maximum=100, mutually exclusive categories]
Source: [Where do the distribution and parameter estimates come from? Include:
  data source, sample size, time period, any data cleaning steps, and
  statistical tests used to select the distribution. If using expert judgment
  instead of data, state that explicitly.]
```

### Variable 2: [Descriptive Name]

```
Name: [variable_name]
Description: [One sentence explanation]
Distribution: [Distribution type]
Parameters: [Parameter values]
Units: [unit of measure]
Constraints: [Valid value restrictions]
Source: [Data source and justification]
```

### Variable N: [Descriptive Name]

```
[Add as many variable blocks as needed. Each uncertain input that affects
the output variable should have its own block.]
```

---

## 3. Dependencies Between Variables

### Are any inputs correlated?

[Describe which input variables are related to each other and how. For each dependency, explain the nature of the relationship (e.g., "Variable A depends on Variable B because..."). Include any statistical evidence such as correlation coefficients, ANOVA results, or domain knowledge. Also note which variables are independent of each other and any evidence supporting that independence.]

### Implementation Method

[Check the method you will use to model dependencies. Choose one or more:]

- [ ] **Conditional distributions** — different parameters depending on a categorical variable. Best for simple models where one variable's distribution shifts based on discrete categories.
- [ ] **Correlation matrix** — pairwise rank (Spearman) correlations between inputs. Use when several inputs move together and you are not modeling what drives them.
- [ ] **Copulas** — for modeling dependencies between non-normal variables. Use when marginal distributions are non-normal but you need to capture joint behavior.
- [ ] **Independent** — all inputs are sampled independently. Use when analysis confirms no meaningful correlations between inputs.

### Conditional Distribution Details

[If using conditional distributions, fill in the table below. Add or remove rows as needed. If using correlation matrices or copulas instead, replace this table with the appropriate specification.]

| Condition | Variable | Distribution | Parameters |
|-----------|----------|-------------|------------|
| [condition_1] | [variable_name] | [distribution] | [parameters] |
| [condition_2] | [variable_name] | [distribution] | [parameters] |
| [condition_3] | [variable_name] | [distribution] | [parameters] |

---

## 4. Model Logic

### Equations

```
[Write out the step-by-step sampling and computation sequence. Each step
should be unambiguous enough for a programmer to implement directly.
Use this format:]

Step 1: Sample [variable_1] from [Distribution(parameters)]
Step 2: Based on [variable_1], sample [variable_2] from [matching distribution]
Step 3: [Any post-processing, e.g., rounding, clipping, transforming]
Step 4: Sample [variable_3] from [Distribution(parameters)]
Step 5: [output_variable] = [formula using sampled variables]

[Add as many steps as needed. The final step should compute the output variable.]
```

### Business Rules and Constraints

```
[List all constraints that must be enforced during simulation. These are
rules that prevent impossible or invalid values. Examples:]
1. [variable_name] must be [constraint, e.g., a non-negative integer]
2. [variable_name] must be [constraint, e.g., positive]
3. [output_variable] cannot be [constraint, e.g., negative]
[Add more as needed.]
```

### Hand-Check

```
[Compute the expected value of the output variable using the mean of each
input. This provides a sanity check for simulation results. Show your work:]

E[variable_1] = [calculation]
E[variable_2] = [calculation]
E[output] = [formula] = [expected value]

[Compare this to any thresholds in your business question. Does the expected
value seem reasonable? Is it above or below the threshold? This tells you
roughly what to expect from the simulation.]
```

---

## 5. Simulation Settings

```
Number of iterations: [Typical starting point is 10,000. Increase to 50,000
  or 100,000 if tail percentiles have not converged.]
Random seed: [An integer for reproducibility, e.g., 42]
```

---

## 6. Required Outputs

### Statistics

[List the summary statistics to compute from the simulation results. At minimum include:]

- Mean, median, standard deviation of [output_variable]
- Percentiles: 5th, 25th, 75th, 95th
- **P([output_variable] < [primary threshold])** — the primary decision metric
- P([output_variable] < [stress threshold]) — worst-case stress check
- P([output_variable] > [upside threshold]) — upside potential

### Visualizations

[Check all visualizations to generate:]

- [ ] Histogram of [output_variable] with a vertical line at the [threshold] value
- [ ] Cumulative distribution function (CDF) with [threshold] annotated
- [ ] Sensitivity tornado chart showing which input drives the most variation in [output_variable]
- [ ] Convergence plot showing mean and 5th/95th percentiles stabilizing over iterations

---

## 7. Code Requirements

> These instructions tell an LLM how to generate the simulation code from sections 1–6 above.

```
Generate a complete Python Monte Carlo simulation from the specification above.

Structure:
- Use numpy for random sampling with seed=[seed from Section 5]
- Use scipy.stats for any distributions not natively supported by numpy
  (e.g., lognormal, triangular, beta)
- Return results as a pandas DataFrame with columns: iteration,
  [list all input variable names], [output_variable]
- Separate functions for: input sampling, model logic, simulation loop,
  statistics calculation, and visualization
- Include a main() function that runs everything
- Make number of iterations configurable via a constant at the top

Style:
- PEP 8 compliant
- Docstrings and type hints on all functions
- Clear variable names matching the specification

Output:
- Print summary statistics to console (mean, median, std, percentiles,
  threshold probabilities)
- Save results to CSV ([descriptive_filename].csv)
- Generate and save all visualizations as PNG files

Include validation code that:
- Prints sampled mean and std dev for each input variable and compares
  to target parameters from the specification
- Confirms no constraint violations exist in the sampled data
  (e.g., no negative values where prohibited)
- Plots convergence of mean and 5th/95th percentiles of [output_variable]
```

---

## 8. Validation Checklist

> After running the simulation, verify the following before trusting the results.

**Input checks:**

- [ ] Sampled proportions for categorical variables match target probabilities (within ~2% for 10,000 iterations)
- [ ] Sampled means for each continuous variable are within 5% of target parameters
- [ ] Sampled standard deviations for each continuous variable are within 10% of target parameters
- [ ] No constraint violations in sampled data (e.g., no negative values, no out-of-range values)

**Output checks:**

- [ ] Mean of [output_variable] is close to the hand-check expected value from Section 4
- [ ] No impossible values in the output (e.g., no negative values where prohibited)
- [ ] 95th percentile is plausible (compute a rough upper bound from extreme input values)
- [ ] 5th percentile is plausible (compute a rough lower bound from extreme input values)

**Convergence:**

- [ ] Mean of [output_variable] has stabilized by the final iteration count
- [ ] 5th and 95th percentiles have stabilized (tails converge slower — check these)
- [ ] If not converged, increase iterations (e.g., to 50,000 or 100,000)

**Sensitivity:**

- [ ] Tornado chart identifies the top driver(s) of output variability
- [ ] The ranking of drivers matches domain knowledge expectations

---

## Pre-Submission Checklist

- [ ] Business question is specific and includes a measurable threshold
- [ ] All input variables have distributions, parameters, and documented sources
- [ ] Dependencies are identified and an implementation method is chosen
- [ ] Model equations are written out and verified with a hand calculation
- [ ] Business rules and edge cases are documented
- [ ] Number of iterations and random seed are set
- [ ] Required statistics and visualizations are listed
- [ ] Validation checklist items are defined with plausible bounds
