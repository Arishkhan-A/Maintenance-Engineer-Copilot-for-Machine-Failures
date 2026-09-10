# Tier-1 Advanced Industrial Maintenance Engineer Copilot (v3.0)
### Full-Stack AI Platform: Multi-Class Diagnostics, Health Index, Digital CMMS Work Orders & Financial ROI Analytics

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-yellow.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Production-Tier--1%20Advanced-success.svg)]()

---

## 1. Advanced Capabilities Overview

This repository represents a **Tier-1 Advanced Industrial AI Decision-Support Platform** designed to reduce unplanned production downtime across manufacturing facilities.

Key distinguishing capabilities include:
1. **Multi-Class Root-Cause Fault Classifier (Gradient Boosting)**:
   - Diagnoses the physical failure mechanism:
     - `Bearing Degradation` (High frequency vibration velocity, rolling element race spalling)
     - `Motor Overheating` (Thermal runaway, $\Delta T > 45^\circ\text{C}$, stator insulation breakdown)
     - `Hydraulic Fault` (Pump cavitation, accumulator bladder rupture, pressure drop)
     - `Electrical Power Surge` (VFD inverter phase current spikes, rotor bar unbalance)
     - `Nominal Operational State`
2. **Composite Machine Health Index (0 - 100% MHI)**:
   - A multi-parameter health metric synthesizing failure risk, kinematic vibration severity (ISO 10816 limits), thermodynamic differential ($\Delta T$), unsupervised anomaly deviation, and remaining RUL.
3. **Financial Downtime & ROI Prevention Engine**:
   - Compares catastrophic downtime loss (at $2,500/hour plant loss rate) against proactive maintenance intervention, projecting total financial savings prevented.
4. **Autonomous Digital CMMS Work Order Dispatch**:
   - Generates SAP PM / IBM Maximo-compliant work orders with priority classification (P1/P2/P3), Lockout-Tagout (LOTO) protocols, warehouse parts reservation, and step-by-step procedures.
5. **Interactive Executive Industrial Cockpit**:
   - Dark-mode Streamlit dashboard with plant-wide financial savings metrics, live stream visualizer, multi-class diagnostics, and one-click CMMS work order export (Markdown / JSON).

---

## 2. Production Benchmark Performance

| Layer | Architecture | Metrics on Test Split | Performance |
| :--- | :--- | :--- | :--- |
| **Multi-Class Fault Classifier** | HistGradientBoosting | **Accuracy**<br>**Weighted F1**<br>**Macro F1** | **96.7%**<br>**0.9636**<br>**0.7974** |
| **Failure Classifier (24h)** | Tuned Random Forest (Balanced) | **ROC-AUC**<br>**PR-AUC**<br>**F1-Score** | **0.9987**<br>**0.9872**<br>**0.9300** |
| **RUL Regressor** | Random Forest Regressor | **MAE**<br>**RMSE** | **21.98 Hours**<br>**31.48 Hours** |
| **Anomaly Detector** | Isolation Forest (Calibrated) | **Contamination**<br>**Threshold** | **0.04 (4%)**<br>**-0.0000** |
| **Explainable AI** | SHAP TreeExplainer | **Attribution** | Instant percentage attribution of failure drivers |

---

## 3. Full Project Layout

```
MECMF/
├── predictive_maintenance_v3.csv      # Primary industrial dataset (24,130 records, 20 assets)
├── data/
│   ├── processed/
│   │   ├── cleaned_telemetry.csv      # 24,042 cleaned records with temporal imputation
│   │   └── engineered_features.csv    # 60 engineered physics & time-series features
│   └── data_dictionary.md             # Sensor boundaries and operational tolerances
├── documents/
│   ├── manuals/
│   │   ├── motor_manual.txt           # Electric motor specs & bearing tolerances
│   │   ├── pump_manual.txt            # Hydraulic pump cavitation & seal flush Plan 11
│   │   ├── compressor_manual.txt      # Rotary screw compressor bypass valve & MPV
│   │   └── robotic_arm_manual.txt     # 6-Axis robotic arm cycloidal reducer & backlash
│   ├── troubleshooting/
│   │   ├── vibration_guide.txt        # ISO 10816 vibration diagnosis matrix
│   │   ├── overheating_guide.txt      # Thermal runaway & lubrication starvation
│   │   ├── pressure_guide.txt         # Pressure pulsation & bladder accumulator
│   │   ├── electrical_guide.txt       # Phase current unbalance & VFD inverter surges
│   │   └── hydraulic_guide.txt        # Hydraulic cavitation & proportional valve bypass
│   └── incidents/
│       ├── incident_001.txt           # M17 bearing seizure RCA post-mortem
│       ├── incident_002.txt           # M04 seal rupture RCA post-mortem
│       └── incident_003.txt           # M12 thermal trip RCA post-mortem
├── database/
│   ├── schema.sql                     # SQLite schema with multi-asset & mode support
│   ├── init_db.py                     # Database initializer seeding 20 assets & 2,000 readings
│   ├── maintenance.db                 # Production SQLite relational database
│   └── rag_index.json                 # 46 indexed technical passages
├── models/
│   ├── multiclass_model.joblib        # Serialized multi-class Gradient Boosting model
│   ├── fault_label_encoder.joblib     # Serialized fault class label encoder
│   ├── failure_model.joblib           # Serialized Random Forest classifier
│   ├── rul_model.joblib               # Serialized RUL regressor
│   ├── anomaly_model.joblib           # Calibrated Isolation Forest artifact
│   ├── preprocessor.joblib            # Fitted Scikit-Learn ColumnTransformer
│   └── model_metadata.json            # Benchmark evaluation logs
├── simulator/
│   └── sensor_stream.py               # Enterprise fault-injection telemetry streamer
├── src/
│   ├── agent/
│   │   ├── tools.py                   # 10 enterprise agent tools
│   │   ├── workflow.py                # 11-step ReAct diagnostic investigation loop
│   │   └── work_order.py              # SAP PM / Maximo digital work order generator
│   ├── anomaly/                       # Unsupervised anomaly detector
│   ├── api/                           # FastAPI REST backend with CORS & Pydantic v2
│   ├── data/                          # Robust ETL, timestamp parsers & cleaners
│   ├── explainability/                # SHAP local instance and global explainers
│   ├── features/                      # Physics, thermodynamics & lag feature engineering
│   ├── models/
│   │   ├── health_index.py            # Machine Health Index & Financial ROI engine
│   │   ├── train_multiclass.py        # Multi-class fault classifier trainer
│   │   ├── train_failure.py           # Binary failure classifier trainer
│   │   ├── train_rul.py               # RUL regressor trainer
│   │   └── predict.py                 # Multi-task unified inference engine
│   └── rag/                           # Document chunking, vector indexing & RAG generator
├── streamlit_app/
│   └── app.py                         # Tier-1 industrial cockpit
├── tests/                             # 25 automated tests (100% passing)
├── Dockerfile                         # Production container specification
├── requirements.txt                   # Pinned dependency manifest
└── README.md                          # Platform documentation
```

---

## 4. How to Run

### 1. Launch the Tier-1 Industrial Cockpit
```powershell
.\.venv\Scripts\streamlit run streamlit_app\app.py
```
- Available at: `http://localhost:8501`
- Features:
  - **Plant Executive Cockpit**: Fleet MHI average, high-risk assets, downtime avoided, total ROI saved ($).
  - **Machine Telemetry & $\Delta T$**: Real-time sensor trends with ISO 10816 vibration alarm limits.
  - **Multi-Class Fault & RUL**: Categorical fault diagnosis with calibrated probability bars and health penalty decomposition.
  - **CMMS Digital Work Orders**: View, edit, and export SAP-ready work orders (Markdown / JSON).
  - **Autonomous AI Copilot**: Evidence-grounded conversational agent with 1-click work order dispatch.

### 2. Launch the FastAPI REST Server
```powershell
.\.venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Endpoints:
  - `GET /health-index/{machine_id}`
  - `GET /workorders/{machine_id}`
  - `GET /roi-analytics/{machine_id}`
  - `POST /predict`
  - `POST /copilot/chat`

### 3. Run Real-Time Telemetry Simulator
```powershell
.\.venv\Scripts\python simulator\sensor_stream.py --machine M17 --scenario bearing_failure_progression --steps 20 --interval 1.0
```

### 4. Run Automated Test Suite
```powershell
.\.venv\Scripts\pytest -v tests/
```
*(All 25 tests pass with 100% green)*
