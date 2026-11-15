"""
Panel / HoloViews Monte Carlo Dashboard
----------------------------------------
Run with:  panel serve panel_monte_carlo.py
Then open: http://localhost:5006
Requires:  pip install panel holoviews bokeh numpy
"""

import numpy as np
import holoviews as hv
import panel as pn

hv.extension("bokeh")
pn.extension(sizing_mode="stretch_width")

# ── Widgets ──────────────────────────────────────────────────────────
# Panel widgets are composable building blocks — you can mix them
# freely and bind them to any plotting library in the HoloViz ecosystem.

n_simulations = pn.widgets.IntSlider(
    name="Number of simulations", start=500, end=20_000,
    step=500, value=5_000,
)
labor_mean = pn.widgets.IntSlider(
    name="Avg labor cost ($K)", start=100, end=500, step=10, value=250,
)
labor_std = pn.widgets.IntSlider(
    name="Labor uncertainty ($K)", start=10, end=100, step=5, value=40,
)
materials_mean = pn.widgets.IntSlider(
    name="Avg materials cost ($K)", start=50, end=300, step=10, value=120,
)
materials_std = pn.widgets.IntSlider(
    name="Materials uncertainty ($K)", start=5, end=80, step=5, value=25,
)
risk_scenario = pn.widgets.Select(
    name="Risk scenario",
    options={"None": 1.0, "Supply-chain delay (+15%)": 1.15,
             "Regulatory change (+25%)": 1.25},
    value=1.0,
)
budget_threshold = pn.widgets.IntSlider(
    name="Budget threshold ($K)", start=200, end=800, step=10, value=400,
)


# ── Simulation logic ─────────────────────────────────────────────────

def run_simulation(n, l_mu, l_sig, m_mu, m_sig, risk):
    rng = np.random.default_rng(42)
    labor = rng.normal(l_mu, l_sig, n)
    materials = rng.normal(m_mu, m_sig, n)
    return (labor + materials) * risk, labor, materials


# ── Linked views ─────────────────────────────────────────────────────
# HoloViews lets you declare *what* to plot and how plots relate.
# Panel then handles layout, widgets, and serving. This separation
# is what makes multi-panel, linked dashboards straightforward.

def cost_histogram(n, l_mu, l_sig, m_mu, m_sig, risk, threshold):
    """Main histogram with budget threshold overlay."""
    total, _, _ = run_simulation(n, l_mu, l_sig, m_mu, m_sig, risk)
    over_pct = (total > threshold).mean() * 100

    frequencies, edges = np.histogram(total, bins=60)

    hist = hv.Histogram((edges, frequencies)).opts(
        color="#4A90D9", alpha=0.85, line_color="white",
        xlabel="Total Project Cost ($K)", ylabel="Frequency",
        title="Simulated Cost Distribution",
        height=350,
    )
    threshold_line = hv.VLine(threshold).opts(
        color="#D94A4A", line_dash="dashed", line_width=2,
    )
    label = hv.Text(
        threshold + 15,
        frequencies.max() * 0.75,
        f"{over_pct:.1f}% over budget",
    ).opts(text_color="#D94A4A", text_font_size="11pt")

    return hist * threshold_line * label


def component_scatter(n, l_mu, l_sig, m_mu, m_sig, risk, threshold):
    """Scatter of labor vs. materials — points colored by over/under budget."""
    total, labor, materials = run_simulation(
        n, l_mu, l_sig, m_mu, m_sig, risk
    )
    # Downsample for readability
    idx = np.random.default_rng(0).choice(len(total), min(2000, len(total)),
                                          replace=False)
    status = np.where(total[idx] > threshold, "Over budget", "Under budget")

    scatter = hv.Scatter(
        {"Labor ($K)": labor[idx], "Materials ($K)": materials[idx],
         "Status": status},
        kdims=["Labor ($K)"], vdims=["Materials ($K)", "Status"],
    ).opts(
        color="Status",
        cmap={"Over budget": "#D94A4A", "Under budget": "#4A90D9"},
        alpha=0.45, size=4,
        title="Component Cost Breakdown",
        height=350,
        legend_position="top_left",
    )
    return scatter


def cdf_plot(n, l_mu, l_sig, m_mu, m_sig, risk, threshold):
    """Cumulative distribution function with threshold annotation."""
    total, _, _ = run_simulation(n, l_mu, l_sig, m_mu, m_sig, risk)
    sorted_costs = np.sort(total)
    cumulative = np.arange(1, len(sorted_costs) + 1) / len(sorted_costs)

    cdf_curve = hv.Curve(
        (sorted_costs, cumulative),
        kdims=["Total Cost ($K)"], vdims=["Cumulative Probability"],
    ).opts(
        color="#4A90D9", line_width=2,
        title="Cumulative Distribution Function",
        height=350,
    )
    threshold_line = hv.VLine(threshold).opts(
        color="#D94A4A", line_dash="dashed", line_width=2,
    )
    prob_at_threshold = (total <= threshold).mean()
    label = hv.Text(
        threshold + 10, prob_at_threshold,
        f"P(cost ≤ ${threshold}K) = {prob_at_threshold:.1%}",
    ).opts(text_color="#D94A4A", text_font_size="10pt",
           text_align="left")

    return cdf_curve * threshold_line * label


# ── Bind widgets to plots ────────────────────────────────────────────
# pn.bind wires each widget to all three plotting functions.
# When any slider moves, every linked panel updates together.

bind_args = dict(
    n=n_simulations, l_mu=labor_mean, l_sig=labor_std,
    m_mu=materials_mean, m_sig=materials_std,
    risk=risk_scenario, threshold=budget_threshold,
)

hist_panel = pn.bind(cost_histogram, **bind_args)
scatter_panel = pn.bind(component_scatter, **bind_args)
cdf_panel = pn.bind(cdf_plot, **bind_args)


# ── Metrics pane ─────────────────────────────────────────────────────

def metrics_pane(n, l_mu, l_sig, m_mu, m_sig, risk, threshold):
    total, _, _ = run_simulation(n, l_mu, l_sig, m_mu, m_sig, risk)
    over_pct = (total > threshold).mean() * 100
    return pn.pane.Markdown(
        f"**Mean:** ${total.mean():,.0f}K &nbsp;&nbsp; "
        f"**P5:** ${np.percentile(total, 5):,.0f}K &nbsp;&nbsp; "
        f"**P95:** ${np.percentile(total, 95):,.0f}K &nbsp;&nbsp; "
        f"**Over budget:** {over_pct:.1f}%",
        styles={"background": "#f8f9fa", "padding": "12px",
                "border-radius": "8px", "text-align": "center"},
    )

metrics = pn.bind(metrics_pane, **bind_args)


# ── Layout ───────────────────────────────────────────────────────────
# Panel's layout primitives (Row, Column, Tabs, GridSpec) let you
# compose multi-panel dashboards from independent pieces.

sidebar = pn.Column(
    "## Controls",
    n_simulations, labor_mean, labor_std,
    materials_mean, materials_std,
    risk_scenario, budget_threshold,
    width=280,
)

main = pn.Column(
    "# Monte Carlo: Project Cost Estimator",
    metrics,
    pn.Row(hist_panel, scatter_panel),
    cdf_panel,
)

pn.template.FastListTemplate(
    title="Monte Carlo Cost Estimator",
    sidebar=[sidebar],
    main=[main],
).servable()
