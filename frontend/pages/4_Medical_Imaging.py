import pandas as pd
import requests
import streamlit as st
from utils import api_get, api_post, render_page_header

st.set_page_config(page_title="Medical Imaging — MediFusion AI", page_icon="🩻", layout="wide")
render_page_header(
    "🩻 Medical Imaging",
    "X-ray / CT / MRI upload → demo vision model abnormality flags + confidence scores",
)
st.caption(
    "Demo classifier scope: pretrained chest X-ray pneumonia-detection model. Results are "
    "indicative only for chest X-ray-style images — a finding support tool, not a radiologist "
    "replacement or diagnosis."
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
st.subheader("Upload a scan")
modality = st.radio("Modality", ["X-ray", "CT", "MRI"], horizontal=True)
image_file = st.file_uploader(
    "Image file", type=["png", "jpg", "jpeg", "bmp", "tiff", "webp"], key=f"img_upload_{patient_id}"
)

if image_file is not None:
    st.image(image_file, width=300)
    if st.button("Run AI-assisted analysis", type="primary"):
        with st.spinner("Analyzing image... first run downloads the model."):
            try:
                result = api_post(
                    f"/patients/{patient_id}/images",
                    data={"modality": modality},
                    files={"file": (image_file.name, image_file.getvalue(), image_file.type)},
                    timeout=300,
                )
                st.success("Analysis complete.")
                st.metric("Top finding", result["top_label"], f"{result['top_confidence']*100:.1f}% confidence")
                st.markdown("**All predictions:**")
                df = pd.DataFrame(result["predictions"])
                df["confidence"] = (df["confidence"] * 100).round(1)
                st.bar_chart(df.set_index("label")["confidence"])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.rerun()
            except requests.exceptions.HTTPError as exc:
                if exc.response.status_code == 503:
                    st.warning(
                        "🩻 Image analysis isn't available on this deployment — the vision "
                        "model needs more memory than this hosting tier provides. Other "
                        "modules (Speech, OCR, Risk Prediction) are unaffected."
                    )
                else:
                    st.error(f"Analysis failed: {exc.response.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Request failed: {exc}")

st.markdown("---")
st.subheader("Imaging history")
images = api_get(f"/patients/{patient_id}/images")
if not images:
    st.info("No images uploaded yet for this patient.")
else:
    for img in images:
        with st.expander(
            f"{img['created_at'][:16].replace('T', ' ')} — {img['modality']} — "
            f"{img['top_label']} ({img['top_confidence']*100:.1f}%)"
        ):
            df = pd.DataFrame(img["predictions"])
            df["confidence"] = (df["confidence"] * 100).round(1)
            st.dataframe(df, use_container_width=True, hide_index=True)
