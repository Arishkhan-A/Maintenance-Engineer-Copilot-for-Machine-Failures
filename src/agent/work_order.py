"""
Enterprise Digital CMMS Maintenance Work Order Generator.
Produces production-ready maintenance work orders compliant with SAP PM / IBM Maximo standards.
"""

from datetime import datetime
from typing import Dict, Any, List

def generate_digital_work_order(
    machine_id: str,
    machine_type: str,
    location: str,
    fault_diagnosis: str,
    fault_confidence: float,
    risk_level: str,
    health_index: float,
    rul_hours: float,
    recommended_checks: List[str],
    spares: List[Dict[str, Any]],
    financial_roi: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate a formal CMMS Digital Work Order for maintenance dispatch.
    """
    now = datetime.now()
    wo_id = f"WO-{now.strftime('%Y%m%d')}-{machine_id}-01"

    # Priority assessment
    if risk_level == "Critical" or health_index < 40.0:
        priority = "P1 - EMERGENCY IMMEDIATE SHUTDOWN"
        sla_hours = 2.0
    elif risk_level == "High" or health_index < 65.0:
        priority = "P2 - URGENT INTERVENTION (< 24 HOURS)"
        sla_hours = 24.0
    else:
        priority = "P3 - SCHEDULED ROUTINE WINDOW"
        sla_hours = 72.0

    # Technician assignment
    if "robot" in machine_type.lower():
        technician = "David Chen (Lead Robotics Specialist)"
    elif "pump" in machine_type.lower() or "hydraul" in fault_diagnosis.lower():
        technician = "Marcus Vance (Senior Hydraulics Technician)"
    elif "compressor" in machine_type.lower():
        technician = "Carlos Ruiz (Pneumatic Systems Engineer)"
    else:
        technician = "John Doe (Senior Millwright Mechanical Specialist)"

    # Safety protocols
    loto_protocols = [
        "LOTO Protocol #E-401: De-energize 400V 3-phase main circuit breaker and attach safety padlock.",
        "LOTO Protocol #P-204: Relieve all residual line pressure to 0.0 bar gauge before unseating flanges.",
        "PPE Required: Anti-vibration mechanic gloves, safety goggles, NFPA 70E Arc-Flash Class 2 shield.",
        "Permit: Confined Space & Hot Work Permit NOT required for external mechanical inspection."
    ]

    # Format spare parts list
    reserved_spares = []
    for sp in spares[:3]:
        reserved_spares.append({
            "component": sp.get("component"),
            "part_number": sp.get("part_number"),
            "quantity_required": 1,
            "warehouse_bin": sp.get("location", "Warehouse Central")
        })

    # Work order markdown document
    markdown_doc = f"""# 🛠️ MAINTENANCE WORK ORDER: {wo_id}
**Asset**: {machine_id} ({machine_type}) | **Location**: {location}
**Issue Date**: {now.strftime('%Y-%m-%d %H:%M')} | **Priority**: {priority}
**Assigned Specialist**: {technician} | **SLA Dispatch Target**: Within {sla_hours} hrs

---

### 1. Diagnostic Findings & AI Telemetry Triangulation
- **Diagnosed Fault Mechanism**: **{fault_diagnosis}** (Confidence: {fault_confidence * 100:.1f}%)
- **Machine Health Index (MHI)**: **{health_index}%**
- **Failure Risk Tier**: **{risk_level}** | **Remaining Useful Life**: **{rul_hours} Hours**
- **Projected Downtime Loss Prevented**: **${financial_roi.get('net_financial_savings', 0):,.2f}**

### 2. Lockout-Tagout (LOTO) & Safety Mandates
"""
    for proto in loto_protocols:
        markdown_doc += f"- [ ] {proto}\n"

    markdown_doc += "\n### 3. Required Warehouse Spares (Pre-Allocated)\n"
    if reserved_spares:
        for r_sp in reserved_spares:
            markdown_doc += f"- [ ] **{r_sp['component']}** | Part #{r_sp['part_number']} | Qty: {r_sp['quantity_required']} | Staged at: `{r_sp['warehouse_bin']}`\n"
    else:
        markdown_doc += "- [ ] Standard mechanical overhaul kit (Seals & NLGI-2 lubricant)\n"

    markdown_doc += "\n### 4. Step-by-Step Maintenance Protocol\n"
    for idx, check in enumerate(recommended_checks, 1):
        markdown_doc += f"{idx}. {check}\n"

    markdown_doc += """
### 5. Post-Intervention Sign-Off
- [ ] Vibration baseline reverification (< 2.0 mm/s RMS)
- [ ] Thermal equilibrium check (delta-T < 30°C after 30 min full load)
- [ ] Technician Signature: ______________________ Date: ___________
"""

    return {
        "work_order_id": wo_id,
        "machine_id": machine_id,
        "machine_type": machine_type,
        "location": location,
        "priority": priority,
        "sla_hours": sla_hours,
        "assigned_technician": technician,
        "fault_diagnosis": fault_diagnosis,
        "fault_confidence": fault_confidence,
        "health_index": health_index,
        "rul_hours": rul_hours,
        "loto_protocols": loto_protocols,
        "reserved_spares": reserved_spares,
        "procedures": recommended_checks,
        "financial_summary": financial_roi,
        "markdown_document": markdown_doc
    }
