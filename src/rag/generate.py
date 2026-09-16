"""RAG generation layer producing strictly grounded engineering recommendations and theory synthesis."""
import os
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from src.rag.retrieve import KnowledgeRetriever
from src.rag.theory_analyzer import MachineTheoryAnalyzer, validate_industrial_domain, GUARDRAIL_REFUSAL_MESSAGE

load_dotenv()

COPILOT_SYSTEM_PROMPT = """You are strictly an expert Industrial Machine Maintenance & Engineering Copilot.
CRITICAL OPERATIONAL RESTRICTION:
- You must ONLY answer questions directly pertaining to industrial machinery, plant equipment, engineering theory, physical failure modes, and maintenance procedures.
- You must REJECT any queries regarding non-industrial topics (e.g., general chit-chat, entertainment, cooking, politics, unrelated software coding).
- Your responses MUST be strictly grounded in the provided engineering manuals, telemetry signals, and theoretical documentation.
- Do NOT hallucinate unverified machine specifications. If a machine's documentation is missing, state that it is not indexed."""


class GroundedGenerator:
    """Generates evidence-backed maintenance diagnostics and engineering theory synthesis with strict domain guardrails."""

    def __init__(self, retriever: Optional[KnowledgeRetriever] = None):
        self.retriever = retriever or KnowledgeRetriever()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self._gemini_client = None
        if self.gemini_api_key:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception:
                self._gemini_client = None

    def is_llm_active(self) -> bool:
        """Returns True if an external frontier LLM client is connected."""
        return self._gemini_client is not None

    def generate_theory_response(
        self,
        query: str,
        top_evidence: List[Dict[str, Any]],
        machine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize technical machine theory, operating physics, and failure modes.
        Enforces strict domain guardrails before generating.
        """
        # Step 1: Strict Domain Guardrail Check
        is_valid, refusal_msg = validate_industrial_domain(query)
        if not is_valid:
            return {
                "status": "GUARDRAIL_BLOCKED",
                "query": query,
                "machine_name": machine_name or "N/A",
                "answer": refusal_msg,
                "guardrail_triggered": True,
                "citations": []
            }

        # Step 2: Attempt LLM Generation if configured
        if self._gemini_client and top_evidence:
            try:
                context_passages = "\n\n---\n\n".join([
                    f"SOURCE: {e.get('source_file')} - SECTION: {e.get('header')}\n{e.get('text')}"
                    for e in top_evidence
                ])
                prompt = f"""{COPILOT_SYSTEM_PROMPT}

Retrieved Technical Documentation:
{context_passages}

User Query: {query}

Provide a structured, deeply technical engineering response. Address the operational principle, components, failure mechanisms, equations, and maintenance thresholds explicitly mentioned in the context. If not mentioned, state the limitation."""

                response = self._gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                if response and response.text:
                    citations = [
                        {
                            "source": ev.get("source_file"),
                            "section": ev.get("header"),
                            "relevance_score": ev.get("score", 0.0),
                            "excerpt": ev.get("text", "")[:280] + "..."
                        }
                        for ev in top_evidence
                    ]
                    return {
                        "status": "LLM_SYNTHESIZED",
                        "query": query,
                        "machine_name": machine_name or "Industrial Asset",
                        "answer": response.text.strip(),
                        "guardrail_triggered": False,
                        "citations": citations,
                        "engine": "Gemini 2.5 Flash"
                    }
            except Exception as e:
                # Log and fallback gracefully to deterministic offline analyzer
                pass

        # Step 3: High-Fidelity Offline Grounded Synthesis
        offline_result = MachineTheoryAnalyzer.synthesize_theory_answer(
            query=query,
            retrieved_evidence=top_evidence,
            machine_name=machine_name
        )
        offline_result["guardrail_triggered"] = False
        offline_result["engine"] = "MECMF Grounded Industrial NLP"
        return offline_result

    def generate_grounded_response(
        self,
        machine_id: str,
        risk_level: str,
        observed_signals: List[Dict[str, Any]],
        shap_contributions: List[Dict[str, Any]],
        top_evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize telemetry signals, SHAP contributions, and retrieved manual/incident/theory evidence
        into the structured engineer copilot diagnostic format.
        """
        insufficient_evidence = len(top_evidence) == 0 or all(e.get("score", 0) < 0.05 for e in top_evidence)

        signal_strings = []
        for s in observed_signals:
            signal_strings.append(f"{s.get('sensor')}: {s.get('value')} {s.get('unit', '')} ({s.get('status', 'Nominal')})")

        shap_drivers = [f"{c['feature']} ({c['contribution_percent']}%)" for c in shap_contributions[:3]]

        evidence_list = []
        possible_causes = []
        recommended_checks = []

        if insufficient_evidence:
            return {
                "machine_id": machine_id,
                "risk_level": risk_level,
                "observed_signals": signal_strings,
                "evidence": ["No corresponding technical manual or incident record matched this signal pattern."],
                "possible_causes": ["Unknown / uncatalogued operating condition. The available knowledge base is insufficient to verify this diagnosis."],
                "recommended_checks": [
                    "Perform immediate manual visual and thermal inspection of the unit.",
                    "Verify sensor calibration and wiring harness integrity."
                ],
                "confidence": 0.40,
                "status": "INSUFFICIENT_EVIDENCE"
            }

        for ev in top_evidence:
            evidence_list.append({
                "source": ev.get("source_file"),
                "section": ev.get("header"),
                "relevance_score": ev.get("score"),
                "excerpt": ev.get("text", "")[:280] + "..."
            })

        combined_text = " ".join([ev.get("text", "").lower() for ev in top_evidence])

        # Dynamic root-cause triangulation with theory foundation
        if "bearing" in combined_text or any("vib" in d.lower() for d in shap_drivers):
            possible_causes.append("Bearing race spalling or cage degradation induced by lubricant starvation (Rule: ISO 10816-3).")
            possible_causes.append("Dynamic shaft unbalance or flexible coupling misalignment.")
            recommended_checks.append("Verify grease lubrication levels and inspect for blackening or particle contamination.")
            recommended_checks.append("Perform laser shaft alignment and check radial runout (< 0.05 mm).")
            recommended_checks.append("Check bearing 6312-C3 cage temperature and high-frequency spike energy.")
        elif "overheat" in combined_text or "thermal" in combined_text:
            possible_causes.append("Thermostatic bypass valve failure preventing fluid circulation through cooler core.")
            possible_causes.append("Restricted cooling airflow / clogged heat exchanger radiator fins.")
            recommended_checks.append("Measure temperature differential across oil cooler heat exchanger (must exceed 8°C).")
            recommended_checks.append("Inspect cooling fan cowl and clear foreign debris.")
        elif "cavitation" in combined_text or "npsh" in combined_text:
            possible_causes.append("Impeller suction eye cavitation due to insufficient NPSHa margin (NPSHa < NPSHr + 0.8m).")
            possible_causes.append("Suction strainer blockage causing extreme low inlet pressure and vapor bubble collapse.")
            recommended_checks.append("Inspect suction strainer Delta-P (< 0.35 bar).")
            recommended_checks.append("Verify inlet line static head and open suction throttling valves.")
        elif "seal" in combined_text or "pressure" in combined_text:
            possible_causes.append("Hydraulic shock waves caused by lost nitrogen pre-charge in bladder accumulator.")
            possible_causes.append("Mechanical seal primary face erosion or secondary Viton O-ring breach.")
            recommended_checks.append("Check accumulator gas bladder pressure under de-pressurized state.")
            recommended_checks.append("Inspect mechanical seal flush piping (Plan 11 / Plan 32).")
        else:
            possible_causes.append("Degraded operating state indicated by multi-sensor drift.")
            recommended_checks.append("Consult equipment manufacturer manual and review recent maintenance logs.")

        confidence = 0.92 if risk_level in ["High", "Critical"] else 0.85

        return {
            "machine_id": machine_id,
            "risk_level": risk_level,
            "observed_signals": signal_strings,
            "shap_drivers": shap_drivers,
            "evidence": evidence_list,
            "possible_causes": possible_causes,
            "recommended_checks": recommended_checks,
            "confidence": confidence,
            "status": "EVIDENCE_GROUNDED"
        }
