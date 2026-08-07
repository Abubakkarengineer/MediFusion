import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="OCR Results — MediFusion AI", page_icon="🧾", layout="wide")
render_page_header(
    "🧾 OCR Results",
    "Prescription / lab report upload → EasyOCR extraction of medicines, lab values, patient info",
)

st.info("This module will be built in Phase 4.")
