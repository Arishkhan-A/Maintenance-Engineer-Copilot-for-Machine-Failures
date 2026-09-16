# Industrial Machine Predictive Maintenance Dataset Dictionary

## Overview
- **Dataset File**: `data/raw/machine_predictive_maintenance.csv`
- **Total Records**: 12,000 observations
- **Target Population**: 20 industrial machines (M01 - M20) across 3 machine classes.
- **Sampling Frequency**: 10-minute sensor telemetry intervals.

## Column Definitions

| Column Name | Data Type | Physical Unit | Description & Operational Range |
| :--- | :--- | :--- | :--- |
| `timestamp` | Datetime (ISO) | YYYY-MM-DD HH:MM:SS | Continuous telemetry observation time. |
| `machine_id` | String / Categorical | ID (M01 - M20) | Unique identifier for the monitored industrial machine. |
| `machine_type` | Categorical | Class Name | Equipment classification: `CNC_Milling`, `Hydraulic_Pump`, `Screw_Compressor`. |
| `temperature` | Float | °C (Celsius) | Main drive bearing/casing temperature (Nominal: 50-80°C, Critical: > 85°C). |
| `vibration` | Float | mm/s RMS | Broadband vibration velocity (Nominal: 1.5-2.8 mm/s, Critical: > 4.5 mm/s). |
| `pressure` | Float | bar (Gauge) | Hydraulic/pneumatic delivery pressure (Nominal: 6-32 bar dependent on machine type). |
| `current` | Float | Amperes (A) | Electric motor RMS current draw (Nominal: 30-55 A, Overload: > 60 A). |
| `rpm` | Float | Revs per Minute | Shaft rotational speed (Nominal: 1450-2950 RPM). |
| `load` | Float | Percentage (%) | Operational mechanical capacity (Nominal: 40-85%). |
| `operating_hours` | Float | Hours (h) | Cumulative hours run since commissioning or previous overhaul. |
| `failure_within_24h` | Integer Binary | 0 or 1 | **Primary Prediction Target**: 1 if mechanical or electrical failure occurs within 24h. |
| `failure_type` | Categorical | Text Mode | Specific failure classification (`Bearing_Wear`, `Heat_Dissipation`, `Overstrain`, `Power_Failure`, `None`). |
| `rul` | Float | Hours (h) | **Secondary Target**: Remaining Useful Life until next breakdown. |

## Data Lineage & Leakage Prevention Rules
1. **No Future Leakage**: No rolling statistics or aggregations use future lookahead windows.
2. **Temporal Split Order**: Machine records must strictly maintain sequential time ordering during train/val/test splits.
