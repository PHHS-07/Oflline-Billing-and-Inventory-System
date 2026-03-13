from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BASE_DIR = Path(__file__).resolve().parent
INVOICE_DIR = BASE_DIR / "invoices"


def generate_invoice_pdf(invoice_no, customer_name, invoice_date, items, subtotal, gst, total):
    INVOICE_DIR.mkdir(exist_ok=True)
    pdf_path = INVOICE_DIR / f"invoice_{invoice_no}.pdf"

    document = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Invoice #{invoice_no}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Customer: {customer_name}", styles["Normal"]),
        Paragraph(f"Date: {invoice_date}", styles["Normal"]),
        Spacer(1, 16),
    ]

    table_rows = [["Product", "Qty", "Unit Price", "Line Total"]]
    for item in items:
        line_total = float(item["qty"]) * float(item["price"])
        table_rows.append(
            [
                item["name"],
                str(item["qty"]),
                f"{float(item['price']):.2f}",
                f"{line_total:.2f}",
            ]
        )

    summary_rows = [
        ["", "", "Subtotal", f"{subtotal:.2f}"],
        ["", "", "GST", f"{gst:.2f}"],
        ["", "", "Total", f"{total:.2f}"],
    ]
    table_rows.extend(summary_rows)

    table = Table(table_rows, colWidths=[210, 60, 90, 100])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -4), colors.whitesmoke),
                ("BACKGROUND", (2, -3), (-1, -1), colors.HexColor("#e8f1f8")),
                ("FONTNAME", (2, -3), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ]
        )
    )

    story.append(table)
    document.build(story)
    return pdf_path
