"""
Coffee Shop Synthetic Data Generator
=====================================
Generates realistic daily operations data for the Monte Carlo simulation
example in Chapter 4 of "Simulation Models for Data Science."

Produces two CSV files:
  - coffee_shop_daily_operations.csv  (730 rows, one per day)
  - weather_reference.csv             (4 rows, one per category)

And a codebook:
  - coffee_shop_codebook.md

Usage:
    python generate_coffee_shop_data.py [--seed 42] [--output-dir ./data]
"""

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Configuration: all target parameters in one place
# ---------------------------------------------------------------------------

CONFIG = {
    "seed": 42,
    "n_years": 2,
    "start_date": "2024-07-01",

    # Customer count targets (negative binomial)
    # NOTE: These are the *conditional* overdispersion values. The marginal
    # overdispersion (measured from the full dataset) will be higher because
    # day-of-week, seasonal, and weather mean-shifts add between-group variance.
    # Target marginal overdispersion: weekday ~1.3-1.5, weekend ~1.5-1.8
    "customers_weekday_mean": 145.0,
    "customers_weekday_overdispersion": 1.04,
    "customers_weekend_mean": 180.0,
    "customers_weekend_overdispersion": 1.08,

    # Day-of-week multipliers (Mon=0 ... Sun=6)
    # Kept mild to avoid inflating marginal overdispersion
    "dow_multipliers": {
        0: 0.950,   # Monday    (~115 after all effects)
        1: 0.970,   # Tuesday
        2: 0.990,   # Wednesday
        3: 1.010,   # Thursday
        4: 1.060,   # Friday    (~145 after all effects)
        5: 1.000,   # Saturday  (weekend baseline)
        6: 0.980,   # Sunday
    },

    # Seasonal multipliers by month (1=Jan ... 12=Dec)
    # Kept mild: ±4% max
    "seasonal_multipliers": {
        1: 0.96, 2: 0.97, 3: 1.01, 4: 1.03, 5: 1.03, 6: 0.99,
        7: 0.97, 8: 0.97, 9: 1.02, 10: 1.03, 11: 1.01, 12: 0.97,
    },

    # Transaction value targets (lognormal)
    "transaction_weekday_median": 6.50,
    "transaction_weekday_sigma": 0.28,
    "transaction_weekend_median": 7.00,
    "transaction_weekend_sigma": 0.26,

    # Weather category baseline frequencies
    "weather_freqs_baseline": {
        "sunny": 0.40, "cloudy": 0.30, "rainy": 0.22, "extreme": 0.08
    },

    # Weather impact on customer count
    "weather_multipliers": {
        "sunny": 1.00, "cloudy": 0.96, "rainy": 0.90, "extreme": 0.78
    },

    # Weather impact on transaction value (bad weather → slightly higher spend)
    "weather_transaction_boost": {
        "sunny": 1.00, "cloudy": 1.02, "rainy": 1.05, "extreme": 1.08
    },

    # Operating costs
    "fixed_cost_per_day": 350.0,
    "variable_cost_per_customer": 2.00,

    # Outlier events (day indices into the 730-day series)
    "power_outage_day": 187,         # ~6 months in
    "equipment_failure_days": [412, 589],  # partial closures

    # Correlation targets
    "corr_customers_transaction": -0.08,
}


# ---------------------------------------------------------------------------
# Helper: negative binomial parameterization
# ---------------------------------------------------------------------------

def negbinom_params(mean, overdispersion_ratio):
    """Convert mean and overdispersion ratio to scipy's (n, p) parameterization.

    For a negative binomial with mean=μ and variance=μ*k (where k is the
    overdispersion ratio), scipy's parameters are:
        n = μ² / (variance - μ)  = μ / (k - 1)
        p = n / (n + μ)
    """
    variance = mean * overdispersion_ratio
    n = mean ** 2 / (variance - mean)
    p = n / (n + mean)
    return n, p


# ---------------------------------------------------------------------------
# Step 1: Calendar spine
# ---------------------------------------------------------------------------

def build_calendar(start_date, n_years):
    n_days = n_years * 365
    dates = pd.date_range(start=start_date, periods=n_days, freq="D")
    df = pd.DataFrame({"date": dates})
    df["day_of_week"] = df["date"].dt.day_name()
    df["dow_num"] = df["date"].dt.dayofweek          # 0=Mon, 6=Sun
    df["is_weekend"] = df["dow_num"].isin([5, 6])
    df["month"] = df["date"].dt.month
    df["season"] = df["month"].map({
        12: "winter", 1: "winter", 2: "winter",
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "fall", 10: "fall", 11: "fall",
    })
    return df


# ---------------------------------------------------------------------------
# Step 2: Weather categories with seasonal adjustment
# ---------------------------------------------------------------------------

def generate_weather(df, rng, cfg):
    categories = ["sunny", "cloudy", "rainy", "extreme"]
    base = np.array([cfg["weather_freqs_baseline"][c] for c in categories])

    # Seasonal adjustments: shift probability mass
    seasonal_shifts = {
        "winter": np.array([-0.08, 0.00, +0.05, +0.03]),
        "spring": np.array([+0.03, +0.02, -0.03, -0.02]),
        "summer": np.array([+0.08, -0.02, -0.04, -0.02]),
        "fall":   np.array([-0.02, +0.02, +0.02, -0.02]),
    }

    weather = []
    for _, row in df.iterrows():
        probs = base + seasonal_shifts[row["season"]]
        probs = np.clip(probs, 0.01, None)
        probs /= probs.sum()
        weather.append(rng.choice(categories, p=probs))

    df["weather_category"] = weather
    return df


# ---------------------------------------------------------------------------
# Step 3: Customer counts
# ---------------------------------------------------------------------------

def generate_customer_counts(df, rng, cfg):
    n_days = len(df)
    counts = np.zeros(n_days, dtype=int)

    # Pre-compute the average multiplier effects so we can calibrate the
    # base mean to hit targets after all adjustments are applied.
    # The base mean in the config is the *target marginal mean*, so we
    # need to inflate it to compensate for the average drag from weather,
    # seasonal, and day-of-week multipliers.

    for i, row in df.iterrows():
        if row["is_weekend"]:
            base_mean = cfg["customers_weekend_mean"]
            od = cfg["customers_weekend_overdispersion"]
        else:
            base_mean = cfg["customers_weekday_mean"]
            od = cfg["customers_weekday_overdispersion"]

        # Apply adjustments additively rather than multiplicatively
        # to prevent compounding that drags the mean too far down.
        dow_offset = (cfg["dow_multipliers"][row["dow_num"]] - 1.0) * base_mean
        seasonal_offset = (cfg["seasonal_multipliers"][row["month"]] - 1.0) * base_mean
        weather_offset = (cfg["weather_multipliers"][row["weather_category"]] - 1.0) * base_mean

        adjusted_mean = base_mean + dow_offset + seasonal_offset + weather_offset
        adjusted_mean = max(adjusted_mean, 10)  # floor

        n_param, p_param = negbinom_params(adjusted_mean, od)
        counts[i] = rng.negative_binomial(max(n_param, 1), min(p_param, 0.999))

    df["customer_count"] = counts

    # Inject outlier events
    df.loc[cfg["power_outage_day"], "customer_count"] = rng.integers(8, 16)
    for day_idx in cfg["equipment_failure_days"]:
        normal_count = df.loc[day_idx, "customer_count"]
        df.loc[day_idx, "customer_count"] = int(normal_count * rng.uniform(0.30, 0.50))

    return df


# ---------------------------------------------------------------------------
# Step 4: Transaction values with correlations
# ---------------------------------------------------------------------------

def generate_transaction_values(df, rng, cfg):
    n_days = len(df)
    transactions = np.zeros(n_days)

    for i, row in df.iterrows():
        if row["is_weekend"]:
            mu_log = np.log(cfg["transaction_weekend_median"])
            sigma_log = cfg["transaction_weekend_sigma"]
        else:
            mu_log = np.log(cfg["transaction_weekday_median"])
            sigma_log = cfg["transaction_weekday_sigma"]

        # Weather boost
        weather_boost = cfg["weather_transaction_boost"][row["weather_category"]]

        # Draw base transaction value
        base_val = rng.lognormal(mu_log, sigma_log)
        transactions[i] = base_val * weather_boost

    # Induce weak negative correlation with customer count
    # Sort-and-match approach: partially shuffle to achieve target correlation
    target_corr = cfg["corr_customers_transaction"]
    customers = df["customer_count"].values.astype(float)

    # Standardize both
    c_rank = stats.rankdata(customers)
    t_rank = stats.rankdata(transactions)

    # Mix original ranks with correlated ranks
    # Use a blending weight to achieve approximate target correlation
    blend = abs(target_corr)
    n = len(transactions)
    # Create anti-correlated component by reversing customer ranks
    anti_rank = n + 1 - c_rank
    # Blend: partially sort transactions to match anti-correlated order
    mixed_rank = (1 - blend) * t_rank + blend * anti_rank
    sort_order = np.argsort(np.argsort(mixed_rank))
    sorted_transactions = np.sort(transactions)
    transactions = sorted_transactions[sort_order]

    df["avg_transaction_value"] = np.round(transactions, 2)

    # Fix outlier day transactions to look realistic
    df.loc[cfg["power_outage_day"], "avg_transaction_value"] = round(
        rng.lognormal(np.log(6.50), 0.35), 2
    )
    for day_idx in cfg["equipment_failure_days"]:
        df.loc[day_idx, "avg_transaction_value"] = round(
            rng.lognormal(np.log(7.00), 0.30), 2
        )

    return df


# ---------------------------------------------------------------------------
# Step 5: Derived fields
# ---------------------------------------------------------------------------

def compute_derived_fields(df, cfg):
    df["daily_revenue"] = np.round(
        df["customer_count"] * df["avg_transaction_value"], 2
    )
    df["operating_costs"] = np.round(
        cfg["fixed_cost_per_day"] + cfg["variable_cost_per_customer"] * df["customer_count"], 2
    )
    df["daily_profit"] = np.round(df["daily_revenue"] - df["operating_costs"], 2)
    return df


# ---------------------------------------------------------------------------
# Step 6: Validation
# ---------------------------------------------------------------------------

def validate_dataset(df, cfg):
    """Run validation checks and print a summary report."""
    print("\n" + "=" * 60)
    print("VALIDATION REPORT")
    print("=" * 60)

    checks_passed = 0
    checks_total = 0

    def check(name, value, low, high):
        nonlocal checks_passed, checks_total
        checks_total += 1
        passed = low <= value <= high
        status = "PASS" if passed else "FAIL"
        if passed:
            checks_passed += 1
        print(f"  [{status}] {name}: {value:.2f} (target: {low:.2f}–{high:.2f})")

    # Customer count means
    weekday = df[~df["is_weekend"]]
    weekend = df[df["is_weekend"]]

    # Exclude outlier days for parameter checks
    outlier_indices = [cfg["power_outage_day"]] + cfg["equipment_failure_days"]
    clean = df.drop(index=outlier_indices)
    clean_weekday = clean[~clean["is_weekend"]]
    clean_weekend = clean[clean["is_weekend"]]

    print("\nCustomer Counts (excluding outliers):")
    check("  Weekday mean", clean_weekday["customer_count"].mean(), 120, 137)
    check("  Weekend mean", clean_weekend["customer_count"].mean(), 155, 175)

    # Overdispersion
    wd_od = clean_weekday["customer_count"].var() / clean_weekday["customer_count"].mean()
    we_od = clean_weekend["customer_count"].var() / clean_weekend["customer_count"].mean()
    print("\nOverdispersion (variance/mean):")
    check("  Weekday", wd_od, 1.1, 2.0)
    check("  Weekend", we_od, 1.2, 2.5)

    # Transaction values
    print("\nTransaction Values (excluding outliers):")
    check("  Overall mean", clean["avg_transaction_value"].mean(), 6.80, 7.60)
    check("  Weekday median", clean_weekday["avg_transaction_value"].median(), 6.00, 7.00)
    check("  Weekend median", clean_weekend["avg_transaction_value"].median(), 6.50, 7.50)

    # Weather frequencies
    print("\nWeather Frequencies:")
    weather_freq = df["weather_category"].value_counts(normalize=True)
    for cat, target in cfg["weather_freqs_baseline"].items():
        if cat in weather_freq:
            check(f"  {cat}", weather_freq[cat], target - 0.05, target + 0.05)

    # Correlations
    print("\nCorrelations (excluding outliers):")
    weather_severity = clean["weather_category"].map(
        {"sunny": 0, "cloudy": 1, "rainy": 2, "extreme": 3}
    )
    corr_weather_cust = weather_severity.corr(clean["customer_count"])
    check("  Weather severity ↔ customers", corr_weather_cust, -0.45, -0.25)

    corr_cust_trans = clean["customer_count"].corr(clean["avg_transaction_value"])
    check("  Customers ↔ transaction value", corr_cust_trans, -0.20, 0.02)

    # Break-even analysis
    breakeven = 630
    below_breakeven = (df["daily_revenue"] < breakeven).mean()
    print(f"\nBreak-even Analysis:")
    check("  % days below $630", below_breakeven * 100, 5, 16)

    # Revenue distribution shape
    rev_mean = df["daily_revenue"].mean()
    rev_median = df["daily_revenue"].median()
    print(f"\nRevenue Distribution Shape:")
    checks_total += 1
    if rev_mean > rev_median:
        checks_passed += 1
        print(f"  [PASS] Right-skewed: mean ({rev_mean:.0f}) > median ({rev_median:.0f})")
    else:
        print(f"  [FAIL] Not right-skewed: mean ({rev_mean:.0f}) <= median ({rev_median:.0f})")

    # Outlier detectability
    print(f"\nOutlier Events:")
    power_rev = df.loc[cfg["power_outage_day"], "daily_revenue"]
    q1 = df["daily_revenue"].quantile(0.25)
    iqr = df["daily_revenue"].quantile(0.75) - q1
    lower_fence = q1 - 1.5 * iqr
    checks_total += 1
    if power_rev < lower_fence:
        checks_passed += 1
        print(f"  [PASS] Power outage day (${power_rev:.0f}) below IQR fence (${lower_fence:.0f})")
    else:
        print(f"  [FAIL] Power outage day (${power_rev:.0f}) NOT below IQR fence (${lower_fence:.0f})")

    # No negative values
    checks_total += 1
    if (df[["customer_count", "avg_transaction_value", "daily_revenue"]] >= 0).all().all():
        checks_passed += 1
        print(f"  [PASS] No negative values in key fields")
    else:
        print(f"  [FAIL] Negative values found")

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {checks_passed}/{checks_total} checks passed")
    print(f"{'=' * 60}\n")

    return checks_passed == checks_total


# ---------------------------------------------------------------------------
# Weather reference table
# ---------------------------------------------------------------------------

def create_weather_reference(cfg):
    return pd.DataFrame({
        "weather_category": ["sunny", "cloudy", "rainy", "extreme"],
        "historical_frequency": [0.40, 0.30, 0.22, 0.08],
        "customer_impact": ["Baseline", "~8% reduction", "~22% reduction", "~45% reduction"],
        "description": [
            "Clear skies, comfortable temperature",
            "Overcast but dry, mild conditions",
            "Rain or steady drizzle throughout the day",
            "Severe weather: heavy storms, ice, extreme heat/cold",
        ],
    })


# ---------------------------------------------------------------------------
# Codebook
# ---------------------------------------------------------------------------

CODEBOOK = """# Coffee Shop Daily Operations: Data Codebook

## Source
Point-of-sale system and local weather service records for a single-location
coffee shop. Data covers {n_years} years of daily operations from {start} to {end}.

## File: coffee_shop_daily_operations.csv

| Field | Type | Units | Description |
|-------|------|-------|-------------|
| date | date | YYYY-MM-DD | Calendar date |
| day_of_week | string | — | Day name (Monday–Sunday) |
| is_weekend | boolean | — | True for Saturday and Sunday |
| weather_category | string | — | sunny, cloudy, rainy, or extreme |
| customer_count | integer | customers | Number of customers served |
| avg_transaction_value | float | USD | Mean transaction amount for the day |
| daily_revenue | float | USD | customer_count × avg_transaction_value |
| operating_costs | float | USD | Fixed ($350) + variable ($2.00/customer) |
| daily_profit | float | USD | daily_revenue − operating_costs |

## Known Data Quality Issues

1. **{outage_date}**: Power outage closed the shop for most of the day.
   Customer count is abnormally low (~12). Consider removing this record
   before fitting distributions.

2. **{equip_1} and {equip_2}**: Equipment failures caused partial-day closures.
   Customer counts are roughly 30–50% of normal. Analyst judgment required
   on whether to remove, segment, or retain these records.

3. **Seasonal patterns**: Customer traffic varies by season. Consider
   segmenting by season or including seasonal adjustments when fitting
   distributions.

## File: weather_reference.csv

Lookup table with four weather categories, their historical frequencies,
customer impact descriptions, and plain-language definitions.

## Break-Even Threshold

Daily break-even revenue is approximately $630, based on fixed costs of $350
and variable costs of $2.00 per customer at typical traffic levels.
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate coffee shop synthetic data")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="./data",
                        help="Output directory for CSV files")
    args = parser.parse_args()

    cfg = CONFIG.copy()
    cfg["seed"] = args.seed
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(cfg["seed"])

    print("Generating coffee shop synthetic data...")
    print(f"  Seed: {cfg['seed']}")
    print(f"  Output: {output_dir}")

    # Build dataset
    df = build_calendar(cfg["start_date"], cfg["n_years"])
    df = generate_weather(df, rng, cfg)
    df = generate_customer_counts(df, rng, cfg)
    df = generate_transaction_values(df, rng, cfg)
    df = compute_derived_fields(df, cfg)

    # Validate
    all_passed = validate_dataset(df, cfg)

    # Select output columns
    output_cols = [
        "date", "day_of_week", "is_weekend", "weather_category",
        "customer_count", "avg_transaction_value", "daily_revenue",
        "operating_costs", "daily_profit",
    ]
    df_out = df[output_cols].copy()
    df_out["date"] = df_out["date"].dt.strftime("%Y-%m-%d")

    # Write CSVs
    ops_path = output_dir / "coffee_shop_daily_operations.csv"
    df_out.to_csv(ops_path, index=False)
    print(f"Wrote {len(df_out)} rows to {ops_path}")

    weather_ref = create_weather_reference(cfg)
    weather_path = output_dir / "weather_reference.csv"
    weather_ref.to_csv(weather_path, index=False)
    print(f"Wrote weather reference to {weather_path}")

    # Write codebook
    outage_date = df.loc[cfg["power_outage_day"], "date"].strftime("%Y-%m-%d")
    equip_dates = [df.loc[d, "date"].strftime("%Y-%m-%d") for d in cfg["equipment_failure_days"]]
    codebook_text = CODEBOOK.format(
        n_years=cfg["n_years"],
        start=df["date"].iloc[0].strftime("%Y-%m-%d"),
        end=df["date"].iloc[-1].strftime("%Y-%m-%d"),
        outage_date=outage_date,
        equip_1=equip_dates[0],
        equip_2=equip_dates[1],
    )
    codebook_path = output_dir / "coffee_shop_codebook.md"
    codebook_path.write_text(codebook_text)
    print(f"Wrote codebook to {codebook_path}")

    if not all_passed:
        print("\nWARNING: Some validation checks failed. Review the report above.")
        print("You may need to adjust CONFIG parameters and re-run.")


if __name__ == "__main__":
    main()
