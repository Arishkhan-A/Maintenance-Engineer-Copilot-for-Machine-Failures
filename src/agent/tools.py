"""Controlled AI Agent Tools for Predictive Maintenance."""
import os
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional
from src.models.predict import MachineInferenceEngine
from src.rag.retrieve import KnowledgeRetriever

DB_PATH = "database/maintenance.db"

class MaintenanceAgentTools:
    """Safe, validated, read-only tools for the Maintenance Engineer Copilot Agent."""

    def __init__(self, db_path: str = DB_PATH, models_dir: str = "models", docs_dir: str = "documents"):
        self.db_path = db_path
        self.inference_engine = MachineInferenceEngine(models_dir=models_dir)
        self.retriever = KnowledgeRetriever(docs_dir=docs_dir)

    def _get_db_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # 1. get_machine_status
    def get_machine_status(self, machine_id: str) -> Dict[str, Any]:
        """Fetch current operational status, machine type, and location for machine_id."""
        with self._get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM machines WHERE machine_id = ?", (machine_id,))
            row = cursor.fetchone()
            if not row:
                return {"error": f"Machine {machine_id} not found in database."}
            return dict(row)

    # 2. get_sensor_history
    def get_sensor_history(self, machine_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve the most recent sensor telemetry readings for machine_id."""
        with self._get_db_conn() as conn:
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
            # return in chronological order
            return [dict(r) for r in reversed(rows)]

    # 3. predict_failure
    def predict_failure(self, machine_id: str) -> Dict[str, Any]:
        """Run ML failure prediction on the latest sensor window for machine_id."""
        history = self.get_sensor_history(machine_id, limit=15)
        if not history or len(history) < 3:
            return {"error": f"Insufficient sensor history for machine {machine_id} to compute features."}

        machine_info = self.get_machine_status(machine_id)
        df_window = pd.DataFrame(history)
        df_window["machine_id"] = machine_id
        df_window["machine_type"] = machine_info.get("machine_type", "CNC")
        df_window["temperature_motor"] = df_window.get("temperature", 60.0)
        df_window["vibration_rms"] = df_window.get("vibration", 1.8)
        df_window["pressure_level"] = df_window.get("pressure", 6.0)
        df_window["current_phase_avg"] = df_window.get("current", 35.0)

        inference = self.inference_engine.predict_window(df_window)
        return {
            "machine_id": machine_id,
            "failure_probability": inference["failure_probability"],
            "risk_level": inference["risk_level"],
            "top_contributing_features": inference["top_contributing_features"]
        }

    # 4. get_rul
    def get_rul(self, machine_id: str) -> Dict[str, Any]:
        """Estimate Remaining Useful Life (RUL) in operating hours for machine_id."""
        history = self.get_sensor_history(machine_id, limit=15)
        if not history:
            return {"error": f"No telemetry available for machine {machine_id}"}

        machine_info = self.get_machine_status(machine_id)
        df_window = pd.DataFrame(history)
        df_window["machine_id"] = machine_id
        df_window["machine_type"] = machine_info.get("machine_type", "CNC")
        df_window["temperature_motor"] = df_window.get("temperature", 60.0)
        df_window["vibration_rms"] = df_window.get("vibration", 1.8)
        df_window["pressure_level"] = df_window.get("pressure", 6.0)
        df_window["current_phase_avg"] = df_window.get("current", 35.0)

        inference = self.inference_engine.predict_window(df_window)
        return {
            "machine_id": machine_id,
            "rul_hours": inference["rul_hours"],
            "timestamp": inference["timestamp"]
        }

    # 5. get_maintenance_history
    def get_maintenance_history(self, machine_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieve logged past maintenance actions and component replacements."""
        with self._get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT date, action, component, technician, cost
                   FROM maintenance_records
                   WHERE machine_id = ?
                   ORDER BY date DESC
                   LIMIT ?""",
                (machine_id, limit)
            )
            return [dict(r) for r in cursor.fetchall()]

    # 6. search_manual
    def search_manual(self, query: str, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Search manufacturer technical manuals and troubleshooting procedures."""
        cat = filters.get("category") if filters else None
        tag = filters.get("tag") if filters else None
        return self.retriever.retrieve(query, top_k=3, category=cat, tag=tag)

    # 7. search_incidents
    def search_incidents(self, query: str, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """Search historical incident reports and Root Cause Analysis (RCA) records."""
        return self.retriever.retrieve(query, top_k=2, category="incident")

    # 8. get_spare_parts
    def get_spare_parts(self, component: str) -> List[Dict[str, Any]]:
        """Check spare parts inventory stock and minimum reorder thresholds."""
        with self._get_db_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT component, part_number, quantity, min_threshold, location
                   FROM spare_parts
                   WHERE component LIKE ? OR part_number LIKE ?""",
                (f"%{component}%", f"%{component}%")
            )
            return [dict(r) for r in cursor.fetchall()]

    # 9. diagnose_fault_type
    def diagnose_fault_type(self, machine_id: str) -> Dict[str, Any]:
        """Diagnose exact physical root fault mechanism using multi-class Gradient Boosting model."""
        history = self.get_sensor_history(machine_id, limit=15)
        if not history:
            return {"error": f"No telemetry available for {machine_id}"}
        machine_info = self.get_machine_status(machine_id)
        df_win = pd.DataFrame(history)
        df_win["machine_id"] = machine_id
        df_win["machine_type"] = machine_info.get("machine_type", "CNC")
        inf = self.inference_engine.predict_window(df_win)
        return {
            "machine_id": machine_id,
            "fault_diagnosis": inf["fault_diagnosis"],
            "confidence": inf["fault_confidence"],
            "probabilities": inf["all_fault_probabilities"]
        }

    # 10. generate_work_order
    def generate_work_order(self, machine_id: str) -> Dict[str, Any]:
        """Generate a formal digital CMMS Maintenance Work Order (SAP PM / Maximo compliant)."""
        from src.agent.work_order import generate_digital_work_order
        machine_info = self.get_machine_status(machine_id)
        if "error" in machine_info:
            return {"error": machine_info["error"]}
        history = self.get_sensor_history(machine_id, limit=15)
        if not history:
            return {"error": f"No telemetry available for machine {machine_id} to generate work order."}
        df_win = pd.DataFrame(history)
        df_win["machine_id"] = machine_id
        df_win["machine_type"] = machine_info.get("machine_type", "CNC")
        inf = self.inference_engine.predict_window(df_win)

        # Retrieve spares
        fault = inf["fault_diagnosis"].lower()
        query_comp = "Bearing" if "bearing" in fault else ("Seal" if "hydraulic" in fault else "Valve")
        spares = self.get_spare_parts(query_comp)

        # Formulate checks
        checks = [
            f"Perform immediate physical inspection for {inf['fault_diagnosis']}.",
            "Verify lubrication viscosity, color, and cleanliness.",
            "Conduct dynamic laser shaft and coupling alignment check.",
            "Log post-repair vibration RMS and verify baseline < 2.0 mm/s."
        ]

        return generate_digital_work_order(
            machine_id=machine_id,
            machine_type=machine_info.get("machine_type", "CNC"),
            location=machine_info.get("location", "Plant Floor"),
            fault_diagnosis=inf["fault_diagnosis"],
            fault_confidence=inf["fault_confidence"],
            risk_level=inf["risk_level"],
            health_index=inf["health_index"]["health_score"],
            rul_hours=inf["rul_hours"],
            recommended_checks=checks,
            spares=spares,
            financial_roi=inf["financial_roi"]
        )
