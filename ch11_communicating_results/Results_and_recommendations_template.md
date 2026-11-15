# Template: Results and Recommendations

## Purpose

This template captures the structured output of a completed simulation. It serves two roles: it's the source document for your results report, and it's the input you feed to an LLM when generating decision briefs in different risk framings.

Fill in each section with the outputs from your validated simulation. Be specific with numbers, scenarios, and confidence levels. Vague inputs produce vague briefs.

---

## How to Use This Template

1. Complete each section below after your simulation is validated.
2. Replace the placeholder text in brackets with your actual simulation outputs.
3. For the LLM-assisted workflow described in Chapter 11: copy the completed template into a prompt and ask the LLM to generate a decision brief, a results report, or both. You can also request specific risk framings (risk-averse, risk-neutral, risk-tolerant) and the LLM will adjust the recommendations accordingly.

### Example prompt for generating a decision brief:

```
Using the following Template outputs, draft a one-page decision brief
with a risk-averse framing. Include: one sentence on the problem, one
paragraph on the key finding, two sentences on the recommendation, and
one visualization description. Add a confidence statement.

[Paste completed template here]
```

### Example prompt for generating a results report:

```
Using the following Template outputs, draft a results report with
these sections: executive summary, business context, results, scenarios,
risk assessment, and recommendations. Include 3-5 visualization
descriptions. Add a limitations and caveats section.

[Paste completed template here]
```

### Example prompt for generating three risk framings:

```
Using the following emplate outputs, generate three versions of a
two-sentence recommendation:
1. Risk-averse framing (prioritize protecting against worst case)
2. Risk-neutral framing (prioritize expected value)
3. Risk-tolerant framing (prioritize upside potential)

[Paste completed template here]
```

---

## Section 1: Executive Summary

Provide a concise overview that can stand on its own. This section maps directly to the decision brief described in Chapter 11.

**Business question investigated:**
[State the specific question this simulation was built to answer. Example: "What is the probability that warehouse throughput improvements from rebalancing pick zones will offset the $1.2M implementation cost within 18 months?"]

**Key finding (one paragraph):**
[Summarize the primary result in business terms, not statistical terms. Lead with the outcome that matters to the decision maker. Example: "Rebalancing pick zones produces a 23% throughput improvement in the expected case, saving approximately $840K annually in labor costs. There is a 78% probability of recovering the $1.2M implementation cost within 14 months."]

**Recommended action (two to three sentences):**
[State what you recommend and why. Tie the recommendation to a specific scenario or probability. Example: "We recommend proceeding with a two-week pilot in Zone 3, which handles 35% of daily volume. Pilot results will validate the simulation's throughput projections before committing to the full $1.2M rollout."]

**Confidence level:** [High / Medium / Low]
**Basis for confidence:** [Example: "High confidence based on 18 months of historical pick-rate data, validated against three independent time periods with mean absolute error below 4%."]

---

## Section 2: Business Context

Provide the background a reader needs to understand why this simulation was conducted and what decisions it informs.

**Business problem:**
[Describe the problem in operational or financial terms. What is happening (or might happen) that motivated this analysis? Example: "Current pick zone allocation was designed for 2019 product mix. SKU distribution has shifted 40% toward high-velocity items concentrated in Zone 1, creating bottlenecks that increase average pick time by 18 seconds per order."]

**Decision to be made:**
[What specific decision does this simulation inform? Example: "Whether to invest $1.2M in pick zone rebalancing, and if so, which rebalancing strategy to implement."]

**Stakeholders:**
[Who will use these results and what do they need from them?]
- [Role 1]: [What they need. Example: "VP Operations: Go/no-go decision on the investment"]
- [Role 2]: [What they need. Example: "Warehouse managers: Implementation sequencing across zones"]
- [Role 3]: [What they need. Example: "Finance: Payback period and budget impact"]

**Constraints and boundaries:**
[What limits apply to the decision? Budget caps, timeline requirements, regulatory constraints, resource limitations. Example: "Implementation must not reduce throughput below 85% of current levels during transition. Capital budget ceiling is $1.5M for FY2026."]

---

## Section 3: Simulation Design Summary

Provide enough detail for a technical reviewer to understand the approach without repeating the full specification (Template 7).

**Simulation type:** [Monte Carlo / Discrete Event / Agent-Based / System Dynamics / Digital Twin]

**Key input variables and distributions:**

| Variable | Distribution | Parameters | Data Source |
|----------|-------------|------------|-------------|
| [Example: Pick rate per worker] | [Normal] | [mean=42 items/hr, sd=6.3] | [18 months of shift-level data] |
| [Example: Order arrival rate] | [Poisson] | [lambda=127 orders/hr] | [12 months of order timestamps] |
| [Example: SKU zone assignment] | [Empirical] | [Current vs. proposed allocation] | [Inventory management system] |

**Number of simulation runs:** [Example: 50,000 Monte Carlo trials]

**Key assumptions:**
- [Example: Worker productivity is independent across zones]
- [Example: Order arrival patterns remain consistent with historical data]
- [Example: No changes to staffing levels during the analysis period]

**Validation summary:** [Brief reference to Template 9 validation results. Example: "Model validated against Q3 2025 actuals with 3.8% mean absolute error on daily throughput and 5.2% MAE on labor hours. See Template 9 for full validation report."]

---

## Section 4: Results

Present the primary simulation outputs. Use business metrics, not just statistical measures.

**Primary output metric:** [Example: Annual labor cost savings from pick zone rebalancing]

**Summary statistics:**

| Metric | Value |
|--------|-------|
| Mean | [Example: $840K annual savings] |
| Median | [Example: $815K annual savings] |
| 5th percentile | [Example: $520K annual savings] |
| 95th percentile | [Example: $1.18M annual savings] |
| Probability of exceeding [threshold] | [Example: 92% probability of exceeding $600K] |

**Key visualizations (describe each; attach files separately):**

1. [Example: "Histogram of annual savings with threshold line at $600K break-even point. 92% of simulated outcomes exceed break-even. See Figure X."]
2. [Example: "Tornado diagram showing pick rate variability and order volume as the two largest drivers of savings uncertainty. See Figure X."]
3. [Example: "CDF of payback period showing 78% probability of payback within 14 months. See Figure X."]

**Secondary findings:**
[Results that weren't the primary question but are worth noting. Example: "The simulation also revealed that Zone 4 operates at only 62% capacity under the proposed rebalancing, suggesting an opportunity to consolidate Zones 4 and 5 in a future phase."]

---

## Section 5: Scenario Analysis

Present the three standard scenarios with concrete business metrics for each. This section feeds directly into the scenario narrative described in Chapter 11.

### Best Case Scenario
**Conditions:** [What goes right. Example: "Order volume grows 10%, worker retention stays above 90%, SKU mix stabilizes at projected levels."]
**Key metrics:**

| Metric | Value |
|--------|-------|
| [Example: Annual savings] | [Example: $1.18M] |
| [Example: Payback period] | [Example: 10 months] |
| [Example: Throughput improvement] | [Example: 31%] |

**Probability of this scenario or better:** [Example: 12%]

### Expected Case Scenario
**Conditions:** [Baseline assumptions hold. Example: "Order volume flat, normal worker turnover, current SKU trends continue."]
**Key metrics:**

| Metric | Value |
|--------|-------|
| [Example: Annual savings] | [Example: $840K] |
| [Example: Payback period] | [Example: 14 months] |
| [Example: Throughput improvement] | [Example: 23%] |

**Probability of this scenario or better:** [Example: 55%]

### Worst Case Scenario
**Conditions:** [What goes wrong. Example: "Order volume drops 15%, worker turnover spikes to 40%, new SKU category disrupts zone allocation."]
**Key metrics:**

| Metric | Value |
|--------|-------|
| [Example: Annual savings] | [Example: $320K] |
| [Example: Payback period] | [Example: 38 months] |
| [Example: Throughput improvement] | [Example: 9%] |

**Probability of this scenario or worse:** [Example: 8%]

---

## Section 6: Risk Assessment

Identify and quantify the key risks surfaced by the simulation.

**Top risks ranked by impact (from sensitivity analysis):**

| Rank | Risk Factor | Impact on Primary Metric | Mitigation |
|------|-------------|-------------------------|------------|
| 1 | [Example: Worker turnover spike] | [Example: Reduces savings by $280K per 10% increase in turnover] | [Example: Retention bonuses during transition period] |
| 2 | [Example: Order volume decline] | [Example: Reduces savings by $150K per 5% volume drop] | [Example: Phased implementation tied to volume triggers] |
| 3 | [Example: SKU mix shift] | [Example: Reduces savings by $90K if high-velocity SKU share drops below 55%] | [Example: Quarterly zone rebalancing review] |

**Tail risk:** [Describe the worst outcomes in the distribution and their business consequences. Example: "In 3% of simulations, the rebalancing produces less than $200K in annual savings, extending the payback period beyond 5 years. This outcome is driven primarily by a simultaneous drop in order volume and spike in worker turnover."]

**What would change the recommendation:**
[Identify the conditions under which you'd recommend a different course of action. Example: "If Q1 2026 order volume falls below 95 orders/hour (a 25% decline from current levels), the expected payback period extends beyond 24 months and we would recommend deferring the investment."]

---

## Section 7: Recommendations

Provide actionable recommendations tied to the simulation results. Structure these so an LLM can reframe them for different risk tolerances.

**Primary recommendation:**
[Example: "Proceed with a two-week pilot in Zone 3. Zone 3 handles 35% of daily volume and represents the highest-impact rebalancing opportunity. Pilot cost is approximately $45K, providing a low-risk validation of the simulation's throughput projections before committing to the full rollout."]

**Implementation sequence:**
1. [Example: "Weeks 1-2: Pilot in Zone 3, measure actual vs. simulated pick rates"]
2. [Example: "Week 3: Analyze pilot results, calibrate simulation if needed"]
3. [Example: "Weeks 4-8: Roll out to Zones 1 and 2 if pilot confirms projections"]
4. [Example: "Weeks 9-12: Assess Zones 4-5 consolidation opportunity"]

**Decision triggers:**
[Define the criteria that should trigger specific actions. Example: "If pilot throughput improvement is within 5 percentage points of the simulated 23%, proceed with full rollout. If improvement is below 15%, pause and recalibrate the model before continuing."]

**Risk-framed alternatives:**

- **Risk-averse recommendation:** [Example: "Run the pilot in Zone 3 only. Do not commit to full rollout until pilot data confirms simulated savings within 10%. Budget $45K for pilot only."]
- **Risk-neutral recommendation:** [Example: "Run the pilot in Zone 3 and begin planning the Zone 1-2 rollout in parallel. Commit to full implementation if pilot results are within 20% of projections. Budget $1.2M with $400K contingency."]
- **Risk-tolerant recommendation:** [Example: "Proceed directly to full implementation across all zones. The expected 14-month payback and 92% probability of exceeding break-even justify the investment without a pilot. Budget $1.2M."]

---

## Section 8: Limitations and Caveats

Be transparent about what the simulation does not capture. This section builds trust.

**Model limitations:**
- [Example: "The simulation assumes worker productivity is independent across zones. In practice, morale effects from rebalancing could temporarily reduce productivity."]
- [Example: "Seasonal demand patterns were modeled using only 18 months of data. A longer history might reveal additional cyclical effects."]
- [Example: "The model does not account for equipment downtime during zone reconfiguration."]

**Data limitations:**
- [Example: "Pick rate data before March 2024 used a different tracking methodology and was excluded from calibration."]
- [Example: "Order arrival data does not distinguish between standard and expedited orders, which have different pick time profiles."]

**What this simulation does not address:**
[Explicitly scope what's out of bounds. Example: "This simulation models throughput and labor cost impacts only. It does not model customer satisfaction effects, worker safety incidents, or long-term maintenance costs of the new zone configuration."]

---

## Metadata

**Simulation model version:** [Example: v2.3.1, commit abc1234]
**Template 10 completed by:** [Name and role]
**Date completed:** [YYYY-MM-DD]
**Linked templates:**
- Template 7 (Model Specification): [Location or reference]
- Template 9 (Validation Report): [Location or reference]
**Dashboard location:** [URL or file path to interactive dashboard, if applicable]
**Code repository:** [URL or file path to simulation code]
