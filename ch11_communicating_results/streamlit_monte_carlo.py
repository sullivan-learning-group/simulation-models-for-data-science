"""
Simple Streamlit Monte Carlo Dashboard
---------------------------------------
Run with:  streamlit run streamlit_monte_carlo.py
Requires:  pip install streamlit numpy matplotlib
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("Monte Carlo: Project Cost Estimator")
st.markdown(
    "Adjust the sliders to see how input uncertainty affects the "
    "total project cost distribution."
)

# --- Sidebar controls (sliders + dropdown) ---
st.sidebar.header("Simulation Parameters")

n_simulations = st.sidebar.slider(
    "Number of simulations", 500, 20_000, 5_000, step=500
)

labor_mean = st.sidebar.slider(
    "Avg labor cost ($K)", 100, 500, 250
)
labor_std = st.sidebar.slider(
    "Labor uncertainty ($K)", 10, 100, 40
)

materials_mean = st.sidebar.slider(
    "Avg materials cost ($K)", 50, 300, 120
)
materials_std = st.sidebar.slider(
    "Materials uncertainty ($K)", 5, 80, 25
)

risk_event = st.sidebar.selectbox(
    "Risk scenario",
    ["None", "Supply-chain delay (+15%)", "Regulatory change (+25%)"]
)

# --- Run simulation ---
np.random.seed(42)

labor = np.random.normal(labor_mean, labor_std, n_simulations)
materials = np.random.normal(materials_mean, materials_std, n_simulations)
total_cost = labor + materials

# Apply risk scenario
if risk_event == "Supply-chain delay (+15%)":
    total_cost *= 1.15
elif risk_event == "Regulatory change (+25%)":
    total_cost *= 1.25

# --- Summary metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("Mean cost", f"${total_cost.mean():,.0f}K")
col2.metric("5th percentile", f"${np.percentile(total_cost, 5):,.0f}K")
col3.metric("95th percentile", f"${np.percentile(total_cost, 95):,.0f}K")

# --- Histogram with annotated threshold ---
budget_threshold = st.slider(
    "Budget threshold ($K)", 200, 800, 400
)

fig, ax = plt.subplots(figsize=(8, 4))
ax.hist(total_cost, bins=60, color="#4A90D9", edgecolor="white", alpha=0.85)
ax.axvline(budget_threshold, color="#D94A4A", linewidth=2, linestyle="--",
           label=f"Budget: ${budget_threshold}K")

# Shade the over-budget region
over_budget_pct = (total_cost > budget_threshold).mean() * 100
ax.fill_betweenx(
    [0, ax.get_ylim()[1] * 0.9],
    budget_threshold, total_cost.max(),
    color="#D94A4A", alpha=0.12
)

ax.set_xlabel("Total Project Cost ($K)")
ax.set_ylabel("Frequency")
ax.set_title("Simulated Cost Distribution")
ax.legend()
ax.text(
    budget_threshold + 10, ax.get_ylim()[1] * 0.75,
    f"{over_budget_pct:.1f}% over budget",
    color="#D94A4A", fontsize=11, fontweight="bold"
)

st.pyplot(fig)

st.caption(
    f"Based on {n_simulations:,} simulations. "
    f"There is a {over_budget_pct:.1f}% probability of exceeding "
    f"the ${budget_threshold}K budget threshold."
)
