import os
import sys
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage, HRFlowable, PageBreak
)

NAVY = colors.HexColor("#1a2540")
ACCENT_BLUE = colors.HexColor("#3b6ea5")
LIGHT_GREY = colors.HexColor("#f2f3f5")
DARK_TEXT = colors.HexColor("#1d1d1d")
MUTED_TEXT = colors.HexColor("#6b7280")
DANGER_RED = colors.HexColor("#c0392b")
SAFE_GREEN = colors.HexColor("#1e8449")
WARNING_AMBER = colors.HexColor("#b8860b")

LOGO_CANDIDATES = ["../assets/logo.png", "assets/logo.png", "./assets/logo.png"]

MATERIAL_NOTES = {
    "Silicon": "Standard semiconductor substrate material. Moderate thermal conductivity (148 W/m·K), industry default for ASIC dies.",
    "Copper": "High thermal conductivity (401 W/m·K). Commonly used in heat spreaders and interconnects for superior heat dissipation.",
    "Aluminum": "Moderate-to-high thermal conductivity (237 W/m·K). Lightweight and cost-effective alternative for heat sink applications.",
    "Diamond": "Exceptional thermal conductivity (2200 W/m·K). Used in high-power-density applications where conventional materials are insufficient."
}


def _find_logo():
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath("..")
    candidate = os.path.join(base_path, "assets", "logo.png")
    if os.path.exists(candidate):
        return candidate
    for path in LOGO_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


class _HeaderFooterCanvas:
    def __init__(self, material):
        self.material = material

    def __call__(self, canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4
        band_height = 28 * mm
        canvas_obj.setFillColor(NAVY)
        canvas_obj.rect(0, page_height - band_height, page_width, band_height, stroke=0, fill=1)

        logo_path = _find_logo()
        text_x = 20 * mm
        if logo_path:
            try:
                logo_h = 14 * mm
                canvas_obj.drawImage(
                    logo_path, 20 * mm, page_height - band_height + 7 * mm,
                    height=logo_h, width=logo_h, preserveAspectRatio=True, mask='auto'
                )
                text_x = 20 * mm + logo_h + 5 * mm
            except Exception:
                pass

        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(text_x, page_height - 14 * mm, "MAH QUANTUM")
        canvas_obj.setFont("Helvetica", 9.5)
        canvas_obj.drawString(text_x, page_height - 20 * mm, "Thermal Digital Twin — ASIC FEM Analysis Report")

        canvas_obj.setFont("Helvetica", 8.5)
        canvas_obj.drawRightString(
            page_width - 20 * mm, page_height - 20 * mm,
            datetime.datetime.now().strftime('%Y-%m-%d  %H:%M')
        )

        canvas_obj.setStrokeColor(colors.HexColor("#d0d3d8"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(20 * mm, 14 * mm, page_width - 20 * mm, 14 * mm)

        canvas_obj.setFillColor(MUTED_TEXT)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(20 * mm, 10 * mm, "Confidential — MAH Quantum Engineering Document")
        canvas_obj.drawRightString(page_width - 20 * mm, 10 * mm, f"Page {doc.page}")
        canvas_obj.restoreState()


def _section_title(text):
    style = ParagraphStyle("SectionTitle", fontName="Helvetica-Bold", fontSize=12.5,
                            textColor=NAVY, spaceBefore=4, spaceAfter=6)
    return Paragraph(text, style)


def _body_text(text):
    style = ParagraphStyle("Body", fontName="Helvetica", fontSize=9.5,
                            textColor=DARK_TEXT, leading=14, spaceAfter=8)
    return Paragraph(text, style)


def _kv_table(rows, col_widths=(60 * mm, 100 * mm)):
    data = [[Paragraph(f"<b>{k}</b>", ParagraphStyle("k", fontSize=9.5, textColor=DARK_TEXT)),
             Paragraph(str(v), ParagraphStyle("v", fontSize=9.5, textColor=DARK_TEXT))]
            for k, v in rows]
    t = Table(data, colWidths=col_widths)
    style = [
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d0d3d8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e3e5e8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    t.setStyle(TableStyle(style))
    return t


def _heat_sources_table(heat_sources):
    header = ["Block Name", "X-Range (mm)", "Y-Range (mm)", "Power Temp (°C)"]
    data = [[Paragraph(f"<b>{h}</b>", ParagraphStyle("h", fontSize=9, textColor=colors.white)) for h in header]]
    for src in heat_sources:
        data.append([
            Paragraph(src["name"], ParagraphStyle("c", fontSize=9, textColor=DARK_TEXT)),
            Paragraph(f"{src['x_range'][0]} – {src['x_range'][1]}", ParagraphStyle("c", fontSize=9, textColor=DARK_TEXT)),
            Paragraph(f"{src['y_range'][0]} – {src['y_range'][1]}", ParagraphStyle("c", fontSize=9, textColor=DARK_TEXT)),
            Paragraph(f"{src['power_temp']}", ParagraphStyle("c", fontSize=9, textColor=DARK_TEXT)),
        ])
    t = Table(data, colWidths=[45 * mm, 38 * mm, 38 * mm, 38 * mm])
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d0d3d8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e3e5e8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GREY))
    t.setStyle(TableStyle(style))
    return t


def generate_pdf_report(report, material, config, heatmap_image_path,
                         history_image_path=None,
                         save_path="../outputs/thermal_report.pdf"):

    doc = SimpleDocTemplate(
        save_path, pagesize=A4,
        topMargin=36 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm
    )

    elements = []

    # ================= PAGE 1: Executive Summary =================
    elements.append(_section_title("Executive Summary"))
    max_temp = report['max_temp']
    severity_color = DANGER_RED if max_temp >= 100 else (WARNING_AMBER if max_temp >= 85 else SAFE_GREEN)
    severity_label = (
        "Critical — exceeds 100°C, active cooling intervention recommended" if max_temp >= 100
        else "Elevated — monitor under sustained load" if max_temp >= 85
        else "Within nominal operating range"
    )

    summary_text = (
        f"A finite-element thermal simulation was performed on a {config['width']} mm × {config['height']} mm "
        f"semiconductor die fabricated from <b>{material}</b>, discretized into a {config['nx']} × {config['ny']} "
        f"computational mesh. The model incorporates {len(config['heat_sources'])} independent heat-generating "
        f"functional blocks under an ambient boundary temperature of {config['ambient_temp']}°C. "
        f"The transient heat diffusion equation was solved over {config['iterations']} time steps using an "
        f"implicit (Backward Euler) scheme with convective boundary cooling."
    )
    elements.append(_body_text(summary_text))

    elements.append(_kv_table([
        ("Peak Junction Temperature", f"{max_temp:.2f} °C"),
        ("Thermal Status", severity_label),
        ("Average Die Temperature", f"{report['avg_temp']:.2f} °C"),
        ("Hotspot Coverage", f"{report['hotspot_count']} mesh cells exceed 80°C"),
    ]))
    elements.append(Spacer(1, 14))

    # ================= Chip Configuration =================
    elements.append(_section_title("Chip Configuration"))
    config_rows = [
        ("Material", material),
        ("Chip Dimensions", f"{config['width']} mm × {config['height']} mm"),
        ("Mesh Resolution", f"{config['nx']} × {config['ny']} elements"),
        ("Ambient Temperature", f"{config['ambient_temp']} °C"),
        ("Solver Iterations", str(config['iterations'])),
        ("Thermal Conductivity", f"{config.get('conductivity', 'N/A')} W/m·K"),
    ]
    elements.append(_kv_table(config_rows))
    elements.append(Spacer(1, 10))

    material_note = MATERIAL_NOTES.get(material, "")
    if material_note:
        elements.append(_body_text(f"<b>Material Note:</b> {material_note}"))
    elements.append(Spacer(1, 10))

    # ================= Heat Source Breakdown =================
    elements.append(_section_title("Heat Source Configuration"))
    elements.append(_heat_sources_table(config["heat_sources"]))
    elements.append(Spacer(1, 16))

    # ================= Hotspot Analysis Results =================
    elements.append(_section_title("Hotspot Analysis Results"))
    result_rows = [
        ("Maximum Temperature", f"{max_temp:.2f} °C"),
        ("Average Temperature", f"{report['avg_temp']:.2f} °C"),
        ("Temperature Variance", f"{report['variance']:.2f}"),
        ("Hotspot Cells (> 80°C)", str(report['hotspot_count'])),
    ]
    elements.append(_kv_table(result_rows))
    elements.append(Spacer(1, 6))

    status_style = ParagraphStyle("Status", fontName="Helvetica-Bold", fontSize=10, textColor=severity_color)
    elements.append(Paragraph(f"Status: {severity_label}", status_style))
    elements.append(PageBreak())

    # ================= PAGE 2: Thermal Distribution Map =================
    elements.append(_section_title("Thermal Distribution Map"))
    if heatmap_image_path and os.path.exists(heatmap_image_path):
        try:
            img = RLImage(heatmap_image_path, width=170 * mm, height=95 * mm)
            img.hAlign = "CENTER"
            elements.append(img)
        except Exception:
            elements.append(_body_text("Heatmap image could not be loaded."))
    else:
        elements.append(_body_text("Heatmap image not found."))
    elements.append(Spacer(1, 14))

    elements.append(_section_title("Peak Temperature Over Time"))
    if history_image_path and os.path.exists(history_image_path):
        try:
            img2 = RLImage(history_image_path, width=170 * mm, height=80 * mm)
            img2.hAlign = "CENTER"
            elements.append(img2)
        except Exception:
            elements.append(_body_text("Time-history graph could not be loaded."))
    else:
        elements.append(_body_text(
            "Time-history graph not provided. Peak temperature stabilized at "
            f"{max_temp:.2f} °C across the simulated time window."
        ))
    elements.append(Spacer(1, 16))

    # ================= Engineering Recommendations =================
    elements.append(_section_title("Engineering Recommendations"))
    recommendations = []
    if max_temp >= 100:
        recommendations.append(
            "Peak temperature exceeds 100°C. Consider switching to a higher-conductivity material "
            "(e.g. Copper or Diamond), increasing convective cooling, or redistributing high-power blocks "
            "further apart to reduce localized thermal density."
        )
    else:
        recommendations.append(
            "Peak temperature is within an acceptable range for the simulated configuration. "
            "Continued monitoring under sustained operating load is recommended."
        )
    if report['variance'] > 400:
        recommendations.append(
            "High temperature variance indicates significant thermal gradients across the die. "
            "A thermally conductive interposer or heat-spreading layer may help homogenize the temperature profile."
        )
    recommendations.append(
        "This simulation uses a simplified single-layer FEM model with convective boundary cooling. "
        "Results should be validated against physical prototype measurements before production sign-off."
    )
    for rec in recommendations:
        elements.append(_body_text(f"• {rec}"))

    elements.append(Spacer(1, 18))
    closing_style = ParagraphStyle("Closing", fontName="Helvetica-Oblique", fontSize=8.5,
                                    textColor=MUTED_TEXT, leading=12)
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d0d3d8")))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Generated automatically by the Thermal Digital Twin engine. "
        "Results are simulation estimates derived from a finite-element approximation and should be "
        "validated against physical measurements before production sign-off.", closing_style
    ))

    on_page = _HeaderFooterCanvas(material)
    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

    return save_path