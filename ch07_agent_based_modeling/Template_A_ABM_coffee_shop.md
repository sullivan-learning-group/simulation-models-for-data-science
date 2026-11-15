# ABM Template A — Completed Example: Neighborhood Coffee Market (ODD Protocol)

Completed ODD-based spec for the coffee shop market entry model in Chapter 7. Content migrated from the pre-ODD Template A, with the gaps ODD exposed now filled explicitly: the per-step schedule (Element 3), sensing assumptions (Element 4), and submodel parameter tables (Element 7).

> **Note on proposed values:** Parameters marked *[proposed]* did not exist in the pre-ODD spec — the choice function referenced `loyalty_weight`, `distance_weight`, and a purchase threshold without ever assigning them values, and the raw price term was on a different scale than the quality term. ODD's submodel discipline is what surfaced both problems. Align these values with the final model code before publication.

---

## Section 0: Business Context *(book addition — not part of ODD)*

**Business Question:** If our owner opens a second location in this neighborhood, what market share can she expect after 12 months, and how does the outcome change based on her pricing strategy?

**Decision and Decision-Maker:** The coffee shop owner is deciding whether to open a second location in a neighborhood where a national chain and a local artisan roaster already operate, and — if she enters — which positioning strategy to adopt.

**Scenarios to Compare**

| Scenario | Description | What Changes |
|----------|-------------|-------------|
| Baseline | Two existing competitors, no new entry | No owner shop |
| Quality positioning | Owner opens, prices 10% above chain, invests in quality | Owner price = $4.40, quality = 0.75 |
| Competitive pricing | Owner opens, matches chain pricing | Owner price = $4.00, quality = 0.75 |
| Differentiation | Owner opens, adds food menu (higher transaction, slower service) | Owner capacity reduced, avg transaction up |

**Key Assumptions**
```
1. Fixed total customer population; no market expansion from new entrants.
2. Customer preferences initialized from distributions, not survey data.
3. Shops adapt through simple rule-based strategies, not optimization.
```

---

## Element 1: Purpose and Patterns

**Purpose**
```
This model was built to estimate the 12-month market share a new
coffee shop location can capture in a three-competitor neighborhood
market, and to compare the risk profiles of alternative pricing
strategies given that competitors react to the entry.
```

**Patterns** — the credibility criteria for this model. Each becomes a validation row in Template C.

| # | Pattern | Type | How We'll Check It |
|---|---------|------|--------------------|
| 1 | Market share stabilizes after ~100 steps as loyalty accumulates | Expected | Coefficient of variation of daily share falls below 5% and stays there |
| 2 | Price wars emerge in some (not all) replications when shops independently react to revenue declines | Expected | Frequency count across 30 replications; price trajectory plots |
| 3 | Spatial clustering: loyal customers concentrate around each shop, with contested boundary zones | Expected | Loyalty heatmap at step 365 |
| 4 | Quality positioning produces a narrower outcome range than competitive pricing | Expected | Std dev of owner share across replications, by scenario |
| 5 | Higher-priced shops survive on smaller, more loyal customer bases (observed structure of real coffee markets: chain / independent / artisan tiers coexist) | Empirical | Artisan retains positive share with high repeat-visit fraction in most replications |

---

## Element 2: Entities, State Variables, and Scales

**Entities**
```
Agent types:     Customer, Shop
Spatial units:   Grid cells carrying a population-density weight
                 (used only at initialization to place customers)
Environment:     50×50 bounded grid; no global dynamic variables
Collectives:     None
```

### Agent Type: Customer

**Population:** 500 (fixed across the run; see Assumption 1)

**Attributes** (fixed at initialization):

| Attribute | Distribution / Value | Description |
|-----------|---------------------|-------------|
| location | Clustered around transit stops (grid center) + uniform component | Home/work location on grid |
| income_level | Categorical: low (0.3), mid (0.5), high (0.2) | Determines price sensitivity |
| quality_pref | Uniform(0.3, 0.9) | Weight on quality in choice function |
| price_sensitivity | Conditional on income: low=0.7, mid=0.5, high=0.2 | Weight on (normalized) price in choice function |
| max_distance | Lognormal, mean = 8 grid cells | Farthest they'll travel |

**State variables** (change during simulation):

| State Variable | Initial Value | Updated By (submodel) | Description |
|----------------|--------------|----------------------|-------------|
| loyalty[shop] | 0 for all shops | update_loyalty, word_of_mouth | Habit strength per shop; bounded [0, 1] |
| chosen_shop_today | none | choose_shop | Today's choice (or "skip"); used by observation |

### Agent Type: Shop

**Population:** 3–4 depending on scenario

**Attributes** (fixed at initialization):

| Attribute | Owner's Shop | National Chain | Artisan Roaster |
|-----------|-------------|----------------|-----------------|
| location | Scenario coordinates | Fixed coordinates | Fixed coordinates |
| quality | 0.75 | 0.55 | 0.90 |
| base_price | Scenario variable | $4.00 | $6.50 |
| capacity | 150 customers/day | 250 customers/day | 80 customers/day |
| strategy | Scenario variable | Price-cutter | Price-holder |

**State variables** (change during simulation):

| State Variable | Initial Value | Updated By (submodel) | Description |
|----------------|--------------|----------------------|-------------|
| price | base_price | adapt_strategy | Current posted price |
| visits_today | 0 | choose_shop (customer visits) | Resets each step; drives crowding |
| revenue_this_month | 0 | choose_shop (customer visits) | Accumulates over 30-step window |
| revenue_last_month | 0 | adapt_strategy | Basis for trend comparison |

### Spatial Units and Environment

```
Space type:    Grid
Dimensions:    50×50
Topology:      Bounded edges (a neighborhood, not a torus)
```

**Environmental variables:**

| Variable | Spatial Pattern | Static or Dynamic | Description |
|----------|----------------|-------------------|-------------|
| population_density | Higher near transit stops (center), lower at edges | Static | Weights customer placement at initialization only |

### Scales

```
One step represents:   One day
Run length:            365 steps (one year)
One grid cell spans:   ~20 m × 20 m
Spatial extent:        50×50 cells ≈ 1 km² neighborhood
```

---

## Element 3: Process Overview and Scheduling

**Per-step schedule:**

```
Each step (one day):
1. reset_daily_counters — all shops: visits_today = 0
2. decay_loyalty        — all customers: loyalty to every shop decays
                          (applied before choices, so today's visit
                          rebuilds what decay removed)
3. choose_shop + visit  — customers, in random order: evaluate
                          utilities, choose a shop or skip; visiting
                          updates shop revenue/visits and triggers
                          update_loyalty for the visited shop
4. word_of_mouth        — customers, in random order: with probability
                          p_wom, boost a nearby neighbor's loyalty to
                          their currently preferred shop
5. record_observations  — DataCollector records model- and agent-level
                          metrics

Every 30 steps (monthly), after process 5:
6. adapt_strategy       — all shops: compare revenue_this_month to
                          revenue_last_month; trigger strategy response;
                          roll the monthly revenue window
```

**Scheduling decisions:**

```
Activation order:   Random activation for customers, reshuffled each
                    step. Rationale: within a day, arrival order at
                    capacity-constrained shops should not privilege
                    the same customers every day.
State updates:      Immediate for shop visit counts (a customer
                    arriving after capacity is reached experiences
                    crowding TODAY — this is what makes the capacity
                    constraint bind). Loyalty updates are immediate
                    but only read by the choice function on the NEXT
                    step, so within-day order effects on choice are nil.
Periodic processes: Shop adaptation fires at the END of each 30-step
                    cycle, after that day's customer choices — shops
                    react to a completed month, never to a partial one.
```

---

## Element 4: Design Concepts

### Core concepts

**Emergence**
```
Market share equilibria, price wars, and spatial loyalty territories
all emerge from customer choices and shop reactions; none is coded
into any rule. Patterns 1–4 in Element 1 are the emergent outcomes
this model exists to study. NOT emergent (imposed): the fixed
customer population, shop capacities, and the three-tier
quality/price structure of the initial market.
```

**Adaptation**
```
Shops adapt: monthly (every 30 steps), each shop compares revenue to
the prior month and triggers its strategy rule (see adapt_strategy
submodel). Customers do not adapt their decision RULE — their choice
function is fixed — but their loyalty state shifts which choice the
rule produces (see Learning).
```

**Objectives**
```
Customers maximize per-day utility: a weighted combination of
quality, price (negative), habit (loyalty), and travel cost
(negative). Weights vary by agent, which is what makes the
population heterogeneous. Plausibility check for the owner: "some
of my customers chase quality, some chase price, most stick with
habit unless something changes" — the utility function is that
sentence written down.

Shops satisfice rather than optimize: they act only when revenue
moves more than ±10% month-over-month, mirroring how small
businesses actually monitor performance (react to trends, not
continuous optimization).
```

**Sensing**
```
Customers perceive:
- Posted price of every reachable shop (public information)
- Quality of every reachable shop (treated as common knowledge via
  reputation/reviews — a simplifying assumption; a stricter model
  would let customers learn quality only through visits)
- Distance to each shop, and their own loyalty state
- Crowding only upon visiting (NOT observable before choosing)

Shops perceive:
- Their OWN revenue and visit counts only
- NOT competitors' prices, revenue, or strategies

This last restriction matters: price wars in this model emerge
without any shop watching its competitors — each reacts only to its
own revenue decline. Emergence with minimal sensing is a stronger
(and more defensible) result than emergence built on assumed
competitive intelligence.
```

**Interaction**

| Interaction | Type | From → To | Mechanism | Effect |
|-------------|------|-----------|-----------|--------|
| Visit | Direct | Customer → Shop | Customer chooses, spends money | Shop revenue += transaction; visits_today += 1 |
| Quality experience | Direct | Shop → Customer | Service delivered at shop.quality (crowding-adjusted) | Drives loyalty update for the visited shop |
| Crowding | Indirect | Customer → Customer (via shop) | Visits beyond capacity degrade experienced quality | Late-arriving customers gain less loyalty |
| Price/strategy change | Indirect | Shop → all Customers | Monthly adaptation changes posted price | Alters every future utility evaluation |
| Word-of-mouth | Social | Customer → Customer | P = 0.1 per step, random neighbor within 3 cells | Neighbor's loyalty to speaker's preferred shop += boost |

**Stochasticity**

| Random Element | Where It Occurs | Why Stochastic |
|----------------|-----------------|----------------|
| Attribute draws (location, income, preferences, max_distance) | Initialization | Represents real population heterogeneity |
| Customer activation order | Each step | Prevents fixed arrival-order privilege at capacity-bound shops |
| Word-of-mouth trigger and neighbor selection | Each step | Stands in for unmodeled social contact detail |
| Utility tie-breaking | choose_shop | Rare; uniform random among tied shops |

All stochastic draws flow from a single seeded RNG per replication (see Section 8).

**Observation**
```
Model-level (each step):
- Market share per shop (fraction of the day's purchasing customers)
- Revenue per shop
- Current price per shop
- Number of customers who skipped (no purchase)
- Mean experienced quality (crowding-adjusted) across purchases

Agent-level (each step):
- Per customer: shop chosen, top utility value, loyalty vector
- Per shop: visits_today, revenue_this_month

End-of-run only:
- Spatial loyalty map: dominant-loyalty shop per grid cell
```

### Optional concepts

**Basic principles**
```
Customer choice: deterministic discrete-choice (utility-maximization)
with heterogeneous weights — a simplified cousin of random-utility
models used in retail location analysis. Loyalty: habit formation as
simple reinforcement with decay. Shop behavior: satisficing
(Simon) — threshold-triggered rules rather than optimization.
```

**Learning**
```
Borderline case, included deliberately as a teaching point: loyalty
accumulation is a minimal form of learning (experience changes future
choices via state) even though the choice RULE never changes. Shops
do not learn — their strategy rules are fixed for the entire run.
```

**Prediction**
```
No explicit forecasting. One tacit prediction worth naming: the
chain's price-cut rule tacitly predicts that lower prices recover
revenue. When many replications show price cuts failing to recover
revenue (a price war), the model is revealing that this tacit
prediction can be collectively self-defeating.
```

**Collectives**
```
Not used. Customers act individually; shops are single locations,
not chains coordinating strategy across sites.
```

---

## Element 5: Initialization

```
Total agents:           500 customers; 3 shops (baseline) or 4
                        (entry scenarios)
Spatial placement:      Shops at fixed scenario coordinates. Customers
                        placed by sampling cells weighted by
                        population_density (transit-centered), with a
                        uniform component.
Attribute assignment:   Drawn per customer from the distributions in
                        Element 2 at t = 0
Initial state values:   loyalty = 0 for every customer–shop pair;
                        shop price = base_price; all revenue and visit
                        counters = 0
Varies across runs?     All customer attribute draws and placements are
                        re-drawn each replication from that
                        replication's seed. Shop attributes and
                        locations are identical across replications.
From data?              No — initialization is entirely by assumption
                        (see Assumption 2). With neighborhood survey or
                        POS data, the preference distributions and
                        density map are the natural calibration targets.
```

Zero-loyalty initialization means the first ~100 steps are a loyalty-formation transient; Pattern 1 predicts stabilization after it. Whether to treat this as warm-up (excluded from measurement) or as substantively interesting (the entry scenario IS a transient) is recorded in Section 8.

---

## Element 6: Input Data

```
None. The model is driven entirely by its internal rules and
parameters. No external time series (weather, seasonal demand, foot
traffic) enters during the run — every dynamic in the results is
generated by the model itself. Seasonality is a known limitation,
recorded in Template C.
```

---

## Element 7: Submodels

### Submodel: decay_loyalty

**Executed by / when:** All customers; step process 2, before choices.

**Logic:**
```
for each shop s:
    loyalty[s] = max(0, loyalty[s] − loyalty_decay)
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| loyalty_decay | 0.01 | per day | Assumption: habit fades over months, not days (≈100-day half-life scale) |

### Submodel: choose_shop

**Executed by / when:** Each customer, in random order; step process 3. This is the heart of the model.

**Logic:**
```
reachable = shops with distance(customer, shop) < max_distance
for each shop s in reachable:
    utility[s] = quality_pref × s.quality
               − price_sensitivity × (s.price / price_ref)
               + loyalty_weight × loyalty[s]
               − distance_weight × distance(customer, s)
if max(utility) ≥ purchase_threshold:
    visit argmax shop (uniform random among ties):
        shop.revenue_this_month += transaction_value
        shop.visits_today += 1
        experienced_quality = s.quality × (1 if visits_today ≤ capacity
                                           else crowding_factor)
        run update_loyalty(s, experienced_quality)
else:
    skip (no purchase today)
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| price_ref | $5.00 | $ | *[proposed]* Normalizes price to ~[0.8, 1.3] so price and quality terms are on comparable scales; the pre-ODD spec used raw dollars, which let price dominate every other term |
| loyalty_weight | 0.3 | – | *[proposed]* Habit matters but doesn't override a large quality/price gap |
| distance_weight | 0.05 | per cell | *[proposed]* At max_distance ≈ 8 cells, travel cost ≈ 0.4 — comparable to a full quality-preference swing |
| purchase_threshold | 0.2 | – | *[proposed]* Calibrate so the skip rate is plausible (~10–20% of customers on a typical day) |
| transaction_value | shop price (differentiation scenario: price + food margin) | $ | Scenario definition |

### Submodel: update_loyalty

**Executed by / when:** The visiting customer, immediately upon a visit; called from choose_shop.

**Logic:**
```
loyalty[visited_shop] = min(1, loyalty[visited_shop]
                            + loyalty_gain × experienced_quality / shop.quality)
(Crowded visits earn proportionally less loyalty; an uncrowded visit
earns the full loyalty_gain.)
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| loyalty_gain | 0.05 | per visit | With decay 0.01/day, a ~weekly customer sustains loyalty; less frequent visitors drift away |
| crowding_factor | 0.5 | – | Assumption: an over-capacity visit delivers half the quality experience |

### Submodel: word_of_mouth

**Executed by / when:** All customers, in random order; step process 4.

**Logic:**
```
with probability p_wom:
    neighbor = random customer within wom_radius
    preferred = argmax over shops of this customer's loyalty
    if loyalty[preferred] > 0:
        neighbor.loyalty[preferred] += wom_boost (capped at 1)
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| p_wom | 0.1 | per customer per day | Assumption; sensitivity-swept in Template C |
| wom_radius | 3 | grid cells (~60 m) | Word-of-mouth is hyper-local (neighbors, coworkers) |
| wom_boost | 0.02 | – | Weaker than direct experience (0.05); hearsay < habit |

### Submodel: adapt_strategy

**Executed by / when:** All shops; every 30 steps, after that day's step processes.

**Logic:**
```
trend = (revenue_this_month − revenue_last_month) / revenue_last_month
if trend < −drop_threshold[strategy]:
    Chain:  price = max(price × (1 − price_cut_pct), price_floor)
    Owner:  scenario-dependent — price cut (competitive pricing) or
            hold price / maintain quality investment (quality
            positioning, differentiation)
    Artisan: hold price; reduce hours (modeled as capacity × 0.85)
elif trend > +growth_threshold:
    Chain, Owner: price = price × (1 + price_raise_pct)
    Artisan: no change
roll window: revenue_last_month = revenue_this_month; reset accumulator
```

**Parameters:**

| Parameter | Value | Units | Source / Justification |
|-----------|-------|-------|------------------------|
| drop_threshold | Chain/Owner: 0.10; Artisan: 0.15 | – | Scenario definition (pre-ODD spec) |
| growth_threshold | 0.10 | – | Symmetric with drop trigger |
| price_cut_pct | 0.05 | – | *[proposed]* Small repeated cuts let wars escalate gradually across months |
| price_raise_pct | 0.03 | – | *[proposed]* Raises are more cautious than cuts |
| price_floor | $3.00 | $ | *[proposed]* Approximate unit-cost bound; prevents runaway race to zero |

---

## Section 8: Simulation Experiments *(book addition — not part of ODD)*

**Scenario parameterization:**

| Parameter | Baseline | Quality Positioning | Competitive Pricing | Differentiation |
|-----------|----------|--------------------|--------------------|-----------------|
| Owner shop present | No | Yes | Yes | Yes |
| Owner base_price | — | $4.40 | $4.00 | $4.40 |
| Owner quality | — | 0.75 | 0.75 | 0.75 |
| Owner capacity | — | 150/day | 150/day | 110/day |
| Owner transaction_value | — | price | price | price + $2.50 food margin |
| Owner adapt rule | — | Hold price | Cut price on drop | Hold price |

**Run design:**

```
Steps per run:    365
Replications:     30 per scenario (adequacy verified by the
                  convergence check in Template C, Section 5)
Random seeds:     Sequential from base seed 42; one RNG per replication
Warm-up:          None excluded — the loyalty-formation transient
                  (first ~100 steps) is part of the entry story, not
                  noise. Report 12-month (step 365) metrics as primary,
                  and note stabilization timing per Pattern 1.
Outputs recorded: As specified in Element 4, Observation
```

---

*This completed example accompanies Chapter 7 of "Simulation Models for Data Science" by Dan Sullivan, published by O'Reilly Media.*
