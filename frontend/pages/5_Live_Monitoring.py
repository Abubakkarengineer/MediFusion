import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from utils import api_get, api_post, render_page_header

st.set_page_config(page_title="Live Monitoring — MediFusion AI", page_icon="📈", layout="wide")
render_page_header(
    "📈 Live Monitoring & Simulation",
    "HR, BP, SpO2, RR, Temperature — manual entry and simulated scenarios",
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
col1, col2 = st.columns(2)

with col1:
    st.subheader("Manual vital entry")
    with st.form(f"manual_vitals_{patient_id}", clear_on_submit=True):
        v1, v2, v3 = st.columns(3)
        heart_rate = v1.number_input("Heart rate (bpm)", 0, 300, 80)
        systolic = v2.number_input("Systolic BP", 0, 300, 120)
        diastolic = v3.number_input("Diastolic BP", 0, 250, 80)
        v4, v5, v6 = st.columns(3)
        spo2 = v4.number_input("SpO2 (%)", 0, 100, 98)
        rr = v5.number_input("Resp. rate", 0, 100, 16)
        temperature = v6.number_input("Temp (°C)", 25.0, 45.0, 37.0, step=0.1)
        if st.form_submit_button("Record vital", type="primary"):
            try:
                api_post(
                    f"/patients/{patient_id}/vitals",
                    json={
                        "heart_rate": heart_rate, "systolic_bp": systolic, "diastolic_bp": diastolic,
                        "spo2": spo2, "respiratory_rate": rr, "temperature": temperature,
                    },
                )
                st.success("Vital recorded.")
                st.rerun()
            except requests.exceptions.HTTPError as exc:
                st.error(f"Could not record vital: {exc.response.text}")

with col2:
    st.subheader("Simulate a scenario")
    st.caption(
        "Generates 10 synthetic readings over a simulated timeline, following the chosen "
        "physiological pattern, for workflow demonstration purposes."
    )
    scenario = st.selectbox(
        "Scenario",
        ["Stable", "Gradual Deterioration", "Recovery", "Cardiac Pattern", "Respiratory Pattern"],
    )
    if st.button("▶ Run simulation", type="primary"):
        try:
            api_post(f"/patients/{patient_id}/vitals/simulate", params={"scenario": scenario})
            st.success(f"Simulated '{scenario}' scenario — 10 readings added.")
            st.rerun()
        except requests.exceptions.HTTPError as exc:
            st.error(f"Simulation failed: {exc.response.text}")

st.markdown("---")
st.subheader("Vitals trend")
try:
    vitals = api_get(f"/patients/{patient_id}/vitals")
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load vitals: {exc}")
    st.stop()

if not vitals:
    st.info("No vitals recorded yet for this patient.")
else:
    df = pd.DataFrame(vitals)
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    df = df.sort_values("recorded_at")

    latest = df.iloc[-1]
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Heart rate", f"{latest['heart_rate']:.0f} bpm")
    m2.metric("BP", f"{latest['systolic_bp']:.0f}/{latest['diastolic_bp']:.0f}")
    m3.metric("SpO2", f"{latest['spo2']:.0f}%")
    m4.metric("Resp. rate", f"{latest['respiratory_rate']:.0f}")
    m5.metric("Temp", f"{latest['temperature']:.1f}°C")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["heart_rate"], name="Heart rate (bpm)", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["spo2"], name="SpO2 (%)", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=df["recorded_at"], y=df["respiratory_rate"], name="Resp. rate", mode="lines+markers"))
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["recorded_at"], y=df["systolic_bp"], name="Systolic BP", mode="lines+markers"))
    fig2.add_trace(go.Scatter(x=df["recorded_at"], y=df["diastolic_bp"], name="Diastolic BP", mode="lines+markers"))
    fig2.add_trace(go.Scatter(x=df["recorded_at"], y=df["temperature"] * 10, name="Temp x10 (°C)", mode="lines+markers"))
    fig2.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Raw readings"):
        st.dataframe(
            df[["recorded_at", "heart_rate", "systolic_bp", "diastolic_bp", "spo2", "respiratory_rate", "temperature", "source"]],
            use_container_width=True, hide_index=True,
        )
