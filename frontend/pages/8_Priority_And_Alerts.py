import pandas as pd
import requests
import streamlit as st
from utils import api_get, priority_badge, render_page_header

st.set_page_config(page_title="Priority & Alerts — MediFusion AI", page_icon="🚨", layout="wide")
render_page_header(
    "🚨 Priority & Alerts",
    "LOW / MODERATE / HIGH / CRITICAL classification, priority history, clinical alerts",
)

try:
    patients = api_get("/patients")
except requests.exceptions.RequestException:
    st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")
    st.stop()

if not patients:
    st.info("No patients registered yet. Register one in Patient Management first.")
    st.stop()

st.subheader("Priority queue (all patients)")
sorted_patients = sorted(
    patients,
    key=lambda p: {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}.get(p["priority"], 4),
)
rows = [
    {
        "Priority": priority_badge(p["priority"]),
        "MRN": p["mrn"],
        "Name": p["full_name"],
        "Department": p["department"],
        "Status": p["status"],
    }
    for p in sorted_patients
]
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

critical_count = sum(1 for p in patients if p["priority"] == "CRITICAL")
high_count = sum(1 for p in patients if p["priority"] == "HIGH")
if critical_count:
    st.error(f"🔴 {critical_count} patient(s) at CRITICAL priority — immediate review recommended.")
if high_count:
    st.warning(f"🟠 {high_count} patient(s) at HIGH priority.")

st.markdown("---")
options_map = {f"{p['mrn']} — {p['full_name']}": p["id"] for p in patients}
selected_label = st.selectbox("View priority history for", list(options_map.keys()))
patient_id = options_map[selected_label]

history = api_get(f"/patients/{patient_id}/priority-history")
if not history:
    st.info("No priority transitions recorded yet for this patient. Record vitals or run a simulation to trigger prioritization.")
else:
    st.subheader("Priority transition history")
    for h in history:
        st.markdown(
            f"**{h['changed_at'][:19].replace('T', ' ')}** — "
            f"{priority_badge(h['previous_priority'])} → {priority_badge(h['new_priority'])}  \n"
            f"_{h['reason']}_"
        )
        st.markdown("---")
