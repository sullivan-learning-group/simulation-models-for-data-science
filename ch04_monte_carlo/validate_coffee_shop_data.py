"""
Coffee Shop Data: Exploratory Analysis & Distribution Fitting
==============================================================
Validates the synthetic dataset by fitting distributions using the
techniques taught in Chapter 3. Confirms that recovered parameters
match the simulation targets from Chapter 4.

This script also serves as a teaching example: readers can run it
against the generated data to practice the Chapter 3 workflow.

Usage:
    python validate_coffee_shop_data.py [--data-dir ./data] [--save-plots]
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Plot styling for O'Reilly B&W print compatibility
# ---------------------------------------------------------------------------

def setup_plot_style():
    plt.rcParams.update({
        "figure.figsize": (6.5, 4.0),
        "figure.dpi": 300,
        "font.size": 10,
        "font.family": "serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
    })


# ---------------------------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------------------------

def load_data(data_dir):
    df = pd.read_csv(data_dir / "coffee_shop_daily_operations.csv",
                     parse_dates=["date"])
    print(f"Loaded {len(df)} records from {df['date'].min()} to {df['date'].max()}")
    return df


def identify_outliers(df):
    """Flag outlier days using IQR method on daily_revenue."""
    q1 = df["daily_revenue"].quantile(0.25)
    q3 = df["daily_revenue"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    outliers = df[(df["daily_revenue"] < lower) | (df["daily_revenue"] > upper)]
    print(f"\nOutliers detected (IQR method): {len(outliers)} days")
    for _, row in outliers.iterrows():
        print(f"  {row['date'].strftime('%Y-%m-%d')} ({row['day_of_week']}): "
              f"{row['customer_count']} customers, ${row['daily_revenue']:.0f} revenue")
    return outliers.index


# ---------------------------------------------------------------------------
# Distribution fitting
# ---------------------------------------------------------------------------

def fit_customer_counts(df, label, save_plots=False, plot_dir=None):
    """Fit negative binomial to customer counts and report parameters."""
    counts = df["customer_count"].values

    # Method of moments for negative binomial
    mean = counts.mean()
    var = counts.var()
    overdispersion = var / mean

    # Scipy parameterization: n, p
    n_param = mean ** 2 / (var - mean) if var > mean else mean
    p_param = n_param / (n_param + mean)

    print(f"\n--- Customer Counts: {label} ---")
    print(f"  Sample mean:    {mean:.1f}")
    print(f"  Sample var:     {var:.1f}")
    print(f"  Overdispersion: {overdispersion:.2f}")
    print(f"  NB params:      n={n_param:.2f}, p={p_param:.4f}")

    # Goodness of fit: compare to Poisson
    poisson_loglik = stats.poisson.logpmf(counts, mean).sum()
    nb_loglik = stats.nbinom.logpmf(counts, n_param, p_param).sum()
    print(f"  Poisson log-lik:  {poisson_loglik:.0f}")
    print(f"  NegBinom log-lik: {nb_loglik:.0f}")
    print(f"  NegBinom preferred: {nb_loglik > poisson_loglik}")

    if save_plots and plot_dir:
        fig, ax = plt.subplots()
        ax.hist(counts, bins=30, density=True, alpha=0.7, color="0.6",
                edgecolor="0.4", label="Observed")

        x = np.arange(counts.min(), counts.max() + 1)
        ax.plot(x, stats.nbinom.pmf(x, n_param, p_param), "k-", lw=1.5,
                label=f"NegBin(n={n_param:.1f}, p={p_param:.3f})")
        ax.plot(x, stats.poisson.pmf(x, mean), "k--", lw=1.0, alpha=0.6,
                label=f"Poisson(λ={mean:.1f})")

        ax.set_xlabel("Daily Customer Count")
        ax.set_ylabel("Probability")
        ax.set_title(f"Customer Count Distribution: {label}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(plot_dir / f"customers_{label.lower().replace(' ', '_')}.png")
        plt.close(fig)

    return {"mean": mean, "var": var, "overdispersion": overdispersion,
            "n": n_param, "p": p_param}


def fit_transaction_values(df, label, save_plots=False, plot_dir=None):
    """Fit lognormal to transaction values and report parameters."""
    vals = df["avg_transaction_value"].values

    # MLE for lognormal
    shape, loc, scale = stats.lognorm.fit(vals, floc=0)
    mu_log = np.log(scale)
    sigma_log = shape

    print(f"\n--- Transaction Values: {label} ---")
    print(f"  Sample mean:   ${vals.mean():.2f}")
    print(f"  Sample median: ${np.median(vals):.2f}")
    print(f"  Lognormal μ:   {mu_log:.3f} (implies median=${np.exp(mu_log):.2f})")
    print(f"  Lognormal σ:   {sigma_log:.3f}")

    # K-S test
    ks_stat, ks_p = stats.kstest(vals, "lognorm", args=(shape, loc, scale))
    print(f"  K-S test:      stat={ks_stat:.4f}, p={ks_p:.4f}")

    if save_plots and plot_dir:
        fig, ax = plt.subplots()
        ax.hist(vals, bins=35, density=True, alpha=0.7, color="0.6",
                edgecolor="0.4", label="Observed")

        x = np.linspace(vals.min() * 0.8, vals.max() * 1.1, 200)
        ax.plot(x, stats.lognorm.pdf(x, shape, loc, scale), "k-", lw=1.5,
                label=f"Lognormal(μ={mu_log:.2f}, σ={sigma_log:.2f})")

        ax.set_xlabel("Average Transaction Value ($)")
        ax.set_ylabel("Density")
        ax.set_title(f"Transaction Value Distribution: {label}")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(plot_dir / f"transactions_{label.lower().replace(' ', '_')}.png")
        plt.close(fig)

    return {"mean": vals.mean(), "median": np.median(vals),
            "mu_log": mu_log, "sigma_log": sigma_log, "ks_p": ks_p}


# ---------------------------------------------------------------------------
# Correlation analysis
# ---------------------------------------------------------------------------

def analyze_correlations(df, save_plots=False, plot_dir=None):
    """Compute and report correlation structure."""
    weather_num = df["weather_category"].map(
        {"sunny": 0, "cloudy": 1, "rainy": 2, "extreme": 3}
    )

    print("\n--- Correlation Matrix ---")
    corr_data = pd.DataFrame({
        "weather_severity": weather_num,
        "customer_count": df["customer_count"],
        "avg_transaction": df["avg_transaction_value"],
    })
    corr_matrix = corr_data.corr()
    print(corr_matrix.round(3).to_string())

    if save_plots and plot_dir:
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))

        axes[0].scatter(df["customer_count"], df["avg_transaction_value"],
                        s=5, alpha=0.3, color="0.4")
        axes[0].set_xlabel("Customer Count")
        axes[0].set_ylabel("Avg Transaction ($)")
        axes[0].set_title("Customers vs. Transaction Value")

        weather_order = ["sunny", "cloudy", "rainy", "extreme"]
        weather_counts = [df[df["weather_category"] == w]["customer_count"]
                          for w in weather_order]
        bp = axes[1].boxplot(weather_counts, labels=weather_order,
                             patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("0.8")
        axes[1].set_xlabel("Weather Category")
        axes[1].set_ylabel("Customer Count")
        axes[1].set_title("Weather Impact on Traffic")

        fig.tight_layout()
        fig.savefig(plot_dir / "correlations.png")
        plt.close(fig)


# ---------------------------------------------------------------------------
# Revenue distribution summary
# ---------------------------------------------------------------------------

def summarize_revenue(df, save_plots=False, plot_dir=None):
    """Produce the revenue distribution summary that readers will compare
    against their simulation output."""
    rev = df["daily_revenue"]

    print("\n--- Daily Revenue Summary ---")
    print(f"  Mean:   ${rev.mean():,.0f}")
    print(f"  Median: ${rev.median():,.0f}")
    print(f"  Std:    ${rev.std():,.0f}")
    print(f"  P5:     ${rev.quantile(0.05):,.0f}")
    print(f"  P25:    ${rev.quantile(0.25):,.0f}")
    print(f"  P75:    ${rev.quantile(0.75):,.0f}")
    print(f"  P95:    ${rev.quantile(0.95):,.0f}")
    print(f"  Min:    ${rev.min():,.0f}")
    print(f"  Max:    ${rev.max():,.0f}")

    profit = df["daily_profit"]
    loss_days = (profit < 0).sum()
    pct = loss_days / len(df) * 100
    print(f"\n  Days with negative profit: {loss_days} ({pct:.1f}%)")

    if save_plots and plot_dir:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

        # Histogram with reference lines
        ax1.hist(profit, bins=40, alpha=0.7, color="0.6", edgecolor="0.4")
        ax1.axvline(profit.mean(), color="0.2", ls="-", lw=1.5, label=f"Mean: ${profit.mean():,.0f}")
        ax1.axvline(profit.median(), color="0.2", ls="--", lw=1.5, label=f"Median: ${profit.median():,.0f}")
        ax1.axvline(0, color="0.0", ls=":", lw=2, label="Break-even (profit=0)")
        ax1.set_xlabel("Daily Profit ($)")
        ax1.set_ylabel("Frequency")
        ax1.set_title("Daily Profit Distribution")
        ax1.legend(fontsize=8)

        # CDF
        sorted_profit = np.sort(profit)
        cdf = np.arange(1, len(sorted_profit) + 1) / len(sorted_profit)
        ax2.plot(sorted_profit, cdf, "k-", lw=1.5)
        ax2.axhline(0.05, color="0.5", ls="--", lw=0.8, alpha=0.5)
        ax2.axhline(0.95, color="0.5", ls="--", lw=0.8, alpha=0.5)
        ax2.axvline(0, color="0.0", ls=":", lw=1.5)
        ax2.set_xlabel("Daily Profit ($)")
        ax2.set_ylabel("Cumulative Probability")
        ax2.set_title("Profit CDF")

        fig.tight_layout()
        fig.savefig(plot_dir / "revenue_distribution.png")
        plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate coffee shop synthetic data")
    parser.add_argument("--data-dir", type=str, default="./data")
    parser.add_argument("--save-plots", action="store_true",
                        help="Save validation plots as PNG files")
    args = parser.parse_args()

    setup_plot_style()
    data_dir = Path(args.data_dir)
    plot_dir = data_dir / "plots"

    if args.save_plots:
        plot_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(data_dir)

    # Step 1: Identify and remove outliers (as taught in Chapter 3)
    outlier_idx = identify_outliers(df)
    df_clean = df.drop(index=outlier_idx)
    print(f"Clean dataset: {len(df_clean)} rows")

    # Step 2: Segment weekday vs. weekend
    weekday = df_clean[~df_clean["is_weekend"]]
    weekend = df_clean[df_clean["is_weekend"]]

    # Step 3: Fit customer count distributions
    fit_customer_counts(weekday, "Weekday", args.save_plots, plot_dir)
    fit_customer_counts(weekend, "Weekend", args.save_plots, plot_dir)

    # Step 4: Fit transaction value distributions
    fit_transaction_values(weekday, "Weekday", args.save_plots, plot_dir)
    fit_transaction_values(weekend, "Weekend", args.save_plots, plot_dir)

    # Step 5: Analyze correlations
    analyze_correlations(df_clean, args.save_plots, plot_dir)

    # Step 6: Revenue summary (full dataset including outliers for realism)
    summarize_revenue(df, args.save_plots, plot_dir)

    # Weather frequency check
    print("\n--- Weather Frequencies ---")
    freq = df["weather_category"].value_counts(normalize=True).sort_index()
    for cat, pct in freq.items():
        print(f"  {cat}: {pct:.1%}")

    if args.save_plots:
        print(f"\nPlots saved to {plot_dir}/")


if __name__ == "__main__":
    main()
