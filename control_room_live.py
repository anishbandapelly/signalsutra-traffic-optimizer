"""Live control-room dashboard for hardware/API integration.

Run after starting api_server.py:
    streamlit run control_room_live.py

This app reads runtime/latest_plan.json, so it updates when the ESP32-S3 or
ElatoAI bridge posts a transcript to the FastAPI backend.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

from runtime_store import DEVICE_STATUS_PATH, LATEST_PLAN_PATH, default_device_status, read_events, read_json
from voice_parser import DEFAULT_COMMAND

API_BASE = "http://127.0.0.1:8001"

st.set_page_config(page_title="SignalSutra Live Control Room", page_icon="🚦", layout="wide")

st.markdown(
    """
<style>
.stApp { background: #06101f; color: #d7e9ff; }
section[data-testid="stSidebar"] { background: #081529; border-right: 1px solid #1d3b63; }
.live-card { border:1px solid #1d3b63; border-radius:16px; padding:16px; background:rgba(12,27,50,.82); }
.warn { display:inline-block; padding:6px 12px; border-radius:999px; background:rgba(245,166,35,.13); border:1px solid rgba(245,166,35,.35); color:#ffd78c; font-weight:700; font-size:12px; }
.green { color:#00e87e; } .red { color:#ff4757; } .amber { color:#f5a623; } .blue { color:#38b6ff; } .purple { color:#a78bfa; }
.logline { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color:#bcd3ec; font-size:13px; border-left:2px solid #1d3b63; padding:3px 10px; }
.small { color:#7a9abc; font-size:13px; }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
# 🚦 SignalSutra Live Control Room
<span class="warn">CONTROL ROOM ANALYSIS UI ONLY — FIELD TRAFFIC OFFICERS USE ESP32-S3 VOICE WEARABLE, NO SCREEN</span>

The ESP32-S3 / ElatoAI field unit sends the officer's voice transcript to the backend. This dashboard reads the latest generated plan for monitoring, analysis, and human approval.
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Backend")
    api_base = st.text_input("API base URL", API_BASE)
    c1, c2 = st.columns(2)
    if c1.button("Health", use_container_width=True):
        try:
            st.json(requests.get(f"{api_base}/health", timeout=3).json())
        except Exception as exc:
            st.error(f"Backend not reachable: {exc}")
    if c2.button("Run demo command", use_container_width=True):
        try:
            r = requests.post(
                f"{api_base}/api/traffic-command",
                json={"transcript": DEFAULT_COMMAND, "source": "control-room-demo", "device_id": "dashboard"},
                timeout=10,
            )
            st.success(r.json().get("status", "done"))
        except Exception as exc:
            st.error(f"Demo command failed: {exc}")

    st.divider()
    st.subheader("Device Status")
    device = read_json(DEVICE_STATUS_PATH) or default_device_status()
    st.write(f"**Device:** {device.get('device', 'ESP32-S3 Field Unit')}")
    st.write(f"**Device ID:** {device.get('device_id')}")
    st.write(f"**Connection:** {device.get('connection')}")
    st.write(f"**Battery:** {device.get('battery')}")
    st.write(f"**LED:** {device.get('led')} — {device.get('led_meaning')}")
    st.caption(f"Updated: {device.get('updated_at')}")

    st.divider()
    st.subheader("Manual Hardware Test")
    transcript = st.text_area("Send transcript to API", DEFAULT_COMMAND, height=130)
    if st.button("POST as ESP32 transcript", use_container_width=True):
        try:
            r = requests.post(
                f"{api_base}/api/traffic-command",
                json={"transcript": transcript, "source": "dashboard-test", "device_id": "dashboard"},
                timeout=10,
            )
            st.success(r.json().get("status", "done"))
        except Exception as exc:
            st.error(f"POST failed: {exc}")

if st.button("🔄 Refresh latest hardware plan", use_container_width=True):
    st.rerun()

plan = read_json(LATEST_PLAN_PATH)
if not plan:
    st.info("No hardware command received yet. Start the backend, flash the ESP32 firmware, then press the ESP32 button or run demo command.")
    st.code("uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload\nstreamlit run control_room_live.py", language="bash")
    st.stop()

st.caption(f"Latest plan generated at: {plan.get('timestamp')} · Source: {plan.get('source')} · Device: {plan.get('device_id')}")
st.markdown(f"**Transcript:** {plan.get('transcript')}")

metrics = plan["metrics"]
m1, m2, m3, m4 = st.columns(4)
m1.metric("Before Ripple", f"{metrics['before_ripple']:.0f}")
m2.metric("After Ripple", f"{metrics['after_ripple']:.0f}", delta=f"-{metrics['before_ripple'] - metrics['after_ripple']:.0f}")
m3.metric("Congestion Reduction", f"{metrics['congestion_reduction_pct']:.0f}%")
m4.metric("Plan Confidence", f"{metrics['plan_confidence_pct']}%")

left, right = st.columns([1, 1])
with left:
    st.markdown("### Parsed Voice Command")
    parsed = plan["parsed_command"]
    st.dataframe(pd.DataFrame([
        ["Location", parsed.get("location")],
        ["Direction", parsed.get("direction")],
        ["Connected Pressure", ", ".join(parsed.get("connected_pressure", []))],
        ["Time Window", parsed.get("time_window")],
        ["Mode", parsed.get("mode")],
    ], columns=["Field", "Value"]), hide_index=True, use_container_width=True)
    st.markdown("### Signal Genome")
    st.code(plan["optimizer"]["signal_genome_text"], language="text")
with right:
    st.markdown("### Hardware Feedback")
    hf = plan.get("hardware_feedback", {})
    st.markdown(f"**LED:** {hf.get('led')}")
    st.markdown(f"**Speaker response:** {hf.get('speaker_text')}")
    st.markdown("### Fairness Guard")
    fg = plan["fairness_guard"]
    st.write("✅ Minimum green time maintained" if fg["minimum_green_time_maintained"] else "❌ Minimum green time issue")
    st.write("✅ Side-road starvation prevented" if fg["side_road_starvation_prevented"] else "❌ Starvation risk")
    st.write("✅ No unsafe signal reduction" if fg["no_unsafe_signal_reduction"] else "❌ Unsafe reduction")
    st.write(f"**Approval status:** {fg['approval_status']}")
    if st.button("✓ Approve Signal Plan", use_container_width=True):
        try:
            r = requests.post(f"{api_base}/api/approve", json={"approved_by": "Control Room Officer"}, timeout=5)
            st.success(r.json().get("status", "approved"))
            st.rerun()
        except Exception as exc:
            st.error(f"Approval failed: {exc}")

st.markdown("### Green-Time Budget Plan")
st.dataframe(pd.DataFrame(plan["signal_plan"]), hide_index=True, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("### Congestion Ripple Ranking")
    st.dataframe(pd.DataFrame(plan["ripple_ranking"]), hide_index=True, use_container_width=True)
with c2:
    st.markdown("### Static vs Greedy vs SignalSutra")
    st.dataframe(pd.DataFrame(plan["baseline_comparison"]), hide_index=True, use_container_width=True)

st.markdown("### Live Optimizer Log")
for line in plan.get("logs", []):
    st.markdown(f"<div class='logline'>{line}</div>", unsafe_allow_html=True)

st.markdown("### Recent Hardware/API Events")
st.json(read_events(15))
