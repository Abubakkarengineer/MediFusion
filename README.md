# MediFusion — Multimodal Clinical Intelligence Platform

## Overview

MediFusion is an AI-powered clinical intelligence platform that assists
healthcare professionals by combining multiple sources of patient
information into a single dashboard. Instead of switching between different
hospital systems, doctors can view medical history, prescriptions,
laboratory reports, medical images, vital signs and clinical notes in one
place. The platform analyzes this information to estimate patient urgency,
assign a priority level, and provide explainable AI insights that support
faster clinical decisions.

## Problem Statement

Hospitals manage large numbers of patients every day. Patient information
is scattered across multiple systems, making it difficult to quickly
understand a patient's condition. This delay can affect emergency care and
increase the workload of doctors and nurses.

## Solution

MediFusion integrates multimodal clinical data into one intelligent
platform. It performs speech-to-text, OCR, medical image analysis, risk
prediction, patient prioritization, explainable AI and clinical routing to
assist healthcare professionals.

## Key Features

- Unified patient profile
- Speech-to-text symptom capture
- OCR for prescriptions and lab reports
- Medical image analysis
- Risk prediction using Machine Learning
- Dynamic patient prioritization
- Explainable AI
- Clinical concern routing
- Interactive dashboard
- Real-time patient simulation

## System Workflow

```
Patient Registration
        |
Medical History + Reports + Images + Vitals + Speech
        |
Multimodal Data Fusion
        |
Risk Prediction
        |
Priority Assignment
        |
Explainable AI
        |
Clinical Concern Routing
        |
Doctor Dashboard
        |
Final Clinical Decision
```

The platform assists healthcare professionals with triage and monitoring;
it never diagnoses disease or prescribes treatment. Final clinical
decisions always rest with the doctor.

## Technology Stack

Python, FastAPI, Streamlit, SQLite, SQLAlchemy, Scikit-learn, faster-whisper,
Tesseract OCR, Plotly, Docker, Git & GitHub. Medical image classification
uses Hugging Face Transformers as an **optional** dependency -- present for
local/full deployments, gracefully disabled on memory-constrained hosting
(see Deployment below).

## Architecture

```
backend/    FastAPI service (REST API, DB, ML inference)
frontend/   Streamlit multi-page dashboard (UI)
data/       Synthetic demo data, SQLite DB, uploaded files
```

## Running locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (separate terminal):

```bash
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Backend runs at http://127.0.0.1:8000 (docs at `/docs`).
Frontend runs at http://127.0.0.1:8501.

## Deployment (Render)

Both `backend/` and `frontend/` include a `Dockerfile` -- deploy each as a
separate Render Web Service with **Environment: Docker**, Root Directory
set to the matching folder, and Dockerfile/Build Context Directory also set
to that folder. The frontend needs one env var:

- `MEDIFUSION_API_URL` = `<backend-service-url>/api`

**Memory-constrained tiers (Free/Starter, 512MB):** the default backend
dependencies already avoid PyTorch (Tesseract for OCR, faster-whisper for
speech, a lightweight coefficient-based method for explainability) to fit.
Medical image classification needs the optional `transformers` package and
is disabled with a clear message when it isn't installed, rather than
crashing.

**Do not set `MEDIFUSION_DATA_DIR`, `EASYOCR_MODEL_DIR`, or `HF_HOME`
unless you've attached a matching Render Persistent Disk.** These exist to
redirect the SQLite DB and model caches onto a mounted disk so they survive
redeploys -- pointing them at a path (e.g. `/data`) that isn't actually
mounted causes `PermissionError: [Errno 13] Permission denied: '/data'` at
startup, since the container can't create that directory. Persistent Disks
generally require a paid plan; on Free tier, leave these env vars unset and
accept that the DB and model downloads reset on every restart/redeploy.

## Modules & Build Status

1. ✅ Project Foundation — FastAPI + Streamlit + SQLite/SQLAlchemy scaffold, logging, health checks
2. ✅ Patient Management — registration, queue, details, vitals, demo staff auto-assignment
3. ✅ Speech AI (Whisper via faster-whisper) — multilingual transcription + symptom extraction
4. ✅ OCR (Tesseract) — prescription/lab report extraction with reference-range flags
5. ✅ Medical Image Analysis — chest X-ray demo classifier with confidence scores (optional dependency, see Deployment)
6. ✅ Vital Monitoring & Simulation — manual entry + 5 scenario simulator with live charts
7. ✅ Multimodal Data Fusion — unified patient profile across all sources
8. ✅ ML Risk Prediction — Logistic Regression vs Random Forest, best model selected on held-out AUC
9. ✅ Dynamic Patient Prioritization — LOW/MODERATE/HIGH/CRITICAL with full transition history
10. ✅ Explainable AI (linear coefficient / feature-importance attribution) & Clinical Concern Routing — per-prediction feature contribution + department/specialist routing + alerts

## Future Scope

- Hospital Information System integration
- Wearable device connectivity
- Cloud deployment
- Mobile application
- Knowledge graph integration
- Federated learning

## Contributors

Abubakkar Siddiq J, Akil, Hari, Divakar

## License

Educational and Hackathon Demonstration Project.
