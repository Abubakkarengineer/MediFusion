import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Risk Prediction — MediFusion AI", page_icon="📉", layout="wide")
render_page_header(
    "📉 Deterioration Risk Prediction",
    "Logistic Regression / Random Forest deterioration probability + confidence",
)

st.info("This module will be built in Phase 8.")
