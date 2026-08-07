import requests
import streamlit as st
from utils import API_BASE_URL, render_disclaimer_banner

st.set_page_config(
    page_title="MediFusion AI",
    page_icon="🩺",
    layout="wide",
)

st.title("🩺 MediFusion AI")
st.caption("Multimodal Clinical Intelligence Platform")
render_disclaimer_banner()

st.markdown("---")

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("About this platform")
    st.markdown(
        """
MediFusion AI demonstrates an end-to-end workflow for **AI-assisted clinical
decision support**, from raw patient data collection to a unified insights
dashboard for a reviewing clinician.

**Modules** (use the sidebar to navigate):
1. **Patient Management** — registration, queue, details, vitals, staff assignment
2. **Speech Analysis** — multilingual Whisper transcription + symptom extraction
3. **OCR Results** — prescription / lab report extraction (EasyOCR)
4. **Medical Imaging** — X-ray / CT / MRI abnormality flags (demo vision model)
5. **Live Monitoring** — continuous vitals + simulated scenarios
6. **Multimodal Patient Profile** — fused view of all data sources
7. **Risk Prediction** — ML deterioration probability (Logistic Regression / Random Forest)
8. **Priority & Alerts** — LOW/MODERATE/HIGH/CRITICAL classification + alerts
9. **Explainable AI** — SHAP-based feature importance and concern routing
10. **System Information** — backend health and diagnostics

All data in this demo is synthetic. No real patient information should be
entered.
        """
    )

with col2:
    st.subheader("Backend status")
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5).json()
        st.success(f"API online — {health['app_name']} ({health['environment']})")
    except Exception as exc:
        st.error("API offline. Start the backend with:\n\nuvicorn app.main:app --reload")
        st.code(str(exc))
