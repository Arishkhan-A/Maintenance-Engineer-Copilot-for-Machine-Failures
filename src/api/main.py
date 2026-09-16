"""FastAPI REST backend serving predictive maintenance inference, database queries, and AI Copilot."""
import os
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import pandas as pd

from src.models.predict import MachineInferenceEngine
from src.agent.workflow import MaintenanceCopilotAgent
from src.utils.file_converter import UniversalFileConverter
from src.rag.theory_analyzer import MachineTheoryAnalyzer, validate_industrial_domain
from src.rag.ingest import index_raw_theory

app = FastAPI(
    title="Maintenance Engineer Copilot API",
    description="Industrial AI Platform for Failure Prediction, Anomaly Detection, SHAP Explainability & Grounded RAG Copilot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "database/maintenance.db"
inference_engine = MachineInferenceEngine()
agent = MaintenanceCopilotAgent()
file_converter = UniversalFileConverter()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic models
class SensorReadingInput(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "M17"})
    machine_type: Optional[str] = Field("CNC", json_schema_extra={"example": "CNC"})
    temperature: float = Field(..., json_schema_extra={"example": 84.2})
    vibration: float = Field(..., json_schema_extra={"example": 4.65})
    pressure: float = Field(..., json_schema_extra={"example": 6.1})
    current: float = Field(..., json_schema_extra={"example": 41.5})
    rpm: float = Field(..., json_schema_extra={"example": 2400.0})
    ambient_temp: Optional[float] = Field(25.0, json_schema_extra={"example": 24.5})
    operating_mode: Optional[str] = Field("normal", json_schema_extra={"example": "normal"})
    hours_since_maintenance: Optional[float] = Field(500.0, json_schema_extra={"example": 520.0})

class CopilotChatRequest(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Why is M17 at high risk?"})
    machine_id: Optional[str] = Field(None, json_schema_extra={"example": "M17"})

class TheoryAnalyzeRequest(BaseModel):
    content: str = Field(..., json_schema_extra={"example": "Centrifugal pumps convert rotational kinetic energy into hydrodynamic energy using impeller vanes."})
    machine_name: Optional[str] = Field(None, json_schema_extra={"example": "Centrifugal Pump"})

class TheoryIngestRequest(BaseModel):
    content: str = Field(..., json_schema_extra={"example": "# Technical Theory: Industrial Boiler\n\n## 1. Principles\nBoilers generate steam..."})
    doc_name: str = Field(..., json_schema_extra={"example": "industrial_boiler_theory.txt"})
    machine_name: Optional[str] = Field(None, json_schema_extra={"example": "Industrial Boiler"})
    category: Optional[str] = Field("theory", json_schema_extra={"example": "theory"})

class TheoryQueryRequest(BaseModel):
    query: str = Field(..., json_schema_extra={"example": "Explain cavitation physics in centrifugal pumps"})
    machine_name: Optional[str] = Field(None, json_schema_extra={"example": "Pump"})
    top_k: Optional[int] = Field(3, ge=1, le=10)

@app.get("/")
def root():
    return {
        "service": "Maintenance Engineer Copilot REST Backend",
        "status": "online",
        "version": "2.0.0-enterprise",
        "endpoints": [
            "/health",
            "/machines",
            "/machines/{machine_id}",
            "/machines/{machine_id}/sensors",
            "/predict",
            "/risk/{machine_id}",
            "/maintenance/{machine_id}",
            "/spares",
            "/copilot/chat",
            "/rag/theory/analyze",
            "/rag/theory/ingest",
            "/rag/theory/query",
            "/files/upload",
            "/files/converted",
            "/files/stats",
            "/files/download/{file_id}"
        ]
    }

@app.get("/health")
def health_check():
    db_ok = os.path.exists(DB_PATH)
    models_ok = inference_engine.is_ready()
    return {
        "status": "healthy" if (db_ok and models_ok) else "degraded",
        "database_connected": db_ok,
        "models_loaded": models_ok,
        "models_directory": "models"
    }

@app.get("/machines")
def list_machines():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM machines ORDER BY machine_id")
        return [dict(r) for r in cursor.fetchall()]

@app.get("/machines/{machine_id}")
def get_machine(machine_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM machines WHERE machine_id = ?", (machine_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
        return dict(row)

@app.get("/machines/{machine_id}/sensors")
def get_machine_sensors(machine_id: str, limit: int = Query(30, ge=1, le=500)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT timestamp, temperature, vibration, pressure, current, rpm, ambient_temp, operating_mode, hours_since_maintenance
               FROM sensor_readings
               WHERE machine_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (machine_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(r) for r in reversed(rows)]

@app.post("/predict")
def predict_telemetry(payload: SensorReadingInput):
    # Fetch recent history from DB to form valid lag/rolling features
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT timestamp, machine_id, temperature, vibration, pressure, current, rpm, ambient_temp, operating_mode, hours_since_maintenance
               FROM sensor_readings
               WHERE machine_id = ?
               ORDER BY timestamp DESC
               LIMIT 14""",
            (payload.machine_id,)
        )
        history = [dict(r) for r in reversed(cursor.fetchall())]

    # Append current payload as the newest observation
    new_reading = {
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "machine_id": payload.machine_id,
        "machine_type": payload.machine_type or "CNC",
        "temperature_motor": payload.temperature,
        "vibration_rms": payload.vibration,
        "pressure_level": payload.pressure,
        "current_phase_avg": payload.current,
        "rpm": payload.rpm,
        "ambient_temp": payload.ambient_temp or 25.0,
        "operating_mode": payload.operating_mode or "normal",
        "hours_since_maintenance": payload.hours_since_maintenance or 500.0
    }
    history.append(new_reading)

    df_window = pd.DataFrame(history)
    df_window["machine_type"] = payload.machine_type or "CNC"

    result = inference_engine.predict_window(df_window)

    # Insert into sensor_readings and update machine status in SQLite
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO sensor_readings (timestamp, machine_id, temperature, vibration, pressure, current, rpm, ambient_temp, operating_mode, hours_since_maintenance)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (new_reading["timestamp"], payload.machine_id, payload.temperature, payload.vibration,
             payload.pressure, payload.current, payload.rpm, payload.ambient_temp or 25.0,
             payload.operating_mode or "normal", payload.hours_since_maintenance or 500.0)
        )
        c.execute(
            """UPDATE machines SET status = ?, operating_mode = ? WHERE machine_id = ?""",
            (result["risk_level"], payload.operating_mode or "normal", payload.machine_id)
        )
        c.execute(
            """INSERT INTO predictions (machine_id, timestamp, risk, probability, rul_hours, is_anomaly, anomaly_score, model_version, top_contributing_feature)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (payload.machine_id, new_reading["timestamp"], result["risk_level"], result["failure_probability"],
             result["rul_hours"], 1 if result["is_anomaly"] else 0, result["anomaly_score"], "2.0.0",
             result["top_contributing_features"][0]["feature"] if result["top_contributing_features"] else "None")
        )
        conn.commit()

    return result

@app.get("/risk/{machine_id}")
def get_machine_risk(machine_id: str):
    res = agent.tools.predict_failure(machine_id)
    rul = agent.tools.get_rul(machine_id)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return {
        "machine_id": machine_id,
        "failure_probability": res["failure_probability"],
        "risk_level": res["risk_level"],
        "rul_hours": rul.get("rul_hours", 0.0),
        "top_contributing_features": res.get("top_contributing_features", [])
    }

@app.get("/maintenance/{machine_id}")
def get_maintenance(machine_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM maintenance_records WHERE machine_id = ? ORDER BY date DESC", (machine_id,))
        records = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM failure_events WHERE machine_id = ? ORDER BY timestamp DESC", (machine_id,))
        failures = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM incidents WHERE machine_id = ? ORDER BY timestamp DESC", (machine_id,))
        incidents = [dict(r) for r in cursor.fetchall()]

    return {
        "machine_id": machine_id,
        "maintenance_records": records,
        "failure_events": failures,
        "incidents": incidents
    }

@app.get("/spares")
def get_spare_parts():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM spare_parts ORDER BY component")
        return [dict(r) for r in cursor.fetchall()]

@app.get("/health-index/{machine_id}")
def get_machine_health_index(machine_id: str):
    history = agent.tools.get_sensor_history(machine_id, limit=15)
    if not history:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found or has no readings")
    machine_info = agent.tools.get_machine_status(machine_id)
    df_win = pd.DataFrame(history)
    df_win["machine_id"] = machine_id
    df_win["machine_type"] = machine_info.get("machine_type", "CNC")
    inf = inference_engine.predict_window(df_win)
    return {
        "machine_id": machine_id,
        "health_index": inf["health_index"],
        "fault_diagnosis": inf["fault_diagnosis"],
        "risk_level": inf["risk_level"]
    }

@app.get("/workorders/{machine_id}")
def get_machine_work_order(machine_id: str):
    res = agent.tools.generate_work_order(machine_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@app.get("/roi-analytics/{machine_id}")
def get_roi_analytics(machine_id: str):
    history = agent.tools.get_sensor_history(machine_id, limit=15)
    if not history:
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    machine_info = agent.tools.get_machine_status(machine_id)
    df_win = pd.DataFrame(history)
    df_win["machine_id"] = machine_id
    df_win["machine_type"] = machine_info.get("machine_type", "CNC")
    inf = inference_engine.predict_window(df_win)
    return {
        "machine_id": machine_id,
        "financial_roi": inf["financial_roi"],
        "risk_level": inf["risk_level"]
    }

@app.post("/copilot/chat")
def copilot_chat(req: CopilotChatRequest):
    response = agent.chat(req.message, default_machine=req.machine_id or "M17")
    return response

# ----------------- MACHINE THEORY & RAG KNOWLEDGE ENDPOINTS -----------------
@app.post("/rag/theory/analyze")
def analyze_machine_theory(req: TheoryAnalyzeRequest):
    """Deeply decompose raw machine theory content into principles, subsystems, limits, failure modes, and equations."""
    return MachineTheoryAnalyzer.analyze_theory_content(req.content, req.machine_name)

@app.post("/rag/theory/ingest")
def ingest_machine_theory(req: TheoryIngestRequest):
    """Dynamically chunk, tag, and index machine theory content into the active RAG database."""
    chunks = index_raw_theory(
        text=req.content,
        doc_name=req.doc_name,
        machine_name=req.machine_name,
        category=req.category or "theory",
        output_json="database/rag_index.json"
    )
    agent.tools.retriever.reload_index()
    return {
        "status": "INGESTED",
        "doc_name": req.doc_name,
        "machine_name": req.machine_name or "Custom Machine",
        "chunks_indexed": len(chunks),
        "total_active_chunks": len(agent.tools.retriever.chunks)
    }

@app.post("/rag/theory/query")
def query_machine_theory(req: TheoryQueryRequest):
    """Retrieve and synthesize evidence-backed answers for machine theory questions with strict guardrails."""
    is_valid, refusal_msg = validate_industrial_domain(req.query)
    if not is_valid:
        return {
            "status": "GUARDRAIL_BLOCKED",
            "query": req.query,
            "answer": refusal_msg,
            "guardrail_triggered": True,
            "citations": []
        }
    theory_chunks = agent.tools.retriever.search_theory(req.query, top_k=req.top_k or 3, machine_type=req.machine_name)
    response = agent.generator.generate_theory_response(req.query, theory_chunks, machine_name=req.machine_name)
    return response

# ----------------- UNIVERSAL FILE INGESTION & CSV CONVERSION -----------------
@app.post("/files/upload")
async def upload_and_convert_file(file: UploadFile = File(...)):
    """
    Ingests any uploaded file format, converts content into structured CSV format,
    persists in data/converted/, records in SQLite audit registry, and returns summary & preview.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    result = file_converter.convert_and_store(content, file.filename or "uploaded_file")
    return {
        "file_id": result["file_id"],
        "original_filename": result["original_filename"],
        "file_format": result["file_format"],
        "original_size_bytes": result["original_size_bytes"],
        "converted_csv_filename": result["converted_csv_filename"],
        "converted_csv_path": result["converted_csv_path"],
        "row_count": result["row_count"],
        "column_count": result["column_count"],
        "columns": result["columns"],
        "upload_timestamp": result["upload_timestamp"],
        "status": result["status"],
        "preview": result["preview"]
    }

@app.get("/files/converted")
def list_converted_files(limit: int = Query(50, ge=1, le=500)):
    """List all previously converted CSV files in SQLite registry."""
    return file_converter.list_converted_files(limit=limit)

@app.get("/files/stats")
def get_file_stats():
    """Get aggregated summary metrics of all ingested and converted files."""
    return file_converter.get_ingestion_stats()

@app.get("/files/download/{file_id}")
def download_converted_file(file_id: str):
    """Download the converted CSV file."""
    meta = file_converter.get_converted_file(file_id)
    if not meta or not meta.get("converted_csv_path"):
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")

    path = meta["converted_csv_path"]
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File no longer exists on disk")

    return FileResponse(
        path,
        media_type="text/csv",
        filename=meta.get("converted_csv_filename", f"{file_id}.csv")
    )
