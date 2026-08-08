import re

import requests
import streamlit as st
from utils import API_BASE_URL, is_authenticated, login, render_page_header, show_page_transition

st.set_page_config(
    page_title="MediFusion AI",
    page_icon="🩺",
    layout="wide",
)

if not is_authenticated():
    show_page_transition("login")

    st.title("🩺 MediFusion AI")
    st.caption("Multimodal Clinical Intelligence Platform — sign in to continue")
    st.info(
        "Access is restricted to hospital **Administrators** and **Doctors**. "
        "Use the demo credentials below for evaluation.",
        icon="🔒",
    )

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        role = st.radio("I am signing in as", ["Administrator", "Doctor"], horizontal=True)
        id_label = "Admin ID" if role == "Administrator" else "Doctor ID"
        id_placeholder = "ADM-001" if role == "Administrator" else "DOC-001"

        with st.form("login_form"):
            login_id = st.text_input(id_label, placeholder=id_placeholder)
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", use_container_width=True)

            if submitted:
                cleaned_id = login_id.strip().upper()
                if not re.match(r"^(ADM|DOC)-\d{3,}$", cleaned_id):
                    st.error(f"Enter a valid {id_label} (e.g. {id_placeholder}).")
                elif not password:
                    st.error("Password is required.")
                elif role == "Administrator" and not cleaned_id.startswith("ADM-"):
                    st.error("That ID isn't an Administrator ID. Switch role or check the ID.")
                elif role == "Doctor" and not cleaned_id.startswith("DOC-"):
                    st.error("That ID isn't a Doctor ID. Switch role or check the ID.")
                else:
                    try:
                        login(cleaned_id, password)
                        st.rerun()
                    except requests.exceptions.HTTPError:
                        st.error("Invalid ID or password.")
                    except requests.exceptions.RequestException:
                        st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")

        with st.expander("Demo credentials"):
            st.code("Administrator -> ADM-001 / Admin@123\nDoctor        -> DOC-001 / Doctor@123", language=None)

else:
    render_page_header("🩺 MediFusion AI", "Multimodal Clinical Intelligence Platform")

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
3. **OCR Results** — prescription / lab report extraction (Tesseract)
4. **Medical Imaging** — X-ray / CT / MRI abnormality flags (demo vision model)
5. **Live Monitoring** — continuous vitals + simulated scenarios
6. **Multimodal Patient Profile** — fused view of all data sources
7. **Risk Prediction** — ML deterioration probability (Logistic Regression / Random Forest)
8. **Priority & Alerts** — LOW/MODERATE/HIGH/CRITICAL classification + alerts
9. **Explainable AI** — per-prediction feature attribution and concern routing
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
