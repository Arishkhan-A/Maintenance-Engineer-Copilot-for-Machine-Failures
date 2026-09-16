"""
Real-Time Industrial Sensor Telemetry Simulator (v3.0 Enterprise).
Simulates continuous multi-sensor telemetry streams across 7 realistic operational scenarios:
1. Normal Operating State
2. Gradual Vibration Drift (Bearing Degradation)
3. Temperature Rise & Thermal Runaway (Cooling Failure)
4. Sensor Abnormality / Transient Spike (Anomaly Attribution Test)
5. Compound High Failure Condition (Multi-Sensor Breakdown)
6. Maintenance Intervention (Technician Shutdown & Servicing)
7. Full Recovery to Baseline (Post-Repair Nominal Run)
"""

import argparse
import math
import random
import time
import requests
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

API_URL = "http://localhost:8000/predict"
DB_PATH = "database/maintenance.db"

SCENARIOS = {
    "normal": "1. Normal Operating State (Nominal baseline, ISO Class A/B)",
    "vibration_drift": "2. Gradual Vibration Drift (Bearing race wear, ISO 10816-3 breach)",
    "temperature_rise": "3. Temperature Rise & Thermal Runaway (Heat exchanger fouling, elevated ΔT)",
    "sensor_abnormality": "4. Sensor Abnormality / Transient Spike (Transient spike for anomaly attribution)",
    "high_failure_probability": "5. Compound High Failure Condition (Multi-sensor severe degradation)",
    "maintenance_intervention": "6. Maintenance Intervention (Shutdown, lubrication, component swap)",
    "recovery": "7. Full Recovery to Baseline (Post-service restoration to normal health)"
}

class MachineSensorSimulator:
    """Generates continuous telemetry streams and injects controlled failure scenarios."""

    def __init__(self, machine_id: str = "M17", machine_type: str = "CNC", use_api: bool = True):
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.use_api = use_api

        # Nominal Baselines per machine class
        m_lower = machine_type.lower()
        if "pump" in m_lower:
            self.base_temp = 62.0
            self.base_vib = 2.2
            self.base_pres = 30.0
            self.base_curr = 44.0
            self.base_rpm = 1500.0
        elif "compressor" in m_lower:
            self.base_temp = 78.0
            self.base_vib = 2.5
            self.base_pres = 9.5
            self.base_curr = 52.0
            self.base_rpm = 2950.0
        elif "robot" in m_lower:
            self.base_temp = 48.0
            self.base_vib = 1.2
            self.base_pres = 5.0
            self.base_curr = 28.0
            self.base_rpm = 1800.0
        else:  # CNC
            self.base_temp = 55.0
            self.base_vib = 1.8
            self.base_pres = 6.0
            self.base_curr = 35.0
            self.base_rpm = 2400.0

        self.ambient_temp = 25.0
        self.operating_mode = "normal"
        self.hours_since_maint = 520.0
        self.step_idx = 0

    def generate_next_reading(self, scenario: str = "normal") -> Dict[str, Any]:
        """Generate next telemetry packet based on operational scenario."""
        self.step_idx += 1
        self.hours_since_maint += 0.2

        t_noise = random.gauss(0, 0.35)
        v_noise = random.gauss(0, 0.06)
        p_noise = random.gauss(0, 0.12)
        c_noise = random.gauss(0, 0.45)
        rpm_noise = random.gauss(0, 8.0)
        mode_wave = math.sin(self.step_idx / 6.0) * 4.0

        temp = self.base_temp + t_noise + (mode_wave * 0.08)
        vib = self.base_vib + v_noise
        pres = self.base_pres + p_noise
        curr = self.base_curr + c_noise + (mode_wave * 0.1)
        rpm = self.base_rpm + rpm_noise
        amb = self.ambient_temp + random.gauss(0, 0.2)
        mode = "normal"

        scenario = scenario.lower().strip()

        # 1. Normal State
        if scenario in ["normal", "1"]:
            mode = "normal"

        # 2. Gradual Vibration Drift (bearing race degradation)
        elif scenario in ["vibration_drift", "2"]:
            mode = "warning"
            drift_progress = min(1.0, self.step_idx / 12.0)
            vib += drift_progress * 4.5  # climbs to ~6.3 mm/s (ISO Unacceptable)
            temp += drift_progress * 8.0
            curr += drift_progress * 4.0

        # 3. Temperature Rise & Thermal Runaway (cooling failure)
        elif scenario in ["temperature_rise", "3"]:
            mode = "warning"
            rise_progress = min(1.0, self.step_idx / 10.0)
            temp += rise_progress * 42.0  # climbs to ~97°C
            curr += rise_progress * 18.0  # climbs to ~53A
            vib += rise_progress * 1.5

        # 4. Sensor Abnormality / Transient Spike (Anomaly attribution testing)
        elif scenario in ["sensor_abnormality", "4"]:
            mode = "normal"
            if self.step_idx % 4 == 0:
                # Sudden single-cycle abnormal spike in pressure and vibration
                pres += 14.5  # huge spike
                vib += 5.2
            elif self.step_idx % 5 == 0:
                curr += 28.0  # current surge

        # 5. Compound High Failure Condition (multi-sensor severe breakdown)
        elif scenario in ["high_failure_probability", "bearing_failure_progression", "5"]:
            mode = "critical"
            prog = min(1.0, self.step_idx / 10.0)
            vib += prog * 6.0     # climbs to >7.5 mm/s
            temp += prog * 38.0   # climbs to >92°C
            curr += prog * 24.0   # climbs to >58A
            pres += prog * 4.0

        # 6. Maintenance Intervention (controlled shutdown & overhaul)
        elif scenario in ["maintenance_intervention", "6"]:
            mode = "maintenance"
            rpm = max(0.0, self.base_rpm * (1.0 - min(1.0, self.step_idx / 4.0)))
            curr = max(0.5, self.base_curr * (1.0 - min(1.0, self.step_idx / 4.0)))
            vib = max(0.05, self.base_vib * (1.0 - min(1.0, self.step_idx / 5.0)))
            temp = max(self.ambient_temp + 2.0, temp - (self.step_idx * 3.5))

        # 7. Full Recovery to Baseline (restored nominal health)
        elif scenario in ["recovery", "7"]:
            mode = "normal"
            vib = self.base_vib * 0.95 + random.gauss(0, 0.04)
            temp = self.base_temp + random.gauss(0, 0.25)
            curr = self.base_curr + random.gauss(0, 0.3)
            self.hours_since_maint = 0.5

        return {
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "temperature": round(max(10.0, temp), 2),
            "vibration": round(max(0.05, vib), 3),
            "pressure": round(max(0.1, pres), 2),
            "current": round(max(0.0, curr), 2),
            "rpm": round(max(0.0, rpm), 1),
            "ambient_temp": round(amb, 1),
            "operating_mode": mode,
            "hours_since_maintenance": round(self.hours_since_maint, 1)
        }

    def emit_reading(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """Send reading either to FastAPI /predict endpoint or directly to SQLite DB."""
        if self.use_api:
            try:
                resp = requests.post(API_URL, json=reading, timeout=4.0)
                if resp.status_code == 200:
                    return resp.json()
            except Exception:
                pass

        # Direct database write fallback
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            """INSERT INTO sensor_readings (timestamp, machine_id, temperature, vibration, pressure, current, rpm, ambient_temp, operating_mode, hours_since_maintenance)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (now_str, reading["machine_id"], reading["temperature"], reading["vibration"],
             reading["pressure"], reading["current"], reading["rpm"],
             reading.get("ambient_temp", 25.0), reading.get("operating_mode", "normal"),
             reading.get("hours_since_maintenance", 500.0))
        )
        conn.commit()
        conn.close()
        return {"status": "saved_to_db", "reading": reading}

    def run_stream(self, scenario: str = "normal", steps: int = 15, interval: float = 1.0):
        scenario_desc = SCENARIOS.get(scenario, scenario)
        print(f"\n========================================================")
        print(f"🏭 MECMF Industrial Stream Simulator (v3.0)")
        print(f"Asset: {self.machine_id} [{self.machine_type}]")
        print(f"Scenario: {scenario_desc}")
        print(f"Cycles: {steps} | Interval: {interval}s | Route: {'FastAPI REST' if self.use_api else 'Direct SQLite'}")
        print(f"========================================================\n")

        for i in range(steps):
            packet = self.generate_next_reading(scenario=scenario)
            result = self.emit_reading(packet)

            risk = result.get("risk_level", "Unknown") if isinstance(result, dict) else "Logged"
            prob = result.get("failure_probability", 0.0) if isinstance(result, dict) else 0.0
            rul = result.get("rul_hours", 0.0) if isinstance(result, dict) else 0.0
            anomaly = "⚠️ ANOMALY" if (isinstance(result, dict) and result.get("is_anomaly")) else "NOMINAL"

            delta_t = packet["temperature"] - packet["ambient_temp"]
            print(f"[Cycle {i+1:02d}/{steps:02d}] "
                  f"Vib: {packet['vibration']:5.3f} mm/s | "
                  f"Temp: {packet['temperature']:5.1f}°C (ΔT {delta_t:4.1f}°C) | "
                  f"Pres: {packet['pressure']:4.1f} bar | "
                  f"Risk: {risk:<8} (p={prob:.3f}) | "
                  f"RUL: {rul:5.1f}h | "
                  f"{anomaly}")
            time.sleep(interval)

        print("\n✅ Telemetry simulation stream completed successfully.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Machine Sensor Simulator (v3.0 Enterprise)")
    parser.add_argument("--machine", default="M17", help="Target Machine ID (e.g. M01 to M20)")
    parser.add_argument("--type", default="CNC", help="Machine Type (CNC, Pump, Compressor, Robotic Arm)")
    parser.add_argument(
        "--scenario",
        default="vibration_drift",
        choices=list(SCENARIOS.keys()),
        help="Operational scenario name"
    )
    parser.add_argument("--steps", type=int, default=15, help="Number of telemetry cycles")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between cycles")
    parser.add_argument("--no-api", action="store_true", help="Write directly to DB bypassing REST API")

    args = parser.parse_args()
    sim = MachineSensorSimulator(machine_id=args.machine, machine_type=args.type, use_api=not args.no_api)
    sim.run_stream(scenario=args.scenario, steps=args.steps, interval=args.interval)
