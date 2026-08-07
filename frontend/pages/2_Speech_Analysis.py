import streamlit as st
from utils import render_page_header

st.set_page_config(page_title="Speech Analysis — MediFusion AI", page_icon="🎙️", layout="wide")
render_page_header(
    "🎙️ Speech Analysis",
    "Audio upload → multilingual Whisper transcription → symptom extraction",
)

st.info("This module will be built in Phase 3.")
