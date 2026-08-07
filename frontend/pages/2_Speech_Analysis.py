import requests
import streamlit as st
from utils import api_get, api_post, render_page_header

st.set_page_config(page_title="Speech Analysis — MediFusion AI", page_icon="🎙️", layout="wide")
render_page_header(
    "🎙️ Speech Analysis",
    "Audio upload → multilingual Whisper transcription → symptom extraction",
)

try:
    patients = api_get("/patients")
except requests.exceptions.RequestException:
    st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")
    st.stop()

if not patients:
    st.info("No patients registered yet. Register one in Patient Management first.")
    st.stop()

options_map = {f"{p['mrn']} — {p['full_name']}": p["id"] for p in patients}
selected_label = st.selectbox("Select a patient", list(options_map.keys()))
patient_id = options_map[selected_label]

st.markdown("---")
st.subheader("Upload patient voice note")
st.caption(
    "Supported formats: WAV, MP3, M4A, OGG, FLAC, WEBM. The model auto-detects the "
    "spoken language. First transcription after a backend restart may take a minute "
    "while the Whisper model loads."
)

audio_file = st.file_uploader(
    "Audio file", type=["wav", "mp3", "m4a", "ogg", "flac", "webm"], key=f"upload_{patient_id}"
)

if audio_file is not None:
    st.audio(audio_file)
    if st.button("Transcribe & extract symptoms", type="primary"):
        with st.spinner("Transcribing with Whisper... this can take a minute on first run."):
            try:
                result = api_post(
                    f"/patients/{patient_id}/speech",
                    files={"audio": (audio_file.name, audio_file.getvalue(), audio_file.type)},
                    timeout=300,
                )
                st.success("Transcription complete.")
                st.markdown(f"**Detected language:** `{result['detected_language']}`")
                st.markdown("**Transcript:**")
                st.write(result["transcript"])
                if result["symptoms"]:
                    st.markdown("**Extracted symptom mentions:**")
                    st.markdown(" ".join(f"`{s}`" for s in result["symptoms"]))
                else:
                    st.info("No symptom keywords detected in this transcript.")
                st.rerun()
            except requests.exceptions.HTTPError as exc:
                st.error(f"Transcription failed: {exc.response.text}")
            except requests.exceptions.RequestException as exc:
                st.error(f"Request failed: {exc}")

st.markdown("---")
st.subheader("Speech note history")
notes = api_get(f"/patients/{patient_id}/speech")
if not notes:
    st.info("No speech notes recorded yet for this patient.")
else:
    for note in notes:
        with st.expander(
            f"{note['created_at'][:16].replace('T', ' ')} — {note['audio_filename']} "
            f"({note['detected_language'] or 'unknown'})"
        ):
            st.write(note["transcript"])
            if note["symptoms"]:
                st.markdown(" ".join(f"`{s}`" for s in note["symptoms"]))
