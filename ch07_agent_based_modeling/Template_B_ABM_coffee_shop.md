# ABM Template B — Completed Example: Neighborhood Coffee Market (ODD-Based)

The completed code-generation prompt for the coffee shop market model. The ODD spec (Template_A_ABM_coffee_shop.md) is pasted where indicated; the architecture and outputs sections below are the filled-in versions.

---

## The Completed Prompt

```
Generate an agent-based simulation in Python using Mesa based on the
following ODD specification.

===============================================================
ODD SPECIFICATION
===============================================================

[Paste Template_A_ABM_coffee_shop.md here, Sections 0–8]

===============================================================
TECHNICAL REQUIREMENTS
===============================================================

Libraries: mesa, numpy, pandas, matplotlib
Random seeds: sequential from base seed 42, one seed per replication
(Section 8). Route ALL randomness — customer attribute draws,
activation order, word-of-mouth triggers and neighbor selection,
utility tie-breaking — through a single numpy Generator seeded per
replication.

===============================================================
CODE ARCHITECTURE — FOLLOW THE ODD MAPPING
===============================================================

1. Agent subclasses (Element 2):
   - CustomerAgent(mesa.Agent): attributes location, income_level,
     quality_pref, price_sensitivity, max_distance; state variables
     loyalty (dict keyed by shop), chosen_shop_today
   - ShopAgent(mesa.Agent): attributes location, quality, base_price,
     capacity, strategy; state variables price, visits_today,
     revenue_this_month, revenue_last_month

2. CoffeeMarketModel(mesa.Model).step() executes the Element 3
   schedule in exactly this order:
     1. reset_daily_counters (all shops)
     2. decay_loyalty (all customers)
     3. choose_shop (customers, random order re-shuffled each step;
        visits update shop state immediately so crowding binds
        within the day)
     4. word_of_mouth (customers, random order)
     5. DataCollector.collect()
     6. every 30 steps, after collection: adapt_strategy (all shops)

3. One method per Element 7 submodel, names matching the spec:
   decay_loyalty, choose_shop, update_loyalty, word_of_mouth,
   adapt_strategy. Use the parameter values from the Element 7
   parameter tables (price_ref=5.00, loyalty_weight=0.3,
   distance_weight=0.05, purchase_threshold=0.2, loyalty_gain=0.05,
   loyalty_decay=0.01, crowding_factor=0.5, p_wom=0.1, wom_radius=3,
   wom_boost=0.02, price_cut_pct=0.05, price_raise_pct=0.03,
   price_floor=3.00). Do not invent values.

4. Sensing restrictions (Element 4) — enforce in code:
   - CustomerAgent.choose_shop may read: each reachable shop's price,
     quality, and location; its own loyalty and attributes. It may
     NOT read visits_today before choosing (crowding is experienced,
     not observed).
   - ShopAgent.adapt_strategy may read ONLY its own revenue history.
     It must never read another shop's price, revenue, or strategy.

5. CoffeeMarketModel.__init__ implements Element 5: shops at fixed
   scenario coordinates; customers placed by density-weighted cell
   sampling (transit-centered + uniform component); customer
   attributes re-drawn each replication; loyalty initialized to 0.

6. DataCollector (Element 4, Observation):
   Model-level, each step: market share per shop, revenue per shop,
   current price per shop, skip count, mean experienced quality.
   Agent-level, each step: per customer — chosen shop, top utility,
   loyalty vector; per shop — visits_today, revenue_this_month.
   End of run: dominant-loyalty shop per grid cell (spatial map).

7. run_scenario(scenario_config, n_replications, base_seed):
   replication loop per Section 8; scenario configs implement the
   Section 8 parameterization table (Baseline, Quality Positioning,
   Competitive Pricing, Differentiation).

8. analyze_replications(results_list): cross-replication statistics
   and the visualizations below.

===============================================================
REQUIRED OUTPUTS
===============================================================

Per-replication:
- Market share time series per shop (365 steps)
- Price evolution per shop
- Final loyalty distribution across customers

Cross-replication (30 runs), tied to the Element 1 patterns:
- Median market share trajectory per shop with 10th–90th percentile
  bands                                   [Patterns 1, 4]
- Distribution of 12-month market share per shop (histogram)
                                          [Pattern 4]
- Frequency of price-war emergence across replications, with the
  detection rule stated in code (e.g., any shop's price falls below
  90% of its base_price)                  [Pattern 2]
- Spatial loyalty heatmap at step 365 (grid colored by dominant
  shop loyalty per cell)                  [Pattern 3]
- Artisan repeat-visit fraction and final share distribution
                                          [Pattern 5]

Plots:
- Market share trajectories with confidence bands
- Price evolution overlay (all shops, single representative run)
- Spatial loyalty heatmap at step 365
- Owner's 12-month market share histogram across replications

Optional (include if relevant):
- Sensitivity sweep: market share vs. choice-function weights
- Agent trace utility: given a customer ID and step range, print each
  step's utilities, choice, and loyalty state (used directly by
  Template C submodel verification)
- Capacity utilization per shop over time

===============================================================
BEFORE WRITING CODE
===============================================================

List any ambiguities, missing parameters, or contradictions you find
in the spec, and how you resolved them. Do not silently fill gaps.
```

---

## Notes on This Example

The agent-trace utility in the optional outputs is worth requesting every time: Template C's submodel verification needs per-step traces of individual agents, and asking for the tracing tool up front is far cheaper than reconstructing traces from DataCollector output later.

The price-war detection rule is deliberately specified here rather than left to the assistant. "Price war" is an emergent pattern, but *counting* it requires an operational definition, and that definition belongs to you, not to the code generator.

---

*This completed example accompanies Chapter 7 of "Simulation Models for Data Science" by Dan Sullivan, published by O'Reilly Media.*
