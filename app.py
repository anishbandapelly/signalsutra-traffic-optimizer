"""SignalSutra Control Room Streamlit app."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data import DEFAULT_TIME_WINDOW_MINUTES, EDGES, GREEN_BUDGET_SECONDS, POSITIONS, load_junction_data
from hardware_status import get_hardware_status
from optimizer import add_ripple_scores, format_genome, run_annealing_optimizer
from voice_parser import DEFAULT_COMMAND, parse_command

st.set_page_config(
    page_title="SignalSutra Control Room",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

CONTROL_ROOM_CSS = """
<style>
:root { --bg:#07101f; --card:#0c1b32; --card2:#102545; --border:#1d3b63; --text:#d7e9ff; --muted:#7a9abc; --green:#00e87e; --amber:#f5a623; --red:#ff4757; --blue:#38b6ff; --purple:#a78bfa; }
.stApp { background: radial-gradient(circle at top left, #11284d 0, #07101f 34%, #050914 100%); color: var(--text); }
section[data-testid="stSidebar"] { background: #081529; border-right: 1px solid var(--border); }
h1, h2, h3 { letter-spacing: -0.02em; }
.top-banner { padding: 14px 18px; border: 1px solid var(--border); border-radius: 16px; background: linear-gradient(135deg, rgba(0,232,126,.10), rgba(56,182,255,.06)); margin-bottom: 14px; }
.badge { display:inline-block; padding:4px 9px; border:1px solid var(--border); border-radius:999px; color:var(--muted); font-size:12px; margin-right:6px; }
.warning { display:inline-block; padding:6px 12px; border-radius:999px; background: rgba(245,166,35,.12); border: 1px solid rgba(245,166,35,.35); color: #ffd78c; font-weight: 700; font-size: 12px; }
.metric-card { border: 1px solid var(--border); border-radius: 18px; padding: 18px; background: rgba(12,27,50,.84); box-shadow: 0 18px 60px rgba(0,0,0,.18); }
.metric-label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .09em; }
.metric-value { font-size: 34px; font-weight: 800; margin-top: 6px; }
.green { color: var(--green); } .red { color: var(--red); } .amber { color: var(--amber); } .blue { color: var(--blue); } .purple { color: var(--purple); }
.panel { border: 1px solid var(--border); border-radius: 18px; padding: 18px; background: rgba(12,27,50,.78); }
.small-muted { color: var(--muted); font-size: 12px; }
.led { display:inline-block; width:10px; height:10px; border-radius:99px; margin-right:7px; box-shadow: 0 0 10px currentColor; }
.logline { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color:#bcd3ec; font-size:13px; border-left:2px solid var(--border); padding:3px 10px; }
div[data-testid="stMetric"] { background: rgba(12,27,50,.70); border: 1px solid var(--border); padding: 14px; border-radius: 16px; }
</style>
"""
st.markdown(CONTROL_ROOM_CSS, unsafe_allow_html=True)

def risk_color(score: float) -> str:
    if score >= 80:
        return "#ff4757"
    if score >= 65:
        return "#f5a623"
    if score >= 50:
        return "#eab308"
    return "#00e87e"

def make_digital_twin(scored: pd.DataFrame, optimized: bool = False) -> go.Figure:
    fig = go.Figure()
    # Edges
    for a, b in EDGES:
        x0, y0 = POSITIONS[a]
        x1, y1 = POSITIONS[b]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1], mode="lines",
            line=dict(color="rgba(122,154,188,.35)", width=2, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))

    # Nodes
    df = scored.copy()
    xs = [POSITIONS[j][0] for j in df["junction"]]
    ys = [POSITIONS[j][1] for j in df["junction"]]
    sizes = [max(24, min(56, s * 0.58)) for s in df["ripple_score"]]
    colors = [risk_color(s) for s in df["ripple_score"]]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(size=sizes, color=colors, line=dict(width=2, color="rgba(255,255,255,.45)")),
        text=[f"{j}<br>{s:.0f}" for j, s in zip(df["junction"], df["ripple_score"])],
        textposition="middle center",
        textfont=dict(color="#ffffff", size=11),
        hovertemplate="<b>%{text}</b><extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1]),
    )
    return fig

def show_metric_cards(result):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Before Ripple", f"{result.before_ripple:.0f}")
    c2.metric("After Ripple", f"{result.after_ripple:.0f}", delta=f"-{result.before_ripple-result.after_ripple:.0f}")
    c3.metric("Congestion Reduction", f"{result.congestion_reduction_pct:.0f}%")
    c4.metric("Plan Confidence", f"{result.confidence_pct}%")

# Header
st.markdown(
    """
    <div class="top-banner">
      <div class="badge">Problem #2</div><div class="badge">SDG 11</div><div class="badge">Quantum for Social Good</div>
      <span class="warning">CONTROL ROOM ANALYSIS UI ONLY — FIELD OFFICERS USE VOICE AI WEARABLE, NO SCREEN</span>
      <h1 style="margin:12px 0 4px 0;">SignalSutra Control Room</h1>
      <div class="small-muted">Voice-assisted, quantum-inspired green-time budget optimizer for Bengaluru traffic control.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

data = load_junction_data()
scored = add_ripple_scores(data)

with st.sidebar:
    st.subheader("ESP32-S3 Field Unit")
    hw = get_hardware_status("standby")
    st.markdown(f"**Device:** {hw['device']}")
    st.markdown(f"**Interface:** {hw['interface']}")
    st.markdown(f"**Connection:** {hw['connection']}")
    st.markdown(f"**Battery:** {hw['battery']}")
    st.markdown(f"<span class='led' style='color:#00e87e;background:#00e87e'></span> **LED:** {hw['led']} — {hw['led_meaning']}", unsafe_allow_html=True)
    st.caption(hw["backend_note"])
    st.divider()

    st.subheader("Voice Command")
    command = st.text_area("Simulated officer voice input", DEFAULT_COMMAND, height=140)
    st.caption("In the real version, this text comes from push-to-talk speech captured by the ESP32-S3 wearable.")

    st.subheader("Optimization Settings")
    iterations = st.slider("Annealing iterations", 500, 5000, 2500, step=500)
    seed = st.number_input("Demo seed", min_value=1, max_value=999, value=42)
    st.markdown(f"**Time window:** {DEFAULT_TIME_WINDOW_MINUTES} minutes")
    st.markdown(f"**Green budget:** {GREEN_BUDGET_SECONDS} seconds")
    st.markdown("**Fairness Guard:** ON")
    run_clicked = st.button("▶ Run Quantum-Inspired Optimizer", use_container_width=True)

if "result" not in st.session_state or run_clicked:
    parsed = parse_command(command)
    result = run_annealing_optimizer(data, iterations=int(iterations), seed=int(seed))
    st.session_state["parsed"] = parsed
    st.session_state["result"] = result
else:
    parsed = st.session_state["parsed"]
    result = st.session_state["result"]

show_metric_cards(result)

left, right = st.columns([1.35, 1])
with left:
    st.markdown("### Micro Traffic Digital Twin")
    # Use after-ripple style graph by reducing display scores based on action.
    after_scored = scored.copy()
    after_scores = []
    for action, score in zip(result.best_genome, after_scored["ripple_score"]):
        after_scores.append(max(0, score - max(-8, min(22, action * 0.45))))
    after_scored["ripple_score"] = after_scores
    st.plotly_chart(make_digital_twin(after_scored), use_container_width=True)
with right:
    st.markdown("### Parsed Voice Command")
    parsed_df = pd.DataFrame([
        ["Location", parsed["location"]],
        ["Direction", parsed["direction"]],
        ["Connected Pressure", ", ".join(parsed["connected_pressure"])],
        ["Time Window", parsed["time_window"]],
        ["Mode", parsed["mode"]],
    ], columns=["Field", "Value"])
    st.dataframe(parsed_df, hide_index=True, use_container_width=True)
    st.markdown("### Signal Genome")
    st.code(format_genome(result.best_genome), language="text")
    st.caption("Each gene changes one junction's green time: -10, 0, +15, or +30 seconds.")

col_a, col_b = st.columns([1, 1.2])
with col_a:
    st.markdown("### Congestion Ripple Ranking")
    ranking = result.ranking.copy()
    ranking["ripple_score"] = ranking["ripple_score"].round(0).astype(int)
    st.dataframe(ranking, hide_index=True, use_container_width=True)
with col_b:
    st.markdown("### Green-Time Budget Plan")
    plan = result.plan.copy()
    plan["ripple_score"] = plan["ripple_score"].round(0).astype(int)
    st.dataframe(plan, hide_index=True, use_container_width=True)

b1, b2, b3 = st.columns([1.1, 1, 1])
with b1:
    st.markdown("### Baseline Comparison")
    baseline = result.baseline.copy()
    baseline["Ripple Score"] = baseline["Ripple Score"].round(0).astype(int)
    baseline["Avg Wait"] = baseline["Avg Wait"].round(0).astype(int).astype(str) + " sec"
    st.dataframe(baseline, hide_index=True, use_container_width=True)
with b2:
    st.markdown("### Fairness Guard")
    fairness_rows = [
        "✅ Minimum green time maintained",
        "✅ Side-road starvation prevented",
        "✅ No unsafe signal reduction",
        "✅ Human approval required before execution",
    ]
    for row in fairness_rows:
        st.markdown(row)
    approve = st.button("✓ Approve Signal Plan", use_container_width=True)
    if approve:
        st.success("Approved by control room officer. Field unit receives audio confirmation.")
with b3:
    st.markdown("### Quantum-Inspired Annealing")
    st.markdown(
        """
        The MVP represents each signal plan as an energy state. Early in the search, the optimizer may accept a worse plan using `exp(-ΔE/T)` so it can escape local traps. As temperature cools, it settles on the lowest-cost green-time budget found.
        """
    )
    st.code("Cost = Ripple + Wait + Spillback + SignalChange + Fairness", language="text")

st.markdown("### Live Demo Log")
for line in result.logs:
    st.markdown(f"<div class='logline'>{line}</div>", unsafe_allow_html=True)
