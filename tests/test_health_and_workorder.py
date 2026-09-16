"""Unit tests for Machine Health Index (MHI), Financial ROI, and CMMS Work Order dispatch."""
import pytest
from src.models.health_index import compute_machine_health_index, calculate_financial_roi
from src.agent.work_order import generate_digital_work_order

def test_machine_health_index_nominal():
    res = compute_machine_health_index(
        failure_prob=0.05,
        is_anomaly=False,
        anomaly_score=0.15,
        vibration_rms=1.5,
        temperature_motor=55.0,
        ambient_temp=25.0,
        rul_hours=120.0
    )
    assert res["health_score"] >= 90.0
    assert res["category"] == "Optimal"
    assert "failure_risk_penalty" in res["penalty_breakdown"]

def test_machine_health_index_critical():
    res = compute_machine_health_index(
        failure_prob=0.92,
        is_anomaly=True,
        anomaly_score=-0.25,
        vibration_rms=6.8,
        temperature_motor=92.0,
        ambient_temp=24.0,
        rul_hours=12.0
    )
    assert res["health_score"] < 40.0
    assert res["category"] == "Critical Risk"
    assert res["indicator_color"] == "#ef4444"

def test_financial_roi_calculation():
    roi = calculate_financial_roi(estimated_repair_cost=4500.0, estimated_downtime_hours=10.0, is_high_risk=True)
    assert roi["unplanned_catastrophic_cost"] == 29500.0 # (10 * 2500) + 4500
    assert roi["proactive_intervention_cost"] == 950.0 # 500 + 450
    assert roi["net_financial_savings"] == 28550.0
    assert roi["roi_percentage"] > 2000.0

def test_digital_work_order_generation():
    spares = [{"component": "Bearing", "part_number": "SKF-6312-C3", "location": "Bin-12"}]
    roi = calculate_financial_roi(estimated_repair_cost=4000.0, estimated_downtime_hours=8.0)
    wo = generate_digital_work_order(
        machine_id="M17",
        machine_type="CNC",
        location="Shop Floor Bay 2",
        fault_diagnosis="Bearing Degradation",
        fault_confidence=0.94,
        risk_level="High",
        health_index=38.5,
        rul_hours=18.0,
        recommended_checks=["Inspect bearing radial play", "Replace SKF-6312-C3 bearing"],
        spares=spares,
        financial_roi=roi
    )
    assert "WO-" in wo["work_order_id"]
    assert "M17" in wo["work_order_id"]
    assert "P1" in wo["priority"] or "P2" in wo["priority"]
    assert len(wo["loto_protocols"]) > 0
    assert len(wo["reserved_spares"]) == 1
    assert "MAINTENANCE WORK ORDER" in wo["markdown_document"]
