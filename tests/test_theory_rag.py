"""Unit tests for Industrial Machine Theory Analysis, RAG Ingestion, and Domain Guardrails."""
import pytest
from src.rag.theory_analyzer import MachineTheoryAnalyzer, validate_industrial_domain, GUARDRAIL_REFUSAL_MESSAGE
from src.rag.ingest import DocumentChunker, index_raw_theory
from src.rag.retrieve import KnowledgeRetriever
from src.rag.generate import GroundedGenerator
from src.agent.workflow import MaintenanceCopilotAgent

# 1. Test Domain Guardrail Validation
def test_domain_guardrail_approves_industrial_queries():
    valid_queries = [
        "Explain cavitation in centrifugal pumps",
        "What is the Arrhenius rule for electric motor stator insulation?",
        "How does a rotary screw compressor intermeshing rotor work?",
        "Why is machine M17 vibrating at 5.2 mm/s?",
        "What are the ISO 10816 vibration severity alarm limits for motors?",
        "Calculate slip for a 4-pole induction motor at 50Hz",
        "What causes hydraulic seal leakage in pumps?",
        "What is regenerative chatter stability lobe theory in CNC spindles?"
    ]
    for q in valid_queries:
        is_valid, msg = validate_industrial_domain(q)
        assert is_valid is True, f"Failed on valid industrial query: {q}"
        assert msg == ""

def test_domain_guardrail_rejects_off_topic_queries():
    invalid_queries = [
        "What is the best recipe for chocolate cake?",
        "Who is the most famous movie actor in Hollywood?",
        "Tell me a funny joke about politics",
        "Who won the cricket world cup?",
        "What is the weather like today in Paris?",
        "Write a romantic poem for my girlfriend"
    ]
    for q in invalid_queries:
        is_valid, msg = validate_industrial_domain(q)
        assert is_valid is False, f"Guardrail failed to block off-topic query: {q}"
        assert msg == GUARDRAIL_REFUSAL_MESSAGE

# 2. Test Theory Content Decomposition
def test_theory_analyzer_extraction():
    sample_theory = """# Technical Theory: Industrial Steam Turbine

## 1. Fundamental Principles & Governing Equations
Steam turbines convert thermodynamic thermal energy into shaft mechanical work.
Isentropic Expansion:
W_turbine = m_steam * (h_inlet - h_exhaust) * eta_isentropic

## 2. Component Architecture & Subsystems
- High-Pressure Rotor: Forged nickel-chromium rotor forging.
- Nozzle Diaphragm: Fixed guide vanes directing high-pressure steam at optimum blade angles.
- Labyrinth Gland Seals: Steam-purge labyrinth rings preventing vacuum air ingress.

## 3. Operating Parameters & Standard Thresholds
- Operating Speed: 3,000 RPM
- Inlet Steam Pressure: 60.0 bar
- Permissible Vibration RMS: < 2.8 mm/s

## 4. Theoretical Failure Modes & Physical Mechanisms
### Solid Particle Erosion (SPE)
Exfoliated boiler tube magnetite oxide scales impact turbine blade leading edges at supersonic velocity, causing blade profile thinning and loss of aerodynamic efficiency.

## 5. Maintenance & Diagnostic Guidelines
- Inspect blade root fir-tree attachments for fretting fatigue during 25,000-hour major overhaul."""

    decomp = MachineTheoryAnalyzer.analyze_theory_content(sample_theory, machine_name="Industrial Steam Turbine")
    assert decomp["machine_name"] == "Industrial Steam Turbine"
    assert len(decomp["principles"]) > 0
    assert len(decomp["subsystems"]) >= 2
    assert any("Rotor" in s["component"] or "Seal" in s["component"] for s in decomp["subsystems"])
    assert len(decomp["operating_parameters"]) >= 2
    assert len(decomp["failure_modes"]) >= 1
    assert any("Solid Particle Erosion" in fm["mode"] for fm in decomp["failure_modes"])
    assert len(decomp["governing_formulas"]) >= 1

# 3. Test Ingestion and Dynamic Indexing
def test_dynamic_theory_ingestion():
    custom_doc = """# Technical Theory: Precision Lathe Spindle

## 1. Principles
Converts motor torque into accurate chuck rotation for metal turning.

## 2. Components
- Headstock Bearings: Angular contact pair.
- Chuck Mechanism: 3-jaw hydraulic chuck."""

    chunks = index_raw_theory(
        text=custom_doc,
        doc_name="test_lathe_theory.txt",
        machine_name="Precision Lathe Spindle",
        category="theory",
        output_json="database/rag_index.json"
    )
    assert len(chunks) > 0
    assert chunks[0]["category"] == "theory"
    assert "Precision Lathe Spindle" in chunks[0]["applicable_machines"]

# 4. Test Theory Search in KnowledgeRetriever
def test_retriever_theory_search():
    retriever = KnowledgeRetriever()
    results = retriever.search_theory("centrifugal pump cavitation NPSH", top_k=2)
    assert len(results) > 0
    assert any("pump" in r["source_file"].lower() or "pump" in r["header"].lower() for r in results)

# 5. Test Grounded Generator Theory Response and Guardrails
def test_generator_theory_response():
    generator = GroundedGenerator()
    evidence = [
        {
            "source_file": "centrifugal_pump_theory.txt",
            "header": "Cavitation Dynamics & NPSH Starvation",
            "text": "Cavitation occurs when local pressure falls below fluid vapor pressure. Margin = NPSHa - NPSHr >= 0.8m.",
            "score": 0.88
        }
    ]
    # Valid theory query
    res = generator.generate_theory_response("Explain cavitation physics in pumps", evidence, machine_name="Pump")
    assert res["status"] in ["EVIDENCE_GROUNDED", "LLM_SYNTHESIZED"]
    assert "Cavitation" in res["answer"]
    assert res["guardrail_triggered"] is False

    # Guardrail blocked query
    blocked = generator.generate_theory_response("What is the recipe for beef lasagna?", evidence)
    assert blocked["status"] == "GUARDRAIL_BLOCKED"
    assert blocked["guardrail_triggered"] is True

# 6. Test AI Copilot Intent Routing
def test_copilot_chat_intent_routing():
    copilot = MaintenanceCopilotAgent()

    # Intent 1: Theory QA
    theory_reply = copilot.chat("Explain cavitation physics in centrifugal pumps")
    assert theory_reply["response_type"] == "theory_qa"
    assert "theory_response" in theory_reply
    assert len(theory_reply["theory_response"]) > 50

    # Intent 2: Telemetry Investigation
    investigate_reply = copilot.chat("Investigate M17 and check risk level")
    assert investigate_reply["response_type"] == "telemetry_investigation"
    assert investigate_reply["machine_id"] == "M17"
    assert "risk_level" in investigate_reply

    # Intent 3: Guardrail Refusal
    guardrail_reply = copilot.chat("Who is the president of France?")
    assert guardrail_reply["response_type"] == "guardrail_refusal"
    assert guardrail_reply["guardrail_triggered"] is True
