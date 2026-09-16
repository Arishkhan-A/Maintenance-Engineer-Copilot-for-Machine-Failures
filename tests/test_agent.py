"""Unit tests for Controlled AI Agent tools and workflow."""
import pytest
from src.agent.tools import MaintenanceAgentTools
from src.agent.workflow import MaintenanceCopilotAgent

@pytest.fixture
def agent_tools():
    return MaintenanceAgentTools()

def test_machine_status_tool(agent_tools):
    status = agent_tools.get_machine_status("M17")
    assert "machine_id" in status
    assert status["machine_id"] == "M17"
    assert "machine_type" in status

def test_sensor_history_tool(agent_tools):
    sensors = agent_tools.get_sensor_history("M17", limit=5)
    assert isinstance(sensors, list)

def test_search_manual_tool(agent_tools):
    results = agent_tools.search_manual("vibration bearing", filters={"category": "troubleshooting"})
    assert isinstance(results, list)
    assert len(results) > 0

def test_spare_parts_tool(agent_tools):
    spares = agent_tools.get_spare_parts("Bearing")
    assert isinstance(spares, list)
    assert any("Bearing" in s["component"] for s in spares)

def test_copilot_investigation_structure():
    agent = MaintenanceCopilotAgent()
    investigation = agent.investigate_machine("M17")
    assert investigation["machine_id"] == "M17"
    assert "risk_level" in investigation
    assert "rul_hours" in investigation
    assert "shap_explanation" in investigation
    assert "diagnostic_summary" in investigation
    assert "tool_trace" in investigation
    assert len(investigation["tool_trace"]) >= 5
