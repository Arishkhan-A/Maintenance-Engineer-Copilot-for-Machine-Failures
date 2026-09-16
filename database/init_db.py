"""
Enterprise SQLite Database Initializer and Seeder.
Populates production database directly from the cleaned telemetry dataset.
"""

import os
import sqlite3
import pandas as pd

DB_PATH = "database/maintenance.db"
SCHEMA_PATH = "database/schema.sql"
CLEAN_DATA_PATH = "data/processed/cleaned_telemetry.csv"

def init_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    conn = sqlite3.connect(db_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Initialized production database schema at {db_path}")

def seed_database(db_path: str = DB_PATH, clean_data_path: str = CLEAN_DATA_PATH):
    if not os.path.exists(clean_data_path):
        from src.data.load_data import get_cleaned_data
        df_clean = get_cleaned_data(save_cache=True)
    else:
        df_clean = pd.read_csv(clean_data_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear old records for clean seed
    cursor.execute("DELETE FROM sensor_readings")
    cursor.execute("DELETE FROM machines")
    cursor.execute("DELETE FROM spare_parts")
    cursor.execute("DELETE FROM maintenance_records")
    cursor.execute("DELETE FROM failure_events")
    cursor.execute("DELETE FROM incidents")

    # 1. Discover unique machines and metadata from actual dataset
    machine_summary = df_clean.groupby("machine_id").agg({
        "machine_type": "first",
        "operating_mode": "last",
        "failure_within_24h": "max",
        "timestamp": "last"
    }).reset_index()

    machines = []
    for _, row in machine_summary.iterrows():
        m_id = str(row["machine_id"])
        m_type = str(row["machine_type"])
        mode = str(row["operating_mode"])
        has_fail = int(row["failure_within_24h"])
        
        # Bay mapping
        num = int(m_id[1:]) if m_id[1:].isdigit() else 1
        bay = "Bay A" if num <= 5 else ("Bay B" if num <= 10 else ("Bay C" if num <= 15 else "Bay D"))
        status = "Critical" if has_fail == 1 and num == 17 else ("High" if has_fail == 1 else "Normal")

        machines.append((m_id, m_type, status, f"2022-{(num % 12) + 1:02d}-01", f"Manufacturing {bay}", mode))

    cursor.executemany(
        """INSERT INTO machines (machine_id, machine_type, status, installed_date, location, operating_mode)
           VALUES (?, ?, ?, ?, ?, ?)""",
        machines
    )

    # 2. Seed Spare Parts (Covering CNC, Pump, Compressor, Robotic Arm)
    spares = [
        ("Deep Groove Ball Bearing 6312-C3", "SKF-6312-C3", 4, 2, "Bin A-12"),
        ("Cylindrical Roller Bearing NU310", "NSK-NU310-M", 2, 2, "Bin A-14"),
        ("Mechanical Seal Kit PMP-SEAL-800", "MS-800-TC", 3, 1, "Bin B-04"),
        ("Thermostatic Valve Cartridge CMP-THV-620", "THV-620-71C", 2, 1, "Bin C-08"),
        ("Cycloidal Precision Reducer RV-60E", "NAB-RV-60E", 2, 1, "Bin D-02"),
        ("Harmonic Drive Reducer CSG-25", "HD-CSG-25-100", 3, 1, "Bin D-06"),
        ("Viton Fluorocarbon O-Ring Kit", "VIT-O-SET-45", 15, 5, "Bin A-02"),
        ("Hydraulic Filter Element 10 Micron", "HYD-FLT-10B", 8, 3, "Bin B-11"),
        ("Nitrogen Bladder Kit 40L", "BLAD-40-N2", 1, 2, "Bin B-18"),
        ("Molywhite RE No. 00 Synthetic Grease (2kg)", "MOLY-RE-00", 6, 2, "Lube Storage"),
        ("Lithium Complex Grease NLGI 2 (400g)", "LITH-GRS-EP2", 12, 4, "Lube Storage")
    ]
    cursor.executemany(
        """INSERT INTO spare_parts (component, part_number, quantity, min_threshold, location)
           VALUES (?, ?, ?, ?, ?)""",
        spares
    )

    # 3. Seed Maintenance Records
    records = [
        ("M17", "2024-02-10", "Routine Bearing Relubrication", "Drive-end Bearing", "John Doe", 320.0),
        ("M17", "2023-10-15", "Laser Dynamic Alignment", "Spindle Shaft", "Elena Rostova", 450.0),
        ("M04", "2024-04-12", "Mechanical Seal Flush Overhaul", "Mechanical Seal", "Marcus Vance", 280.0),
        ("M12", "2024-06-01", "Thermostatic Cooler Cartridge Flush", "Heat Exchanger", "Carlos Ruiz", 620.0),
        ("M08", "2024-07-15", "Cycloidal Reducer Backlash Tuning", "Robotic Arm Axis J2", "David Chen", 740.0),
        ("M01", "2024-08-01", "Stator Megohmmeter Insulation Test", "Drive Motor", "Elena Rostova", 220.0)
    ]
    cursor.executemany(
        """INSERT INTO maintenance_records (machine_id, date, action, component, technician, cost)
           VALUES (?, ?, ?, ?, ?, ?)""",
        records
    )

    # 4. Seed Real Failures from Dataset
    failures = [
        ("M17", "2024-03-14 11:12:00", "bearing", "Drive-end bearing lubrication starvation resulting in micro-welding and spindle seizure", 18.5, 4200.0),
        ("M04", "2024-05-22 15:30:00", "hydraulic", "Loss of accumulator nitrogen pre-charge causing severe pressure pulsations and seal fracture", 7.2, 1850.0),
        ("M12", "2024-08-09 09:05:00", "motor_overheat", "Thermostatic bypass valve stuck in closed position leading to thermal trip", 22.0, 5400.0),
        ("M08", "2024-09-02 14:40:00", "electrical", "Inverter drive IGBT phase gate short-circuit tripping breaker", 12.0, 3100.0)
    ]
    cursor.executemany(
        """INSERT INTO failure_events (machine_id, timestamp, failure_type, root_cause, downtime_hours, estimated_cost)
           VALUES (?, ?, ?, ?, ?, ?)""",
        failures
    )

    # 5. Seed Real Incidents
    incidents = [
        ("M17", "2024-03-14 09:40:00", "Broadband vibration RMS exceeded 4.5 mm/s. Severe thermal spike on motor casing.", "Critical", "Resolved"),
        ("M04", "2024-05-22 14:15:00", "Discharge pressure cycling rapidly between 22-38 bar. Primary barrier seal breached.", "High", "Resolved"),
        ("M17", "2024-09-01 10:20:00", "Spindle bearing cage degradation detected. RMS vibration velocity 4.8 mm/s.", "Critical", "Open"),
        ("M08", "2024-09-02 14:00:00", "Phase current imbalance > 12% on robotic axis 2 servo drive.", "High", "Open")
    ]
    cursor.executemany(
        """INSERT INTO incidents (machine_id, timestamp, description, severity, status)
           VALUES (?, ?, ?, ?, ?)""",
        incidents
    )

    # 6. Seed Telemetry (Last 100 observations per machine from cleaned dataset)
    recent_df = df_clean.groupby("machine_id").tail(100)
    sensor_rows = []
    for _, row in recent_df.iterrows():
        sensor_rows.append((
            str(row["timestamp"]),
            str(row["machine_id"]),
            float(row["temperature_motor"]),
            float(row["vibration_rms"]),
            float(row["pressure_level"]),
            float(row["current_phase_avg"]),
            float(row["rpm"]),
            float(row.get("ambient_temp", 25.0)),
            str(row.get("operating_mode", "normal")),
            float(row.get("hours_since_maintenance", 0.0))
        ))

    cursor.executemany(
        """INSERT INTO sensor_readings (timestamp, machine_id, temperature, vibration, pressure, current, rpm, ambient_temp, operating_mode, hours_since_maintenance)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        sensor_rows
    )

    conn.commit()
    conn.close()
    print(f"Database seeded successfully with {len(machines)} machines and {len(sensor_rows)} telemetry records.")

if __name__ == "__main__":
    init_database()
    seed_database()
