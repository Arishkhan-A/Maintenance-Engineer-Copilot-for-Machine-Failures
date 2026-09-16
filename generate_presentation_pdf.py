"""
Script to compile the complete MECMF Project Presentation PDF using ReportLab.
Produces a Tier-1 Enterprise Presentation Deck (Landscape A4) with slide layouts.
"""

import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = "MECMF_Project_Presentation.pdf"

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count and corporate running footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Cover page has its own full-bleed styling
            return

        self.saveState()
        # Top banner line
        self.setStrokeColor(colors.HexColor("#0284C7"))
        self.setLineWidth(1.5)
        self.line(40, 560, 802, 560)

        # Header Text
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#0369A1"))
        self.drawString(40, 566, "MECMF • TIER-1 ADVANCED INDUSTRIAL MAINTENANCE COPILOT")

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(802, 566, "EXECUTIVE PRESENTATION DECK")

        # Bottom footer line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.8)
        self.line(40, 35, 802, 35)

        # Footer Text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(40, 22, "CONFIDENTIAL & PROPRIETARY • FOR PRESENTATION & EVALUATION PURPOSES ONLY")
        self.drawRightString(802, 22, f"Slide {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=landscape(A4),
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=34,
        textColor=colors.HexColor("#0F172A")
    )
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#0284C7")
    )
    slide_title_style = ParagraphStyle(
        "SlideTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A")
    )
    slide_subtitle_style = ParagraphStyle(
        "SlideSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0284C7")
    )
    body_style = ParagraphStyle(
        "SlideBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    body_bold = ParagraphStyle(
        "SlideBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    card_title_style = ParagraphStyle(
        "CardTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0369A1")
    )
    code_snippet_style = ParagraphStyle(
        "CodeSnippet",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # =========================================================================
    # SLIDE 1: COVER SLIDE
    # =========================================================================
    story.append(Spacer(1, 40))
    cover_tag = Paragraph("<font color='#0284C7'><b>ENTERPRISE AI PLATFORM • INDUSTRY 4.0</b></font>", subtitle_style)
    story.append(cover_tag)
    story.append(Spacer(1, 10))
    cover_title = Paragraph("<b>MECMF: Multimodal Edge Condition Monitoring & AI Maintenance Copilot</b>", title_style)
    story.append(cover_title)
    story.append(Spacer(1, 12))
    cover_desc = Paragraph(
        "Full-Stack Predictive Maintenance Architecture Featuring Multi-Class Physical Fault Diagnostics, "
        "Dynamic Remaining Useful Life (RUL) Estimation, Composite Machine Health Index (MHI), "
        "Evidence-Grounded Technical RAG, and Autonomous CMMS Work Order Dispatch.",
        subtitle_style
    )
    story.append(cover_desc)
    story.append(Spacer(1, 45))

    meta_table_data = [
        [
            Paragraph("<b>PROJECT VERSION:</b> v3.0 (Enterprise Tier-1)", body_style),
            Paragraph("<b>CORE STACK:</b> Python 3.12 • FastAPI • Streamlit • Scikit-Learn • SHAP", body_style)
        ],
        [
            Paragraph("<b>INTEGRATION:</b> SAP PM / IBM Maximo CMMS Compliant", body_style),
            Paragraph("<b>ACCURACY:</b> 96.7% Multi-Class Fault Diagnosis • 0.9987 ROC-AUC", body_style)
        ],
        [
            Paragraph("<b>BENCHMARK STATUS:</b> 25/25 Tests Passing (100% Green)", body_style),
            Paragraph("<b>TARGET ASSETS:</b> CNC Mills, Hydraulic Pumps, Screw Compressors, 6-Axis Robots", body_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[380, 380])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 2: EXECUTIVE SUMMARY & INDUSTRIAL PROBLEM
    # =========================================================================
    story.append(Paragraph("EXECUTIVE PROBLEM STATEMENT & INDUSTRIAL CONTEXT", slide_subtitle_style))
    story.append(Paragraph("The High Cost of Unplanned Industrial Downtime", slide_title_style))
    story.append(Spacer(1, 10))

    col1_text = Paragraph("""
    <b>The Manufacturing Reality:</b><br/>
    • Unplanned downtime costs automotive and heavy manufacturing facilities an average of <b>$2,500 per hour</b>, exceeding $60,000 per 24-hour shift on critical production lines.<br/><br/>
    • <b>82% of industrial plants</b> still rely on reactive ('run-to-failure') or calendar-based preventive maintenance, replacing expensive parts prematurely while still suffering surprise breakdowns.<br/><br/>
    • <b>Tribal Knowledge Loss:</b> Senior millwrights and mechanical engineers are retiring, creating an operational vacuum in diagnosing root-cause failure mechanisms from sensor signals.<br/><br/>
    • <b>Sensor Overload Without Context:</b> Modern plants have thousands of SCADA/IoT sensors, but maintenance teams lack intelligent correlation between vibration, heat, and physical failure modes.
    """, body_style)

    col2_text = Paragraph("""
    <b>The MECMF Innovation:</b><br/>
    • <b>Pre-Emptive 24-Hour Horizon:</b> Predicts catastrophic machine trips before they manifest on the plant floor.<br/><br/>
    • <b>Multi-Class Root Cause Diagnosis:</b> Identifies whether failure is bearing spalling, motor overheating, hydraulic seal breach, or electrical surge with <b>96.7% accuracy</b>.<br/><br/>
    • <b>Single Source of Truth Health Score (0-100% MHI):</b> Converts complex multi-sensor dynamics into an intuitive executive condition index.<br/><br/>
    • <b>Immediate CMMS Work Orders:</b> Generates ready-to-dispatch maintenance work orders complete with ISO/NFPA Lockout-Tagout protocols and warehouse parts reservations.<br/><br/>
    • <b>Proven ROI:</b> Demonstrated net savings of <b>$38,400 per critical intervention</b> by stopping line failure.
    """, body_style)

    problem_table = Table([[col1_text, col2_text]], colWidths=[375, 375])
    problem_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#FFF1F2")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#FDA4AF")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#F0FDF4")),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#86EFAC")),
        ('PADDING', (0, 0), (-1, -1), 14),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(problem_table)
    story.append(Spacer(1, 15))

    stats_table = Table([
        [
            Paragraph("<b>$2,500 / hr</b><br/><font size=7 color='#64748B'>Industry Downtime Cost</font>", card_title_style),
            Paragraph("<b>96.7%</b><br/><font size=7 color='#64748B'>Fault Classification Acc.</font>", card_title_style),
            Paragraph("<b>0.9987</b><br/><font size=7 color='#64748B'>Failure ROC-AUC</font>", card_title_style),
            Paragraph("<b>21.98 hrs</b><br/><font size=7 color='#64748B'>RUL Prediction MAE</font>", card_title_style),
            Paragraph("<b>$38,400+</b><br/><font size=7 color='#64748B'>Avg. Catastrophic Loss Prevented</font>", card_title_style)
        ]
    ], colWidths=[150, 150, 150, 150, 150])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 3: COMPLETE END-TO-END SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("SYSTEM DESIGN & ARCHITECTURE", slide_subtitle_style))
    story.append(Paragraph("Enterprise Multi-Layer Technical Topology", slide_title_style))
    story.append(Spacer(1, 10))

    arch_layers = [
        [
            Paragraph("<b>LAYER</b>", body_bold),
            Paragraph("<b>CORE MODULES & TECHNOLOGIES</b>", body_bold),
            Paragraph("<b>KEY RESPONSIBILITIES & CAPABILITIES</b>", body_bold)
        ],
        [
            Paragraph("<b>1. Telemetry Ingestion</b>", body_style),
            Paragraph("<code>src/data/load_data.py</code><br/><code>simulator/sensor_stream.py</code>", body_style),
            Paragraph("• Temporal parsing of industrial 12h/24h timestamps<br/>• Sensor dropout handling & forward/backward temporal imputation<br/>• Real-time fault progression streaming (5 failure injection modes)", body_style)
        ],
        [
            Paragraph("<b>2. Feature Engineering</b>", body_style),
            Paragraph("<code>src/features/build_features.py</code><br/>60 Engineered Signals", body_style),
            Paragraph("• Rolling statistics (5 & 10 step mean, std, max) & multi-step shift lags<br/>• Thermodynamics: Differential Delta-T (ΔT) = T_motor - T_ambient<br/>• Kinematics: Vibration velocity to RPM ratio (ISO 10816 limits)", body_style)
        ],
        [
            Paragraph("<b>3. Machine Learning Core</b>", body_style),
            Paragraph("HistGradientBoosting • Random Forest<br/>Isolation Forest • SHAP Explainer", body_style),
            Paragraph("• Binary Failure Prediction (24h lookahead)<br/>• 5-Class Physical Fault Mechanism Diagnosis<br/>• Remaining Useful Life (RUL) regression<br/>• Unsupervised calibrated anomaly detection (4% contamination)", body_style)
        ],
        [
            Paragraph("<b>4. Grounded RAG Engine</b>", body_style),
            Paragraph("<code>src/rag/retrieve.py</code><br/><code>src/rag/generate.py</code>", body_style),
            Paragraph("• TF-IDF & Cosine similarity vector search over OEM manuals & RCAs<br/>• Zero-hallucination guardrails (explicit fallback on low relevance score)<br/>• Auto-generates grounded action checklists and technical excerpts", body_style)
        ],
        [
            Paragraph("<b>5. Autonomous Agent</b>", body_style),
            Paragraph("<code>src/agent/workflow.py</code><br/><code>src/agent/tools.py</code>", body_style),
            Paragraph("• 11-step deterministic ReAct investigation loop<br/>• Automatic entity and machine extraction from natural queries<br/>• CMMS digital work order dispatch (SAP PM / IBM Maximo standard)", body_style)
        ],
        [
            Paragraph("<b>6. Enterprise Interface</b>", body_style),
            Paragraph("FastAPI Backend • REST API<br/>Streamlit v3.0 Industrial Cockpit", body_style),
            Paragraph("• High-performance REST endpoints with Pydantic v2 schemas<br/>• TALOS·AI dark executive cockpit with 10 specialized navigation views<br/>• Instant work order exports (Markdown / JSON) & real-time telemetry HUD", body_style)
        ]
    ]

    arch_table = Table(arch_layers, colWidths=[130, 210, 410])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284C7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(arch_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 4: MACHINE LEARNING MODELS & EVALUATION BENCHMARKS
    # =========================================================================
    story.append(Paragraph("MODEL PERFORMANCE & SCIENTIFIC RIGOR", slide_subtitle_style))
    story.append(Paragraph("Industrial Benchmark Evaluation Metrics", slide_title_style))
    story.append(Spacer(1, 10))

    model_metrics_data = [
        [
            Paragraph("<b>PREDICTION TASK</b>", body_bold),
            Paragraph("<b>ALGORITHM ARCHITECTURE</b>", body_bold),
            Paragraph("<b>KEY METRIC EVALUATION</b>", body_bold),
            Paragraph("<b>INDUSTRIAL VALUE & IMPACT</b>", body_bold)
        ],
        [
            Paragraph("<b>Multi-Class Root-Cause Fault Classifier</b>", body_style),
            Paragraph("HistGradientBoosting<br/>with balanced class weighting", body_style),
            Paragraph("• <b>Accuracy: 96.7%</b><br/>• <b>Weighted F1: 0.9636</b><br/>• Macro F1: 0.7974", body_style),
            Paragraph("Distinguishes bearing spalling from thermal overload, preventing wrong parts dispatch and saving hours of guesswork.", body_style)
        ],
        [
            Paragraph("<b>Binary Failure Prediction (Next 24h)</b>", body_style),
            Paragraph("Tuned Balanced Random Forest<br/>(150 Estimators, Temporal Split)", body_style),
            Paragraph("• <b>ROC-AUC: 0.9987</b><br/>• <b>PR-AUC: 0.9872</b><br/>• F1-Score: 0.9300", body_style),
            Paragraph("Provides reliable 24-hour advance warning before complete catastrophic mechanical seizure.", body_style)
        ],
        [
            Paragraph("<b>Remaining Useful Life (RUL) Regressor</b>", body_style),
            Paragraph("Random Forest Regressor<br/>with thermodynamic features", body_style),
            Paragraph("• <b>MAE: 21.98 Hours</b><br/>• RMSE: 31.48 Hours<br/>• Range: 0 - 250 Hours", body_style),
            Paragraph("Accurate wear horizon forecasting enables scheduling maintenance in planned shift turnarounds.", body_style)
        ],
        [
            Paragraph("<b>Unsupervised Anomaly Detector</b>", body_style),
            Paragraph("Calibrated Isolation Forest<br/>trained on baseline normal regimes", body_style),
            Paragraph("• Contamination: 0.04 (4%)<br/>• Score Threshold: -0.0000<br/>• Calibrated Percentile", body_style),
            Paragraph("Flags previously uncatalogued multi-sensor drifts and subtle micro-faults before conventional threshold alarms trip.", body_style)
        ],
        [
            Paragraph("<b>Explainable AI (XAI) Attribution</b>", body_style),
            Paragraph("SHAP (SHapley Additive exPlanations)<br/>TreeExplainer", body_style),
            Paragraph("• Instant local attribution<br/>• Percentage driver ranking<br/>• Global feature impact", body_style),
            Paragraph("Eliminates 'black box' machine learning; gives millwright technicians mathematical proof of why risk is elevated.", body_style)
        ]
    ]

    metrics_table = Table(model_metrics_data, colWidths=[150, 160, 180, 260])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("""
    <b>Data Leakage Prevention Guarantee:</b> All models were trained using strict <i>Temporal Train-Test Splitting (80/20)</i> 
    computed individually per machine asset. No future time observations leak into past rolling windows or lag calculations.
    """, body_style))
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 5: COMPOSITE MACHINE HEALTH INDEX (MHI) & PHYSICS RULES
    # =========================================================================
    story.append(Paragraph("HEALTH SCORING & PHYSICS FOUNDATIONS", slide_subtitle_style))
    story.append(Paragraph("Composite Machine Health Index (0 - 100% MHI)", slide_title_style))
    story.append(Spacer(1, 10))

    mhi_expl = Paragraph("""
    Rather than presenting engineers with confusing raw probability outputs, MECMF computes a <b>Deterministic Composite Machine Health Index (MHI)</b>. 
    Starting from a baseline of <b>100%</b>, points are deducted based on physics-backed thresholds, international vibration standards, and ML inferences:
    """, body_style)
    story.append(mhi_expl)
    story.append(Spacer(1, 8))

    mhi_penalties = [
        [
            Paragraph("<b>HEALTH FACTOR</b>", body_bold),
            Paragraph("<b>ENGINEERING / PHYSICS BASIS</b>", body_bold),
            Paragraph("<b>PENALTY WEIGHT</b>", body_bold),
            Paragraph("<b>ALARM THRESHOLDS</b>", body_bold)
        ],
        [
            Paragraph("<b>Failure Risk Penalty</b>", body_style),
            Paragraph("Machine Learning Binary Failure Model Probability ($P_{fail}$)", body_style),
            Paragraph("<b>Up to 35.0 Points</b>", body_style),
            Paragraph("Linear scale: $35.0 \times P_{fail}$", body_style)
        ],
        [
            Paragraph("<b>Vibration Severity Penalty</b>", body_style),
            Paragraph("ISO 10816-3 Industrial Mechanical Vibration Standards", body_style),
            Paragraph("<b>Up to 25.0 Points</b>", body_style),
            Paragraph("&gt; 4.5 mm/s (Alert) • &gt; 7.1 mm/s (Critical Trip)", body_style)
        ],
        [
            Paragraph("<b>Thermodynamic Delta (Delta-T (ΔT))</b>", body_style),
            Paragraph("Motor temperature rise above ambient: Delta-T (ΔT) = T_motor - T_ambient", body_style),
            Paragraph("<b>Up to 20.0 Points</b>", body_style),
            Paragraph("&gt; 35°C (Elevated) • &gt; 50°C (Thermal Runaway)", body_style)
        ],
        [
            Paragraph("<b>Unsupervised Anomaly Penalty</b>", body_style),
            Paragraph("Isolation Forest calibrated decision boundary deviation", body_style),
            Paragraph("<b>Up to 10.0 Points</b>", body_style),
            Paragraph("Score &lt; 0.0 indicates uncatalogued operating state", body_style)
        ],
        [
            Paragraph("<b>Remaining Useful Life (RUL)</b>", body_style),
            Paragraph("Operating hours left before expected component breakdown", body_style),
            Paragraph("<b>Up to 10.0 Points</b>", body_style),
            Paragraph("&lt; 48 Hours: 5.0 pts • &lt; 24 Hours: 10.0 pts", body_style)
        ]
    ]

    mhi_table = Table(mhi_penalties, colWidths=[150, 240, 140, 220])
    mhi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0369A1")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(mhi_table)
    story.append(Spacer(1, 12))

    categories_box = Table([
        [
            Paragraph("<b>OPTIMAL CONDITION (85 - 100%)</b><br/><font size=7 color='#10B981'>All parameters nominal. Standard scheduled shift inspections.</font>", body_style),
            Paragraph("<b>GOOD CONDITION (70 - 84%)</b><br/><font size=7 color='#38BDF8'>Minor operational drift. Baseline logging continues.</font>", body_style),
            Paragraph("<b>DEGRADED WARNING (40 - 69%)</b><br/><font size=7 color='#F59E0B'>Elevated vibration or temperature. P3 Work Order dispatched.</font>", body_style),
            Paragraph("<b>CRITICAL RISK (&lt; 40%)</b><br/><font size=7 color='#EF4444'>Imminent catastrophic failure. P1 Emergency LOTO shutdown.</font>", body_style)
        ]
    ], colWidths=[185, 185, 190, 190])
    categories_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#ECFDF5")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#A7F3D0")),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#F0F9FF")),
        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#BAE6FD")),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor("#FFFBEB")),
        ('BOX', (2, 0), (2, 0), 1, colors.HexColor("#FDE68A")),
        ('BACKGROUND', (3, 0), (3, 0), colors.HexColor("#FEF2F2")),
        ('BOX', (3, 0), (3, 0), 1, colors.HexColor("#FECACA")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(categories_box)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 6: GROUNDED RAG KNOWLEDGE BASE & AUTONOMOUS AGENT
    # =========================================================================
    story.append(Paragraph("ARTIFICIAL INTELLIGENCE AGENT WORKFLOW", slide_subtitle_style))
    story.append(Paragraph("Evidence-Grounded RAG & Controlled ReAct Agent", slide_title_style))
    story.append(Spacer(1, 10))

    agent_text = Paragraph("""
    Unlike generative models that can hallucinate dangerous maintenance procedures, MECMF uses a 
    <b>Controlled ReAct (Reason + Act) Agent</b> with <b>Deterministic Tools</b> and a <b>Grounded Technical RAG</b> layer.
    """, body_style)
    story.append(agent_text)
    story.append(Spacer(1, 8))

    rag_steps = [
        [
            Paragraph("<b>11-STEP CONTROLLED AGENT WORKFLOW</b>", body_bold),
            Paragraph("<b>GROUNDED RAG EVIDENCE CORPUS</b>", body_bold)
        ],
        [
            Paragraph("""
            <b>1. Entity Extraction:</b> Parses target asset ID (e.g. M17) and query intent.<br/>
            <b>2. Asset Status:</b> Reads machine type, location bay, and baseline limits.<br/>
            <b>3. Sensor Window:</b> Retrieves last 15-step sliding window.<br/>
            <b>4. ML Inference:</b> Runs failure classifier, RUL regressor, and anomaly detector.<br/>
            <b>5. Fault Diagnosis:</b> Evaluates 5-class Gradient Boosting root cause.<br/>
            <b>6. SHAP Attribution:</b> Computes top feature impact percentages.<br/>
            <b>7. Maintenance History:</b> Audits past service interventions & replacements.<br/>
            <b>8. Technical Manual Search:</b> Semantic search in OEM engineering specs.<br/>
            <b>9. Incident RCA Search:</b> Searches historical post-mortems for matching patterns.<br/>
            <b>10. Warehouse Spares Check:</b> Verifies inventory stock and bin locations.<br/>
            <b>11. CMMS Work Order Synthesis:</b> Emits formal work order & action checklist.
            """, body_style),
            Paragraph("""
            <b>Curated Engineering Corpus (46 Structured Passages):</b><br/><br/>
            • <b>Manufacturer Operating Manuals:</b><br/>
              - Electric Motors: SKF bearing clearances, ISO balance grades<br/>
              - Hydraulic Pumps: Plan 11 seal flushes, cavitation limits<br/>
              - Rotary Compressors: Thermostatic valves, minimum pressure valves<br/>
              - 6-Axis Robots: Cycloidal reducer backlash, harmonic drive wear<br/><br/>
            • <b>Troubleshooting Standard Operating Procedures (SOPs):</b><br/>
              - ISO 10816 Vibration severity diagnostic matrix<br/>
              - Thermal runaway differential (Delta-T (ΔT)) mitigation procedures<br/>
              - Hydraulic seal erosion & proportional valve bypass checklists<br/><br/>
            • <b>Real-World Incident Reports & Root Cause Analyses (RCAs):</b><br/>
              - INC-2023-M17: Spindle bearing race spalling from lube starvation<br/>
              - INC-2024-M04: Primary Viton O-ring seal rupture under surge<br/>
              - INC-2024-M12: Oil cooler radiator fin clogging thermal trip
            """, body_style)
        ]
    ]

    rag_table = Table(rag_steps, colWidths=[375, 375])
    rag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284C7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
    ]))
    story.append(rag_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 7: CMMS DIGITAL WORK ORDERS & FINANCIAL ROI
    # =========================================================================
    story.append(Paragraph("BUSINESS IMPACT & CMMS INTEGRATION", slide_subtitle_style))
    story.append(Paragraph("Automated CMMS Work Order Dispatch & Financial ROI", slide_title_style))
    story.append(Spacer(1, 10))

    wo_text = Paragraph("""
    When an asset enters Degraded or Critical condition, the copilot automatically synthesizes an 
    <b>Enterprise Digital Work Order</b> conforming to <b>SAP PM / IBM Maximo</b> standards:
    """, body_style)
    story.append(wo_text)
    story.append(Spacer(1, 8))

    cmms_split = [
        [
            Paragraph("<b>GENERATED WORK ORDER STRUCTURE (SAP PM READY)</b>", body_bold),
            Paragraph("<b>FINANCIAL DOWNTIME LOSS PREVENTION ENGINE</b>", body_bold)
        ],
        [
            Paragraph("""
            <b>• Work Order Header:</b> Unique ID <code>WO-YYYYMMDD-M17-01</code><br/>
            <b>• Priority & SLA:</b><br/>
              - P1 Emergency (SLA: &lt; 2h, Immediate LOTO Shutdown)<br/>
              - P2 Urgent (SLA: &lt; 24h, Proactive Intervention)<br/>
              - P3 Routine (SLA: &lt; 72h, Scheduled Window)<br/>
            <b>• Assigned Specialist:</b> Matched by machine domain (e.g. Senior Millwright for CNC, Hydraulic Specialist for Pumps).<br/>
            <b>• Safety LOTO Protocols:</b><br/>
              - <code>LOTO #E-401</code>: 400V 3-phase breaker padlock lock.<br/>
              - <code>LOTO #P-204</code>: Zero-pressure line relief before flange unseating.<br/>
              - PPE: Arc-flash Class 2 shield, anti-vibe mechanic gloves.<br/>
            <b>• Pre-Allocated Warehouse Spares:</b> Reserved part number (e.g., SKF-6312-C3) and warehouse bin location (Bin A-12).<br/>
            <b>• Step-by-Step Procedure & Sign-Off:</b> Inspection, replacement, alignment, and post-repair baseline verification.
            """, body_style),
            Paragraph("""
            <b>Quantifiable Cost-Benefit Comparison:</b><br/><br/>
            <b>Scenario A: Unplanned Catastrophic Breakdown</b><br/>
            • Production Line Downtime: 14.0 Hours @ $2,500/hr = <b>$35,000</b><br/>
            • Emergency Expedited Parts & Secondary Damage: <b>$4,200</b><br/>
            • Emergency Technician Overtime: <b>$1,200</b><br/>
            • <b>Total Catastrophic Loss: $40,400</b><br/><br/>
            <b>Scenario B: Proactive MECMF Intervention</b><br/>
            • Controlled Planned Window: 0.5 Hours downtime = <b>$1,250</b><br/>
            • Standard Warehouse Spare Stock: <b>$450</b><br/>
            • Standard Technician Shift Hours: <b>$300</b><br/>
            • <b>Total Proactive Cost: $2,000</b><br/><br/>
            <b>Net Financial Savings Prevented: $38,400</b><br/>
            <b>Projected Return on Investment (ROI): &gt; 1,900%</b>
            """, body_style)
        ]
    ]

    cmms_table = Table(cmms_split, colWidths=[375, 375])
    cmms_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
    ]))
    story.append(cmms_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 8: STREAMLIT EXECUTIVE COCKPIT & REST API
    # =========================================================================
    story.append(Paragraph("USER EXPERIENCE & REST SERVICES", slide_subtitle_style))
    story.append(Paragraph("TALOS·AI Cockpit: Total Asset & Lifetime Operational Safeguard", slide_title_style))
    story.append(Spacer(1, 10))

    ui_text = Paragraph("""
    The user experience is delivered through an executive-grade <b>TALOS·AI (Total Asset & Lifetime Operational Safeguard) Industrial Cockpit</b> built on Streamlit v3.0, 
    powered by an asynchronous <b>FastAPI REST Backend</b>:
    """, body_style)
    story.append(ui_text)
    story.append(Spacer(1, 8))

    cockpit_modules = [
        [
            Paragraph("<b>NAVIGATION MODULE</b>", body_bold),
            Paragraph("<b>CORE FEATURES & INTERACTIVE CAPABILITIES</b>", body_bold)
        ],
        [
            Paragraph("<b>1. Plant Executive Overview</b>", body_style),
            Paragraph("Fleet assets overview, plant risk breakdown (Normal/Medium/High/Critical), downtime hours avoided, and cumulative plant financial savings counter.", body_style)
        ],
        [
            Paragraph("<b>2. Live Telemetry & Delta-T (ΔT)</b>", body_style),
            Paragraph("High-frequency telemetry line charts with ISO 10816 vibration alarm lines (4.5 & 7.1 mm/s) and thermal delta (Delta-T (ΔT)) warnings.", body_style)
        ],
        [
            Paragraph("<b>3. Multi-Class Fault & RUL</b>", body_style),
            Paragraph("Machine Health Index gauge, diagnosed physical fault mechanism with probability breakdown bars, and remaining useful life horizon.", body_style)
        ],
        [
            Paragraph("<b>4. SHAP Attribution & RCA</b>", body_style),
            Paragraph("Instant visual decomposition showing exact percentage contributions of vibration, temperature, and pressure to the risk score.", body_style)
        ],
        [
            Paragraph("<b>5. CMMS Digital Work Orders</b>", body_style),
            Paragraph("Rendered industrial work order document with safety LOTO checkboxes and one-click export buttons (Markdown and SAP-compliant JSON).", body_style)
        ],
        [
            Paragraph("<b>6. Maintenance & Spares</b>", body_style),
            Paragraph("Historical equipment maintenance logs, past breakdown events, incident post-mortems, and warehouse spare parts stock thresholds.", body_style)
        ],
        [
            Paragraph("<b>7. Autonomous AI Copilot</b>", body_style),
            Paragraph("Evidence-grounded conversational agent with 1-click prompt presets (Investigate M17, Generate Work Order, Calculate ROI) and full tool execution trace.", body_style)
        ],
        [
            Paragraph("<b>8. Model Benchmarks</b>", body_style),
            Paragraph("Live display of model metadata, ROC-AUC, PR-AUC, MAE, confusion matrices, and per-class classification metrics.", body_style)
        ],
        [
            Paragraph("<b>9. Fault Progression Sim</b>", body_style),
            Paragraph("Interactive fault injection simulator (Bearing Wear, Temperature Rise, Vibration Drift) streaming directly into the active database.", body_style)
        ]
    ]

    ui_table = Table(cockpit_modules, colWidths=[200, 550])
    ui_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284C7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(ui_table)
    story.append(PageBreak())

    # =========================================================================
    # SLIDE 9: VERIFICATION, DEPLOYMENT & FUTURE ROADMAP
    # =========================================================================
    story.append(Paragraph("PRODUCTION READINESS & NEXT STEPS", slide_subtitle_style))
    story.append(Paragraph("System Verification, Deployment & Industrial Roadmap", slide_title_style))
    story.append(Spacer(1, 10))

    final_split = [
        [
            Paragraph("<b>AUTOMATED QUALITY ASSURANCE & VERIFICATION</b>", body_bold),
            Paragraph("<b>DEPLOYMENT ARCHITECTURE & ROADMAP</b>", body_bold)
        ],
        [
            Paragraph("""
            <b>Comprehensive Automated Test Suite:</b><br/>
            • <b>Pytest Suite: 25 / 25 Passed (100% Green)</b><br/>
              - <code>test_agent.py</code>: Agent tool invocation & entity extraction<br/>
              - <code>test_api.py</code>: All 12 FastAPI REST endpoints verified<br/>
              - <code>test_features.py</code>: 60-feature temporal transform & data cleaning<br/>
              - <code>test_health_and_workorder.py</code>: MHI, ROI & CMMS work orders<br/>
              - <code>test_models.py</code>: Inference engine, RUL, and SHAP bounds<br/>
              - <code>test_multiclass.py</code>: Gradient boosting fault mechanisms<br/><br/>
            <b>Edge Case Robustness:</b><br/>
            • Defensive error handling for empty sensor history (clean 404 response).<br/>
            • Input DataFrame validation preventing schema mismatch.<br/>
            • Guardrails on RAG retrieval ensuring no hallucinated maintenance steps.
            """, body_style),
            Paragraph("""
            <b>Production Containerization:</b><br/>
            • <b>Docker Multi-Stage Build:</b> Containerizes FastAPI backend, SQLite database, and pre-computed RAG vector index.<br/>
            • Edge deployable on industrial IPCs (Advantech, Siemens IPC) or cloud Kubernetes clusters.<br/><br/>
            <b>Industrial Roadmap (Phase 4):</b><br/>
            • <b>MQTT / OPC-UA Real-Time Connector:</b> Direct ingestion from industrial PLCs (Siemens S7, Rockwell Allen-Bradley).<br/>
            • <b>Acoustic Audio Spectrum Analysis:</b> Integration of ultrasonic acoustic microphone streams for early bearing lubrication micro-cracks.<br/>
            • <b>Direct SAP PM BAPI Connector:</b> Automated two-way work order synchronization directly into enterprise ERP databases.
            """, body_style)
        ]
    ]

    final_table = Table(final_split, colWidths=[375, 375])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
    ]))
    story.append(final_table)
    story.append(Spacer(1, 20))

    conclusion_box = Table([
        [
            Paragraph("""
            <b>Conclusion:</b> MECMF bridges the critical gap between academic machine learning models and real-world plant floor operations. 
            By uniting high-precision multi-class models (96.7% accuracy), explainable AI (SHAP), domain-grounded RAG, and automated CMMS dispatch, 
            the platform transforms unplanned downtime into predictable, cost-optimized maintenance workflows.
            """, body_style)
        ]
    ], colWidths=[750])
    conclusion_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#86EFAC")),
        ('PADDING', (0, 0), (0, 0), 10),
    ]))
    story.append(conclusion_box)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated presentation PDF: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
