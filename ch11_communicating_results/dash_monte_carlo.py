"""
Dash/Plotly Monte Carlo Dashboard
----------------------------------
Run with:  python dash_monte_carlo.py
Then open: http://127.0.0.1:8050
Requires:  pip install dash plotly numpy
"""

import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ── App setup ────────────────────────────────────────────────────────
app = Dash(__name__)

# ── Layout ───────────────────────────────────────────────────────────
# Unlike Streamlit, Dash separates layout (what you see) from
# callbacks (how it behaves). This gives you explicit control
# over both, at the cost of more boilerplate.

app.layout = html.Div(
    style={"fontFamily": "Arial, sans-serif", "margin": "0 auto",
           "maxWidth": "960px", "padding": "24px"},
    children=[
        html.H2("Monte Carlo: Project Cost Estimator"),
        html.P(
            "Adjust the controls to see how input uncertainty "
            "affects the total project cost distribution."
        ),

        # ── Control panel ────────────────────────────────────────────
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                   "gap": "24px", "marginBottom": "24px",
                   "padding": "16px", "backgroundColor": "#f8f9fa",
                   "borderRadius": "8px"},
            children=[
                html.Div([
                    html.Label("Number of simulations"),
                    dcc.Slider(
                        id="n-simulations", min=500, max=20_000,
                        step=500, value=5_000,
                        marks={500: "500", 10_000: "10K", 20_000: "20K"},
                    ),
                ]),
                html.Div([
                    html.Label("Risk scenario"),
                    dcc.Dropdown(
                        id="risk-scenario",
                        options=[
                            {"label": "None", "value": "none"},
                            {"label": "Supply-chain delay (+15%)",
                             "value": "supply"},
                            {"label": "Regulatory change (+25%)",
                             "value": "regulatory"},
                        ],
                        value="none", clearable=False,
                    ),
                ]),
                html.Div([
                    html.Label("Avg labor cost ($K)"),
                    dcc.Slider(
                        id="labor-mean", min=100, max=500,
                        step=10, value=250,
                        marks={100: "$100K", 300: "$300K", 500: "$500K"},
                    ),
                ]),
                html.Div([
                    html.Label("Avg materials cost ($K)"),
                    dcc.Slider(
                        id="materials-mean", min=50, max=300,
                        step=10, value=120,
                        marks={50: "$50K", 175: "$175K", 300: "$300K"},
                    ),
                ]),
                html.Div([
                    html.Label("Labor uncertainty ($K)"),
                    dcc.Slider(
                        id="labor-std", min=10, max=100,
                        step=5, value=40,
                        marks={10: "10", 50: "50", 100: "100"},
                    ),
                ]),
                html.Div([
                    html.Label("Materials uncertainty ($K)"),
                    dcc.Slider(
                        id="materials-std", min=5, max=80,
                        step=5, value=25,
                        marks={5: "5", 40: "40", 80: "80"},
                    ),
                ]),
                html.Div([
                    html.Label("Budget threshold ($K)"),
                    dcc.Slider(
                        id="budget-threshold", min=200, max=800,
                        step=10, value=400,
                        marks={200: "$200K", 500: "$500K", 800: "$800K"},
                    ),
                ]),
            ],
        ),

        # ── Metrics row ─────────────────────────────────────────────
        html.Div(
            id="metrics-row",
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr",
                   "gap": "16px", "marginBottom": "24px",
                   "textAlign": "center"},
        ),

        # ── Chart ────────────────────────────────────────────────────
        dcc.Graph(id="cost-histogram"),

        html.P(id="caption",
               style={"fontSize": "0.85em", "color": "#666",
                       "marginTop": "8px"}),
    ],
)


# ── Callbacks ────────────────────────────────────────────────────────
# Dash uses explicit callbacks to wire inputs to outputs.
# This is more verbose than Streamlit's top-to-bottom rerun,
# but gives you precise control over what updates and when.

@app.callback(
    Output("cost-histogram", "figure"),
    Output("metrics-row", "children"),
    Output("caption", "children"),
    Input("n-simulations", "value"),
    Input("labor-mean", "value"),
    Input("labor-std", "value"),
    Input("materials-mean", "value"),
    Input("materials-std", "value"),
    Input("risk-scenario", "value"),
    Input("budget-threshold", "value"),
)
def update_dashboard(n_sims, labor_mu, labor_sig,
                     mat_mu, mat_sig, risk, threshold):

    rng = np.random.default_rng(42)
    labor = rng.normal(labor_mu, labor_sig, n_sims)
    materials = rng.normal(mat_mu, mat_sig, n_sims)
    total = labor + materials

    if risk == "supply":
        total *= 1.15
    elif risk == "regulatory":
        total *= 1.25

    over_pct = (total > threshold).mean() * 100

    # ── Plotly figure ────────────────────────────────────────────
    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=total, nbinsx=60,
        marker_color="#4A90D9", marker_line_color="white",
        marker_line_width=0.5, opacity=0.85,
        name="Simulated costs",
    ))

    fig.add_vline(
        x=threshold, line_dash="dash", line_color="#D94A4A",
        line_width=2, annotation_text=f"Budget: ${threshold}K",
        annotation_position="top left",
        annotation_font_color="#D94A4A",
    )

    # Shade over-budget region
    fig.add_vrect(
        x0=threshold, x1=total.max(),
        fillcolor="#D94A4A", opacity=0.08, line_width=0,
    )

    fig.update_layout(
        title="Simulated Cost Distribution",
        xaxis_title="Total Project Cost ($K)",
        yaxis_title="Frequency",
        template="plotly_white",
        margin=dict(t=48, b=48),
        showlegend=False,
    )

    # ── Metric cards ─────────────────────────────────────────────
    def metric_card(label, value):
        return html.Div(
            style={"padding": "12px", "backgroundColor": "#f8f9fa",
                   "borderRadius": "8px"},
            children=[
                html.Div(label, style={"fontSize": "0.85em",
                                        "color": "#666"}),
                html.Div(value, style={"fontSize": "1.4em",
                                        "fontWeight": "bold"}),
            ],
        )

    metrics = [
        metric_card("Mean cost", f"${total.mean():,.0f}K"),
        metric_card("5th percentile", f"${np.percentile(total, 5):,.0f}K"),
        metric_card("95th percentile", f"${np.percentile(total, 95):,.0f}K"),
    ]

    caption = (
        f"Based on {n_sims:,} simulations. "
        f"There is a {over_pct:.1f}% probability of exceeding "
        f"the ${threshold}K budget threshold."
    )

    return fig, metrics, caption


# ── Run server ───────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
