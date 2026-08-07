import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Fusion Profile — MediFusion AI", page_icon="🧬", layout="wide")
render_page_header(
    "🧬 Multimodal Patient Profile",
    "Unified view combining speech, OCR, imaging, history and vitals",
)

st.info("This module will be built in Phase 7.")
