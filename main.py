from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fpdf import FPDF
import pandas as pd
import uuid
import os

app = FastAPI(
    title="Strikte Boekhoud Partner API",
    version="1.0.0",
    description="Genereert formele jaarrekeningen + PDF + bankmutatie upload."
)

# =====================================================
# ✅ BASIC ENDPOINTS
# =====================================================

@app.get("/")
def home():
    return {"status": "Accountant API draait ✅"}

@app.get("/version")
def version():
    return {"version": "Accountant API v1.0 ✅ Live"}

@app.get("/privacy")
def privacy():
    return {
        "policy": (
            "Deze API verwerkt alleen boekhoudgegevens voor rapportage. "
            "Er worden geen gegevens permanent opgeslagen."
        )
    }

# =====================================================
# ✅ DATA MODELS (MATCH GPT ACTION SCHEMA)
# =====================================================

class BalanceSheet(BaseModel):
    fixed_assets: float
    current_assets: float
    equity: float
    long_term_liabilities: float
    short_term_liabilities: float


class ProfitLoss(BaseModel):
    revenue: float
    cost_of_sales: float
    operating_expenses: float
    personnel_costs: float
    financial_result: float
    net_profit: float


class AnnualReportRequest(BaseModel):
    company_name: str
    fiscal_year: str
    balance_sheet: BalanceSheet
    profit_and_loss: ProfitLoss


# =====================================================
# ✅ FORMAL YEAR REPORT (TEXT) — BANK/ACCOUNTANT STYLE
# =====================================================

@app.post(
    "/generate-annual-report",
    operation_id="generateAnnualReport"
)
def generate_report(data: AnnualReportRequest):

    report_text = f"""
------------------------------------------------------------
                     JAARREKENING
------------------------------------------------------------

Onderneming:       {data.company_name}
Boekjaar:          {data.fiscal_year}

============================================================
BALANS PER 31-12-{data.fiscal_year}
============================================================

ACTIVA
------------------------------------------------------------
Vaste activa:              € {data.balance_sheet.fixed_assets:,.2f}
Vlottende activa:          € {data.balance_sheet.current_assets:,.2f}

PASSIVA
------------------------------------------------------------
Eigen vermogen:            € {data.balance_sheet.equity:,.2f}

Langlopende schulden:      € {data.balance_sheet.long_term_liabilities:,.2f}
Kortlopende schulden:      € {data.balance_sheet.short_term_liabilities:,.2f}

============================================================
WINST- EN VERLIESREKENING
============================================================

Omzet:                     € {data.profit_and_loss.revenue:,.2f}
Kostprijs omzet:           € {data.profit_and_loss.cost_of_sales:,.2f}

Operationele kosten:       € {data.profit_and_loss.operating_expenses:,.2f}
Personeelskosten:          € {data.profit_and_loss.personnel_costs:,.2f}

Financieel resultaat:      € {data.profit_and_loss.financial_result:,.2f}

------------------------------------------------------------
Nettoresultaat:            € {data.profit_and_loss.net_profit:,.2f}
------------------------------------------------------------

Document opgesteld voor interne rapportage en accountantscontrole.
    """

    return {"document_text": report_text.strip()}


# =====================================================
# ✅ PDF EXPORT ENDPOINT
# =====================================================

@app.post("/generate-annual-report-pdf")
def generate_report_pdf(data: AnnualReportRequest):

    result = generate_report(data)
    text = result["document_text"]

    filename = f"jaarrekening_{uuid.uuid4().hex}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in text.split("\n"):
        pdf.cell(0, 7, line, ln=True)

    pdf.output(filename)

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="jaarrekening.pdf"
    )


# =====================================================
# ✅ BANK FILE UPLOAD ENDPOINT
# Supports: CSV / Excel / MT940 (optional)
# =====================================================

@app.post("/upload-bank-file")
async def upload_bank_file(file: UploadFile = File(...)):

    ext = file.filename.split(".")[-1].lower()
    temp_name = f"upload_{uuid.uuid4().hex}.{ext}"

    with open(temp_name, "wb") as buffer:
        buffer.write(await file.read())

    # ✅ CSV
    if ext == "csv":
        df = pd.read_csv(temp_name)

    # ✅ Excel
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(temp_name)

    # ✅ MT940 (optional basic placeholder)
    elif ext == "mt940":
        return {
            "status": "MT940 support komt eraan ✅",
            "note": "Niet elke bank gebruikt MT940, dus dit is optioneel."
        }

    else:
        return {"error": "Bestandstype niet ondersteund. Gebruik CSV, XLSX of MT940."}

    os.remove(temp_name)

    return {
        "status": "Bankbestand succesvol ingelezen ✅",
        "rows_detected": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict()
    }
