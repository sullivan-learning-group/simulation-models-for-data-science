"""
Monte Carlo Simulation: Coffee Shop Daily Revenue
===================================================
Simulates daily revenue for a small coffee shop to estimate
the probability of falling below the $930/day break-even point.

Based on specification:
  revenue = daily_customers × avg_spend_per_customer
  where customer count depends on weather (sunny/cloudy/rainy)
  and avg spend follows a lognormal distribution.
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── Configuration ──────────────────────────────────────────────
N_ITERATIONS: int = 10_000
RANDOM_SEED: int = 42
BREAK_EVEN: float = 630.0

# Weather probabilities
WEATHER_PROBS = {"sunny": 0.50, "cloudy": 0.30, "rainy": 0.20}
WEATHER_CATEGORIES = list(WEATHER_PROBS.keys())
WEATHER_P = list(WEATHER_PROBS.values())

# Customer count parameters (Normal, conditional on weather)
CUSTOMER_PARAMS: dict[str, dict[str, float]] = {
    "sunny":  {"mean": 170, "std": 25},
    "cloudy": {"mean": 140, "std": 30},
    "rainy":  {"mean": 100, "std": 20},
}

# Avg spend parameters (Lognormal underlying normal params)
SPEND_MU: float = 1.60
SPEND_SIGMA: float = 0.30


# ── Sampling Functions ─────────────────────────────────────────
def sample_weather(rng: np.random.Generator, n: int) -> np.ndarray:
    """Sample n weather conditions from the categorical distribution."""
    return rng.choice(WEATHER_CATEGORIES, size=n, p=WEATHER_P)


def sample_customers(rng: np.random.Generator, weather: np.ndarray) -> np.ndarray:
    """Sample daily customer counts conditional on weather.

    Returns non-negative integers.
    """
    customers = np.empty(len(weather), dtype=float)
    for cat, params in CUSTOMER_PARAMS.items():
        mask = weather == cat
        count = mask.sum()
        if count > 0:
            customers[mask] = rng.normal(params["mean"], params["std"], size=count)
    # Round to nearest int, clip at 0
    customers = np.clip(np.rint(customers), 0, None).astype(int)
    return customers


def sample_avg_spend(rng: np.random.Generator, n: int) -> np.ndarray:
    """Sample average spend per customer from Lognormal(mu, sigma)."""
    return rng.lognormal(mean=SPEND_MU, sigma=SPEND_SIGMA, size=n)


# ── Model Logic ────────────────────────────────────────────────
def compute_revenue(daily_customers: np.ndarray, avg_spend: np.ndarray) -> np.ndarray:
    """Calculate daily revenue = customers × avg_spend."""
    return daily_customers * avg_spend


# ── Simulation Loop ────────────────────────────────────────────
def run_simulation(n: int = N_ITERATIONS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Run the full Monte Carlo simulation and return a DataFrame of results."""
    rng = np.random.default_rng(seed)

    weather = sample_weather(rng, n)
    customers = sample_customers(rng, weather)
    spend = sample_avg_spend(rng, n)
    revenue = compute_revenue(customers, spend)

    return pd.DataFrame({
        "iteration": np.arange(1, n + 1),
        "weather": weather,
        "daily_customers": customers,
        "avg_spend": np.round(spend, 2),
        "daily_revenue": np.round(revenue, 2),
    })


# ── Statistics ─────────────────────────────────────────────────
def compute_statistics(df: pd.DataFrame) -> dict:
    """Compute summary statistics and threshold probabilities."""
    rev = df["daily_revenue"]
    return {
        "mean": rev.mean(),
        "median": rev.median(),
        "std": rev.std(),
        "p5": rev.quantile(0.05),
        "p25": rev.quantile(0.25),
        "p75": rev.quantile(0.75),
        "p95": rev.quantile(0.95),
        "p_below_breakeven": (rev < BREAK_EVEN).mean(),
        "p_below_600": (rev < 600).mean(),
        "p_above_1000": (rev > 1000).mean(),
    }


def print_statistics(s: dict) -> None:
    """Print formatted summary statistics."""
    print("\n" + "=" * 55)
    print("  MONTE CARLO SIMULATION RESULTS — DAILY REVENUE")
    print("=" * 55)
    print(f"  Mean revenue:        ${s['mean']:>10,.2f}")
    print(f"  Median revenue:      ${s['median']:>10,.2f}")
    print(f"  Std deviation:       ${s['std']:>10,.2f}")
    print("-" * 55)
    print(f"  5th percentile:      ${s['p5']:>10,.2f}")
    print(f"  25th percentile:     ${s['p25']:>10,.2f}")
    print(f"  75th percentile:     ${s['p75']:>10,.2f}")
    print(f"  95th percentile:     ${s['p95']:>10,.2f}")
    print("-" * 55)
    print(f"  P(revenue < ${BREAK_EVEN:,.0f}):   {s['p_below_breakeven']:>10.1%}   ← primary metric")
    print(f"  P(revenue < $600):   {s['p_below_600']:>10.1%}   ← stress check")
    print(f"  P(revenue > $1,000): {s['p_above_1000']:>10.1%}   ← upside potential")
    print("=" * 55 + "\n")


# ── Validation ─────────────────────────────────────────────────
def validate_inputs(df: pd.DataFrame) -> None:
    """Validate that sampled inputs match target parameters."""
    print("\n--- INPUT VALIDATION ---\n")

    # Weather proportions
    weather_counts = df["weather"].value_counts(normalize=True)
    print("Weather proportions (target → actual):")
    for cat, target in WEATHER_PROBS.items():
        actual = weather_counts.get(cat, 0)
        print(f"  {cat:>6s}: {target:.0%} → {actual:.1%}")

    # Customer count stats by weather
    print("\nCustomer counts by weather (target → actual):")
    for cat, params in CUSTOMER_PARAMS.items():
        subset = df.loc[df["weather"] == cat, "daily_customers"]
        print(f"  {cat:>6s}: mean {params['mean']} → {subset.mean():.1f}, "
              f"std {params['std']} → {subset.std():.1f}")

    # Avg spend
    expected_spend = np.exp(SPEND_MU + SPEND_SIGMA**2 / 2)
    actual_spend = df["avg_spend"].mean()
    print(f"\nAvg spend: expected ${expected_spend:.2f} → actual ${actual_spend:.2f}")

    # Edge-case checks
    neg_customers = (df["daily_customers"] < 0).sum()
    neg_revenue = (df["daily_revenue"] < 0).sum()
    print(f"\nNegative customer counts: {neg_customers}")
    print(f"Negative revenue values:  {neg_revenue}")
    print()


# ── Visualizations ─────────────────────────────────────────────
def plot_histogram(df: pd.DataFrame, output_dir: str) -> None:
    """Histogram of daily revenue with break-even line."""
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df["daily_revenue"], bins=80, color="#4A90D9", edgecolor="white",
            alpha=0.85, label="Daily revenue")
    ax.axvline(BREAK_EVEN, color="#E74C3C", linewidth=2, linestyle="--",
               label=f"Break-even (${BREAK_EVEN:,.0f})")
    ax.set_xlabel("Daily Revenue ($)", fontsize=12)
    ax.set_ylabel("Frequency", fontsize=12)
    ax.set_title("Distribution of Simulated Daily Revenue", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.legend(fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(f"{output_dir}/histogram_revenue.png", dpi=150)
    plt.close(fig)


def plot_cdf(df: pd.DataFrame, output_dir: str) -> None:
    """CDF of daily revenue with break-even annotation."""
    sorted_rev = np.sort(df["daily_revenue"].values)
    cdf = np.arange(1, len(sorted_rev) + 1) / len(sorted_rev)
    p_below = (df["daily_revenue"] < BREAK_EVEN).mean()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sorted_rev, cdf, color="#4A90D9", linewidth=2)
    ax.axvline(BREAK_EVEN, color="#E74C3C", linewidth=1.5, linestyle="--")
    ax.axhline(p_below, color="#E74C3C", linewidth=1, linestyle=":", alpha=0.6)
    ax.plot(BREAK_EVEN, p_below, "o", color="#E74C3C", markersize=8)
    ax.annotate(f"P(rev < ${BREAK_EVEN:,.0f}) = {p_below:.1%}",
                xy=(BREAK_EVEN, p_below), xytext=(BREAK_EVEN + 80, p_below + 0.08),
                fontsize=11, color="#E74C3C",
                arrowprops=dict(arrowstyle="->", color="#E74C3C"))
    ax.set_xlabel("Daily Revenue ($)", fontsize=12)
    ax.set_ylabel("Cumulative Probability", fontsize=12)
    ax.set_title("Cumulative Distribution of Daily Revenue", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(f"{output_dir}/cdf_revenue.png", dpi=150)
    plt.close(fig)


def plot_tornado(df: pd.DataFrame, output_dir: str) -> None:
    """Sensitivity tornado chart — one-at-a-time swing analysis.

    For each input variable, fix the other at its mean and swing the
    variable between its 10th and 90th percentile to show the impact
    on revenue.
    """
    # Base-case values
    base_customers = df["daily_customers"].mean()
    base_spend = df["avg_spend"].mean()
    base_revenue = base_customers * base_spend

    # Swing: daily_customers
    cust_lo = df["daily_customers"].quantile(0.10)
    cust_hi = df["daily_customers"].quantile(0.90)
    rev_cust_lo = cust_lo * base_spend
    rev_cust_hi = cust_hi * base_spend

    # Swing: avg_spend
    spend_lo = df["avg_spend"].quantile(0.10)
    spend_hi = df["avg_spend"].quantile(0.90)
    rev_spend_lo = base_customers * spend_lo
    rev_spend_hi = base_customers * spend_hi

    labels = ["Daily Customers", "Avg Spend / Customer"]
    lows = [rev_cust_lo - base_revenue, rev_spend_lo - base_revenue]
    highs = [rev_cust_hi - base_revenue, rev_spend_hi - base_revenue]
    ranges = [highs[i] - lows[i] for i in range(len(labels))]
    order = np.argsort(ranges)

    fig, ax = plt.subplots(figsize=(10, 5))
    y_pos = np.arange(len(labels))
    for i, idx in enumerate(order):
        ax.barh(i, highs[idx], color="#4A90D9", height=0.5, label="High" if i == 0 else "")
        ax.barh(i, lows[idx], color="#E74C3C", height=0.5, label="Low" if i == 0 else "")

    ax.set_yticks(y_pos)
    ax.set_yticklabels([labels[i] for i in order], fontsize=12)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Change in Daily Revenue ($)", fontsize=12)
    ax.set_title("Sensitivity Analysis — Tornado Chart", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:+,.0f}"))
    ax.legend(fontsize=11)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    fig.savefig(f"{output_dir}/tornado_sensitivity.png", dpi=150)
    plt.close(fig)


def plot_convergence(df: pd.DataFrame, output_dir: str) -> None:
    """Convergence plot: running mean and 5th/95th percentiles."""
    rev = df["daily_revenue"].values
    n = len(rev)
    running_mean = np.cumsum(rev) / np.arange(1, n + 1)

    # Running percentiles (computed in blocks for speed)
    step = max(1, n // 500)
    indices = np.arange(step, n + 1, step)
    p5_vals, p95_vals = [], []
    for i in indices:
        p5_vals.append(np.percentile(rev[:i], 5))
        p95_vals.append(np.percentile(rev[:i], 95))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(np.arange(1, n + 1), running_mean, color="#4A90D9", linewidth=1.5,
            label="Running mean")
    ax.plot(indices, p5_vals, color="#E74C3C", linewidth=1.2, linestyle="--",
            label="Running 5th percentile")
    ax.plot(indices, p95_vals, color="#27AE60", linewidth=1.2, linestyle="--",
            label="Running 95th percentile")
    ax.axhline(BREAK_EVEN, color="gray", linewidth=1, linestyle=":", alpha=0.6,
               label=f"Break-even (${BREAK_EVEN:,.0f})")
    ax.set_xlabel("Iteration", fontsize=12)
    ax.set_ylabel("Daily Revenue ($)", fontsize=12)
    ax.set_title("Convergence of Revenue Estimates", fontsize=14, fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(f"{output_dir}/convergence_plot.png", dpi=150)
    plt.close(fig)


# ── Main ───────────────────────────────────────────────────────
def main() -> None:
    output_dir = "/sessions/practical-lucid-davinci/mnt/ch04"

    print(f"Running Monte Carlo simulation ({N_ITERATIONS:,} iterations, seed={RANDOM_SEED})...")
    df = run_simulation()

    # Validation
    validate_inputs(df)

    # Statistics
    s = compute_statistics(df)
    print_statistics(s)

    # Save CSV
    csv_path = f"{output_dir}/coffee_shop_simulation_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Results saved to {csv_path}")

    # Visualizations
    print("Generating charts...")
    plot_histogram(df, output_dir)
    plot_cdf(df, output_dir)
    plot_tornado(df, output_dir)
    plot_convergence(df, output_dir)
    print("All charts saved.\n")


if __name__ == "__main__":
    main()
