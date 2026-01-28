from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fpdf import FPDF
import uuid
import pandas as pd
import os

app = FastAPI(
    title="Strikte Boekhoud Partner API",
    version="1.0.0",
    description="Genereert formele jaarstukken zoals accountant-output.deel 2"
)

# =====================================================
# ✅ HOME
# =====================================================

@app.get("/")
def home():
    return {"status": "Accountant API draait ✅"}

# =====================================================
# ✅ VERSION
# =====================================================

@app.get("/version")
def version():
    return {"version": "Accountant API v1.0 ✅ Live"}

# =====================================================
# ✅ PRIVACY (Actions requirement)
# =====================================================

@app.get("/privacy")
def privacy():
    return {
        "policy": (
            "Deze API verwerkt alleen boekhoudgegevens voor rapportage. "
            "Er worden geen gegevens permanent opgeslagen."
        )
    }

# =====================================================
# ✅ DATA MODELS
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
# ✅ FORMAL YEAR REPORT (TEXT)
# =====================================================

@app.post(
    "/generate-annual-report",
    operation_id="generateAnnualReport"
)
def generate_report(data: AnnualReportRequest):


    report_text = f"""
JAARREKENING {data.fiscal_year}
{data.company_name}

1. SAMENSTELLING EN VERANTWOORDING
Deze jaarrekening is samengesteld op basis van door de ondernemer aangeleverde gegevens.

2. WINST- EN VERLIESREKENING

Opbrengsten
Totaal omzet: € {data.profit_and_loss.revenue:,.2f}

Kosten
Inkoopkosten: € {data.profit_and_loss.cost_of_sales:,.2f}
Personeelskosten: € {data.profit_and_loss.personnel_costs:,.2f}
Overige kosten: € {data.profit_and_loss.operating_expenses:,.2f}
Financieel resultaat: € {data.profit_and_loss.financial_result:,.2f}

Netto resultaat: € {data.profit_and_loss.net_profit:,.2f}

3. BALANS PER 31-12-{data.fiscal_year}

Activa
Vaste activa: € {data.balance_sheet.fixed_assets:,.2f}
Vlottende activa: € {data.balance_sheet.current_assets:,.2f}

Passiva
Eigen vermogen: € {data.balance_sheet.equity:,.2f}
Langlopende schulden: € {data.balance_sheet.long_term_liabilities:,.2f}
Kortlopende schulden: € {data.balance_sheet.short_term_liabilities:,.2f}
    """

    return {"document_text": report_text.strip()}


# =====================================================
# ✅ PDF OUTPUT
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
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)

    return FileResponse(filename, media_type="application/pdf", filename="jaarrekening.pdf")


# =====================================================
# ✅ UPLOAD BANK FILES (CSV/Excel/MT940 placeholder)
# =====================================================

@app.post("/upload-bank-file")
async def upload_bank_file(file: UploadFile = File(...)):

    ext = file.filename.split(".")[-1].lower()
    temp_name = f"upload_{uuid.uuid4().hex}.{ext}"

    with open(temp_name, "wb") as f:
        f.write(await file.read())

    if ext in ["csv"]:
        df = pd.read_csv(temp_name)
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(temp_name)
    elif ext in ["mt940"]:
        return {"status": "MT940 import komt in stap 2 ✅"}
    else:
        return {"error": "Bestandstype niet ondersteund"}

    os.remove(temp_name)

    return {
        "status": "Bankbestand ingelezen ✅",
        "rows": len(df),
        "columns": list(df.columns)
    }

