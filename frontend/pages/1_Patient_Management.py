import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from utils import api_get, api_post, api_put, priority_badge, render_page_header

NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ɏ][A-Za-zÀ-ɏ .'-]{1,119}$")
MOBILE_PATTERN = re.compile(r"^\d{10}$")


def _extract_error_detail(exc: requests.exceptions.HTTPError) -> str:
    try:
        body = exc.response.json()
        detail = body.get("detail")
        if isinstance(detail, list):  # pydantic validation error list
            return "; ".join(d.get("msg", str(d)) for d in detail)
        if detail:
            return str(detail)
    except Exception:
        pass
    return exc.response.text

st.set_page_config(page_title="Patient Management — MediFusion AI", page_icon="📋", layout="wide")
render_page_header(
    "📋 Patient Management",
    "Registration, patient queue, patient details, vitals, demo staff assignment",
)


@st.cache_data(ttl=30)
def load_options():
    return api_get("/meta/options")


def load_patients(status: str | None = None):
    params = {"status": status} if status else {}
    return api_get("/patients", params=params)


def staff_label(staff: dict | None) -> str:
    if not staff:
        return "Unassigned"
    return f"{staff['name']} ({staff['department']})"


try:
    options = load_options()
except requests.exceptions.RequestException:
    st.error("Cannot reach the backend API. Start it with: uvicorn app.main:app --reload")
    st.stop()

tab_register, tab_queue, tab_details = st.tabs(
    ["🆕 Register Patient", "🗂️ Patient Queue", "🔍 Patient Details & Vitals"]
)

with tab_register:
    st.subheader("Register a new patient")
    st.caption(
        "Only genuine details are accepted: a real name (letters only) and a "
        "valid 10-digit mobile number are required."
    )
    with st.form("register_patient_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full name*", placeholder="e.g. Rahul Sharma")
            age = st.number_input("Age*", min_value=0, max_value=130, value=30)
            gender = st.selectbox("Gender*", options["genders"])
        with col2:
            contact_number = st.text_input("Mobile number* (10 digits)", placeholder="9876543210", max_chars=10)
            department = st.selectbox("Department*", options["departments"])
        chief_complaint = st.text_area("Chief complaint / reason for visit")

        submitted = st.form_submit_button("Register patient", type="primary")
        if submitted:
            errors = []
            cleaned_name = full_name.strip()
            cleaned_mobile = contact_number.strip()

            if not NAME_PATTERN.match(cleaned_name):
                errors.append("Enter a real name using letters only (spaces, hyphens, apostrophes allowed).")
            if not MOBILE_PATTERN.match(cleaned_mobile):
                errors.append("Enter a valid 10-digit mobile number (digits only).")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                try:
                    patient = api_post(
                        "/patients",
                        json={
                            "full_name": cleaned_name,
                            "age": int(age),
                            "gender": gender,
                            "contact_number": cleaned_mobile,
                            "chief_complaint": chief_complaint or None,
                            "department": department,
                        },
                    )
                    st.success(
                        f"Registered **{patient['full_name']}** as **{patient['mrn']}**  \n"
                        f"Assigned doctor: {staff_label(patient['assigned_doctor'])}  \n"
                        f"Assigned nurse: {staff_label(patient['assigned_nurse'])}"
                    )
                except requests.exceptions.HTTPError as exc:
                    st.error(f"Registration failed: {_extract_error_detail(exc)}")

with tab_queue:
    st.subheader("Live patient queue")
    status_filter = st.selectbox(
        "Filter by status", ["All"] + options["statuses"], key="queue_status_filter"
    )
    patients = load_patients(None if status_filter == "All" else status_filter)

    if not patients:
        st.info("No patients registered yet. Use the Register Patient tab to add one.")
    else:
        rows = [
            {
                "MRN": p["mrn"],
                "Name": p["full_name"],
                "Age": p["age"],
                "Gender": p["gender"],
                "Department": p["department"],
                "Status": p["status"],
                "Priority": priority_badge(p["priority"]),
                "Doctor": staff_label(p["assigned_doctor"]),
                "Nurse": staff_label(p["assigned_nurse"]),
                "Registered": p["created_at"][:16].replace("T", " "),
            }
            for p in patients
        ]
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total patients", len(patients))
        c2.metric("Waiting", sum(1 for p in patients if p["status"] == "Waiting"))
        c3.metric("In Consultation", sum(1 for p in patients if p["status"] == "In Consultation"))
        c4.metric("Admitted", sum(1 for p in patients if p["status"] == "Admitted"))

with tab_details:
    st.subheader("Patient details & vitals")
    patients = load_patients()
    if not patients:
        st.info("No patients registered yet.")
    else:
        options_map = {f"{p['mrn']} — {p['full_name']}": p["id"] for p in patients}
        selected_label = st.selectbox("Select a patient", list(options_map.keys()))
        patient_id = options_map[selected_label]
        try:
            patient = api_get(f"/patients/{patient_id}")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not load this patient: {exc}")
            st.stop()

        col1, col2, col3 = st.columns(3)
        col1.metric("MRN", patient["mrn"])
        col2.metric("Priority", priority_badge(patient["priority"]))
        col3.metric("Status", patient["status"])

        with st.expander("Demographics & assignment", expanded=True):
            st.write(f"**Name:** {patient['full_name']}")
            st.write(f"**Age / Gender:** {patient['age']} / {patient['gender']}")
            st.write(f"**Contact:** {patient['contact_number'] or '—'}")
            st.write(f"**Chief complaint:** {patient['chief_complaint'] or '—'}")
            st.write(f"**Department:** {patient['department']}")
            st.write(f"**Assigned doctor:** {staff_label(patient['assigned_doctor'])}")
            st.write(f"**Assigned nurse:** {staff_label(patient['assigned_nurse'])}")

            with st.form(f"edit_patient_{patient_id}"):
                st.markdown("**Edit patient**")
                e1, e2 = st.columns(2)
                with e1:
                    new_department = st.selectbox(
                        "Department",
                        options["departments"],
                        index=options["departments"].index(patient["department"]),
                    )
                with e2:
                    new_status = st.selectbox(
                        "Status",
                        options["statuses"],
                        index=options["statuses"].index(patient["status"]),
                    )
                if st.form_submit_button("Save changes"):
                    api_put(
                        f"/patients/{patient_id}",
                        json={"department": new_department, "status": new_status},
                    )
                    st.success("Patient updated.")
                    st.rerun()

        st.markdown("---")
        st.markdown("**Record new vitals**")
        with st.form(f"vitals_form_{patient_id}", clear_on_submit=True):
            v1, v2, v3, v4, v5 = st.columns(5)
            heart_rate = v1.number_input("Heart rate (bpm)", min_value=0, max_value=300, value=80)
            systolic = v2.number_input("Systolic BP", min_value=0, max_value=300, value=120)
            diastolic = v3.number_input("Diastolic BP", min_value=0, max_value=250, value=80)
            spo2 = v4.number_input("SpO2 (%)", min_value=0, max_value=100, value=98)
            rr = v5.number_input("Resp. rate", min_value=0, max_value=100, value=16)
            temperature = st.number_input(
                "Temperature (°C)", min_value=25.0, max_value=45.0, value=37.0, step=0.1
            )
            if st.form_submit_button("Save vitals", type="primary"):
                api_post(
                    f"/patients/{patient_id}/vitals",
                    json={
                        "heart_rate": heart_rate,
                        "systolic_bp": systolic,
                        "diastolic_bp": diastolic,
                        "spo2": spo2,
                        "respiratory_rate": rr,
                        "temperature": temperature,
                        "source": "manual",
                    },
                )
                st.success("Vitals recorded.")
                st.rerun()

        try:
            vitals = api_get(f"/patients/{patient_id}/vitals")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not load vitals history: {exc}")
            st.stop()
        if vitals:
            vdf = pd.DataFrame(vitals)
            vdf["recorded_at"] = pd.to_datetime(vdf["recorded_at"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=vdf["recorded_at"], y=vdf["heart_rate"], name="Heart rate"))
            fig.add_trace(go.Scatter(x=vdf["recorded_at"], y=vdf["spo2"], name="SpO2"))
            fig.add_trace(
                go.Scatter(x=vdf["recorded_at"], y=vdf["respiratory_rate"], name="Resp. rate")
            )
            fig.add_trace(
                go.Scatter(x=vdf["recorded_at"], y=vdf["systolic_bp"], name="Systolic BP")
            )
            fig.add_trace(
                go.Scatter(x=vdf["recorded_at"], y=vdf["diastolic_bp"], name="Diastolic BP")
            )
            fig.update_layout(
                title="Vitals trend",
                xaxis_title="Time",
                yaxis_title="Value",
                legend_title="Vital sign",
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No vitals recorded yet for this patient.")
