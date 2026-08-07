import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Priority & Alerts — MediFusion AI", page_icon="🚨", layout="wide")
render_page_header(
    "🚨 Priority & Alerts",
    "LOW / MODERATE / HIGH / CRITICAL classification, priority history, clinical alerts",
)

st.info("This module will be built in Phase 9.")
