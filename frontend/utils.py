import os
import time

import requests
import streamlit as st

API_BASE_URL = os.environ.get("MEDIFUSION_API_URL", "http://127.0.0.1:8000/api")


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def _auth_headers() -> dict:
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _merge_headers(kwargs: dict) -> dict:
    headers = {**_auth_headers(), **kwargs.pop("headers", {})}
    kwargs["headers"] = headers
    return kwargs


def api_get(path: str, **kwargs):
    kwargs = _merge_headers(kwargs)
    resp = requests.get(f"{API_BASE_URL}{path}", timeout=10, **kwargs)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, timeout: int = 30, **kwargs):
    kwargs = _merge_headers(kwargs)
    resp = requests.post(f"{API_BASE_URL}{path}", timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp.json()


def api_put(path: str, timeout: int = 30, **kwargs):
    kwargs = _merge_headers(kwargs)
    resp = requests.put(f"{API_BASE_URL}{path}", timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp.json()


def is_authenticated() -> bool:
    return bool(st.session_state.get("auth_token"))


def login(login_id: str, password: str) -> None:
    resp = requests.post(
        f"{API_BASE_URL}/auth/login", json={"login_id": login_id, "password": password}, timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    st.session_state["auth_token"] = data["token"]
    st.session_state["auth_role"] = data["role"]
    st.session_state["auth_display_name"] = data["display_name"]
    st.session_state["auth_login_id"] = data["login_id"]


def logout() -> None:
    for key in ["auth_token", "auth_role", "auth_display_name", "auth_login_id", "_current_page"]:
        st.session_state.pop(key, None)


def require_login() -> None:
    """Call at the top of every page (done automatically by
    render_page_header). Blocks the rest of the page from rendering, and
    from making any API calls, until an Admin or Doctor has logged in."""
    if not is_authenticated():
        st.warning("🔒 Please log in from the Home page to access MediFusion AI.")
        st.stop()

    with st.sidebar:
        st.markdown("---")
        st.caption(f"Logged in as **{st.session_state['auth_display_name']}**")
        st.caption(f"Role: {st.session_state['auth_role']} · ID: {st.session_state['auth_login_id']}")
        if st.button("Log out", key="_logout_btn"):
            logout()
            st.rerun()


# ---------------------------------------------------------------------------
# Page-transition animation
# ---------------------------------------------------------------------------

_TRANSITION_HTML = """
<style>
@keyframes mf-pulse { 0%,100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.15); opacity: 0.7; } }
@keyframes mf-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.mf-overlay {
  position: fixed; inset: 0; z-index: 999999;
  display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  background: rgba(250, 250, 252, 0.55);
}
@media (prefers-color-scheme: dark) {
  .mf-overlay { background: rgba(10, 12, 20, 0.55); }
}
.mf-card { text-align: center; }
.mf-icon-wrap { position: relative; width: 110px; height: 110px; margin: 0 auto 18px; }
.mf-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 4px solid rgba(59,130,246,0.25); border-top-color: #3b82f6;
  animation: mf-spin 1s linear infinite;
}
.mf-emoji { position: absolute; inset: 0; display:flex; align-items:center; justify-content:center;
  font-size: 42px; animation: mf-pulse 1.1s ease-in-out infinite; }
.mf-text { font-size: 16px; font-weight: 600; color: #3b82f6; letter-spacing: 0.3px; }
</style>
<div class="mf-overlay">
  <div class="mf-card">
    <div class="mf-icon-wrap">
      <div class="mf-ring"></div>
      <div class="mf-emoji">🏥</div>
    </div>
    <div class="mf-text">MediFusion AI — loading...</div>
  </div>
</div>
"""


def show_page_transition(page_name: str) -> None:
    """Shows a brief blurred, hospital-themed loading overlay only when
    navigating to a *different* page (not on every widget rerun)."""
    if st.session_state.get("_current_page") == page_name:
        return
    st.session_state["_current_page"] = page_name

    placeholder = st.empty()
    placeholder.markdown(_TRANSITION_HTML, unsafe_allow_html=True)
    time.sleep(0.6)
    placeholder.empty()


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
    require_login()
    show_page_transition(title)
    st.title(title)
    if subtitle:
        st.caption(subtitle)
    render_disclaimer_banner()
