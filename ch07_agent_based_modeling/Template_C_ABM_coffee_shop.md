# ABM Template C — Completed: Neighborhood Coffee Market (ODD-Based)

Validation record for the coffee shop market model, keyed to the ODD spec in
Template_A_ABM_coffee_shop.md and the generated code in `code/coffee_shop_abm.py`
(Mesa 3.3.1, seeds 42–71). **All numbers below are from actual model runs**
(120 core replications + probes; see `code/run_experiments.py` and
`code/results/`). This replaces the earlier illustrative version — the real model
contradicts several of its projected findings, and those contradictions are the
most valuable output of the validation. Full narrative in
`coffee_shop_validation_report.md`.

**Calibration deltas applied before these runs (documented spec deviations):**

| Delta | Spec value | Used | Reason |
|-------|-----------|------|--------|
| purchase_threshold (Element 7) | 0.2 *[proposed]* | −0.30 | As proposed, ~99% of customers skip every day (dead market) |
| Customer placement (build assumption) | 60% clustered, σ=8 | 75% clustered, σ=6 | With max_distance mean 8, wider placement left most customers unable to reach any shop |

---

## Section 1: Submodel Verification (Micro Level)

**choose_shop:** Traced 4 profile customers (price-sensitive near chain,
quality-seeker, near-tied utilities, near purchase threshold) for 10 steps each —
40 decisions independently recomputed from the spec formula: **0 mismatches**.
Tie-breaking draws from the seeded RNG.

**decay_loyalty / update_loyalty:** Loyalty bounds [0, 1] hold across a full
120-step run for all 500 customers × 3 shops. Gains and decay match parameter
values.

**word_of_mouth:** Fires at p = 0.1 among eligible customers; 159 customers
eligible (neighbors + positive loyalty) after 60 steps; boost +0.02 confirmed.

**adapt_strategy / periodic timing:** Fired at exactly steps 30, 60, 90, at the
end-of-step position per the Element 3 schedule. **PASS.**

---

## Section 2: Spec Conformance Checks

```
Scheduling: step() order matches Element 3                       [Y]
Sensing: adapt_strategy reads no other agent's state (static
  inspection of method source)                                   [Y]
Sensing: choose_shop does not read visits_today before choosing  [Y]
Stochasticity: all draws flow from per-replication seeded RNGs   [Y]
Reproducibility: seed 42 twice -> identical dataframes           [Y]
Seed sensitivity: seed 43 differs                                [Y]
Parameters: match Element 7 tables, EXCEPT the documented
  purchase_threshold calibration delta above                     [Y*]
```

---

## Section 3: Pattern-Oriented Validation (Macro Level)

Rows copied from Element 1 of the spec. **Three of five patterns failed — and
each failure is a structural finding, not a bug** (submodels verified correct in
Sections 1–2).

| # | Pattern (from Element 1) | Observed? | Evidence |
|---|--------------------------|-----------|----------|
| 1 | Market share stabilizes after ~100 steps | **NO — stronger than stabilization: the market is frozen from day 1.** | Within-run CV of daily owner share ≤ 0.002 in *every* 50-day window, including days 0–50. There is no transient. |
| 2 | Price war emerges in some replications | **NO — 0 of 120 core runs; no shop ever changed price in any run or probe.** | Price min = max = base price for every shop, every scenario. |
| 3 | Spatial clustering of loyalty with contested boundaries | **YES (with caveat)** | Clear territories in the loyalty map (Figure: spatial_loyalty). Caveat: the pattern is static geometric sorting present from day 1, not a structure that *develops*. |
| 4 | Quality positioning → narrower outcome range than competitive pricing | **NO** | Std of owner share: 0.041 (quality) vs. 0.038 (competitive). Without price wars there is no mechanism to widen the competitive-pricing range. |
| 5 | Artisan survives on smaller, more loyal base | **PARTIAL** | Artisan holds 21–23% share in every run. But repeat-visit fraction is 0.997 for *all three* shops — in a frozen market "more loyal" cannot distinguish anyone. |

**Diagnosis (P1, P2, P4, P5 share one root cause):** the choice function is
deterministic. Given fixed attributes and prices, every customer picks the same
shop on day 1, loyalty entrenches that choice, and nothing ever changes: no
churn, no revenue trends, no adaptation triggers, no dynamics. The spec's
Stochasticity concept lists randomness in initialization, activation order, and
word-of-mouth — but not in the decision itself. See spec revision R1.

**Sanity checks:**
```
Prices within $3.00–$7.00?                  [Y — trivially; prices never moved]
Shares + skip fraction account for all 500? [Y — every step]
Spatial pattern consistent with geography?  [Y]
Skip fraction plausible (target 10–25%)?    [N — 68.7%. 43% of customers are
                                             structurally unable to reach any
                                             shop (max_distance mean 8 on a
                                             50×50 grid); the rest is utility-
                                             driven. See revision R4.]
Capacity constraint ever binds?             [N — 0 days over capacity, any shop,
                                             any run (max owner day: 83 of 150).
                                             The crowding submodel is inert.
                                             See revision R5.]
```

---

## Section 4: Sensitivity to Agent Parameters

10 replications per point, quality-positioning scenario, owner 12-month share:

| Parameter | Low | High | Share @ Low | Share @ High | Swing | Rank |
|-----------|-----|------|-------------|--------------|-------|------|
| purchase_threshold | −0.45 | −0.15 | 38.0% | 43.4% | 5.4 pts | 1 |
| distance_weight | 0.025 | 0.10 | 43.4% | 39.1% | 4.3 pts | 2 |
| qpref bounds (midpoint) | (0.1–0.7) | (0.5–1.1) | 40.8% | 40.1% | 0.7 pts | 3 |
| loyalty_weight | 0.15 | 0.45 | 41.5% | 41.4% | 0.1 pts | 4 |
| p_wom | 0.05 | 0.20 | 41.4% | 41.4% | 0.0 pts | 5 |

**Key driver:** market-size parameters (threshold, distance cost), not
preference parameters. **This inverts the illustrative version's claim** that
quality_pref would be the strongest driver: because the owner sits between the
chain and the artisan on quality and price, preference shifts reallocate share
between the *incumbents* and leave the owner nearly untouched. loyalty_weight
and p_wom have no effect because a frozen market gives loyalty nothing to do.

---

## Section 5: Sensitivity to Population and Scale

| Population | Owner share (10 reps) | Price war freq | Qualitatively same? |
|------------|----------------------|----------------|--------------------|
| 200 | 37.1% | 0.00 | Y (small-n noise at 200) |
| 500 | 41.5% | 0.00 | Y |
| 1,000 | 41.1% | 0.00 | Y |

---

## Section 6: Replication Analysis

Owner 12-month share, quality positioning, 30 replications: mean 40.9%,
median 40.8%, P10 36.5%, P90 46.0%, std 4.1%.

| Replications | Cumulative mean | Change | Stable? |
|--------------|-----------------|--------|---------|
| 10 | 41.5% | — | |
| 20 | 41.1% | −0.4 pts | Approaching |
| 30 | 40.7% | −0.6 pts (25→30) | **Marginal** — still drifting slightly; use 50 replications in the published run |

---

## Section 7: Scenario Comparison

30 replications each; share of purchases at 12 months:

| Metric | Baseline | Quality Positioning | Competitive Pricing | Differentiation |
|--------|----------|--------------------|--------------------|-----------------|
| Owner median share | — | 40.8% | 44.2% | 40.8% |
| Owner P10 / P90 | — | 36.5 / 46.0% | 39.5 / 50.0% | 36.5 / 46.0% |
| Chain median share | 68.0% | 37.3% | 34.6% | 37.3% |
| Artisan median share | 32.0% | 22.1% | 21.2% | 22.1% |
| Price war frequency | 0% | 0% | 0% | 0% |

**Two anomalies vs. the illustrative version:** (1) Competitive pricing
*dominates* quality positioning (+3.4 pts median, no downside) because the price
war that was supposed to punish it never occurs. (2) **Differentiation is
numerically identical to quality positioning** — the reduced capacity (110)
never binds (max 83 visits/day) and the food margin only adds revenue, so the
scenario's intended trade-off never engages.

**Delayed-entry probe** (spec variant: incumbents run alone for 120 days, owner
enters day 120; 10 reps): owner share falls to **32.6%** (quality) / **35.1%**
(competitive) — the incumbents' accumulated loyalty is a real moat, and the
core scenarios (everyone opens simultaneously) overstate the owner's share by
~8 points. Still no price wars: the entry shock spreads across the owner's slow
loyalty build-up, so no incumbent ever sees a >10% month-over-month drop.

---

## Section 8: Results Summary

**One-Paragraph Finding**
```
The verified model is a static sorting model, not a dynamic market: with a
deterministic choice function, customers sort themselves among shops on day
one and never move again. Within that frame, the owner's location captures
37–50% of purchases at 12 months (median ~41%) — but the market itself
reaches only 57% of the 500 residents, competitive pricing carries no
simulated penalty because price wars cannot occur, and simultaneous opening
(no incumbency) inflates the owner's share by roughly 8 points versus a
delayed-entry variant. BUSINESS CONCLUSIONS ARE PREMATURE: the spec needs
the revisions below before its scenario comparison should inform the
owner's decision.
```

**Spec revisions recommended by this validation (in priority order)**
```
R1. Add decision stochasticity (a per-day taste shock in choose_shop, e.g.,
    Normal(0, 0.1–0.2) or logit choice). Probe: restores churn and genuine
    dynamics (late-run share CV 0.02–0.04 vs. 0.002). Without it, Patterns
    1, 2, 4, and 5 are structurally unreachable. Update Element 4
    (Stochasticity) and the choose_shop submodel.
R2. Model entry explicitly: burn in the incumbents, then activate the owner
    mid-run (entry_step). Changes the headline answer by ~8 points and makes
    "entry into an established market" — the business question — the thing
    actually simulated. Update Elements 3 and 5, Section 8.
R3. Redesign the adaptation trigger. Month-over-month revenue trend never
    fires under any variant probed; loyalty_weight 0.3 is a moat no feasible
    price/quality gap can cross, so demand shocks large enough to trigger it
    cannot occur. Consider comparing revenue to a pre-entry reference or a
    cumulative benchmark, and revisit the loyalty/price scale ratio.
R4. Resolve the market-size geometry: max_distance (mean 8 cells) on a 50×50
    grid strands 43% of customers. Probe with mean 15 shows the utility
    distance cost then binds instead (skip stays ~60%). Decide the intended
    served-market fraction and set threshold/distance/max_distance together.
R5. Give differentiation a mechanism: at realized volumes its capacity
    reduction never binds, making it identical to quality positioning plus
    free margin. Lower capacity further, raise demand, or model service-time
    quality effects.
R6. Raise replications to 50 (convergence still drifting ~0.6 pts at 30).
```

**Key Numbers**

| Metric | Value | What It Means |
|--------|-------|---------------|
| Owner median share (simultaneous start) | 41–44% | Upper bound; assumes no incumbency |
| Owner share with 120-day incumbency probe | 33–35% | More faithful to the actual business question |
| Served market | 57% of 500 residents | Geometry + utility exclude the rest |
| Price wars observed | 0 in 120 runs + all probes | Pattern 2 unreachable under current spec |

**Limitations** (read off the spec, plus validation findings)
```
- All spec-level limitations stand (fixed population, assumed preferences, no
  input data / seasonality, satisficing shops).
- Added by validation: deterministic choice (no churn), simultaneous start
  (no incumbency), inert crowding/capacity submodel, and an adaptation trigger
  that cannot fire. These are properties of the spec, faithfully implemented —
  which is exactly what the ODD workflow is supposed to reveal.
```

---

*Produced by the actual model runs of 2026-08-19 (Mesa 3.3.1). Companion code
and results in `code/`; figures in `images/ch07/`.*
