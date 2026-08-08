import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from utils import api_get, api_post, render_page_header

st.set_page_config(page_title="Risk Prediction — MediFusion AI", page_icon="📉", layout="wide")
render_page_header(
    "📉 Deterioration Risk Prediction",
    "Logistic Regression / Random Forest deterioration probability + confidence",
)

try:
    metrics = api_get("/ml/metrics")
    patients = api_get("/patients")
except requests.exceptions.RequestException:
    st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")
    st.stop()

with st.expander("📊 Model comparison (trained on synthetic vitals data)", expanded=False):
    st.caption(metrics["note"])
    st.caption(f"Train size: {metrics['train_size']} | Test size: {metrics['test_size']} (held out, never used in training)")
    comp_df = pd.DataFrame(metrics["comparison"]).T.reset_index().rename(columns={"index": "model"})
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    st.success(f"Selected model: **{metrics['selected_model']}** (highest test-set AUC)")

if not patients:
    st.info("No patients registered yet. Register one in Patient Management first.")
    st.stop()

options_map = {f"{p['mrn']} — {p['full_name']}": p["id"] for p in patients}
selected_label = st.selectbox("Select a patient", list(options_map.keys()))
patient_id = options_map[selected_label]

st.markdown("---")
if st.button("Run risk prediction on latest vitals", type="primary"):
    try:
        result = api_post(f"/patients/{patient_id}/risk/predict")
        st.session_state["last_prediction"] = result
    except requests.exceptions.HTTPError as exc:
        st.error(f"Prediction failed: {exc.response.text}")

if "last_prediction" in st.session_state:
    r = st.session_state["last_prediction"]
    if r["patient_id"] == patient_id:
        col1, col2 = st.columns([1, 1])
        with col1:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=r["probability"] * 100,
                title={"text": "Deterioration probability (%)"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "black"},
                    "steps": [
                        {"range": [0, 30], "color": "#4CAF50"},
                        {"range": [30, 60], "color": "#FFC107"},
                        {"range": [60, 100], "color": "#F44336"},
                    ],
                },
            ))
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.metric("Model used", r["model_used"])
            st.metric("Confidence", f"{r['confidence']*100:.1f}%")
            st.markdown("**Input features (latest vitals + age):**")
            st.json(r["features"])

st.markdown("---")
st.subheader("Prediction history")
preds = api_get(f"/patients/{patient_id}/risk")
if not preds:
    st.info("No predictions run yet for this patient.")
else:
    df = pd.DataFrame(preds)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values("created_at")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["probability"] * 100, mode="lines+markers", name="Risk probability (%)"))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        df[["created_at", "probability", "confidence", "model_used"]],
        use_container_width=True, hide_index=True,
    )
