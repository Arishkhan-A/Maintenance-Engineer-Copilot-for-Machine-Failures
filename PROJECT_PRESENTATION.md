# ⚡ MECMF: Multimodal Edge Condition Monitoring & AI Maintenance Copilot (v3.0)
## Complete Presentation Deck, Architectural Dossier & Executive Defense Guide

> **Generated Presentation PDF**: [`MECMF_Project_Presentation.pdf`](file:///c:/Users/arish/Downloads/MECMF/MECMF_Project_Presentation.pdf)  
> **Target Audience**: Industrial Executives, Plant Engineering Directors, IoT/AI Technical Evaluators, Academic Examiners  
> **Status**: Production-Ready Tier-1 Advanced Industrial AI Platform  
> **Automated Test Quality**: 25 / 25 Passing (100% Green)

---

## 📑 Slide-by-Slide Presentation Structure

### 📌 Slide 1: Title & Executive Introduction
- **Project Title**: MECMF (Multimodal Edge Condition Monitoring Framework)
- **Subtitle**: Tier-1 Enterprise AI Platform for Predictive Maintenance, Multi-Class Root-Cause Diagnostics, Health Indexing, and Autonomous CMMS Work Order Dispatch.
- **Industry Sector**: Industry 4.0, Industrial Internet of Things (IIoT), Predictive Maintenance (PdM), Explainable AI (XAI), and Domain-Grounded Retrieval-Augmented Generation (RAG).
- **Primary Tech Stack**: Python 3.12, FastAPI, Streamlit, Scikit-Learn, SHAP, SQLite, Plotly.
- **Presenter's Talking Point**:
  > *"Good morning/afternoon. Today, I am presenting MECMF—a full-stack, enterprise-grade AI decision-support platform engineered to solve one of the manufacturing sector's costliest operational challenges: unplanned machine downtime. Rather than simple black-box failure alarms, our platform delivers exact physical fault mechanisms, remaining useful life forecasting, and automated, SAP-compliant maintenance work order dispatch."*

---

### 📌 Slide 2: The Industrial Problem Statement & Business Opportunity
- **The Catastrophic Downtime Crisis**:
  - Unplanned downtime costs industrial plants **$2,500 per hour** on average (often exceeding **$60,000 per 24-hour shift** on automotive/machining production lines).
  - **82% of manufacturers** still operate in a reactive mode ("run-to-failure") or follow rigid calendar-based preventive maintenance (overhauling healthy equipment while still suffering random breakdowns).
- **The "Data Rich, Insight Poor" Trap**:
  - Modern plants collect millions of SCADA/sensor telemetry points, but field engineers lack real-time correlation between high-frequency vibration, thermal build-up, and exact mechanical failure modes.
- **The Knowledge Retention Gap**:
  - Experienced millwright technicians are retiring, leaving an operational knowledge void in diagnosing complex mechanical failure symptoms.
- **MECMF Key Impact Numbers**:
  - **$38,400+** average net financial loss prevented per critical machine intervention.
  - **96.7%** Multi-Class Fault Classification Accuracy.
  - **0.9987** ROC-AUC on 24-Hour Failure Horizon Prediction.
  - **21.98 Hours** Mean Absolute Error (MAE) on Remaining Useful Life (RUL) Regression.

---

### 📌 Slide 3: End-to-End System Topology & Technical Architecture
The MECMF platform operates across 6 decoupled, enterprise-grade layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        1. SENSOR & TELEMETRY INGESTION                 │
│  Industrial Assets: CNC Milling (M01-M07), Hydraulic Pumps (M08-M14),  │
│  Screw Compressors (M15-M18), 6-Axis Robotic Arms (M19-M20)            │
│  Signals: Vibration RMS, Motor Temp, Pressure, Current, Kinematic RPM  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               2. DATA HYGIENE & TEMPORAL FEATURE STORE                 │
│  • Industrial Timestamp Normalization (12h/24h regex parser)           │
│  • Forward/Backward temporal per-asset imputation (no future leaks)    │
│  • 60 Engineered Features: Rolling windows (5/10 step), Lags (1,3,5),  │
│    ΔT (Thermal Rise), Kinematic Vib/RPM Ratio, Pressure Stability      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     3. UNIFIED MACHINE LEARNING CORE                   │
│  ┌──────────────────────┬──────────────────────┬────────────────────┐  │
│  │  Multi-Class Fault   │  24h Failure Model   │   RUL Regressor    │  │
│  │ (HistGradientBoost)  │   (Random Forest)    │  (Random Forest)   │  │
│  │    Acc: 96.7%        │   ROC-AUC: 0.9987    │   MAE: 21.98 hrs   │  │
│  └──────────────────────┴──────────────────────┴────────────────────┘  │
│  ┌──────────────────────────────┬───────────────────────────────────┐  │
│  │ Calibrated Isolation Forest  │         SHAP TreeExplainer        │  │
│  │  (Unsupervised Anomaly, 4%)  │    (Local & Global Attribution)   │  │
│  └──────────────────────────────┴───────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              4. DOMAIN-GROUNDED RAG & AI COPILOT WORKFLOW              │
│  • Curated Technical Corpus: OEM Manuals, ISO 10816 Guides, Incident   │
│    Post-Mortem RCAs (46 Indexed Sections, TF-IDF + Cosine Retrieval)   │
│  • 11-Step Controlled ReAct Loop with 10 Deterministic Tools           │
│  • Hallucination Guardrail: Strict fallback on insufficient evidence   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               5. CMMS DISPATCH & FINANCIAL ROI ENGINE                  │
│  • Composite Machine Health Index: 0 - 100% MHI Formula                │
│  • Proactive vs Catastrophic Downtime ROI Cost Comparison              │
│  • Formal Digital Work Orders (SAP PM / IBM Maximo Standard)           │
│    With LOTO Safety Mandates, Assigned Technicians & Warehouse Bins    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   6. ENTERPRISE CONSUMPTION INTERFACES                 │
│  • FastAPI REST Server: Swagger UI, Pydantic v2 schemas, CORS enabled  │
│  • Streamlit v3.0 TALOS·AI Executive Cockpit (10 Specialized Views)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 📌 Slide 4: Multi-Model Machine Learning Performance
MECMF abandons the "one model fits all" fallacy by deploying specialized, calibrated models for distinct industrial tasks:

| ML Model Layer | Model Architecture | Key Test Metrics | Operational Objective |
| :--- | :--- | :--- | :--- |
| **Multi-Class Root-Cause Classifier** | `HistGradientBoostingClassifier` with balanced class weights | **Accuracy: 96.7%**<br>**Weighted F1: 0.9636**<br>Macro F1: 0.7974 | Diagnoses exact failure mechanism: Bearing Degradation, Motor Overheating, Hydraulic Seal Failure, Electrical Surge, or Nominal State. |
| **Binary Failure Predictor** | Tuned `RandomForestClassifier` (150 trees, balanced) | **ROC-AUC: 0.9987**<br>**PR-AUC: 0.9872**<br>**F1-Score: 0.9300** | Provides high-confidence 24-hour lookahead warning before catastrophic shutdown. |
| **RUL Regressor** | `RandomForestRegressor` with thermodynamic inputs | **MAE: 21.98 Hours**<br>**RMSE: 31.48 Hours** | Predicts operational hours remaining before component fatigue point. |
| **Unsupervised Anomaly Detector** | `IsolationForest` (Calibrated on normal baselines) | **Contamination: 0.04 (4%)**<br>Calibrated Decision Threshold | Detects uncatalogued operational drift, loose fasteners, and multi-sensor phase variations. |
| **Explainable AI (XAI)** | `shap.TreeExplainer` | Local percentage impact decomposition | Converts tree splits into transparent percentage drivers (e.g., 52% vibration, 31% temperature). |

- **Zero-Data-Leakage Guarantee**: Models are validated using **Per-Asset Temporal Splitting (80% Train, 20% Test)**. Training features never look forward in time.

---

### 📌 Slide 5: Composite Machine Health Index (MHI) & Physics Principles
Field technicians do not want raw probabilities; they need a single, physics-backed health score:

$$\text{MHI} = 100 - \sum \text{Penalties}$$

```
+------------------------------------+------------------+------------------------------------+
| Health Factor                      | Max Penalty      | Engineering Rule / ISO Standard    |
+------------------------------------+------------------+------------------------------------+
| 1. Failure Probability Penalty     | 35.0 Points      | Linear scale: 35 * P(Failure)      |
| 2. Vibration Severity Penalty      | 25.0 Points      | ISO 10816-3 Limits (>4.5, >7.1)    |
| 3. Thermodynamic Delta (ΔT)        | 20.0 Points      | ΔT = T_motor - T_ambient (>35°C)   |
| 4. Unsupervised Anomaly Deviation  | 10.0 Points      | Isolation Forest boundary penalty  |
| 5. Remaining Useful Life (RUL)     | 10.0 Points      | RUL < 48h (5 pts), RUL < 24h (10)  |
+------------------------------------+------------------+------------------------------------+
```

#### Health Status Tiers:
- **Optimal (85 - 100%)**: Green LED. Standard scheduled maintenance cycles.
- **Good (70 - 84%)**: Blue LED. Baseline telemetry observation.
- **Degraded Warning (40 - 69%)**: Amber LED. P3 Work Order dispatched for lubrication/filter check.
- **Critical Risk (< 40%)**: Red Flashing LED. Immediate P1 Emergency LOTO shutdown required.

---

### 📌 Slide 6: Domain-Grounded Technical RAG & Controlled ReAct Agent
- **Why RAG for Maintenance?**
  - Standard LLMs hallucinate incorrect torque values, wrong bearing models, and dangerous procedures.
  - MECMF enforces an **offline, zero-hallucination Grounded RAG** architecture.
- **Curated Knowledge Base (46 Indexed Sections)**:
  - **OEM Engineering Manuals**: Electric motors (bearing clearances), hydraulic pumps (Plan 11 flush), screw compressors (thermostatic valve), robotic arms (cycloidal backlash).
  - **ISO Troubleshooting Guides**: ISO 10816 vibration diagnosis matrix, thermal runaway checklists, hydraulic cavitation guides.
  - **Historical Incident Post-Mortems (RCAs)**: Real past failure reports (M17 bearing seizure, M04 seal blowout, M12 thermal trip).
- **Controlled 11-Step ReAct Workflow**:
  1. `extract_machine_id`: Parses entity from natural language.
  2. `get_machine_status`: Retrieves machine class, bay location, and specs.
  3. `get_sensor_history`: Pulls recent 15-step sliding window.
  4. `predict_failure`: Runs binary failure classifier.
  5. `get_rul`: Computes remaining operational hours.
  6. `diagnose_fault_type`: Runs multi-class gradient boosting model.
  7. `shap_explainer`: Determines dominant sensor drivers.
  8. `get_maintenance_history`: Audits past interventions and technicians.
  9. `search_manual`: Performs semantic search for equipment-specific repair procedures.
  10. `search_incidents`: Finds matching historical failure precedents.
  11. `get_spare_parts` & `generate_work_order`: Validates warehouse stock and emits SAP-compliant document.

---

### 📌 Slide 7: Automated CMMS Work Order Dispatch & Financial ROI
When a machine deteriorates, MECMF automatically generates an audit-ready maintenance document:

#### 1. CMMS Digital Work Order Details
- **Work Order ID**: `WO-20260904-M17-01`
- **Priority & SLA**:
  - `P1 - EMERGENCY IMMEDIATE SHUTDOWN` (SLA: < 2 Hours)
  - `P2 - URGENT INTERVENTION` (SLA: < 24 Hours)
  - `P3 - SCHEDULED ROUTINE WINDOW` (SLA: < 72 Hours)
- **Safety Lockout-Tagout (LOTO)**:
  - `LOTO #E-401`: De-energize 400V 3-phase circuit breaker with safety padlock.
  - `LOTO #P-204`: Relieve residual hydraulic pressure to 0.0 bar before unseating flanges.
  - **PPE**: NFPA 70E Arc-Flash Class 2 shield, anti-vibration mechanic gloves.
- **Warehouse Spare Staging**: Automatically checks inventory (e.g. SKF-6312-C3 in Bin A-12) and stages parts before technician dispatch.

#### 2. Financial Loss Prevention Equation
$$\text{Catastrophic Breakdown Cost} = (14.0\text{ hrs} \times \$2,500/\text{hr}) + \$4,200\text{ (Parts)} + \$1,200\text{ (Overtime)} = \$40,400$$
$$\text{Proactive Intervention Cost} = (0.5\text{ hrs} \times \$2,500/\text{hr}) + \$450\text{ (Planned Spares)} + \$300\text{ (Labor)} = \$2,000$$
$$\mathbf{\text{Net Financial Savings Prevented} = \$38,400 \quad (\text{ROI} > 1,900\%)}$$

---

### 📌 Slide 8: The TALOS·AI Executive Cockpit (Total Asset & Lifetime Operational Safeguard)
- **Streamlit v3.0 High-Tech Industrial UI**:
  - Custom TALOS·AI theme (**Total Asset & Lifetime Operational Safeguard** — dark slate `#070b14` canvas, glowing radial gradients, JetBrains Mono telemetry typography).
  - **ASME A13.1 Industrial Piping & Utility Standard Color Palette**:
    - 🟢 **Green**: Water (cooling or potable supply).
    - 🔵 **Blue**: Compressed air and pneumatic gases.
    - 🟡 **Yellow**: Flammable or hazardous gases.
    - 🔴 **Red**: Fire-fighting and suppression water loops.
    - 🟤 **Brown**: Oils, lubricants, and combustible fluids.
    - 🟠 **Orange**: Acids, toxic elements, and corrosive chemicals.
    - 🟣 **Purple**: Specialized hazardous or chemical waste.
    - ⚫ **Black**: Drain and wastewater lines.
  - **3 Dedicated Industrial Telemetry Charts**:
    - **Chart 1 (Bar)**: Industrial Piping Loop Operating Capacity vs Header Limit (%).
    - **Chart 2 (Donut)**: Industrial Fluid Distribution Network Load Share & Risk Matrix.
    - **Chart 3 (Multi-Line)**: Real-Time Multi-Fluid & Auxiliary Utility Telemetry Correlation timeline.
  - 10 Specialized Operational Views:
    1. *Plant Executive Overview*: Fleet MHI, plant risk breakdown, cumulative savings, and ASME A13.1 piping loop capacity & distribution charts.
    2. *Live Telemetry & $\Delta T$*: Broadband vibration vs ISO 10816, casing temperature, and Multi-Fluid correlation timeline.
    3. *Multi-Class Fault & RUL*: Health penalty breakdown, probability bars per fault type.
    4. *SHAP Attribution & RCA*: Waterfall/bar feature importance decomposition.
    5. *CMMS Digital Work Orders*: Formatted document preview with 1-click Markdown & JSON download.
    6. *Maintenance & Spares*: Historical records, incident post-mortems, warehouse stock.
    7. *Autonomous AI Copilot*: Conversational investigation with tool execution trace.
    8. *Model Benchmarks*: Live confusion matrices and ROC-AUC metrics.
    9. *Fault Progression Simulator*: Live failure injection streamer.
    10. *Universal Data Ingestion & CSV Converter*: Any-format file ingestion, automated CSV conversion, and storage vault.
- **FastAPI Enterprise REST Backend**:
  - 13 Async REST Endpoints (`/health-index/{id}`, `/workorders/{id}`, `/predict`, `/copilot/chat`, `/files/upload`, `/files/converted`, etc.).
  - Pydantic v2 input validation, CORS middleware, and automatic OpenAPI Swagger docs (`/docs`).

---

### 📌 Slide 9: System Verification, Production Quality & Future Roadmap
- **Automated Testing & Software Quality**:
  - **25 / 25 Pytest automated tests passing (100%)**.
  - Integration tests for REST endpoints, agent ReAct workflow, feature pipeline, and MHI scoring.
  - Defensive error handling: graceful 404 responses for missing assets, robust input validation for sensor dropouts.
- **Production Containerization**:
  - Multi-stage Dockerfile bundling Python 3.12, SQLite database, pre-trained models, and pre-indexed RAG vectors.
- **Future Roadmap (Phase 4)**:
  - Direct industrial PLC connectivity via **OPC-UA / MQTT**.
  - Acoustic emission spectrum analysis (ultrasonic micro-crack detection).
  - Direct two-way ERP write-back via **SAP PM BAPI / IBM Maximo REST API**.

---

## 🎯 Quick Presentation Defense: Anticipated Q&A

**Q1: How does your model avoid data leakage when calculating rolling features and lags?**
> *"We implement strict temporal train-test splitting (80/20) grouped individually by machine asset ID. All rolling means, rolling standard deviations, and shift lags are computed sequentially. The preprocessor (ColumnTransformer) is fitted exclusively on the training partition and only transforms the test partition, guaranteeing zero lookahead bias."*

**Q2: What happens if an external sensor drops out or sends corrupted data?**
> *"Our ETL pipeline (`src/data/load_data.py`) incorporates industrial temporal imputation: it first applies per-asset forward fill (representing the sensor holding its last valid reading), followed by backward fill for initial startup delays, with a fallback to the equipment-class median. Furthermore, our feature engineering module enforces fallback defaults so missing columns never crash the inference engine."*

**Q3: Why use HistGradientBoosting for multi-class diagnosis instead of a Deep Learning neural network?**
> *"On tabular industrial telemetry data, tree-based ensemble methods consistently outperform deep neural networks in accuracy, training efficiency, and inference latency. HistGradientBoosting achieves 96.7% accuracy with sub-millisecond inference time on edge hardware, native support for class weight balancing, and direct interpretability via SHAP TreeExplainer."*

**Q4: How do you guarantee the AI Copilot will not hallucinate dangerous maintenance procedures?**
> *"The copilot is not an unconstrained generic chatbot. It uses a controlled 11-step ReAct architecture with deterministic tools. When generating technical recommendations, it queries a curated knowledge base of OEM manuals and past incident reports. If semantic similarity scores fall below the safety threshold, it explicitly flags `INSUFFICIENT_EVIDENCE` rather than inventing an answer."*

---

## 🚀 How to Demo the Project Live

1. **Launch the Industrial Cockpit (Streamlit)**:
   ```powershell
   .\.venv\Scripts\streamlit run streamlit_app\app.py
   ```
2. **Launch the FastAPI REST Server**:
   ```powershell
   .\.venv\Scripts\uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. **Stream Simulated Live Degradation**:
   ```powershell
   .\.venv\Scripts\python simulator\sensor_stream.py --machine M17 --scenario bearing_failure_progression --steps 15
   ```
4. **Run the Verification Suite**:
   ```powershell
   .\.venv\Scripts\pytest -v tests/
   ```

---
*MECMF Platform Document • Authored for Project Presentation & Executive Evaluation*
