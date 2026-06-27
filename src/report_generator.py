import os
import sys
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage, HRFlowable
)
from reportlab.platypus.flowables import Flowable

# ---------------------------------------------------------------------------
# Brand palette — navy / blue accent, clean corporate look (printer-friendly)
# ---------------------------------------------------------------------------
NAVY = colors.HexColor("#1a2540")
ACCENT_BLUE = colors.HexColor("#3b6ea5")
LIGHT_GREY = colors.HexColor("#f2f3f5")
DARK_TEXT = colors.HexColor("#1d1d1d")
MUTED_TEXT = colors.HexColor("#6b7280")
DANGER_RED = colors.HexColor("#c0392b")
SAFE_GREEN = colors.HexColor("#1e8449")

LOGO_CANDIDATES = ["../assets/logo.png", "assets/logo.png", "./assets/logo.png"]


def _find_logo():
    """Find logo.png whether running as a script or as a bundled .exe."""
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
    """Draws the navy header band and the footer on every page."""

    def __init__(self, material):
        self.material = material

    def __call__(self, canvas_obj, doc):
        canvas_obj.saveState()
        page_width, page_height = A4

        # ---- Header band ----
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

        # ---- Footer ----
        canvas_obj.setStrokeColor(colors.HexColor("#d0d3d8"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(20 * mm, 14 * mm, page_width - 20 * mm, 14 * mm)

        canvas_obj.setFillColor(MUTED_TEXT)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(20 * mm, 10 * mm, "Confidential — MAH Quantum Engineering Document")
        canvas_obj.drawRightString(page_width - 20 * mm, 10 * mm, f"Page {doc.page}")

        canvas_obj.restoreState()


def _section_title(text):
    style = ParagraphStyle(
        "SectionTitle", fontName="Helvetica-Bold", fontSize=12.5,
        textColor=NAVY, spaceBefore=4, spaceAfter=6
    )
    return Paragraph(text, style)


def _kv_table(rows, col_widths=(60 * mm, 100 * mm)):
    """Two-column key/value table with alternating row shading."""
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


def generate_pdf_report(report, material, config, heatmap_image_path,
                         save_path="../outputs/thermal_report.pdf"):

    doc = SimpleDocTemplate(
        save_path, pagesize=A4,
        topMargin=36 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm
    )

    elements = []
    styles = getSampleStyleSheet()

    intro_style = ParagraphStyle(
        "Intro", fontName="Helvetica", fontSize=9.5,
        textColor=MUTED_TEXT, leading=13, spaceAfter=10
    )
    elements.append(Paragraph(
        "This report summarizes the finite-element thermal simulation results for the "
        "configured ASIC layout, including chip configuration, hotspot statistics, and "
        "the resulting thermal distribution.", intro_style
    ))
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d0d3d8")))
    elements.append(Spacer(1, 8))

    # ---- Chip Configuration ----
    elements.append(_section_title("Chip Configuration"))
    config_rows = [
        ("Material", material),
        ("Chip Dimensions", f"{config['width']} mm × {config['height']} mm"),
        ("Mesh Resolution", f"{config['nx']} × {config['ny']}"),
        ("Ambient Temperature", f"{config['ambient_temp']} °C"),
        ("Solver Iterations", str(config['iterations'])),
    ]
    elements.append(_kv_table(config_rows))
    elements.append(Spacer(1, 14))

    # ---- Hotspot Analysis Results ----
    elements.append(_section_title("Hotspot Analysis Results"))

    max_temp = report['max_temp']
    severity_color = DANGER_RED if max_temp >= 100 else SAFE_GREEN
    severity_label = "Critical — exceeds 100°C" if max_temp >= 100 else "Within nominal range"

    result_rows = [
        ("Maximum Temperature", f"{max_temp:.2f} °C"),
        ("Average Temperature", f"{report['avg_temp']:.2f} °C"),
        ("Temperature Variance", f"{report['variance']:.2f}"),
        ("Hotspot Cells (> 80°C)", str(report['hotspot_count'])),
    ]
    elements.append(_kv_table(result_rows))
    elements.append(Spacer(1, 6))

    status_style = ParagraphStyle(
        "Status", fontName="Helvetica-Bold", fontSize=10, textColor=severity_color
    )
    elements.append(Paragraph(f"Status: {severity_label}", status_style))
    elements.append(Spacer(1, 16))

    # ---- Thermal Distribution Map ----
    elements.append(_section_title("Thermal Distribution Map"))
    if os.path.exists(heatmap_image_path):
        try:
            img = RLImage(heatmap_image_path, width=170 * mm, height=95 * mm)
            img.hAlign = "CENTER"
            elements.append(img)
        except Exception:
            elements.append(Paragraph(
                "Heatmap image could not be loaded.",
                ParagraphStyle("err", fontSize=9, textColor=DANGER_RED)
            ))
    else:
        elements.append(Paragraph(
            "Heatmap image not found.",
            ParagraphStyle("err", fontSize=9, textColor=DANGER_RED)
        ))

    elements.append(Spacer(1, 18))

    closing_style = ParagraphStyle(
        "Closing", fontName="Helvetica-Oblique", fontSize=8.5,
        textColor=MUTED_TEXT, leading=12
    )
    elements.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d0d3d8")))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "Generated automatically by the Thermal Digital Twin engine. "
        "Results are simulation estimates and should be validated against "
        "physical measurements before production sign-off.", closing_style
    ))

    on_page = _HeaderFooterCanvas(material)
    doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)

    return save_path