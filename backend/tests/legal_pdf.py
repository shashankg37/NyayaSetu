"""Build a small real-statute PDF for ingestion tests (Code on Wages, 2019)."""
from __future__ import annotations

from pathlib import Path

WAGES_PDF_TEXT = """THE GAZETTE OF INDIA
EXTRAORDINARY
MINISTRY OF LAW AND JUSTICE
Code on Wages, 2019

Section 17. Time limit for payment of wages.
The employer shall pay or cause to be paid wages to the employees on the due date.

Section 19. Deduction of wages.
Deductions from wages of an employee shall be made only in accordance with this Code.
"""


def write_code_on_wages_pdf(path: Path) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    y = height - 72
    for line in WAGES_PDF_TEXT.strip().splitlines():
        pdf.drawString(72, y, line[:110])
        y -= 16
        if y < 72:
            pdf.showPage()
            y = height - 72
    pdf.save()
    return path
