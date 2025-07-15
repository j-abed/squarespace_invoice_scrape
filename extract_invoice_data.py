import os
import fitz  # PyMuPDF
import re

def extract_invoice_data(pdf_path):
    with fitz.open(pdf_path) as doc:
        text = "\n".join(page.get_text() for page in doc)

    # Extract invoice number
    invoice_match = re.search(r"#(\d{6,})", text)
    invoice_number = invoice_match.group(1) if invoice_match else "UNKNOWN"

    # Extract charge date (optional)
    charge_match = re.search(r"Charged on (.+)", text)
    charge_date = charge_match.group(1).strip() if charge_match else ""

    # Extract paid amount
    paid_match = re.search(r"Paid\s+\$([\d,]+\.\d{2})", text)
    amount_paid = paid_match.group(1) if paid_match else "NOT FOUND"

    return {
        "filename": os.path.basename(pdf_path),
        "invoice_number": invoice_number,
        "charge_date": charge_date,
        "amount_paid": amount_paid
    }
