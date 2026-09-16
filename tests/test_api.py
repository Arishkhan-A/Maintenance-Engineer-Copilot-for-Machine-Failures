"""Unit and integration tests for FastAPI backend endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Maintenance Engineer Copilot REST Backend"
    assert data["status"] == "online"

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

def test_list_machines_endpoint():
    response = client.get("/machines")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(m["machine_id"] == "M17" for m in data)

def test_get_machine_detail():
    response = client.get("/machines/M17")
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "M17"

def test_get_machine_sensors():
    response = client.get("/machines/M17/sensors?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_spares():
    response = client.get("/spares")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_copilot_chat_endpoint():
    response = client.post("/copilot/chat", json={"message": "Why is M17 at high risk?", "machine_id": "M17"})
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "M17"
    assert "diagnostic_summary" in data
    assert "tool_trace" in data

def test_health_index_endpoint():
    response = client.get("/health-index/M17")
    assert response.status_code == 200
    data = response.json()
    assert "health_index" in data
    assert "health_score" in data["health_index"]
    assert "fault_diagnosis" in data

def test_work_order_endpoint():
    response = client.get("/workorders/M17")
    assert response.status_code == 200
    data = response.json()
    assert "work_order_id" in data
    assert "priority" in data
    assert "loto_protocols" in data

def test_roi_analytics_endpoint():
    response = client.get("/roi-analytics/M17")
    assert response.status_code == 200
    data = response.json()
    assert "financial_roi" in data
    assert "net_financial_savings" in data["financial_roi"]

def test_file_upload_and_conversion_endpoint():
    file_content = b'{"machine_id": "M17", "vibration": 3.4, "status": "Normal"}'
    response = client.post(
        "/files/upload",
        files={"file": ("test_payload.json", file_content, "application/json")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["row_count"] == 1
    assert "file_id" in data
    file_id = data["file_id"]

    # Test list endpoint
    list_res = client.get("/files/converted")
    assert list_res.status_code == 200
    assert any(f["file_id"] == file_id for f in list_res.json())

    # Test stats endpoint
    stats_res = client.get("/files/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["total_files"] >= 1

    # Test download endpoint
    dl_res = client.get(f"/files/download/{file_id}")
    assert dl_res.status_code == 200
    assert "text/csv" in dl_res.headers.get("content-type", "")
