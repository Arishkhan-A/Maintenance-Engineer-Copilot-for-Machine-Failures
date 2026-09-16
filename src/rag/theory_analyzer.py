"""
Machine Theory Analyzer and Strict Industrial Domain Guardrail Engine.
Extracts operational principles, components, failure mechanisms, and formulas
from machine theory content and enforces strict scope restrictions.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Domain keywords for industrial equipment, engineering mechanics, and plant maintenance
INDUSTRIAL_DOMAIN_KEYWORDS = {
    # Machines and Equipment
    "machine", "motor", "pump", "compressor", "cnc", "robot", "robotic", "spindle",
    "turbine", "boiler", "chiller", "conveyor", "gearbox", "actuator", "generator",
    "heat exchanger", "valve", "fan", "blower", "piping", "accumulator", "press",
    "lathe", "transformer", "drives", "vfd", "inverter", "stator", "rotor", "impeller",
    # Mechanical & Electrical Components
    "bearing", "seal", "shaft", "coupling", "gasket", "piston", "vane", "gear",
    "housing", "casing", "bushing", "flange", "drawbar", "harness", "winding",
    "insulation", "cycloidal", "harmonic", "wire", "cable", "nozzle", "volute",
    # Physical Quantities & Telemetry
    "vibration", "temperature", "pressure", "current", "voltage", "rpm", "speed",
    "torque", "flow", "thermal", "delta-t", "heat", "acoustic", "frequency", "harmonics",
    "amplitude", "velocity", "acceleration", "megohm", "resistance", "rms",
    # Faults & Failure Mechanisms
    "failure", "fault", "cavitation", "spalling", "misalignment", "unbalance",
    "overheat", "overload", "leakage", "wear", "fatigue", "corrosion", "erosion",
    "chatter", "resonance", "flashover", "short circuit", "trip", "alarm", "anomaly",
    "breakdown", "degradation", "damage", "blowhole", "backlash", "looseness",
    # Maintenance & Operations
    "maintenance", "pm", "rca", "work order", "cmms", "sap", "maximo", "lubrication",
    "grease", "oil", "filter", "alignment", "balancing", "inspection", "overhaul",
    "rul", "health index", "iso", "nema", "api", "standard", "threshold", "spec",
    # Engineering Theory & Physics
    "theory", "principle", "physics", "bernoulli", "faraday", "isentropic", "slip",
    "kinematics", "dynamics", "equation", "formula", "arrhenius", "npsh", "head",
    "efficiency", "bep", "affinity", "jacobian", "compliance", "frf", "mechanics"
}

OUT_OF_SCOPE_TRIGGERS = {
    "recipe", "cook", "movie", "film", "song", "lyrics", "politics", "president",
    "election", "cricket", "football", "celebrity", "actor", "joke", "poem", "story",
    "game", "dating", "horoscope", "astrology", "crypto", "bitcoin", "weather today",
    "restaurant", "travel", "flight", "shopping", "clothes", "fashion"
}

GUARDRAIL_REFUSAL_MESSAGE = (
    "⚠️ **Operational Domain Guardrail**: I am strictly configured as an **Industrial Machine "
    "Maintenance & Theory Copilot**. I can only analyze and answer questions related to industrial "
    "machinery, equipment engineering theory, plant telemetry, and maintenance diagnostics.\n\n"
    "Please ask a question regarding machine mechanics, operating principles, failure modes, "
    "or maintenance procedures."
)


def validate_industrial_domain(query: str) -> Tuple[bool, str]:
    """
    Strict deterministic domain guardrail.
    Returns (True, "") if query is relevant to industrial machinery.
    Returns (False, refusal_message) if query is out of scope.
    """
    clean_q = query.lower().strip()
    words = set(re.findall(r"\b[a-z0-9\-_]{2,}\b", clean_q))

    # Check for explicit out-of-scope triggers
    if any(trigger in clean_q for trigger in OUT_OF_SCOPE_TRIGGERS):
        return False, GUARDRAIL_REFUSAL_MESSAGE

    # Allow system commands or generic copilot greetings with industrial context
    if clean_q in ["hi", "hello", "help", "who are you", "what can you do"]:
        return True, ""

    # Check if query matches machine IDs (M01 to M20)
    if re.search(r"\b(m\d{1,2}|machine\s*\d{1,2})\b", clean_q):
        return True, ""

    # Check presence of any industrial domain keyword
    matched_kws = words.intersection(INDUSTRIAL_DOMAIN_KEYWORDS)
    if len(matched_kws) > 0:
        return True, ""

    # If query contains any word matching theory patterns
    theory_patterns = [
        r"\bhow (does|do|can)\b", r"\bwhat is\b", r"\bexplain\b",
        r"\bwhy (does|is)\b", r"\bformula\b", r"\bstandard\b"
    ]
    has_question_pattern = any(re.search(p, clean_q) for p in theory_patterns)

    # If it is a generic question without any industrial/machine context, reject
    if has_question_pattern:
        # Require at least one industrial context word
        return False, GUARDRAIL_REFUSAL_MESSAGE

    # Short unrecognized query
    if len(words) <= 3 and not matched_kws:
        return False, GUARDRAIL_REFUSAL_MESSAGE

    # Default to rejecting ambiguous queries to strictly maintain guardrail
    return False, GUARDRAIL_REFUSAL_MESSAGE


class MachineTheoryAnalyzer:
    """Extracts semantic structure, engineering principles, and failure dynamics from machine theory text."""

    @staticmethod
    def analyze_theory_content(text: str, machine_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Deep structural decomposition of technical theory content.
        Extracts principles, subsystems, parameters, failure modes, and formulas.
        """
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        
        # 1. Infer Machine Name
        extracted_name = machine_name
        if not extracted_name:
            for ln in lines[:5]:
                if ln.startswith("#"):
                    extracted_name = ln.replace("#", "").strip()
                    break
            if not extracted_name:
                extracted_name = "Industrial Machinery"

        # 2. Extract Sections (split on top-level # or ## headers to keep ### subheaders intact)
        sections = re.split(r"(?m)^(?=#{1,2}\s+)", text)
        
        principles: List[str] = []
        subsystems: List[Dict[str, str]] = []
        parameters: List[str] = []
        failure_modes: List[Dict[str, str]] = []
        formulas: List[str] = []
        maintenance_guidelines: List[str] = []

        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            sec_lower = sec_clean.lower()
            sec_lines = sec_clean.splitlines()
            header = sec_lines[0].replace("#", "").strip() if sec_lines else ""
            content_body = "\n".join(sec_lines[1:]).strip() if len(sec_lines) > 1 else ""

            # Check for principles / governing physics
            if any(k in sec_lower for k in ["principle", "governing", "physics", "equation", "conversion", "dynamics"]):
                for ln in sec_lines[1:]:
                    if ln.startswith("-") or ln.startswith("*"):
                        principles.append(ln.lstrip("-* ").strip())
                    elif any(op in ln for op in ["=", "/", "*", "^", "+"]) and len(ln) > 4:
                        formulas.append(ln.strip())
                    elif len(ln) > 30 and not ln.startswith("#"):
                        principles.append(ln.strip())

            # Check for component architecture / subsystems
            if any(k in sec_lower for k in ["component", "architecture", "subsystem", "assembly"]):
                for ln in sec_lines[1:]:
                    if ":" in ln and (ln.startswith("-") or ln.startswith("*") or ln[0].isdigit()):
                        parts = ln.lstrip("-*0123456789. ").split(":", 1)
                        subsystems.append({
                            "component": parts[0].strip(),
                            "details": parts[1].strip() if len(parts) > 1 else ""
                        })
                    elif ln.startswith("-") or ln.startswith("*"):
                        subsystems.append({"component": "Part", "details": ln.lstrip("-* ").strip()})

            # Check for operating parameters / thresholds
            if any(k in sec_lower for k in ["parameter", "threshold", "limit", "specification"]):
                for ln in sec_lines[1:]:
                    if (ln.startswith("-") or ln.startswith("*")) or any(u in ln for u in ["RPM", "°C", "bar", "mm/s", "kW", "V", "Hz", "A"]):
                        clean_ln = ln.lstrip("-* ").strip()
                        if clean_ln and not clean_ln.startswith("#"):
                            parameters.append(clean_ln)

            # Check for failure modes / physical mechanisms
            if any(k in sec_lower for k in ["failure", "damage", "fault", "mechanism", "wear", "breakdown", "erosion", "fatigue", "crack", "spalling"]):
                # Check for subheaders (###)
                sub_chunks = re.split(r"(?m)^(?=###\s+)", sec_clean)
                for sc in sub_chunks:
                    sc_lines = sc.strip().splitlines()
                    if not sc_lines:
                        continue
                    if sc_lines[0].startswith("###"):
                        title = sc_lines[0].replace("###", "").strip()
                        desc = " ".join([l.strip() for l in sc_lines[1:] if l.strip()])
                        failure_modes.append({"mode": title, "mechanism": desc})
                    elif not sc_lines[0].startswith("##") and not sc_lines[0].startswith("#"):
                        for l in sc_lines:
                            if l.startswith("-") or l.startswith("*"):
                                failure_modes.append({"mode": "Observed Mode", "mechanism": l.lstrip("-* ").strip()})

            # Check for maintenance guidelines
            if any(k in sec_lower for k in ["maintenance", "procedure", "guideline", "inspection", "overhaul"]):
                for ln in sec_lines[1:]:
                    if ln.startswith("-") or ln.startswith("*"):
                        maintenance_guidelines.append(ln.lstrip("-* ").strip())

        # Fallback if specific sections were not formatted with headers
        if not formulas:
            for ln in lines:
                if any(sym in ln for sym in ["P_1", "V_1", "N_sync", "s =", "b_lim", "Delta_T", "T_em", "Q_1"]):
                    formulas.append(ln.strip())

        if not principles and lines:
            principles = [l for l in lines[1:6] if not l.startswith("#")]

        # Produce executive engineering summary
        summary = (
            f"Engineering theoretical foundation for **{extracted_name}**. "
            f"Identified {len(principles)} operating principles, {len(subsystems)} critical subsystems, "
            f"{len(parameters)} operating threshold rules, and {len(failure_modes)} documented physical failure mechanisms."
        )

        return {
            "machine_name": extracted_name,
            "principles": principles[:8],
            "subsystems": subsystems[:10],
            "operating_parameters": parameters[:10],
            "failure_modes": failure_modes[:6],
            "governing_formulas": list(set(formulas))[:6],
            "maintenance_guidelines": maintenance_guidelines[:8],
            "executive_summary": summary
        }

    @staticmethod
    def synthesize_theory_answer(
        query: str,
        retrieved_evidence: List[Dict[str, Any]],
        machine_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates an evidence-grounded engineering technical answer from retrieved theory passages.
        Operates fully offline with zero external API dependencies.
        """
        if not retrieved_evidence:
            return {
                "query": query,
                "answer": (
                    "No technical theory manual matched your query in the current knowledge base. "
                    "You can upload or paste the machine's engineering theory document in the "
                    "**Machine Theory & RAG Knowledge** studio to index it immediately."
                ),
                "citations": [],
                "principles_referenced": [],
                "operating_limits": [],
                "status": "NO_EVIDENCE"
            }

        citations = []
        all_text_blocks = []
        for ev in retrieved_evidence:
            source = ev.get("source_file", "Technical Manual")
            header = ev.get("header", "Theory Section")
            text = ev.get("text", "")
            all_text_blocks.append(text)
            citations.append({
                "source": source,
                "section": header,
                "relevance_score": ev.get("score", 0.0),
                "excerpt": text[:300] + "..." if len(text) > 300 else text
            })

        combined_text = "\n\n".join(all_text_blocks)
        decomp = MachineTheoryAnalyzer.analyze_theory_content(combined_text, machine_name)

        # Build grounded narrative answer
        q_lower = query.lower()
        key_paragraphs = []

        # Find best matching paragraph from retrieved chunks
        candidate_paragraphs = []
        for blk in all_text_blocks:
            for p in blk.split("\n\n"):
                p_strip = p.strip()
                if len(p_strip) > 40 and not p_strip.startswith("#"):
                    candidate_paragraphs.append(p_strip)

        # Score candidate paragraphs by query term overlap
        query_words = set(re.findall(r"\w+", q_lower))
        scored_paras = []
        for cp in candidate_paragraphs:
            score = sum(1 for w in query_words if len(w) > 3 and w in cp.lower())
            scored_paras.append((score, cp))
        scored_paras.sort(key=lambda x: x[0], reverse=True)

        top_excerpts = [p[1] for p in scored_paras[:3] if p[0] > 0]
        if not top_excerpts and candidate_paragraphs:
            top_excerpts = candidate_paragraphs[:2]

        explanation_lines = []
        explanation_lines.append(f"### ⚙️ Engineering Theory & Diagnostic Analysis: **{decomp['machine_name']}**")
        explanation_lines.append("")
        
        # Core answer body
        if top_excerpts:
            explanation_lines.append("**Theoretical Explanation & Mechanism:**")
            for exp in top_excerpts:
                explanation_lines.append(f"> {exp}")
            explanation_lines.append("")

        # Include matching failure modes if queried
        matching_failures = [
            f for f in decomp["failure_modes"]
            if any(w in f["mode"].lower() or w in f["mechanism"].lower() for w in query_words if len(w) > 3)
        ]
        if matching_failures:
            explanation_lines.append("**Detailed Failure Dynamics:**")
            for mf in matching_failures:
                explanation_lines.append(f"- **{mf['mode']}**: {mf['mechanism']}")
            explanation_lines.append("")

        # Include governing equations if available
        if decomp["governing_formulas"]:
            explanation_lines.append("**Governing Physical Laws & Mathematical Relations:**")
            for gf in decomp["governing_formulas"][:3]:
                explanation_lines.append(f"```text\n{gf}\n```")
            explanation_lines.append("")

        # Include critical thresholds
        if decomp["operating_parameters"]:
            explanation_lines.append("**Operational Thresholds & Standard Limits:**")
            for op in decomp["operating_parameters"][:4]:
                explanation_lines.append(f"- {op}")
            explanation_lines.append("")

        # Include maintenance instructions
        if decomp["maintenance_guidelines"]:
            explanation_lines.append("**Field Maintenance & Diagnostic Action:**")
            for mg in decomp["maintenance_guidelines"][:3]:
                explanation_lines.append(f"- [ ] {mg}")

        final_answer_text = "\n".join(explanation_lines)

        return {
            "query": query,
            "machine_name": decomp["machine_name"],
            "answer": final_answer_text,
            "citations": citations,
            "extracted_structure": decomp,
            "status": "EVIDENCE_GROUNDED"
        }
