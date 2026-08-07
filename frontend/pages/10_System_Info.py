import streamlit as st
from utils import api_get, render_page_header

st.set_page_config(page_title="System Info — MediFusion AI", page_icon="⚙️", layout="wide")
render_page_header("⚙️ System Information", "Backend health, environment, and API status")

try:
    health = api_get("/health")
    st.success("Backend reachable")
    st.json(health)
except Exception as exc:
    st.error(f"Backend unreachable: {exc}")
