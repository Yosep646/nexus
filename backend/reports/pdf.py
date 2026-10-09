"""Generate a printable detection report without disclosing camera stream URLs."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from backend.database.storage import connect


def build_report(limit=200):
    with connect() as db:
        events = [dict(row) for row in db.execute(
            """SELECT d.created_at, c.name AS camera, d.label, d.confidence,
                      d.review_status FROM detections d
               JOIN cameras c ON c.id=d.camera_id
               ORDER BY d.created_at DESC LIMIT ?""", (min(max(limit, 1), 500),))]
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title="NEXUS RISK AI - Reporte",
                                 leftMargin=36, rightMargin=36)
    styles = getSampleStyleSheet()
    content = [Paragraph("NEXUS RISK AI | Reporte de detecciones", styles["Title"]),
               Paragraph("Eventos registrados. La clasificacion automatica requiere revision humana.", styles["Normal"]),
               Spacer(1, 16)]
    header = ["Fecha (UTC)", "Camara", "Fenomeno", "Conf.", "Revision"]
    rows = [header]
    for item in events:
        rows.append([
            Paragraph(escape(str(item["created_at"])[:19]), styles["BodyText"]),
            Paragraph(escape(str(item["camera"])[:35]), styles["BodyText"]),
            Paragraph(escape(str(item["label"])[:35]), styles["BodyText"]),
            f'{float(item["confidence"]):.1%}',
            Paragraph(escape(str(item["review_status"])), styles["BodyText"]),
        ])
    if not events:
        content.append(Paragraph("No hay detecciones registradas.", styles["Normal"]))
    else:
        table = Table(rows, colWidths=[103, 100, 100, 45, 120], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        content.append(table)
    document.build(content)
    return buffer.getvalue()
