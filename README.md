# Tier-1 Advanced Industrial Maintenance Engineer Copilot (v3.0)
### Full-Stack AI Platform: Multi-Class Diagnostics, Health Index, Digital CMMS Work Orders, Universal File Converter & Industrial Fluid Telemetry

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.4%2B-yellow.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/Tests-33%2F33%20Passing%20(100%25)-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Production-Tier--1%20Advanced-success.svg)]()

---

## 1. Advanced Capabilities Overview

This repository represents a **Tier-1 Advanced Industrial AI Decision-Support Platform** engineered to eliminate unplanned production downtime across discrete and process manufacturing facilities.

### Key Capabilities:
1. **Multi-Class Root-Cause Fault Classifier (Gradient Boosting)**:
   - Diagnoses exact physical failure mechanisms:
     - `Bearing Degradation` (High frequency vibration velocity, rolling element race spalling)
     - `Motor Overheating` (Thermal runaway, $\Delta T > 45^\circ\text{C}$, stator insulation breakdown)
     - `Hydraulic Fault` (Pump cavitation, accumulator bladder rupture, pressure drop)
     - `Electrical Power Surge` (VFD inverter phase current spikes, rotor bar unbalance)
     - `Nominal Operational State`
2. **Composite Machine Health Index (0 - 100% MHI)**:
   - Synthesizes failure risk probability, kinematic vibration severity (ISO 10816 limits), thermodynamic differential ($\Delta T$), unsupervised anomaly deviation, and remaining RUL.
3. **Financial Downtime & ROI Prevention Engine**:
   - Compares catastrophic downtime loss (at $2,500/hour plant loss rate) against proactive maintenance intervention, projecting total financial loss prevented ($38,400+ per critical asset).
4. **Autonomous Digital CMMS Work Order Dispatch**:
   - Generates SAP PM / IBM Maximo-compliant work orders with priority classification (P1/P2/P3), Lockout-Tagout (LOTO) safety protocols, warehouse parts reservations, and step-by-step procedures.
5. **Universal File Ingestion & CSV Conversion Engine**:
   - **Accepts ANY file format**: Excel (`.xlsx`, `.xls`), JSON, Parquet, Server Logs, CSV/TSV, XML, HTML, SQLite DB, and arbitrary binary payloads.
   - **Zero-Failure Architecture**: Automatic schema extraction and binary hex/ASCII chunk fallbacks guarantee that no file is ever rejected.
   - **Storage & Audit Vault**: Converted CSVs are persisted in `data/converted/` with audit logging in SQLite (`uploaded_files` table).
   - **Direct Fleet Telemetry Ingestion**: Automatically detects sensor columns and allows one-click streaming into the fleet SQLite database.
6. **ASME A13.1 Industrial Piping & Utility Telemetry Integration**:
   - Real-time condition monitoring across 8 standard industrial fluid and gas piping loops:
     - 🟢 **Green**: Water (cooling or potable supply)
     - 🔵 **Blue**: Compressed air and pneumatic gases
     - 🟡 **Yellow**: Flammable or hazardous gases
     - 🔴 **Red**: Fire-fighting and suppression water loops
     - 🟤 **Brown**: Oils, lubricants, and combustible fluids
     - 🟠 **Orange**: Acids, toxic elements, and corrosive chemicals
     - 🟣 **Purple**: Specialized hazardous or chemical waste
     - ⚫ **Black**: Drain and wastewater lines
7. **3 Dedicated Industrial Telemetry Charts**:
   - **Chart 1 (Bar)**: Industrial Piping Loop Operating Capacity vs Header Limit (%)
   - **Chart 2 (Donut)**: Industrial Fluid Piping & Risk Matrix Allocation
   - **Chart 3 (Multi-Line)**: Real-Time Multi-Fluid & Auxiliary Utility Telemetry Correlation timeline
8. **Interactive Executive Cockpit (10 Specialized Operational Views)**:
   - Dark-mode TALOS·AI (**Total Asset & Lifetime Operational Safeguard**) Streamlit dashboard with plant financial metrics, sensor visualizer, multi-class diagnostics, file conversion console, and CMMS exports.

---

## 2. Production Benchmark Performance

| Layer | Architecture | Metrics on Test Split | Performance |
| :--- | :--- | :--- | :--- |
| **Multi-Class Fault Classifier** | HistGradientBoosting | **Accuracy**<br>**Weighted F1**<br>**Macro F1** | **96.7%**<br>**0.9636**<br>**0.7974** |
| **Failure Classifier (24h)** | Tuned Random Forest (Balanced) | **ROC-AUC**<br>**PR-AUC**<br>**F1-Score** | **0.9987**<br>**0.9872**<br>**0.9300** |
| **RUL Regressor** | Random Forest Regressor | **MAE**<br>**RMSE** | **21.98 Hours**<br>**31.48 Hours** |
| **Anomaly Detector** | Isolation Forest (Calibrated) | **Contamination**<br>**Threshold** | **0.04 (4%)**<br>**-0.0000** |
| **Explainable AI** | SHAP TreeExplainer | **Attribution** | Instant percentage attribution of failure drivers |
| **Test Quality Suite** | Pytest | **Total Tests** | **33 / 33 Passing (100% Green)** |

---

## 3. ASME A13.1 Industrial Piping & Fluid Color Matrix

| Color | Industrial Classification | Operational System / Monitored Signals |
| :--- | :--- | :--- |
| 🟢 **Green** | Water (cooling or potable supply) | Motor cooling loops, heat exchanger water flow rate (L/min) |
| 🔵 **Blue** | Compressed air and pneumatic gases | Pneumatic tool changers, main air header pressure (bar) |
| 🟡 **Yellow** | Flammable or hazardous gases | Combustible gas detectors, VOC vapors in bearing housings (ppm) |
| 🔴 **Red** | Fire-fighting and suppression loops | Deluge systems, standby loop static line pressure (bar) |
| 🟤 **Brown** | Oils, lubricants, and combustible fluids | Gearbox oil pressure, hydraulic fluid viscosity & varnish (bar) |
| 🟠 **Orange** | Acids, toxic elements, and corrosives | Chemical washes, coolant biocides, acidic passivation lines |
| 🟣 **Purple** | Specialized hazardous / chemical waste | Spent machining coolant return, chemical recovery lines |
| ⚫ **Black** | Drain and wastewater lines | Slurry runoff drains, wastewater discharge gravity flow |

---

## 4. Full Project Layout

```
MECMF/
├── predictive_maintenance_v3.csv      # Primary industrial dataset (24,130 records, 20 assets)
├── MECMF_Project_Presentation.pdf      # Complete executive presentation deck (ReportLab)
├── PROJECT_PRESENTATION.md            # Slide-by-slide presentation structure & Q&A guide
├── data/
│   ├── converted/                     # Converted CSV storage repository (Any format -> CSV)
│   ├── processed/
│   │   ├── cleaned_telemetry.csv      # 24,042 cleaned records with temporal imputation
│   │   └── engineered_features.csv    # 60 engineered physics & time-series features
│   └── data_dictionary.md             # Sensor boundaries and operational tolerances
├── documents/
│   ├── manuals/                       # OEM manuals for motors, pumps, compressors, robots
│   ├── troubleshooting/               # ISO 10816 guides, thermal runaway & cavitation manuals
│   └── incidents/                     # Historical incident post-mortems (M17, M04, M12)
├── database/
│   ├── schema.sql                     # SQLite schema (machines, sensor_readings, uploaded_files)
│   ├── init_db.py                     # Database initializer seeding 20 assets & 2,000 readings
│   ├── maintenance.db                 # Relational SQLite database
│   └── rag_index.json                 # 46 indexed technical passages
├── models/
│   ├── multiclass_model.joblib        # Serialized multi-class Gradient Boosting model
│   ├── failure_model.joblib           # Serialized Random Forest classifier
│   ├── rul_model.joblib               # Serialized RUL regressor
│   ├── anomaly_model.joblib           # Calibrated Isolation Forest artifact
│   └── model_metadata.json            # Model benchmark evaluation records
├── simulator/
│   └── sensor_stream.py               # Fault-injection telemetry streamer
├── src/
│   ├── agent/                         # Controlled 11-step ReAct agent & CMMS work orders
│   ├── anomaly/                       # Unsupervised Isolation Forest detector
│   ├── api/
│   │   └── main.py                    # 13 FastAPI endpoints (REST inference & file uploads)
│   ├── data/                          # Data cleaning, timestamp regex parsing & temporal ETL
│   ├── explainability/                # SHAP local & global attribution
│   ├── features/                      # Physics, thermodynamics & lag feature engineering
│   ├── models/                        # Inference engine, training scripts & MHI scoring
│   ├── rag/                           # Vector indexing & semantic manual retrieval
│   └── utils/
│       ├── __init__.py
│       └── file_converter.py          # Universal file ingestion & CSV conversion engine
├── streamlit_app/
│   └── app.py                         # TALOS·AI (Total Asset & Lifetime Operational Safeguard) cockpit (10 specialized views)
├── tests/
│   ├── test_agent.py                  # Agent ReAct workflow tests
│   ├── test_api.py                    # FastAPI REST endpoints tests
│   ├── test_features.py               # Feature engineering tests
│   ├── test_file_converter.py         # Universal file converter & format tests
│   ├── test_health_and_workorder.py   # Health Index & Work Order tests
│   ├── test_models.py                 # ML model prediction tests
│   └── test_multiclass.py             # Multi-class fault classifier tests
├── Dockerfile                         # Production container specification
├── requirements.txt                   # Dependency manifest (including openpyxl)
└── README.md                          # Platform documentation
```

---

## 5. How to Run

### 1. Launch the Tier-1 Industrial Cockpit (Streamlit)
```powershell
.\.venv\Scripts\streamlit run streamlit_app\app.py
```
- Available at: `http://localhost:8501`
- **10 Specialized Operational Views**:
  1. 📊 **Plant Executive Overview**: Fleet MHI average, risk distribution, savings ($), and **Chart 1 & Chart 2** (ASME A13.1 Industrial Utility Distribution & Load Share).
  2. 📈 **Live Telemetry & $\Delta T$**: Broadband vibration vs ISO 10816, thermal trends, and **Chart 3** (Multi-Fluid & Auxiliary Utility Telemetry Correlation timeline).
  3. ⚠️ **Multi-Class Fault & RUL**: Categorical fault diagnosis with confidence scores and health penalty breakdown.
  4. 🔍 **SHAP Attribution & RCA**: Sensor contribution percentages to impending failures.
  5. 📋 **CMMS Digital Work Orders**: SAP PM / IBM Maximo-ready work order generation with 1-click Markdown/JSON download.
  6. 🛠️ **Maintenance & Spares**: Historical records, plant incident post-mortems, and warehouse parts catalog.
  7. 🤖 **Autonomous AI Copilot**: Evidence-grounded conversational agent with tool execution trace.
  8. 📉 **Model Benchmarks**: Multi-class diagnostics and ROC-AUC / PR-AUC metrics.
  9. ⚡ **Fault Progression Simulator**: Real-time progressive equipment degradation streamer.
  10. 📁 **Data Ingestion & CSV Converter**: Drag-and-drop any file format, automatically convert to standard CSV, preview, download, and ingest into database.

### 2. Launch the FastAPI REST Backend
```powershell
.\.venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Key Endpoints:
  - `POST /files/upload` — Ingest any file format, convert to CSV, and persist.
  - `GET /files/converted` — List all converted CSV files in the audit registry.
  - `GET /files/stats` — Ingestion storage footprint and conversion metrics.
  - `GET /files/download/{file_id}` — Direct download of converted CSV.
  - `GET /health-index/{machine_id}` — Machine Health Index score and penalty breakdown.
  - `GET /workorders/{machine_id}` — CMMS digital work order document.
  - `GET /roi-analytics/{machine_id}` — Net financial savings from proactive intervention.
  - `POST /predict` — Telemetry window inference (failure probability, RUL, fault class).
  - `POST /copilot/chat` — Conversational ReAct AI Copilot investigation.

### 3. Run Real-Time Telemetry Simulator
```powershell
.\.venv\Scripts\python simulator\sensor_stream.py --machine M17 --scenario bearing_failure_progression --steps 20 --interval 1.0
```

### 4. Run Automated Test Suite
```powershell
.\.venv\Scripts\pytest -v tests/
```
*(All 33 tests pass with 100% green)*
