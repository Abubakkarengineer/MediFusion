import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Live Monitoring — MediFusion AI", page_icon="📈", layout="wide")
render_page_header(
    "📈 Live Monitoring & Simulation",
    "HR, BP, SpO2, RR, Temperature — manual entry and simulated scenarios",
)

st.info("This module will be built in Phase 6.")
