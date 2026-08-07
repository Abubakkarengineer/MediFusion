import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Explainable AI — MediFusion AI", page_icon="🔍", layout="wide")
render_page_header(
    "🔍 Explainable AI & Concern Routing",
    "SHAP feature importance, human-readable explanations, department/nurse/specialist routing",
)
st.caption(
    "Explanations describe model behavior only and are not proof of medical causation."
)

st.info("This module will be built in Phase 10.")
