import pandas as pd
import requests
import streamlit as st
from utils import api_get, priority_badge, render_page_header

st.set_page_config(page_title="Fusion Profile — MediFusion AI", page_icon="🧬", layout="wide")
render_page_header(
    "🧬 Multimodal Patient Profile",
    "Unified view combining speech, OCR, imaging, history and vitals",
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

profile = api_get(f"/patients/{patient_id}/profile")
p = profile["patient"]

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("MRN", p["mrn"])
c2.metric("Priority", priority_badge(p["priority"]))
c3.metric("Status", p["status"])
c4.metric("Department", p["department"])

st.markdown(f"**{p['full_name']}** — {p['age']} / {p['gender']} — {p['chief_complaint'] or 'No chief complaint recorded'}")

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🫀 Latest vitals")
    lv = profile["latest_vital"]
    if lv:
        st.metric("Heart rate", f"{lv['heart_rate']:.0f} bpm")
        st.metric("BP", f"{lv['systolic_bp']:.0f}/{lv['diastolic_bp']:.0f}")
        st.metric("SpO2", f"{lv['spo2']:.0f}%")
        st.metric("Resp. rate", f"{lv['respiratory_rate']:.0f}")
        st.metric("Temp", f"{lv['temperature']:.1f}°C")
        st.caption(f"{profile['vitals_count']} readings total")
    else:
        st.info("No vitals recorded.")

with col2:
    st.subheader("🗣️ Reported symptoms")
    if profile["combined_symptoms"]:
        st.markdown(" ".join(f"`{s}`" for s in profile["combined_symptoms"]))
    else:
        st.info("No symptoms extracted from speech notes yet.")
    st.caption(f"From {profile['speech_notes_count']} speech note(s)")

    st.subheader("🩻 Latest imaging")
    li = profile["latest_image"]
    if li:
        st.write(f"**{li['modality']}** — {li['top_label']} ({li['top_confidence']*100:.1f}%)")
    else:
        st.info("No images uploaded.")
    st.caption(f"{profile['images_count']} image(s) total")

with col3:
    st.subheader("💊 Active medicines")
    if profile["active_medicines"]:
        st.dataframe(pd.DataFrame(profile["active_medicines"]), use_container_width=True, hide_index=True)
    else:
        st.info("No medicines extracted yet.")

    st.subheader("🧪 Abnormal lab values")
    if profile["abnormal_lab_values"]:
        st.dataframe(pd.DataFrame(profile["abnormal_lab_values"]), use_container_width=True, hide_index=True)
    else:
        st.info("No abnormal lab values on record.")
    st.caption(f"From {profile['ocr_documents_count']} document(s)")

st.markdown("---")
st.caption(
    "This unified view aggregates data already captured across the Speech, OCR, Imaging and "
    "Monitoring modules for a single-screen clinician review. It does not add new AI inference."
)
