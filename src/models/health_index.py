"""
Enterprise Machine Health Index (MHI) & Financial ROI Analytics Engine.
Quantifies asset health on a continuous 0-100% scale and projects downtime financial savings.
"""

from typing import Dict, Any, List
import numpy as np

# Industrial plant financial parameters
HOURLY_PRODUCTION_LOSS_RATE = 2500.0 # $2,500 / hour of unplanned downtime
PLANNED_MAINTENANCE_LABOR_COST = 500.0 # Standard 2-hour scheduled window
AVERAGE_SPARE_PART_COST = 450.0

def compute_machine_health_index(
    failure_prob: float,
    is_anomaly: bool,
    anomaly_score: float,
    vibration_rms: float,
    temperature_motor: float,
    ambient_temp: float = 25.0,
    rul_hours: float = 100.0
) -> Dict[str, Any]:
    """
    Compute 0-100% composite Machine Health Index (MHI).
    Higher is healthier; <40% triggers immediate engineering intervention.
    """
    # 1. Base score from failure probability (0.0 to 1.0) -> weight 35%
    prob_penalty = failure_prob * 35.0

    # 2. Vibration penalty (ISO 10816: normal < 2.8, alert > 4.5, trip > 7.1) -> weight 25%
    if vibration_rms <= 1.8:
        vib_penalty = 0.0
    elif vibration_rms <= 4.5:
        vib_penalty = ((vibration_rms - 1.8) / (4.5 - 1.8)) * 15.0
    else:
        vib_penalty = 15.0 + min(10.0, ((vibration_rms - 4.5) / 2.6) * 10.0)

    # 3. Thermal differential penalty (motor - ambient) -> weight 20%
    delta_t = max(0.0, temperature_motor - ambient_temp)
    if delta_t <= 35.0:
        thermal_penalty = 0.0
    elif delta_t <= 55.0:
        thermal_penalty = ((delta_t - 35.0) / 20.0) * 12.0
    else:
        thermal_penalty = 12.0 + min(8.0, ((delta_t - 55.0) / 25.0) * 8.0)

    # 4. Anomaly penalty -> weight 10%
    anom_penalty = 10.0 if is_anomaly else max(0.0, -anomaly_score * 50.0)

    # 5. RUL degradation factor -> weight 10%
    if rul_hours >= 80.0:
        rul_penalty = 0.0
    else:
        rul_penalty = ((80.0 - max(0.0, rul_hours)) / 80.0) * 10.0

    total_penalty = prob_penalty + vib_penalty + thermal_penalty + anom_penalty + rul_penalty
    raw_health = max(0.0, min(100.0, 100.0 - total_penalty))
    health_score = round(raw_health, 1)

    if health_score >= 85.0:
        category = "Optimal"
        color = "#10b981" # Green
    elif health_score >= 65.0:
        category = "Acceptable"
        color = "#3b82f6" # Blue
    elif health_score >= 40.0:
        category = "Degraded"
        color = "#f59e0b" # Orange
    else:
        category = "Critical Risk"
        color = "#ef4444" # Red

    return {
        "health_score": health_score,
        "category": category,
        "indicator_color": color,
        "penalty_breakdown": {
            "failure_risk_penalty": round(prob_penalty, 1),
            "vibration_kinematic_penalty": round(vib_penalty, 1),
            "thermal_differential_penalty": round(thermal_penalty, 1),
            "anomaly_penalty": round(anom_penalty, 1),
            "rul_depletion_penalty": round(rul_penalty, 1)
        }
    }

def calculate_financial_roi(
    estimated_repair_cost: float,
    estimated_downtime_hours: float = 12.0,
    is_high_risk: bool = True
) -> Dict[str, Any]:
    """
    Quantifies the exact dollar savings achieved by proactive maintenance intervention
    versus allowing catastrophic machine failure during active production.
    """
    # Catastrophic failure consequences
    downtime_cost = estimated_downtime_hours * HOURLY_PRODUCTION_LOSS_RATE
    emergency_repair_cost = max(2500.0, estimated_repair_cost)
    total_unplanned_cost = downtime_cost + emergency_repair_cost

    # Proactive planned maintenance intervention
    proactive_cost = PLANNED_MAINTENANCE_LABOR_COST + AVERAGE_SPARE_PART_COST

    # Net ROI
    net_savings = max(0.0, total_unplanned_cost - proactive_cost)
    roi_percentage = round((net_savings / max(1.0, proactive_cost)) * 100.0, 1)

    return {
        "unplanned_catastrophic_cost": round(total_unplanned_cost, 2),
        "unplanned_downtime_loss": round(downtime_cost, 2),
        "emergency_repair_cost": round(emergency_repair_cost, 2),
        "proactive_intervention_cost": round(proactive_cost, 2),
        "net_financial_savings": round(net_savings, 2),
        "roi_percentage": roi_percentage,
        "hourly_downtime_rate": HOURLY_PRODUCTION_LOSS_RATE
    }
