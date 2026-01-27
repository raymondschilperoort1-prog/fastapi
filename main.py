from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fpdf import FPDF
import uuid

app = FastAPI(
    title="Strikte Boekhoud Partner API",
    version="1.0.0",
    description="Genereert formele jaarstukken en jaarrekeningen zonder logo."
)

# =====================================================
# ✅ VERSION ENDPOINT (debug)
# =====================================================

@app.get("/version")
def version():
    return {"version": "Accountant API v1.0 ✅ Live"}

# =====================================================
# ✅ HOME ENDPOINT
# =====================================================

@app.get("/")
def home():
    return {"status": "Accountant API draait ✅"}

# =====================================================
# ✅ PRIVACY ENDPOINT (Actions requirement)
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
    net_profit: float


class AnnualReportRequest(BaseModel):
    company_name: str
    fiscal_year: str
    balance_sheet: BalanceSheet
    profit_and_loss: ProfitLoss


# =====================================================
# ✅ TEXT REPORT GENERATOR
# =====================================================

@app.post("/generate-annual-report")
def generate_report(data: AnnualReportRequest):

    report_text = f"""
JAARREKENING — {data.company_name}
Boekjaar: {data.fiscal_year}

--------------------------------------------------
BALANS PER 31-12-{data.fiscal_year}

Vaste activa:              € {data.balance_sheet.fixed_assets:,.2f}
Vlottende activa:          € {data.balance_sheet.current_assets:,.2f}

Eigen vermogen:            € {data.balance_sheet.equity:,.2f}

Langlopende schulden:      € {data.balance_sheet.long_term_liabilities:,.2f}
Kortlopende schulden:      € {data.balance_sheet.short_term_liabilities:,.2f}

--------------------------------------------------
WINST- EN VERLIESREKENING

Omzet:                     € {data.profit_and_loss.revenue:,.2f}
Nettoresultaat:            € {data.profit_and_loss.net_profit:,.2f}

--------------------------------------------------
Document opgesteld voor interne rapportage.
    """

    return {"document_text": report_text.strip()}


# =====================================================
# ✅ PDF REPORT GENERATOR
# =====================================================

@app.post("/generate-annual-report-pdf")
def generate_report_pdf(data: AnnualReportRequest):

    # Generate report text first
    result = generate_report(data)
    text = result["document_text"]

    # Unique filename per request
    filename = f"jaarrekening_{uuid.uuid4().hex}.pdf"

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.cell(0, 8, line, ln=True)

    pdf.output(filename)

    # Return PDF as downloadable file
    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="jaarrekening.pdf"
    )

