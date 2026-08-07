import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Medical Imaging — MediFusion AI", page_icon="🩻", layout="wide")
render_page_header(
    "🩻 Medical Imaging",
    "X-ray / CT / MRI upload → demo vision model abnormality flags + confidence scores",
)
st.caption("AI-assisted image analysis — findings support, but do not replace, radiologist review.")

st.info("This module will be built in Phase 5.")
