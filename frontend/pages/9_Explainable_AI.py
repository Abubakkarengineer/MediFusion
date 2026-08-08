import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from utils import api_get, api_post, priority_badge, render_page_header

st.set_page_config(page_title="Explainable AI — MediFusion AI", page_icon="🔍", layout="wide")
render_page_header(
    "🔍 Explainable AI & Concern Routing",
    "Per-prediction feature attribution, human-readable explanations, department/nurse/specialist routing",
)

try:
    patients = api_get("/patients")
except requests.exceptions.RequestException:
    st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")
    st.stop()

if not patients:
    st.info("No patients registered yet. Register one in Patient Management first.")
    st.stop()

options_map = {f"{p['mrn']} — {p['full_name']}": p["id"] for p in patients}
selected_label = st.selectbox("Select a patient", list(options_map.keys()))
patient_id = options_map[selected_label]

st.markdown("---")
if st.button("Explain latest risk prediction", type="primary"):
    try:
        st.session_state["last_explanation"] = api_post(f"/patients/{patient_id}/explain")
    except requests.exceptions.HTTPError as exc:
        st.error(f"Explanation failed: {exc.response.text}")

if "last_explanation" in st.session_state:
    e = st.session_state["last_explanation"]
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Feature contributions")
        st.caption(f"Method: {e['method']}")
        df = pd.DataFrame(e["feature_importance"])
        colors = ["#F44336" if c > 0 else "#4CAF50" for c in df["contribution"]]
        fig = go.Figure(go.Bar(
            x=df["contribution"], y=df["label"], orientation="h",
            marker_color=colors,
            text=[f"{v}" for v in df["value"]], textposition="outside",
        ))
        fig.update_layout(
            height=320, margin=dict(l=10, r=10, t=30, b=10),
            xaxis_title="Contribution to risk (log-odds)",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info(e["explanation_text"])
        st.caption(e["causation_disclaimer"])

    with col2:
        st.subheader("Clinical concern routing")
        st.metric("Priority", priority_badge(e["priority"]))
        if e["concern"]:
            st.warning(f"Possible pattern: **{e['concern']}**")
            st.write(f"**Department:** {e['department']}")
            st.write(f"**Assigned specialist:** {e['assigned_specialist']}")
            st.write(f"**Assigned nurse:** {e['assigned_nurse']}")
        else:
            st.success("No specific concern pattern flagged.")
        st.caption(
            "Concern routing is a rule-based pattern match on vitals, not a diagnosis. "
            "It never automatically prescribes treatment."
        )

st.markdown("---")
st.subheader("Alerts for this patient")
try:
    alerts = api_get(f"/patients/{patient_id}/alerts")
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load alerts: {exc}")
    st.stop()
if not alerts:
    st.info("No alerts generated yet. Run an explanation on a HIGH/CRITICAL patient to generate one.")
else:
    for a in alerts:
        st.markdown(f"**{a['created_at'][:19].replace('T', ' ')}** — {priority_badge(a['priority'])}  \n{a['message']}")
        st.markdown("---")
