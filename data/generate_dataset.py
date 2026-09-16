"""
Dataset Generator for Industrial Machine Predictive Maintenance.
Generates realistic multi-sensor telemetry with temporal degradation,
failure modes, and RUL targets adhering to Kaggle industrial PM standards.
"""

import csv
import math
import os
import random
from datetime import datetime, timedelta

def generate_telemetry_dataset(output_path: str, num_records_per_machine: int = 600):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)

    machines = [
        {"id": f"M{i:02d}", "type": "CNC_Milling" if i <= 7 else ("Hydraulic_Pump" if i <= 14 else "Screw_Compressor")}
        for i in range(1, 21)
    ]

    fieldnames = [
        "timestamp",
        "machine_id",
        "machine_type",
        "temperature",
        "vibration",
        "pressure",
        "current",
        "rpm",
        "load",
        "operating_hours",
        "failure_within_24h",
        "failure_type",
        "rul"
    ]

    base_time = datetime(2024, 1, 1, 0, 0, 0)
    all_rows = []

    for m in machines:
        m_id = m["id"]
        m_type = m["type"]
        current_time = base_time + timedelta(hours=random.randint(0, 100))

        # Base nominal operating profiles per machine type
        if m_type == "CNC_Milling":
            base_temp = 55.0 + random.uniform(-3, 3)
            base_vib = 1.8 + random.uniform(-0.2, 0.2)
            base_pres = 6.0 + random.uniform(-0.5, 0.5)
            base_curr = 32.0 + random.uniform(-2, 2)
            base_rpm = 2400.0 + random.uniform(-50, 50)
            base_load = 65.0
        elif m_type == "Hydraulic_Pump":
            base_temp = 60.0 + random.uniform(-3, 3)
            base_vib = 2.2 + random.uniform(-0.2, 0.2)
            base_pres = 30.0 + random.uniform(-1, 1)
            base_curr = 45.0 + random.uniform(-2, 2)
            base_rpm = 1500.0 + random.uniform(-30, 30)
            base_load = 75.0
        else: # Screw_Compressor
            base_temp = 78.0 + random.uniform(-3, 3)
            base_vib = 2.5 + random.uniform(-0.2, 0.2)
            base_pres = 9.5 + random.uniform(-0.4, 0.4)
            base_curr = 52.0 + random.uniform(-3, 3)
            base_rpm = 2950.0 + random.uniform(-40, 40)
            base_load = 80.0

        op_hours = random.uniform(200.0, 3500.0)

        # Plan 2-3 degradation and failure episodes for this machine
        # Machine M17 specifically has a highlighted critical bearing wear episode
        num_episodes = 2 if m_id != "M17" else 3
        episode_lengths = num_records_per_machine // num_episodes

        for ep in range(num_episodes):
            failure_type_choice = random.choice([
                "Bearing_Wear", "Heat_Dissipation", "Overstrain", "Power_Failure"
            ]) if m_id != "M17" else "Bearing_Wear"

            fail_point = episode_lengths - random.randint(10, 25)
            degrade_start = fail_point - random.randint(30, 50)

            for step in range(episode_lengths):
                current_time += timedelta(minutes=10) # 10 min sampling rate
                op_hours += 10.0 / 60.0

                # Normal dynamic noise & cyclic shift
                noise_t = random.gauss(0, 0.8)
                noise_v = random.gauss(0, 0.12)
                noise_p = random.gauss(0, 0.2)
                noise_c = random.gauss(0, 0.9)
                noise_rpm = random.gauss(0, 15)
                load_shift = math.sin(step / 15.0) * 8.0

                temp = base_temp + noise_t + (load_shift * 0.2)
                vib = base_vib + noise_v + (load_shift * 0.01)
                pres = base_pres + noise_p + (load_shift * 0.05)
                curr = base_curr + noise_c + (load_shift * 0.15)
                rpm = base_rpm + noise_rpm
                load = max(30.0, min(98.0, base_load + load_shift))

                # Degradation progression
                is_failing_soon = 0
                active_fail_type = "None"
                rul = max(1.0, (fail_point - step) * (10.0 / 60.0))

                if step >= degrade_start:
                    progress = (step - degrade_start) / max(1, (fail_point - degrade_start))
                    progress = min(1.3, progress)

                    if failure_type_choice == "Bearing_Wear":
                        vib += progress * 4.5 # vibration spikes severely
                        temp += progress * 18.0
                        curr += progress * 8.0
                    elif failure_type_choice == "Heat_Dissipation":
                        temp += progress * 28.0 # temperature surges
                        curr += progress * 6.0
                        vib += progress * 1.2
                    elif failure_type_choice == "Overstrain":
                        curr += progress * 22.0 # high current draw
                        load = min(100.0, load + progress * 20.0)
                        vib += progress * 2.8
                    elif failure_type_choice == "Power_Failure":
                        curr += (math.sin(step) * 15.0) * progress
                        pres -= progress * (base_pres * 0.4)

                    if step >= (fail_point - 144): # within 24 hours (144 * 10min = 24h)
                        is_failing_soon = 1
                        active_fail_type = failure_type_choice

                # Clamp negative RUL or capped
                if step >= fail_point:
                    # Machine failure occurs, then serviced & recovered
                    rul = 0.0
                    is_failing_soon = 1
                    active_fail_type = failure_type_choice
                    # Post maintenance reset
                    if step == fail_point + 1:
                        op_hours = 10.0 # reset maintenance interval

                all_rows.append({
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "machine_id": m_id,
                    "machine_type": m_type,
                    "temperature": round(temp, 2),
                    "vibration": round(max(0.2, vib), 3),
                    "pressure": round(max(0.5, pres), 2),
                    "current": round(max(5.0, curr), 2),
                    "rpm": round(rpm, 1),
                    "load": round(load, 1),
                    "operating_hours": round(op_hours, 1),
                    "failure_within_24h": is_failing_soon,
                    "failure_type": active_fail_type,
                    "rul": round(rul, 1)
                })

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Successfully generated {len(all_rows)} telemetry records in {output_path}")

if __name__ == "__main__":
    generate_telemetry_dataset("data/raw/machine_predictive_maintenance.csv", num_records_per_machine=600)
