"""
Coffee Shop System Dynamics Model
=================================

Generated from SD Template A (coffee shop) via SD Template B.

Model time unit: months. Horizon 24 months. Reporting interval 0.1 month.
Integration: scipy.integrate.solve_ivp, segment by segment across the
declared discontinuities so that steps and pulse edges land on segment
boundaries.

Every parameter comes from section 9, section 13, or section 15 of the spec.
Nothing is invented. Where the spec does not supply something the code needs,
the gap is named in SPEC_GAPS (printed by main) rather than filled with a
guess.

State vector
------------
    0  customer_base       stock,  section 6
    1  brand_reputation    stock,  section 6
    2  cash_reserves       stock,  section 6
    3  staff_fte           stock,  section 8/13 (hiring SMOOTH)
    4  wom_smoothed        stock,  section 13 (word of mouth SMOOTH)
    5  cum_revenue         accumulator, not a behavioral stock
    6  cum_expense         accumulator, not a behavioral stock

Indices 5 and 6 have no feedback into the system. They exist only so that
cumulative revenue and cumulative expenses are integrated exactly rather than
reconstructed by quadrature on the 0.1 month reporting grid, which would
misprice the 0.1 month investment pulse.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

try:
    from SALib.sample import sobol as sobol_sample
    from SALib.analyze import sobol as sobol_analyze
    HAVE_SALIB = True
except ImportError:  # pragma: no cover
    HAVE_SALIB = False


# ---------------------------------------------------------------------------
# Spec constants that are not parameters
# ---------------------------------------------------------------------------

WEEKS_PER_MONTH = 4.33          # section 2, conversion factor
HORIZON = 24.0                  # section 2
REPORTING_INTERVAL = 0.1        # section 2

# Section 6 stock table, initial cash. Measured (bank balance).
CASH_RESERVES_INIT = 25_000.0

# Milestones used in the summary table. The spec asks for "key time points"
# and "reporting milestones" without enumerating them; see SPEC_GAPS.
MILESTONES = [0.0, 1.0, 6.0, 12.0, 18.0, 24.0]

STATE_NAMES = [
    "customer_base",
    "brand_reputation",
    "cash_reserves",
    "staff_fte",
    "wom_smoothed",
    "cum_revenue",
    "cum_expense",
]

SPEC_GAPS = [
    "Section 12 describes each feedback loop in words but does not name a "
    "coupling parameter per loop. structural_sensitivity() uses the parameter "
    "each loop's description routes through (R1: wom_coefficient, B1: w_wait, "
    "B2: price_sensitivity) and additionally offers a true B1 knockout that "
    "freezes wait_time_pressure, because scaling w_wait shifts the level of "
    "satisfaction as well as breaking the loop.",
    "Section 16 gives distributions but no Monte Carlo iteration count, and "
    "no Sobol sample size. These are passed in by the caller and reported as "
    "analyst choices, not spec values.",
    "The spec asks for a summary table at 'key time points' without listing "
    "them. MILESTONES = [0, 1, 6, 12, 18, 24] months is an analyst choice.",
    "Section 6 lists brand_reputation initial value as 76.5 while calling it "
    "'its own equilibrium'. The exact equilibrium under section 9 parameters "
    "is 100 x satisfaction(t=0) = 76.4517. initial_state() computes the "
    "equilibrium, per code architecture rule 2; 76.5 is the spec's rounding.",
    "Cumulative revenue and cumulative expense are carried as accumulator "
    "states (initial value 0 by definition). They are not stocks in section 6.",
    "Section 3 gives monthly revenue as 8,500-9,200 historically but "
    "8,500-10,000 in the 'baseline must reproduce' column. The check uses the "
    "must-reproduce column.",
]


# ---------------------------------------------------------------------------
# 1. default_params
# ---------------------------------------------------------------------------

def default_params() -> dict:
    """Parameter dictionary built directly from sections 9, 13 and 15.

    One key per table row, using the spec's names. Delay durations are
    converted from weeks to months here so nothing downstream has to.
    Exogenous inputs carry their baseline (no policy) values, so a scenario
    is a dictionary update rather than a code change.
    """
    p = {
        # --- section 9: demand and retention ---------------------------
        "base_acquisition": 20.0,          # customers/month
        "reference_reputation": 76.5,      # index, fixed
        "wom_coefficient": 0.06,           # leads/customer/month at satisfaction 1
        "conversion_rate": 0.25,           # dimensionless
        "base_churn": 0.07,                # 1/month
        "price_sensitivity": 1.5,          # churn multiplier per unit price change
        "retention_strength": 0.8,         # dimensionless
        "satisfaction_reference": 0.60,    # index, fixed

        # --- section 9: service quality --------------------------------
        "equipment_level_base": 0.60,
        "equipment_level_upgraded": 0.90,
        "staff_experience": 0.70,
        "w_equipment": 0.65,
        "w_staff": 0.35,                   # complement of w_equipment

        # --- section 9: capacity ---------------------------------------
        "equipment_capacity_base": 520.0,      # customers/month
        "equipment_capacity_upgraded": 700.0,  # customers/month
        "customers_per_fte": 130.0,            # customers/month/FTE
        "target_load_per_fte": 100.0,          # customers/month/FTE
        "max_fte": 4.0,                        # FTE, fixed

        # --- section 9: satisfaction and value -------------------------
        "w_service": 0.6,
        "w_wait": 0.3,
        "w_value": 0.1,
        "value_sensitivity": 2.0,

        # --- section 9: financial --------------------------------------
        "visits_per_month": 4.0,           # visits/customer/month
        "avg_transaction": 5.50,           # USD/visit
        "fixed_costs": 5_000.0,            # USD/month
        "variable_cost_fraction": 0.35,    # share of revenue

        # --- section 13: delays, weeks converted to months -------------
        "wom_delay": 6.0 / WEEKS_PER_MONTH,          # 1.386 months
        "reputation_delay": 8.0 / WEEKS_PER_MONTH,   # 1.848 months
        "hiring_delay": 3.0 / WEEKS_PER_MONTH,       # 0.693 months

        # --- section 15: exogenous inputs, baseline values -------------
        "invest_enabled": False,
        "price_enabled": False,
        "investment_amount": 15_000.0,     # USD, section 15/18
        "investment_pulse_time": 1.0,      # month
        "investment_pulse_width": 0.1,     # month
        "equipment_step_time": 1.0,        # month
        "price_step_time": 1.0,            # month
        "price_step_magnitude": 0.10,      # +10%
        "demand_multiplier": 1.0,          # constant, 1.0 in deterministic runs

        # --- structural-analysis hook (see SPEC_GAPS) ------------------
        # None means the loop is live; a float freezes wait_time_pressure
        # at that value, which knocks out B1 without moving satisfaction's
        # level the way w_wait = 0 would.
        "freeze_wait_pressure": None,
    }
    return p


# Section 9 plausible ranges, for the OAT sweep. Rows marked "fixed" or
# "complement of w_equipment" are excluded.
PARAM_RANGES = {
    "base_acquisition": (12.0, 28.0),
    "wom_coefficient": (0.03, 0.10),
    "conversion_rate": (0.18, 0.32),
    "base_churn": (0.055, 0.085),
    "price_sensitivity": (0.8, 2.5),
    "retention_strength": (0.5, 1.1),
    "equipment_level_base": (0.45, 0.70),
    "equipment_level_upgraded": (0.80, 0.95),
    "staff_experience": (0.55, 0.85),
    "w_equipment": (0.5, 0.8),
    "equipment_capacity_base": (480.0, 560.0),
    "equipment_capacity_upgraded": (640.0, 760.0),
    "customers_per_fte": (110.0, 150.0),
    "target_load_per_fte": (85.0, 120.0),
    "w_service": (0.5, 0.7),
    "w_wait": (0.2, 0.4),
    "w_value": (0.05, 0.2),
    "value_sensitivity": (1.0, 3.0),
    "visits_per_month": (3.5, 4.5),
    "avg_transaction": (5.20, 5.80),
    "fixed_costs": (4_700.0, 5_300.0),
    "variable_cost_fraction": (0.30, 0.40),
}


def _with(params: dict, **updates) -> dict:
    """Copy of params with updates applied. w_staff tracks w_equipment."""
    q = dict(params)
    q.update(updates)
    if "w_equipment" in updates:
        q["w_staff"] = 1.0 - q["w_equipment"]   # section 9: complement
    return q


# ---------------------------------------------------------------------------
# Exogenous drivers, section 15
# ---------------------------------------------------------------------------

def exogenous_inputs(t: float, p: dict) -> dict:
    """Equipment state, price level and investment rate at time t.

    Steps are right continuous: the upgrade and the price change are in
    force from t = step_time onward. The investment pulse is closed on the
    left and open on the right, [t0, t0 + width), so its integral is exactly
    investment_amount.
    """
    upgraded = p["invest_enabled"] and t >= p["equipment_step_time"]
    equipment_level = (p["equipment_level_upgraded"] if upgraded
                       else p["equipment_level_base"])
    equipment_capacity = (p["equipment_capacity_upgraded"] if upgraded
                          else p["equipment_capacity_base"])

    price_change = (p["price_step_magnitude"]
                    if (p["price_enabled"] and t >= p["price_step_time"])
                    else 0.0)

    t0 = p["investment_pulse_time"]
    w = p["investment_pulse_width"]
    investment_rate = (p["investment_amount"] / w
                       if (p["invest_enabled"] and t0 <= t < t0 + w)
                       else 0.0)

    return {
        "equipment_level": equipment_level,
        "equipment_capacity": equipment_capacity,
        "price_change": price_change,
        "investment_rate": investment_rate,
    }


# ---------------------------------------------------------------------------
# 4. compute_auxiliaries
# ---------------------------------------------------------------------------

def compute_auxiliaries(state, params: dict, t: float) -> dict:
    """Every auxiliary in section 8, in dependency order.

    Functional forms and anchor points follow section 10 and the equation
    block in section 14 exactly. Clips from section 11 are applied at the
    point each quantity is computed, not afterwards.
    """
    p = params
    customer_base = max(state[0], 0.0)          # section 11 non-negativity
    brand_reputation = state[1]
    staff_fte = state[3]
    wom_smoothed = state[4]

    ex = exogenous_inputs(t, p)
    equipment_level = ex["equipment_level"]
    equipment_capacity = ex["equipment_capacity"]
    price_change = ex["price_change"]
    investment_rate = ex["investment_rate"]

    # capacity chain
    staff_capacity = staff_fte * p["customers_per_fte"]
    capacity = max(min(staff_capacity, equipment_capacity), 1.0)   # section 11
    utilization = customer_base / capacity

    # section 10: linear ramp 0.75 -> 0.0, 0.925 -> 0.5, 1.10 -> 1.0
    if p.get("freeze_wait_pressure") is None:
        wait_time_pressure = min(max((utilization - 0.75) / 0.35, 0.0), 1.0)
    else:
        wait_time_pressure = float(p["freeze_wait_pressure"])

    service_quality_index = (p["w_equipment"] * equipment_level
                             + p["w_staff"] * p["staff_experience"])

    # section 10: 0.0 -> 1.0, +0.10 -> 0.80, +0.50 -> 0.0
    perceived_value = min(max(1.0 - p["value_sensitivity"] * price_change,
                              0.0), 1.0)

    satisfaction = min(max(p["w_service"] * service_quality_index
                           + p["w_wait"] * (1.0 - wait_time_pressure)
                           + p["w_value"] * perceived_value, 0.0), 1.0)

    word_of_mouth = customer_base * satisfaction * p["wom_coefficient"]
    acquisition_from_wom = wom_smoothed          # output of the SMOOTH stock

    # section 10: proportional to reputation / 76.5
    base_acquisition_effective = (p["base_acquisition"]
                                  * (brand_reputation / p["reference_reputation"])
                                  * p["demand_multiplier"])
    acquisition_rate = base_acquisition_effective + acquisition_from_wom

    # section 10: linear in (satisfaction - 0.60), clipped to [-0.5, +0.6]
    retention_effect = min(max(p["retention_strength"]
                               * (satisfaction - p["satisfaction_reference"]),
                               -0.5), 0.6)

    churn_fraction = (p["base_churn"]
                      * (1.0 + p["price_sensitivity"] * price_change)
                      * (1.0 - retention_effect))
    churn_rate = customer_base * churn_fraction

    revenue_inflow = (customer_base * p["visits_per_month"]
                      * p["avg_transaction"] * (1.0 + price_change))
    expense_outflow = (p["fixed_costs"]
                       + p["variable_cost_fraction"] * revenue_inflow
                       + investment_rate)

    reputation_target = 100.0 * satisfaction
    desired_fte = min(max(customer_base / p["target_load_per_fte"], 0.5),
                      p["max_fte"])                                # section 11

    return {
        "equipment_level": equipment_level,
        "equipment_capacity": equipment_capacity,
        "price_change": price_change,
        "investment_rate": investment_rate,
        "staff_capacity": staff_capacity,
        "capacity": capacity,
        "utilization": utilization,
        "wait_time_pressure": wait_time_pressure,
        "service_quality_index": service_quality_index,
        "perceived_value": perceived_value,
        "satisfaction": satisfaction,
        "word_of_mouth": word_of_mouth,
        "acquisition_from_wom": acquisition_from_wom,
        "base_acquisition_effective": base_acquisition_effective,
        "acquisition_rate": acquisition_rate,
        "retention_effect": retention_effect,
        "churn_fraction": churn_fraction,
        "churn_rate": churn_rate,
        "revenue_inflow": revenue_inflow,
        "expense_outflow": expense_outflow,
        "net_cash_flow": revenue_inflow - expense_outflow,
        "reputation_target": reputation_target,
        "desired_fte": desired_fte,
    }


# ---------------------------------------------------------------------------
# 3. system_model
# ---------------------------------------------------------------------------

def system_model(t: float, state, params: dict):
    """Stock equations from section 14, plus the two accumulators."""
    a = compute_auxiliaries(state, params, t)
    p = params

    d_customer_base = a["acquisition_rate"] - a["churn_rate"]
    d_brand_reputation = ((a["reputation_target"] - state[1])
                          / p["reputation_delay"])
    d_cash_reserves = a["revenue_inflow"] - a["expense_outflow"]
    d_staff_fte = (a["desired_fte"] - state[3]) / p["hiring_delay"]
    d_wom_smoothed = ((a["word_of_mouth"] * p["conversion_rate"] - state[4])
                      / p["wom_delay"])

    return [
        d_customer_base,
        d_brand_reputation,
        d_cash_reserves,
        d_staff_fte,
        d_wom_smoothed,
        a["revenue_inflow"],     # cum_revenue accumulator
        a["expense_outflow"],    # cum_expense accumulator
    ]


# ---------------------------------------------------------------------------
# 2. initial_state
# ---------------------------------------------------------------------------

def initial_state(params: dict):
    """Initial state vector.

    customer_base and cash_reserves are measured values from section 6.
    Every stock driven toward a target starts at that target under baseline
    (no policy) inputs, so the baseline does not drift on its own:

      staff_fte        -> desired_fte(t=0)                        = 4.0 FTE
      wom_smoothed     -> customer_base x satisfaction
                          x wom_coefficient x conversion_rate     = 4.59/month
      brand_reputation -> 100 x satisfaction(t=0)                 = 76.45

    Section 6 prints 76.5 for brand_reputation. The exact equilibrium is
    76.4517; the difference is the spec's rounding of satisfaction to 0.765.
    """
    p = params
    customer_base = 400.0        # section 6, measured (loyalty actives)

    # Baseline inputs at t = 0: no upgrade, no price change, no pulse.
    base = _with(p, invest_enabled=False, price_enabled=False)
    staff_fte0 = min(max(customer_base / p["target_load_per_fte"], 0.5),
                     p["max_fte"])

    probe = [customer_base, p["reference_reputation"], CASH_RESERVES_INIT,
             staff_fte0, 0.0, 0.0, 0.0]
    a0 = compute_auxiliaries(probe, base, 0.0)

    brand_reputation = 100.0 * a0["satisfaction"]
    wom_smoothed = (customer_base * a0["satisfaction"]
                    * p["wom_coefficient"] * p["conversion_rate"])

    return [customer_base, brand_reputation, CASH_RESERVES_INIT,
            staff_fte0, wom_smoothed, 0.0, 0.0]


# ---------------------------------------------------------------------------
# 5. breakpoints
# ---------------------------------------------------------------------------

def breakpoints(params: dict, t_span) -> list:
    """Sorted discontinuity times from sections 2 and 15, clipped to horizon.

    Only the discontinuities a scenario actually activates are returned, so
    the baseline integrates as a single segment. Section 2 declares month 1.0
    (equipment and price steps) and month 1.1 (the closing pulse edge).
    """
    t0, t1 = t_span
    times = set()
    if params["invest_enabled"]:
        times.add(params["equipment_step_time"])
        times.add(params["investment_pulse_time"])
        times.add(params["investment_pulse_time"] + params["investment_pulse_width"])
    if params["price_enabled"]:
        times.add(params["price_step_time"])

    interior = sorted(t for t in times if t0 < t < t1)
    return [t0] + interior + [t1]


# ---------------------------------------------------------------------------
# 6. run_scenario
# ---------------------------------------------------------------------------

def run_scenario(params: dict, t_span=(0.0, HORIZON), y0=None,
                 reporting_interval: float = REPORTING_INTERVAL) -> pd.DataFrame:
    """Integrate segment by segment and return the reporting-grid DataFrame.

    Every step and pulse edge lands on a segment boundary rather than inside
    one. In a segment no longer than the reporting interval, max_step is held
    to a quarter of the segment width, which gives four solver evaluations
    across the 0.1 month investment pulse as section 15 requires.
    """
    if y0 is None:
        y0 = initial_state(params)

    edges = breakpoints(params, t_span)
    grid = np.round(np.arange(t_span[0], t_span[1] + 1e-9, reporting_interval), 10)

    times, states = [], []
    y = list(y0)

    for i in range(len(edges) - 1):
        a, b = edges[i], edges[i + 1]
        width = b - a
        if i == 0:
            t_eval = grid[(grid >= a - 1e-9) & (grid <= b + 1e-9)]
        else:
            t_eval = grid[(grid > a + 1e-9) & (grid <= b + 1e-9)]

        max_step = width / 4.0 if width <= reporting_interval + 1e-12 else np.inf

        sol = solve_ivp(
            system_model, (a, b), y, args=(params,),
            method="LSODA", t_eval=t_eval if len(t_eval) else None,
            max_step=max_step, rtol=1e-8, atol=1e-8, dense_output=False,
        )
        if not sol.success:
            raise RuntimeError(f"Integration failed on [{a}, {b}]: {sol.message}")

        if len(t_eval):
            times.extend(sol.t.tolist())
            states.extend(sol.y.T.tolist())
            y = sol.y[:, -1].tolist()
        else:
            # Segment carries no reporting point; still advance the state.
            sol2 = solve_ivp(system_model, (a, b), y, args=(params,),
                             method="LSODA", max_step=max_step,
                             rtol=1e-8, atol=1e-8)
            y = sol2.y[:, -1].tolist()

        # Re-anchor exactly on the boundary so the next segment starts clean.
        if len(t_eval) and abs(times[-1] - b) > 1e-9:
            sol3 = solve_ivp(system_model, (times[-1], b), y, args=(params,),
                             method="LSODA", max_step=max_step,
                             rtol=1e-8, atol=1e-8)
            y = sol3.y[:, -1].tolist()

    arr = np.array(states)
    df = pd.DataFrame(arr, columns=STATE_NAMES)
    df.insert(0, "time", times)

    aux_rows = [compute_auxiliaries(arr[k], params, df["time"].iloc[k])
                for k in range(len(df))]
    df = pd.concat([df, pd.DataFrame(aux_rows)], axis=1)

    df["cum_net_cash"] = df["cash_reserves"] - CASH_RESERVES_INIT
    return df


# ---------------------------------------------------------------------------
# 7. check_reference_behavior
# ---------------------------------------------------------------------------

def check_reference_behavior(baseline_df: pd.DataFrame, verbose: bool = True) -> bool:
    """Test the baseline against every row of the section 3 table."""
    cb = baseline_df["customer_base"]
    rev = baseline_df["revenue_inflow"]
    net = baseline_df["net_cash_flow"]
    acq0 = baseline_df["acquisition_rate"].iloc[0]
    chn0 = baseline_df["churn_rate"].iloc[0]

    checks = [
        ("Customer base within 10% of 400 through month 24",
         bool(cb.min() >= 360.0 and cb.max() <= 440.0),
         f"range {cb.min():.1f} to {cb.max():.1f}"),
        ("Monthly revenue $8,500 to $10,000",
         bool(rev.min() >= 8_500.0 and rev.max() <= 10_000.0),
         f"range ${rev.min():,.0f} to ${rev.max():,.0f}"),
        ("Net cash flow positive and under $1,000/month",
         bool(net.min() > 0.0 and net.max() < 1_000.0),
         f"range ${net.min():,.0f} to ${net.max():,.0f}"),
        ("Acquisition and churn within 2/month of each other at t = 0",
         bool(abs(acq0 - chn0) < 2.0),
         f"acquisition {acq0:.1f} vs churn {chn0:.1f}, gap {abs(acq0-chn0):.2f}"),
        ("Baseline mode flat to mildly growing (350 < base < 500)",
         bool(cb.min() > 350.0 and cb.max() < 500.0),
         f"final {cb.iloc[-1]:.1f}"),
    ]

    ok = True
    if verbose:
        print("\nREFERENCE BEHAVIOR CHECK (section 3)")
        print("-" * 78)
    for label, passed, detail in checks:
        ok &= passed
        if verbose:
            print(f"  [{'PASS' if passed else 'FAIL'}] {label:<58} {detail}")
    if verbose:
        print("-" * 78)
        print(f"  Baseline {'reproduces' if ok else 'DOES NOT reproduce'} "
              f"the reference behavior.")
    return ok


# ---------------------------------------------------------------------------
# Scenario definitions, section 18
# ---------------------------------------------------------------------------

def scenario_definitions() -> dict:
    """Section 18. Each entry is a dictionary update on default_params()."""
    return {
        "Baseline":        {"invest_enabled": False, "price_enabled": False},
        "A: Invest only":  {"invest_enabled": True,  "price_enabled": False},
        "B: Price only":   {"invest_enabled": False, "price_enabled": True},
        "C: Invest+price": {"invest_enabled": True,  "price_enabled": True},
    }


# ---------------------------------------------------------------------------
# 8. compare_scenarios
# ---------------------------------------------------------------------------

def _payback_month(scen_df: pd.DataFrame, base_df: pd.DataFrame,
                   after: float) -> str:
    """First reporting time at which cumulative net cash advantage turns
    positive, searched strictly after the investment lands. Reports
    'none within horizon' rather than extrapolating."""
    adv = scen_df["cum_net_cash"].values - base_df["cum_net_cash"].values
    t = scen_df["time"].values
    mask = (t > after) & (adv > 0.0)
    if not mask.any():
        return "none within horizon"
    return f"month {t[mask][0]:.1f}"


def compare_scenarios(scenario_dict: dict = None, base_params: dict = None,
                      outdir: str = ".", verbose: bool = True):
    """Run every scenario in section 18, plot overlays, summarise."""
    base_params = base_params or default_params()
    scenario_dict = scenario_dict or scenario_definitions()

    runs = {name: run_scenario(_with(base_params, **upd))
            for name, upd in scenario_dict.items()}
    baseline = runs["Baseline"]

    # ---- overlay plots, one panel per stock ---------------------------
    # utilization and wait_time_pressure are both shown, deliberately. The
    # section 10 ramp starts at utilization 0.75, so the two decouple: a
    # utilization panel alone does not show what reaches satisfaction.
    stocks = ["customer_base", "brand_reputation", "cash_reserves",
              "staff_fte", "satisfaction", "utilization",
              "wait_time_pressure", "churn_fraction"]
    fig, axes = plt.subplots(4, 2, figsize=(13, 14))
    for ax, col in zip(axes.ravel(), stocks):
        for name, df in runs.items():
            ax.plot(df["time"], df[col], label=name, lw=1.6)
        ax.set_title(col, fontsize=11)
        ax.set_xlabel("month")
        ax.grid(alpha=0.3)
        if col == "wait_time_pressure":
            ax.axhline(1.0, color="k", ls="--", lw=0.9)
            ax.set_ylim(0, 1.05)
            ax.annotate("section 10 ceiling", xy=(1.0, 1.0),
                        xytext=(1.0, 0.92), fontsize=7)
        if col == "utilization":
            ax.axhline(0.75, color="k", ls="--", lw=0.9)
            ax.annotate("congestion onset, 0.75", xy=(1.0, 0.75),
                        xytext=(1.0, 0.755), fontsize=7)
    axes.ravel()[0].legend(fontsize=8)
    fig.suptitle("Coffee shop SD model: stock trajectories by scenario",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(f"{outdir}/stock_trajectories.png", dpi=140)
    plt.close(fig)

    # ---- cumulative net cash advantage, with crossovers annotated -----
    fig, ax = plt.subplots(figsize=(11, 6))
    invest_end = (base_params["investment_pulse_time"]
                  + base_params["investment_pulse_width"])
    for name, df in runs.items():
        if name == "Baseline":
            continue
        adv = df["cum_net_cash"].values - baseline["cum_net_cash"].values
        ax.plot(df["time"], adv, label=name, lw=1.8)
        t = df["time"].values
        mask = (t > invest_end) & (adv > 0.0)
        if mask.any():
            tc = t[mask][0]
            ax.axvline(tc, ls=":", lw=1.0, alpha=0.6)
            ax.annotate(f"{name}\ncrossover {tc:.1f}",
                        xy=(tc, 0), xytext=(tc + 0.6, ax.get_ylim()[1] * 0.25),
                        fontsize=8)
    ax.axhline(0, color="k", lw=0.9)
    ax.set_xlabel("month")
    ax.set_ylabel("cumulative net cash advantage over baseline (USD)")
    ax.set_title("Scenario comparison: payback against the baseline")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{outdir}/scenario_comparison.png", dpi=140)
    plt.close(fig)

    # ---- phase plot, customer_base against brand_reputation -----------
    fig, ax = plt.subplots(figsize=(7.5, 6))
    for name, df in runs.items():
        ax.plot(df["customer_base"], df["brand_reputation"], lw=1.6, label=name)
        ax.plot(df["customer_base"].iloc[0], df["brand_reputation"].iloc[0],
                "o", ms=5, color="k")
        ax.plot(df["customer_base"].iloc[-1], df["brand_reputation"].iloc[-1],
                "s", ms=5)
    ax.set_xlabel("customer_base")
    ax.set_ylabel("brand_reputation")
    ax.set_title("Phase plot: circle is t = 0, square is month 24")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{outdir}/phase_plot.png", dpi=140)
    plt.close(fig)

    # ---- summary table -------------------------------------------------
    rows = []
    for name, df in runs.items():
        idx = [int(np.argmin(np.abs(df["time"].values - m))) for m in MILESTONES]
        r = {"scenario": name}
        for m, k in zip(MILESTONES, idx):
            r[f"customers @{m:g}"] = round(df["customer_base"].iloc[k], 1)
        r["revenue @24"] = round(df["revenue_inflow"].iloc[-1], 0)
        r["net cash/mo @24"] = round(df["net_cash_flow"].iloc[-1], 0)
        r["cum net cash @24"] = round(df["cum_net_cash"].iloc[-1], 0)
        r["vs baseline @24"] = round(df["cum_net_cash"].iloc[-1]
                                     - baseline["cum_net_cash"].iloc[-1], 0)
        p_scen = _with(base_params, **scenario_dict[name])
        if name == "Baseline":
            r["payback"] = "n/a (baseline)"
        elif not p_scen["invest_enabled"]:
            r["payback"] = "n/a (no investment)"
        else:
            r["payback"] = _payback_month(df, baseline, invest_end)
        rows.append(r)
    summary = pd.DataFrame(rows).set_index("scenario")

    if verbose:
        print("\nSCENARIO SUMMARY (section 18)")
        print("-" * 78)
        with pd.option_context("display.width", 200,
                               "display.max_columns", 50):
            print(summary.to_string())

        print("\nSTEADY STATE AND BINDING CONSTRAINTS (section 11)")
        print("-" * 78)
        for name, df in runs.items():
            dcb = (df["acquisition_rate"] - df["churn_rate"]).iloc[-1]
            frac_staff = float((df["staff_capacity"]
                                <= df["equipment_capacity"]).mean())
            frac_ceiling = float((df["staff_fte"]
                                  >= base_params["max_fte"] - 1e-6).mean())
            frac_wtp_top = float((df["wait_time_pressure"] >= 1.0 - 1e-9).mean())
            frac_wtp_bot = float((df["wait_time_pressure"] <= 1e-9).mean())
            frac_pv_floor = float((df["perceived_value"] <= 1e-9).mean())
            print(f"  {name}")
            print(f"    d(customer_base)/dt at month 24 : {dcb:+.3f} customers/month"
                  f" {'(at rest)' if abs(dcb) < 0.05 else '(still moving)'}")
            print(f"    staffing ceiling binds          : {frac_ceiling:6.1%} of horizon")
            print(f"    staff capacity is the binding   : {frac_staff:6.1%} of horizon")
            print(f"    wait_time_pressure at 1.0 clip  : {frac_wtp_top:6.1%}"
                  f"   at 0.0 clip: {frac_wtp_bot:.1%}")
            print(f"    perceived_value at 0.0 clip     : {frac_pv_floor:6.1%}")

    return runs, summary


# ---------------------------------------------------------------------------
# Loop dominance, section 12
# ---------------------------------------------------------------------------

def loop_dominance(runs: dict, base_params: dict, verbose: bool = True):
    """Measure each loop's contribution to d(customer_base)/dt, phase by phase.

    R1 is the acquisition the loop adds above a no-loop reference: word of
    mouth plus the reputation lift over reference_reputation.
    B1 is the churn avoided or incurred through wait_time_pressure, measured
    against the counterfactual wait_time_pressure = 0.
    B2 is the churn attributable to the price change, measured against
    price_change = 0 in both the multiplier and perceived_value channels.

    All three are reported in customers/month, signed so that positive means
    the loop is pushing the customer base up.
    """
    phases = [(0.0, 6.0), (6.0, 18.0), (18.0, 24.0)]
    out = []

    for name, df in runs.items():
        p = base_params
        # R1: word-of-mouth acquisition plus reputation lift above reference.
        r1 = (df["acquisition_from_wom"]
              + p["base_acquisition"] * p["demand_multiplier"]
              * (df["brand_reputation"] / p["reference_reputation"] - 1.0))

        # B1: churn difference against wait_time_pressure = 0.
        sat_no_wait = np.clip(
            p["w_service"] * df["service_quality_index"]
            + p["w_wait"] * 1.0
            + p["w_value"] * df["perceived_value"], 0.0, 1.0)
        ret_no_wait = np.clip(p["retention_strength"]
                              * (sat_no_wait - p["satisfaction_reference"]),
                              -0.5, 0.6)
        cf_no_wait = (p["base_churn"]
                      * (1.0 + p["price_sensitivity"] * df["price_change"])
                      * (1.0 - ret_no_wait))
        b1 = df["customer_base"] * (cf_no_wait - df["churn_fraction"])

        # B2: churn difference against price_change = 0.
        sat_no_price = np.clip(
            p["w_service"] * df["service_quality_index"]
            + p["w_wait"] * (1.0 - df["wait_time_pressure"])
            + p["w_value"] * 1.0, 0.0, 1.0)
        ret_no_price = np.clip(p["retention_strength"]
                               * (sat_no_price - p["satisfaction_reference"]),
                               -0.5, 0.6)
        cf_no_price = p["base_churn"] * (1.0 - ret_no_price)
        b2 = df["customer_base"] * (cf_no_price - df["churn_fraction"])

        for lo, hi in phases:
            m = (df["time"] >= lo) & (df["time"] <= hi)
            vals = {"R1": r1[m].mean(), "B1": b1[m].mean(), "B2": b2[m].mean()}
            dominant = max(vals, key=lambda k: abs(vals[k]))
            out.append({"scenario": name, "phase": f"{lo:g}-{hi:g}",
                        "R1": round(vals["R1"], 3),
                        "B1": round(vals["B1"], 3),
                        "B2": round(vals["B2"], 3),
                        "observed dominant": dominant})

    tbl = pd.DataFrame(out)

    if verbose:
        expected = {"0-6": "R1", "6-18": "R1, weakening", "18-24": "B1 at parity"}
        print("\nLOOP DOMINANCE (section 12 expected vs observed)")
        print("-" * 78)
        print("  Contributions to d(customer_base)/dt, customers/month, "
              "phase averages.")
        print("  Positive pushes the base up; B1 and B2 are negative when "
              "they brake.\n")
        with pd.option_context("display.width", 200):
            print(tbl.to_string(index=False))
        print("\n  Expected dominance from section 12:")
        for k, v in expected.items():
            print(f"    months {k:<6} {v}")
        print("\n  Mismatches are reported, not reconciled:")
        for _, row in tbl.iterrows():
            exp = expected[row["phase"]].split(",")[0].strip()
            if row["observed dominant"] != exp:
                print(f"    {row['scenario']}, months {row['phase']}: "
                      f"expected {exp}, observed {row['observed dominant']} "
                      f"(R1 {row['R1']:+.2f}, B1 {row['B1']:+.2f}, "
                      f"B2 {row['B2']:+.2f})")
        b1_ratio = tbl[(tbl["phase"] == "18-24")].apply(
            lambda r: abs(r["B1"]) / max(abs(r["R1"]), 1e-9), axis=1)
        print(f"\n  |B1|/|R1| in months 18-24: "
              + ", ".join(f"{n} {v:.2f}" for n, v
                          in zip(tbl[tbl['phase'] == '18-24']['scenario'],
                                 b1_ratio)))
    return tbl


# ---------------------------------------------------------------------------
# 9. sensitivity_sweep
# ---------------------------------------------------------------------------

def _key_outputs(df: pd.DataFrame) -> dict:
    return {
        "customers_24": df["customer_base"].iloc[-1],
        "revenue_24": df["revenue_inflow"].iloc[-1],
        "net_cash_24": df["net_cash_flow"].iloc[-1],
        "cum_net_cash_24": df["cum_net_cash"].iloc[-1],
        "satisfaction_24": df["satisfaction"].iloc[-1],
        "utilization_24": df["utilization"].iloc[-1],
    }


def sensitivity_sweep(base_params: dict, param_name: str, values,
                      scenario: dict = None, plot: bool = False,
                      outdir: str = ".") -> pd.DataFrame:
    """Sweep one parameter with all others held constant.

    Initial state is recomputed at every value, because several section 9
    parameters move the equilibrium the stocks start from. Sweeping without
    re-equilibrating would report drift as if it were policy effect.
    """
    scenario = scenario or {}
    rows = []
    for v in values:
        p = _with(base_params, **{param_name: float(v)})
        p = _with(p, **scenario)
        try:
            df = run_scenario(p)
            rows.append({param_name: v, **_key_outputs(df)})
        except RuntimeError as exc:                       # pragma: no cover
            warnings.warn(f"{param_name}={v}: {exc}")
    out = pd.DataFrame(rows)

    if plot and len(out):
        fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
        for ax, col in zip(axes, ["customers_24", "cum_net_cash_24",
                                  "satisfaction_24"]):
            ax.plot(out[param_name], out[col], marker="o", ms=3)
            ax.set_xlabel(param_name)
            ax.set_ylabel(col)
            ax.grid(alpha=0.3)
        fig.suptitle(f"OAT sweep: {param_name}")
        fig.tight_layout()
        fig.savefig(f"{outdir}/sweep_{param_name}.png", dpi=140)
        plt.close(fig)
    return out


def run_all_sweeps(base_params: dict, n_points: int = 7,
                   metric: str = "customers_24", scenario: dict = None,
                   label: str = "baseline", outdir: str = ".",
                   verbose: bool = True) -> pd.DataFrame:
    """Sweep every section 9 parameter that has a range, then rank by swing.

    The ranking is scenario dependent, and that matters. Under the baseline,
    price_sensitivity, value_sensitivity and both upgraded-equipment
    parameters have exactly zero swing because the levers they attach to are
    switched off. Ranking on the baseline alone would call them irrelevant.
    """
    scenario = scenario or {}
    ranks, curves = [], {}
    for name, (lo, hi) in PARAM_RANGES.items():
        vals = np.linspace(lo, hi, n_points)
        res = sensitivity_sweep(base_params, name, vals, scenario=scenario)
        curves[name] = res
        row = {"parameter": name, "low": lo, "high": hi,
               f"{metric} min": round(res[metric].min(), 2),
               f"{metric} max": round(res[metric].max(), 2),
               "swing": round(res[metric].max() - res[metric].min(), 2),
               "swing cum_net_cash_24": round(
                   res["cum_net_cash_24"].max() - res["cum_net_cash_24"].min(), 0)}
        ranks.append(row)
    ranked = (pd.DataFrame(ranks).sort_values("swing", ascending=False)
              .reset_index(drop=True))

    top3 = ranked["parameter"].head(3).tolist()
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, name in zip(axes, top3):
        res = curves[name]
        ax.plot(res[name], res[metric], marker="o", ms=4)
        ax.set_xlabel(name)
        ax.set_ylabel(metric)
        ax.grid(alpha=0.3)
    fig.suptitle(f"OAT sensitivity, top 3 by swing in {metric} ({label})")
    fig.tight_layout()
    fig.savefig(f"{outdir}/sensitivity_top3_{label.replace(' ', '_')}.png",
                dpi=140)
    plt.close(fig)

    if verbose:
        print(f"\nONE-AT-A-TIME SENSITIVITY, ranked by swing in {metric}, "
              f"scenario: {label}")
        print("-" * 78)
        print(ranked.to_string(index=False))
    return ranked


def verify_sobol_coverage(ranked: pd.DataFrame, problem: dict = None,
                          top_n: int = 5, verbose: bool = True) -> bool:
    """Check that the section 16 Sobol set covers the OAT leaders.

    Code architecture item 10: a parameter that dominates the OAT sweep and
    is missing from the global set means the global analysis is measuring
    the wrong thing. This reports the gap rather than quietly widening the
    Sobol problem, because the bounds are the spec's to set.
    """
    problem = problem or SOBOL_PROBLEM
    top = ranked["parameter"].head(top_n).tolist()
    missing = [p for p in top if p not in problem["names"]]
    if verbose:
        print(f"\nSOBOL COVERAGE CHECK (section 16 vs OAT top {top_n})")
        print("-" * 78)
        print(f"  OAT top {top_n}: {', '.join(top)}")
        if missing:
            print(f"  [FAIL] Not in the section 16 Sobol set: "
                  f"{', '.join(missing)}")
            print("         Section 17 asserts this set covers the OAT top "
                  "five. As run, it does not.")
        else:
            print("  [PASS] Every OAT leader appears in the section 16 set.")
    return not missing


# ---------------------------------------------------------------------------
# 10. global_sensitivity
# ---------------------------------------------------------------------------

SOBOL_PROBLEM = {
    "num_vars": 9,
    "names": ["base_acquisition", "target_load_per_fte", "customers_per_fte",
              "wom_coefficient", "conversion_rate", "base_churn",
              "price_sensitivity", "wom_delay", "retention_strength"],
    "bounds": [[12.0, 28.0], [85.0, 120.0], [110.0, 150.0],
               [0.03, 0.10], [0.18, 0.32], [0.055, 0.085],
               [0.8, 2.5], [0.92, 1.85], [0.5, 1.1]],
}


def global_sensitivity(base_params: dict, problem: dict = None, n: int = 256,
                       scenario: dict = None, outputs=("customers_24",
                                                       "cum_net_cash_24"),
                       outdir: str = ".", verbose: bool = True):
    """Sobol first- and total-order indices using the section 16 bounds."""
    if not HAVE_SALIB:
        print("\nGLOBAL SENSITIVITY: SALib not installed, skipping.")
        return None
    problem = problem or SOBOL_PROBLEM
    scenario = scenario or {}

    X = sobol_sample.sample(problem, n, calc_second_order=False)
    Y = {k: np.zeros(X.shape[0]) for k in outputs}
    for i, row in enumerate(X):
        p = _with(base_params, **dict(zip(problem["names"], row)))
        p = _with(p, **scenario)
        ko = _key_outputs(run_scenario(p))
        for k in outputs:
            Y[k][i] = ko[k]

    results = {}
    for k in outputs:
        Si = sobol_analyze.analyze(problem, Y[k], calc_second_order=False,
                                   print_to_console=False)
        results[k] = pd.DataFrame({
            "parameter": problem["names"],
            "S1": np.round(Si["S1"], 4),
            "ST": np.round(Si["ST"], 4),
        }).sort_values("ST", ascending=False).reset_index(drop=True)

    fig, axes = plt.subplots(1, len(outputs), figsize=(6.5 * len(outputs), 4.2))
    axes = np.atleast_1d(axes)
    for ax, k in zip(axes, outputs):
        d = results[k]
        ax.barh(d["parameter"][::-1], d["ST"][::-1])
        ax.set_xlabel("total-order Sobol index")
        ax.set_title(k)
        ax.grid(alpha=0.3, axis="x")
    fig.suptitle(f"Global sensitivity, section 16 bounds (N={n})")
    fig.tight_layout()
    fig.savefig(f"{outdir}/global_sensitivity.png", dpi=140)
    plt.close(fig)

    if verbose:
        print(f"\nGLOBAL SENSITIVITY, Sobol indices, N={n} "
              f"({X.shape[0]} model runs)")
        print("-" * 78)
        for k in outputs:
            print(f"\n  Output: {k}")
            print(results[k].to_string(index=False))
    return results


# ---------------------------------------------------------------------------
# 11. stochastic_run
# ---------------------------------------------------------------------------

def stochastic_run(base_params: dict, t_span=(0.0, HORIZON), y0=None,
                   n_iterations: int = 200, random_params=None,
                   scenario: dict = None, seed: int = 20260802,
                   outdir: str = ".", label: str = "baseline",
                   plot: bool = True) -> pd.DataFrame:
    """Monte Carlo wrapper around the deterministic ODE, section 16.

    Sampled per iteration:
      wom_delay        Uniform(4, 8) weeks, converted to months
      demand_multiplier Lognormal(mu=0, sigma=0.15), median 1.0
      base_churn       Normal(0.07, 0.008)
      conversion_rate  Uniform(0.18, 0.32)

    y0 is recomputed for every draw, since conversion_rate moves the
    word-of-mouth equilibrium the delay stock starts from.
    """
    rng = np.random.default_rng(seed)
    scenario = scenario or {}
    random_params = random_params or ["wom_delay", "demand_multiplier",
                                      "base_churn", "conversion_rate"]

    def draw():
        d = {}
        if "wom_delay" in random_params:
            d["wom_delay"] = rng.uniform(4.0, 8.0) / WEEKS_PER_MONTH
        if "demand_multiplier" in random_params:
            d["demand_multiplier"] = float(rng.lognormal(0.0, 0.15))
        if "base_churn" in random_params:
            d["base_churn"] = float(rng.normal(0.07, 0.008))
        if "conversion_rate" in random_params:
            d["conversion_rate"] = float(rng.uniform(0.18, 0.32))
        return d

    frames = []
    for i in range(n_iterations):
        p = _with(base_params, **draw())
        p = _with(p, **scenario)
        df = run_scenario(p, t_span=t_span, y0=y0)
        frames.append(pd.DataFrame({
            "iteration": i,
            "time": df["time"],
            "customer_base": df["customer_base"],
            "cum_net_cash": df["cum_net_cash"],
            "satisfaction": df["satisfaction"],
            "net_cash_flow": df["net_cash_flow"],
        }))
    long_df = pd.concat(frames, ignore_index=True)

    if plot:
        q = (long_df.groupby("time")[["customer_base", "cum_net_cash"]]
             .quantile([0.1, 0.5, 0.9]).unstack())
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.4))
        for ax, col in zip(axes, ["customer_base", "cum_net_cash"]):
            t = q.index.values
            ax.fill_between(t, q[(col, 0.1)], q[(col, 0.9)], alpha=0.25,
                            label="10th-90th percentile")
            ax.plot(t, q[(col, 0.5)], lw=1.8, label="median")
            ax.set_xlabel("month")
            ax.set_ylabel(col)
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
        fig.suptitle(f"Stochastic envelope, {label}, "
                     f"{n_iterations} iterations (section 16)")
        fig.tight_layout()
        fig.savefig(f"{outdir}/stochastic_{label.replace(' ', '_')}.png", dpi=140)
        plt.close(fig)

    return long_df


# ---------------------------------------------------------------------------
# 12. structural_sensitivity
# ---------------------------------------------------------------------------

def structural_sensitivity(base_params: dict, scenario: dict = None,
                           metric: str = "customers_24",
                           verbose: bool = True) -> pd.DataFrame:
    """Weaken, strengthen and disable each loop's coupling parameter.

    Section 12 does not name a coupling parameter per loop, so the parameter
    each loop's description routes through is used: R1 wom_coefficient,
    B1 w_wait, B2 price_sensitivity. Zeroing w_wait breaks B1 but also lifts
    satisfaction, so a second B1 variant freezes wait_time_pressure at its
    t = 0 value, which severs the feedback with the level held.
    """
    scenario = scenario or {}
    base = _with(base_params, **scenario)
    ref = _key_outputs(run_scenario(base))[metric]

    loops = {"R1": "wom_coefficient", "B1": "w_wait", "B2": "price_sensitivity"}
    rows = []
    for loop, param in loops.items():
        for label, mult in [("disabled", 0.0), ("weakened", 0.5),
                            ("strengthened", 1.5)]:
            p = _with(base, **{param: base[param] * mult})
            val = _key_outputs(run_scenario(p))[metric]
            rows.append({"loop": loop, "coupling parameter": param,
                         "variation": label,
                         "value": round(base[param] * mult, 4),
                         metric: round(val, 2),
                         "change vs base": round(val - ref, 2)})

    # B1 knockout with the level held
    wtp0 = run_scenario(base)["wait_time_pressure"].iloc[0]
    p = _with(base, freeze_wait_pressure=float(wtp0))
    val = _key_outputs(run_scenario(p))[metric]
    rows.append({"loop": "B1", "coupling parameter": "wait_time_pressure",
                 "variation": "frozen at t=0 (level held)",
                 "value": round(float(wtp0), 4),
                 metric: round(val, 2),
                 "change vs base": round(val - ref, 2)})

    tbl = pd.DataFrame(rows)
    if verbose:
        print(f"\nSTRUCTURAL SENSITIVITY, metric {metric}, "
              f"base value {ref:.2f}")
        print("-" * 78)
        print(tbl.to_string(index=False))
    return tbl


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(outdir: str = ".", n_mc: int = 200, n_sobol: int = 128,
         run_sobol: bool = True):
    pd.set_option("display.width", 200)
    params = default_params()

    print("=" * 78)
    print("COFFEE SHOP SYSTEM DYNAMICS MODEL")
    print("Horizon 24 months, reporting interval 0.1 month, "
          "time unit months")
    print("=" * 78)

    print("\nSPEC GAPS AND IMPLEMENTATION DECISIONS")
    print("-" * 78)
    for i, g in enumerate(SPEC_GAPS, 1):
        print(f"  {i}. {g}")

    y0 = initial_state(params)
    print("\nINITIAL STATE (section 6 plus delay stocks from section 13)")
    print("-" * 78)
    for n, v in zip(STATE_NAMES, y0):
        print(f"  {n:<20} {v:>12,.4f}")

    baseline = run_scenario(params)
    ok = check_reference_behavior(baseline)
    if not ok:
        print("\n  Baseline fails its reference mode. Stopping before "
              "scenario comparison, because a baseline that misses its "
              "reference behavior invalidates everything downstream.")
        return

    runs, summary = compare_scenarios(base_params=params, outdir=outdir)
    loop_dominance(runs, params)

    both_levers = {"invest_enabled": True, "price_enabled": True}
    ranked = run_all_sweeps(params, outdir=outdir, label="baseline")
    ranked_c = run_all_sweeps(params, outdir=outdir, scenario=both_levers,
                              label="C invest plus price")
    verify_sobol_coverage(ranked_c)

    structural_sensitivity(params, scenario=both_levers)

    stochastic_run(params, n_iterations=n_mc, outdir=outdir, label="baseline")
    stochastic_run(params, n_iterations=n_mc, outdir=outdir,
                   label="C invest plus price",
                   scenario={"invest_enabled": True, "price_enabled": True})

    if run_sobol:
        global_sensitivity(params, n=n_sobol, outdir=outdir,
                           scenario=both_levers)

    # Persist the time series for downstream use.
    for name, df in runs.items():
        fn = name.replace(":", "").replace(" ", "_").replace("+", "_")
        df.to_csv(f"{outdir}/timeseries_{fn}.csv", index=False)
    summary.to_csv(f"{outdir}/scenario_summary.csv")
    ranked.to_csv(f"{outdir}/oat_sensitivity_baseline.csv", index=False)
    ranked_c.to_csv(f"{outdir}/oat_sensitivity_scenarioC.csv", index=False)

    print("\nDone. Time series, summary and plots written to "
          f"{outdir}")


if __name__ == "__main__":
    main()
