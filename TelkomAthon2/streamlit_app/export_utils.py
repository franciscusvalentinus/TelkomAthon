"""
Export utilities: DataFrame → CSV, XLSX, DOCX, PPTX, PDF (in-memory bytes).
"""
import io
import pandas as pd


def to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_xlsx(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buf.getvalue()


def to_docx(df: pd.DataFrame, title: str = "Export") -> bytes:
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading(title, level=1)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    # Header
    for i, col in enumerate(df.columns):
        table.rows[0].cells[i].text = str(col)
        table.rows[0].cells[i].paragraphs[0].runs[0].bold = True
    # Rows
    for _, row in df.iterrows():
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val) if val is not None else ""
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def to_pdf(df: pd.DataFrame, title: str = "Export") -> bytes:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 0.4*cm)]

    # Build table data
    cols = list(df.columns)
    data = [cols] + [[str(v) if v is not None else "" for v in row] for _, row in df.iterrows()]

    col_width = (landscape(A4)[0] - 2*cm) / len(cols)
    tbl = Table(data, colWidths=[col_width] * len(cols), repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("WORDWRAP", (0, 0), (-1, -1), True),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(tbl)
    doc.build(elements)
    return buf.getvalue()


# ── Syllabus plain-text export ────────────────────────────────────────────────

def syllabus_to_text(final: dict) -> str:
    """Convert finalized syllabus dict to structured plain text."""
    profile = final.get("org_profile", {})
    course_type = final.get("course_type", "")
    lines = []

    lines.append("=" * 60)
    lines.append("DOKUMEN SILABUS PELATIHAN")
    lines.append("=" * 60)
    lines.append("")

    # Org profile
    lines.append("PROFIL ORGANISASI")
    lines.append("-" * 40)
    lines.append(f"Perusahaan  : {profile.get('organization_name', '-')}")
    lines.append(f"Industri    : {profile.get('industry', '-')}")
    lines.append(f"Visi        : {profile.get('vision', '-')}")
    lines.append(f"Misi        : {profile.get('mission', '-')}")
    lines.append("")
    lines.append("Prioritas Strategis:")
    for p in profile.get("strategic_priorities", []):
        lines.append(f"  - {p}")
    lines.append("")
    lines.append("Kompetensi Inti:")
    for c in profile.get("core_competencies", []):
        lines.append(f"  - {c}")
    lines.append("")
    lines.append(f"Konteks Pembelajaran:")
    lines.append(f"  {profile.get('learning_context', '-')}")
    lines.append("")

    lines.append(f"Tipe Course : {course_type}")
    lines.append("")

    # TLOs
    lines.append("=" * 60)
    lines.append("TERMINAL LEARNING OBJECTIVES (TLO)")
    lines.append("=" * 60)
    for t in final.get("tlos", []):
        lines.append(f"\nTLO {t.get('tlo_number', '')}.")
        lines.append(f"  {t.get('tlo', '')}")
        lines.append(f"  Rationale: {t.get('rationale', '')}")

    lines.append("")

    # Performance Objectives
    lines.append("=" * 60)
    lines.append("PERFORMANCE OBJECTIVES")
    lines.append("=" * 60)
    for p in final.get("performance_objectives", []):
        lines.append(f"\nPO {p.get('perf_number', '')}. [{p.get('related_tlo', '')}]")
        lines.append(f"  {p.get('performance_objective', '')}")
        lines.append(f"  Kondisi  : {p.get('condition', '')}")
        lines.append(f"  Standar  : {p.get('standard', '')}")

    lines.append("")

    # ELOs
    lines.append("=" * 60)
    lines.append("ENABLING LEARNING OBJECTIVES (ELO)")
    lines.append("=" * 60)
    total_dur = sum(e.get("duration_minutes", 0) for e in final.get("elos", []))
    for e in final.get("elos", []):
        lines.append(f"\nELO {e.get('elo_number', '')}. [{e.get('related_performance', '')}]")
        lines.append(f"  {e.get('elo', '')}")
        lines.append(f"  Bloom Level     : {e.get('bloom_level', '')}")
        lines.append(f"  Metode Delivery : {e.get('delivery_method', '')}")
        lines.append(f"  Durasi          : {e.get('duration_minutes', '')} menit")

    lines.append("")
    lines.append("-" * 60)
    lines.append(f"Total Estimasi Durasi: {total_dur} menit")
    lines.append("=" * 60)

    return "\n".join(lines)


def syllabus_to_docx(final: dict, title: str = "Silabus Pelatihan") -> bytes:
    """Export syllabus as plain-text DOCX (no tables)."""
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    profile = final.get("org_profile", {})
    course_type = final.get("course_type", "")

    doc = Document()
    doc.add_heading(title, level=0)

    # Org profile section
    doc.add_heading("Profil Perusahaan", level=1)
    fields = [
        ("Perusahaan", profile.get("organization_name", "-")),
        ("Industri", profile.get("industry", "-")),
        ("Visi", profile.get("vision", "-")),
        ("Misi", profile.get("mission", "-")),
    ]
    for label, val in fields:
        p = doc.add_paragraph()
        p.add_run(f"{label}: ").bold = True
        p.add_run(val)

    doc.add_paragraph("Prioritas Strategis:").runs[0].bold = True
    for item in profile.get("strategic_priorities", []):
        doc.add_paragraph(item, style="List Bullet")

    doc.add_paragraph("Kompetensi Inti:").runs[0].bold = True
    for item in profile.get("core_competencies", []):
        doc.add_paragraph(item, style="List Bullet")

    p = doc.add_paragraph()
    p.add_run("Konteks Pembelajaran: ").bold = True
    p.add_run(profile.get("learning_context", "-"))

    p = doc.add_paragraph()
    p.add_run("Tipe Course: ").bold = True
    p.add_run(course_type)

    # TLOs
    doc.add_heading("Terminal Learning Objectives (TLO)", level=1)
    for t in final.get("tlos", []):
        doc.add_heading(f"TLO {t.get('tlo_number', '')}.", level=2)
        doc.add_paragraph(t.get("tlo", ""))
        p = doc.add_paragraph()
        p.add_run("Rationale: ").bold = True
        p.add_run(t.get("rationale", ""))

    # Performance Objectives
    doc.add_heading("Performance Objectives", level=1)
    for po in final.get("performance_objectives", []):
        doc.add_heading(f"PO {po.get('perf_number', '')}. [{po.get('related_tlo', '')}]", level=2)
        doc.add_paragraph(po.get("performance_objective", ""))
        p = doc.add_paragraph()
        p.add_run("Kondisi: ").bold = True
        p.add_run(po.get("condition", ""))
        p = doc.add_paragraph()
        p.add_run("Standar: ").bold = True
        p.add_run(po.get("standard", ""))

    # ELOs
    doc.add_heading("Enabling Learning Objectives (ELO)", level=1)
    total_dur = sum(e.get("duration_minutes", 0) for e in final.get("elos", []))
    for e in final.get("elos", []):
        doc.add_heading(f"ELO {e.get('elo_number', '')}. [{e.get('related_performance', '')}]", level=2)
        doc.add_paragraph(e.get("elo", ""))
        p = doc.add_paragraph()
        p.add_run("Bloom Level: ").bold = True
        p.add_run(e.get("bloom_level", ""))
        p.add_run("   |   Metode: ").bold = True
        p.add_run(e.get("delivery_method", ""))
        p.add_run("   |   Durasi: ").bold = True
        p.add_run(f"{e.get('duration_minutes', '')} menit")

    doc.add_paragraph(f"\nTotal Estimasi Durasi: {total_dur} menit")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def syllabus_to_pdf(final: dict, title: str = "Silabus Pelatihan") -> bytes:
    """Export syllabus as plain-text PDF (no tables)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.enums import TA_LEFT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    h1 = styles["Heading1"]
    h2 = styles["Heading2"]
    normal = styles["Normal"]
    bold_style = ParagraphStyle("bold", parent=normal, fontName="Helvetica-Bold")
    label_style = ParagraphStyle("label", parent=normal, fontName="Helvetica-Bold",
                                 textColor=colors.HexColor("#1a3c6e"))

    profile = final.get("org_profile", {})
    course_type = final.get("course_type", "")
    elements = []

    def add(text, style=normal, space=0.2):
        elements.append(Paragraph(text, style))
        elements.append(Spacer(1, space * cm))

    def hr():
        elements.append(HRFlowable(width="100%", thickness=0.5,
                                   color=colors.HexColor("#cccccc")))
        elements.append(Spacer(1, 0.2*cm))

    add(title, styles["Title"], 0.4)
    hr()

    add("Profil Perusahaan", h1, 0.1)
    add(f"<b>Perusahaan:</b> {profile.get('organization_name', '-')}")
    add(f"<b>Industri:</b> {profile.get('industry', '-')}")
    add(f"<b>Visi:</b> {profile.get('vision', '-')}")
    add(f"<b>Misi:</b> {profile.get('mission', '-')}")
    add("<b>Prioritas Strategis:</b>")
    for p in profile.get("strategic_priorities", []):
        add(f"• {p}")
    add("<b>Kompetensi Inti:</b>")
    for c in profile.get("core_competencies", []):
        add(f"• {c}")
    add(f"<b>Konteks Pembelajaran:</b> {profile.get('learning_context', '-')}")
    add(f"<b>Tipe Course:</b> {course_type}")
    hr()

    add("Terminal Learning Objectives (TLO)", h1, 0.1)
    for t in final.get("tlos", []):
        add(f"<b>TLO {t.get('tlo_number', '')}.</b>", bold_style, 0.05)
        add(t.get("tlo", ""))
        add(f"<i>Rationale: {t.get('rationale', '')}</i>", space=0.3)
    hr()

    add("Performance Objectives", h1, 0.1)
    for po in final.get("performance_objectives", []):
        add(f"<b>PO {po.get('perf_number', '')}.</b> [{po.get('related_tlo', '')}]", bold_style, 0.05)
        add(po.get("performance_objective", ""))
        add(f"<b>Kondisi:</b> {po.get('condition', '')}")
        add(f"<b>Standar:</b> {po.get('standard', '')}", space=0.3)
    hr()

    add("Enabling Learning Objectives (ELO)", h1, 0.1)
    total_dur = sum(e.get("duration_minutes", 0) for e in final.get("elos", []))
    for e in final.get("elos", []):
        add(f"<b>ELO {e.get('elo_number', '')}.</b> [{e.get('related_performance', '')}]", bold_style, 0.05)
        add(e.get("elo", ""))
        add(f"<b>Bloom:</b> {e.get('bloom_level', '')}  |  "
            f"<b>Metode:</b> {e.get('delivery_method', '')}  |  "
            f"<b>Durasi:</b> {e.get('duration_minutes', '')} menit", space=0.3)
    hr()
    add(f"<b>Total Estimasi Durasi: {total_dur} menit</b>")

    doc.build(elements)
    return buf.getvalue()
