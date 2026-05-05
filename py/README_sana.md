# Sentinel AI — Teammate Guide (What’s Implemented + How to Run)

This document is a **team-facing overview** of the Sentinel AI Document Verification project: what features exist, how the pipeline works (agent-by-agent), what ML/pretrained models are used and why, what UI features were added, and how to run the backend + dashboard on a new machine.

---

## 1) High-Level Overview

Sentinel AI is a **document fraud detection / verification system** with:

- A **multi-agent (agentic) backend pipeline** that runs multiple specialized checks and produces a single result.
- A **forensic engine** that runs classic digital forensics (ELA, DCT, structural checks, etc.) and generates:
  - anomaly list
  - trust score
  - optional heatmap overlay
  - a PDF forensic report
- **Pretrained detectors / validators** (YOLO and Roboflow-based where applicable).
- An optional **Gemini (LLM) reasoning agent** that produces a human-readable explanation (`ai_reasoning`).
- A frontend **dashboard** that supports:
  - file upload preview
  - bounding-box overlays on detected fields
  - heatmap display
  - AI explanation + summary
  - report download

---

## 2) Repository Structure (Key Files)

```
senitel ai/
├── api_server.py                    # Flask API backend (agentic pipeline)
├── agents/
│   ├── orchestrator.py              # Pipeline coordinator + final response builder
│   ├── router_agent.py              # Detects document type (PAN/AADHAAR/CERTIFICATE/UNKNOWN)
│   ├── forensic_agent.py            # Runs forensic_engine + heatmap generation
│   ├── validation_agent.py          # Field validation + pretrained checks + detected_fields bboxes
│   ├── ml_agent.py                  # ML scoring wrapper (graceful fallback)
│   ├── decision_agent.py            # Final trust score + reasoning
│   ├── llm_reasoning_agent.py       # Gemini-powered explanation (ai_reasoning)
│   └── report_agent.py              # Summary + report object in context
├── forensic_engine.py               # Core forensic analysis + PDF generation
├── forensic/
│   └── heatmap_overlay.py           # Heatmap overlay generation (saves PNG in outputs/)
├── models/
│   ├── model.pt                     # YOLO model (field detection)
│   ├── pan_card_model.pt            # YOLO model (PAN field detection)
│   └── pretrained/
│       ├── field_validation.py      # Aadhaar/field detection + OCR extraction + validation
│       ├── pan_validation.py        # PAN field detection + OCR + validation
│       ├── certificate_detector.py  # Roboflow inference + text fallback
│       └── certificate_validation.py# OCR + certificate validation
├── ml/
│   ├── train.py                     # CNN training script (binary classification)
│   ├── preprocess.py                # Dataset preprocessing into ml_data/
│   └── model.h5                     # Trained CNN model
├── dashboard.html                   # Main UI
├── script.js                        # Shared frontend JS utilities
├── style.css                        # UI styles
├── outputs/                         # Generated heatmaps (PNG)
└── forensic_report.pdf              # Generated PDF forensic report (runtime output)
```

---

## 3) Agentic Pipeline (Backend)

The backend runs a sequential multi-agent pipeline.

### Pipeline order (agents/orchestrator.py)
1. **RouterAgent**
   - Goal: determine `document_type` (PAN/AADHAAR/CERTIFICATE/UNKNOWN)
   - Inputs: image
   - Outputs: `document_type`

2. **ForensicAgent**
   - Goal: run forensic checks via `forensic_engine.py`.
   - Outputs:
     - `forensic_score`, `ela_score`
     - `anomalies`, `anomaly_count`
     - `structural_results`, `dct_results`
     - `ocr_text` (if available)
     - `heatmap` (path to generated overlay PNG)

3. **ValidationAgent**
   - Goal: field validation based on doc type.
   - Uses pretrained/heuristic models and OCR.
   - Outputs:
     - `field_score` / `validation_score`
     - `field_results`
     - `pretrained_score`, `pretrained_result`
     - **`detected_fields`: bounding boxes** for UI overlay

4. **MLAgent**
   - Goal: CNN-based fraud prediction from `ml/model.h5` via `ml_engine.py`.
   - Output: `ml_score` (trust score 0–100)
   - Fault tolerance: if model fails to load or inference fails, MLAgent returns a **neutral fallback**.

5. **DecisionAgent**
   - Goal: final trust score + decision label.
   - Output:
     - `trust_score`
     - `status`
     - `reasoning` (rule-based bullet points)

6. **LLMReasoningAgent (Gemini)**
   - Goal: produce human explanation of the decision.
   - Output: `ai_reasoning`
   - If Gemini fails, `ai_reasoning` is set to a safe fallback string.

7. **ReportAgent**
   - Goal: create a `summary` and a structured `report` object.

---

## 4) Models Used

### 4.1 ML (CNN) model — `ml/model.h5`
- **Type:** TensorFlow/Keras CNN
- **Task:** binary classification (genuine vs forged / tampered)
- **Training script:** `ml/train.py`
- **Preprocessing:** `ml/preprocess.py` converts raw dataset folders into `ml_data/` with padding to 256x256.

#### Dataset format (expected by preprocess.py)
The preprocessing script expects a `Dataset/` folder containing:
- `Dataset/Original/Academic`, `Dataset/Original/Id_Kyc`, `Dataset/Original/Employee`
- `Dataset/Forged/F_Aacademic`, `Dataset/Forged/F_Id_KYC`, `Dataset/Forged/F_Employee`

> Reason: preprocessing normalizes size, aspect ratio, and file extensions to keep training stable.

#### Important note (Keras compatibility)
Some environments (newer Keras versions) may fail to load older `.h5` models.
The system is designed to **continue working** even if ML model loading fails.

### 4.2 Pretrained Field Detectors / Validators

#### Aadhaar / general field detection (YOLO)
- `models/model.pt`
- Code: `models/pretrained/field_validation.py`
- Output used:
  - `field_results` (validated extracted fields)
  - `detected_fields` (bboxes) for UI overlay

#### PAN field detection (YOLO)
- `models/pan_card_model.pt`
- Code: `models/pretrained/pan_validation.py`

#### Certificate detection (Roboflow)
- Code: `models/pretrained/certificate_detector.py`
- Uses `inference_sdk` + Roboflow model id: `certificates-zbdhx/1`
- Has text-based fallback (`_text_based_detection`) when API fails.

---

## 5) Key Backend Outputs (API)

### Endpoint: `POST /api/analyze`
Returns JSON including (main ones):
- `trust_score`, `status`, `document_type`
- `forensic_score`, `ml_score`, `validation_score`, `pretrained_score`
- `anomalies`, `anomaly_count`, `ela_score`
- `detected_fields`: list of `{label, bbox:[x,y,w,h], confidence}`
- `heatmap`: path to PNG overlay (e.g. `outputs/image_heatmap.png`)
- `reasoning`: list of rule-based bullets
- `ai_reasoning`: Gemini explanation string (may be fallback)
- `summary`: summarized findings

### Endpoint: `GET /download_report`
Downloads `forensic_report.pdf` (generated during analysis) if present.

---

## 6) Frontend Dashboard Features

File: `dashboard.html`

### Implemented UI flow (investigation order)
1. **Uploaded Document Preview**
2. **Detected fields with bounding boxes overlay** (canvas over the preview)
3. **Trust score bar + status label** (AUTHENTIC / REVIEW / SUSPICIOUS)
4. **Detected anomalies list**
5. **Forgery heatmap** (if backend returns `heatmap`)
6. **Gemini AI explanation** (`ai_reasoning`)
7. **Summary findings** (`summary`)
8. **Download forensic report** button

---

## 7) How to Run (Windows)

### 7.1 One-time setup
```powershell
cd "c:\Users\<YOU>\Desktop\senitel ai"
python -m venv sentinel_env
sentinel_env\Scripts\activate
pip install -r requirements.txt
```

Install Tesseract OCR (Windows):
- https://github.com/UB-Mannheim/tesseract/wiki
- Ensure `tesseract.exe` is installed and available.

### 7.2 Gemini setup (optional)
Create a `.env` file in project root:
```
GEMINI_API_KEY=YOUR_KEY_HERE
```

### 7.3 Start backend
```powershell
cd "c:\Users\<YOU>\Desktop\senitel ai"
sentinel_env\Scripts\activate
python api_server.py
```

Backend runs on:
- `http://localhost:5001`

### 7.4 Start frontend
Open a new terminal:
```powershell
cd "c:\Users\<YOU>\Desktop\senitel ai"
python -m http.server 3000
```

Open:
- `http://localhost:3000/dashboard.html`

---

## 8) Troubleshooting

### Heatmap not visible
- Ensure backend returns a non-empty `heatmap` in `/api/analyze` response.
- Ensure backend is restarted after changes.

### AI reasoning not showing
- Confirm `/api/analyze` response includes `ai_reasoning`.
- If Gemini returns API errors, UI will show fallback message.

### Report download fails
- Run an analysis first (PDF is generated during analysis).
- Ensure `forensic_report.pdf` exists in project root.
- Visit: `http://localhost:5001/download_report`

### ML score is neutral / model load fails
- This can happen due to TensorFlow/Keras version mismatches.
- The pipeline continues with neutral ML contribution.

---

## 9) Notes for Teammates (What NOT to change)
- Do not rename backend response keys like `ai_reasoning`, `summary`, `detected_fields`, `heatmap`.
- The frontend reads these keys safely (if missing -> shows fallback text).

---

## 10) Credits / Ownership
This project combines:
- Classic forensic heuristics
- Pretrained detectors
- A lightweight CNN ML model
- Agentic orchestration
- LLM-based explainability (Gemini)

If you need help running this on your machine, start with:
1) `pip install -r requirements.txt`
2) start `api_server.py`
3) open dashboard via `python -m http.server 3000`
