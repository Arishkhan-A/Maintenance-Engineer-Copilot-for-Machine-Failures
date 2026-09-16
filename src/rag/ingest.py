"""
Enterprise Document Ingestion and Semantic Vector Indexing for Industrial RAG Knowledge Base.
Parses equipment manuals, troubleshooting guides, incident RCAs, and engineering theory documents
with rich metadata (machine applicability, component tags, failure categories, physics equations).
Supports dynamic runtime theory indexing for arbitrary machines.
"""

import glob
import json
import os
import re
from typing import List, Dict, Any, Optional

class DocumentChunker:
    """Chunks engineering documents preserving section headers, equipment types, and failure tags."""

    MACHINE_MAP = {
        "pump": ["Pump", "Hydraulic Pump", "Centrifugal Pump"],
        "motor": ["Motor", "Electric Motor", "Induction Motor", "CNC"],
        "compressor": ["Compressor", "Rotary Screw"],
        "robotic": ["Robotic Arm", "Robot", "Industrial Robot"],
        "robot": ["Robotic Arm", "Robot", "Industrial Robot"],
        "spindle": ["CNC", "Spindle", "CNC Spindle"],
        "cnc": ["CNC", "CNC Machine", "Spindle"],
        "turbine": ["Turbine", "Gas Turbine", "Steam Turbine"],
        "boiler": ["Boiler", "Industrial Boiler"],
        "chiller": ["Chiller", "HVAC Chiller"],
        "conveyor": ["Conveyor", "Conveyor Belt"],
        "gearbox": ["Gearbox", "Speed Reducer"],
        "vibration": ["CNC", "Pump", "Compressor", "Motor", "Robotic Arm"],
        "hydraulic": ["Pump", "Hydraulic System"],
        "electrical": ["Motor", "CNC", "Robotic Arm"],
        "overheating": ["Motor", "Compressor", "Pump", "CNC"],
        "pressure": ["Pump", "Compressor"]
    }

    @staticmethod
    def infer_applicability(filename: str, text: str) -> List[str]:
        text_lower = (filename + " " + text).lower()
        applicable = set()
        for kw, machines in DocumentChunker.MACHINE_MAP.items():
            if kw in text_lower:
                applicable.update(machines)

        # Dynamic extraction of capital equipment names from text
        custom_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Pump|Motor|Compressor|Turbine|Boiler|Chiller|Spindle|Robot|Press|Conveyor|Gearbox))\b", text)
        for cm in custom_matches:
            applicable.add(cm.strip())

        if not applicable:
            applicable = {"General Industrial Equipment"}
        return sorted(list(applicable))

    @staticmethod
    def infer_tags(text: str) -> List[str]:
        sec_lower = text.lower()
        tags = set()
        tag_keywords = {
            "bearing": ["bearing", "6312", "7314", "nu310", "spalling", "cage", "bpfo", "bpfi", "envelope"],
            "vibration": ["vibration", "unbalance", "misalignment", "rms", "iso 10816", "harmonics", "sub-harmonic", "chatter"],
            "thermal": ["temperature", "overheat", "cooling", "delta-t", "heat exchanger", "thermal runaway", "arrhenius"],
            "hydraulic": ["hydraulic", "cavitation", "npsh", "suction", "pressure", "seal", "valve", "bernoulli", "affinity"],
            "electrical": ["current", "phase", "stator", "winding", "overload", "surge", "short", "faraday", "slip", "flux"],
            "lubrication": ["grease", "oil", "lubricant", "viscosity", "iso vg", "particle count", "nlgi"],
            "incident": ["incident", "root cause", "rca", "corrective action", "failure event"],
            "theory": ["theory", "principle", "governing", "equation", "formula", "physics", "kinematics", "thermodynamics"]
        }
        for tag, kws in tag_keywords.items():
            if any(k in sec_lower for k in kws):
                tags.add(tag)

        # Extract specific machine IDs if referenced
        machine_refs = re.findall(r"\bM\d{2}\b", text)
        for m in machine_refs:
            tags.add(m.upper())

        return sorted(list(tags))

    @staticmethod
    def chunk_content(
        content: str,
        source_name: str,
        category: str = "manual",
        machine_override: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Chunks document text content into semantic, header-preserved passages."""
        raw_sections = re.split(r"(?m)^(?=#{1,3}\s+)", content)
        chunks = []

        doc_title = source_name.replace(".txt", "").replace(".md", "").replace("_", " ").title()
        if raw_sections and raw_sections[0].startswith("# "):
            doc_title = raw_sections[0].splitlines()[0].replace("#", "").strip()

        for i, sec in enumerate(raw_sections):
            sec = sec.strip()
            if not sec or len(sec) < 35:
                continue

            lines = sec.splitlines()
            if lines[0].startswith("#"):
                header = lines[0].replace("#", "").strip()
                body = "\n".join(lines[1:]).strip()
            else:
                header = f"{doc_title} (Section {i+1})"
                body = sec

            if not body and i == 0:
                continue

            full_text = f"{header}\n\n{body}" if body else header

            tags = DocumentChunker.infer_tags(full_text)
            if category == "theory":
                tags.append("theory")
                tags = sorted(list(set(tags)))

            applicability = DocumentChunker.infer_applicability(source_name, full_text)
            if machine_override:
                applicability.append(machine_override)
                applicability = sorted(list(set(applicability)))

            base_clean = re.sub(r"[^\w\-]", "_", source_name.replace(".txt", "").replace(".md", ""))
            chunk_id = f"{base_clean}#sec_{i+1}"

            chunks.append({
                "chunk_id": chunk_id,
                "source_file": source_name,
                "document_title": doc_title,
                "category": category,
                "header": header,
                "text": full_text,
                "tags": tags,
                "applicable_machines": applicability,
                "char_length": len(full_text)
            })

        return chunks

    @staticmethod
    def chunk_file(filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        filename = os.path.basename(filepath)
        folder = os.path.basename(os.path.dirname(filepath))

        if folder == "theory":
            category = "theory"
        elif folder == "manuals":
            category = "manual"
        elif folder == "troubleshooting":
            category = "troubleshooting"
        elif folder == "incidents":
            category = "incident"
        else:
            category = "manual"

        return DocumentChunker.chunk_content(content, filename, category=category)


def build_knowledge_index(docs_dir: str = "documents", output_json: str = "database/rag_index.json") -> List[Dict[str, Any]]:
    """Scan documents directory (including theory), parse sections, and persist JSON search index."""
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    all_chunks = []

    file_patterns = [
        os.path.join(docs_dir, "theory", "*.txt"),
        os.path.join(docs_dir, "theory", "*.md"),
        os.path.join(docs_dir, "manuals", "*.txt"),
        os.path.join(docs_dir, "troubleshooting", "*.txt"),
        os.path.join(docs_dir, "incidents", "*.txt")
    ]

    indexed_files = 0
    for pattern in file_patterns:
        for filepath in glob.glob(pattern):
            indexed_files += 1
            chunks = DocumentChunker.chunk_file(filepath)
            all_chunks.extend(chunks)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"[OK] Indexed {len(all_chunks)} semantic chunks across {indexed_files} documents to {output_json}")
    return all_chunks


def index_raw_theory(
    text: str,
    doc_name: str,
    machine_name: Optional[str] = None,
    category: str = "theory",
    output_json: str = "database/rag_index.json"
) -> List[Dict[str, Any]]:
    """
    Dynamically parses and indexes runtime theory content for any machine,
    persisting into the active knowledge index JSON without requiring server restart.
    """
    new_chunks = DocumentChunker.chunk_content(
        content=text,
        source_name=doc_name,
        category=category,
        machine_override=machine_name
    )

    existing_chunks = []
    if os.path.exists(output_json):
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
        except Exception:
            existing_chunks = []

    # Replace existing chunks from same source or append new ones
    chunk_map = {c["chunk_id"]: c for c in existing_chunks}
    for nc in new_chunks:
        chunk_map[nc["chunk_id"]] = nc

    updated_chunks = list(chunk_map.values())
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(updated_chunks, f, indent=2)

    return new_chunks


if __name__ == "__main__":
    build_knowledge_index()
