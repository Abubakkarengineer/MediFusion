import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("MEDIFUSION_API_URL", "http://127.0.0.1:8000/api")


def api_get(path: str, **kwargs):
    resp = requests.get(f"{API_BASE_URL}{path}", timeout=10, **kwargs)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, **kwargs):
    resp = requests.post(f"{API_BASE_URL}{path}", timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


def api_put(path: str, **kwargs):
    resp = requests.put(f"{API_BASE_URL}{path}", timeout=30, **kwargs)
    resp.raise_for_status()
    return resp.json()


PRIORITY_BADGES = {
    "LOW": "🟢 LOW",
    "MODERATE": "🟡 MODERATE",
    "HIGH": "🟠 HIGH",
    "CRITICAL": "🔴 CRITICAL",
}


def priority_badge(priority: str) -> str:
    return PRIORITY_BADGES.get(priority, priority)


@st.cache_data(ttl=60)
def get_disclaimer_text() -> str:
    try:
        return api_get("/disclaimer")["disclaimer"]
    except Exception:
        return (
            "AI-Assisted Clinical Decision Support — outputs are generated "
            "from demonstration/synthetic data and assist, but never "
            "replace, the judgment of a qualified healthcare professional."
        )


def render_disclaimer_banner() -> None:
    st.info(f"**Clinical AI Assist:** {get_disclaimer_text()}", icon="🩺")


def render_page_header(title: str, subtitle: str = "") -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    render_disclaimer_banner()
