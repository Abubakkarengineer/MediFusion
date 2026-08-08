import pandas as pd
import requests
import streamlit as st
from utils import api_get, api_post, render_page_header

st.set_page_config(page_title="OCR Results — MediFusion AI", page_icon="🧾", layout="wide")
render_page_header(
    "🧾 OCR Results",
    "Prescription / lab report upload → OCR extraction of medicines, lab values, patient info",
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
st.subheader("Upload a document")
st.caption(
    "Supported formats: PNG, JPG, BMP, TIFF, WEBP, PDF. Text extraction runs entirely "
    "on-device with Tesseract OCR; values are matched against standard lab reference "
    "ranges for a Low/Normal/High flag only — this does not diagnose any condition."
)

document_type = st.radio("Document type", ["Prescription", "Lab Report"], horizontal=True)
doc_file = st.file_uploader(
    "Document file",
    type=["png", "jpg", "jpeg", "bmp", "tiff", "webp", "pdf"],
    key=f"ocr_upload_{patient_id}",
)

if doc_file is not None:
    if doc_file.type and doc_file.type.startswith("image/"):
        st.image(doc_file, width=300)
    if st.button("Run OCR extraction", type="primary"):
        with st.spinner("Running OCR..."):
            try:
                result = api_post(
                    f"/patients/{patient_id}/ocr",
                    data={"document_type": document_type},
                    files={"file": (doc_file.name, doc_file.getvalue(), doc_file.type)},
                    timeout=300,
                )
                st.success("Extraction complete.")

                if result["patient_info"]:
                    st.markdown("**Detected patient info:**")
                    st.json(result["patient_info"])

                if document_type == "Prescription":
                    st.markdown("**Extracted medicines:**")
                    if result["medicines"]:
                        st.dataframe(pd.DataFrame(result["medicines"]), use_container_width=True, hide_index=True)
                    else:
                        st.info("No known medicine names matched in this document.")
                else:
                    st.markdown("**Extracted lab values:**")
                    if result["lab_values"]:
                        df = pd.DataFrame(result["lab_values"])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        abnormal = [v for v in result["lab_values"] if v["flag"] != "Normal"]
                        if abnormal:
                            st.warning(
                                f"{len(abnormal)} value(s) outside standard reference range — "
                                "flagged for clinician review, not a diagnosis."
                            )
                    else:
                        st.info("No known lab test names matched in this document.")

                with st.expander("Raw OCR text"):
                    st.text(result["raw_text"] or "(no text detected)")
                st.rerun()
            except requests.exceptions.HTTPError as exc:
                st.error(f"OCR extraction failed: {exc.response.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Request failed: {exc}")

st.markdown("---")
st.subheader("Document history")
try:
    docs = api_get(f"/patients/{patient_id}/ocr")
except requests.exceptions.RequestException as exc:
    st.error(f"Could not load document history: {exc}")
    st.stop()
if not docs:
    st.info("No documents uploaded yet for this patient.")
else:
    for doc in docs:
        with st.expander(
            f"{doc['created_at'][:16].replace('T', ' ')} — {doc['document_type']} — {doc['filename']}"
        ):
            if doc["patient_info"]:
                st.markdown("**Patient info:**")
                st.json(doc["patient_info"])
            if doc["medicines"]:
                st.markdown("**Medicines:**")
                st.dataframe(pd.DataFrame(doc["medicines"]), use_container_width=True, hide_index=True)
            if doc["lab_values"]:
                st.markdown("**Lab values:**")
                st.dataframe(pd.DataFrame(doc["lab_values"]), use_container_width=True, hide_index=True)
            st.markdown("**Raw text:**")
            st.text(doc["raw_text"] or "(no text detected)")
