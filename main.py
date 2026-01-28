from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fpdf import FPDF
import pandas as pd
import uuid
import os
import csv
import io

app = FastAPI(
    title="Strikte Boekhoud Partner API",
    version="1.0.0",
    description="Genereert formele jaarrekeningen + PDF + bankmutatie upload + CSV jaarrekening generator."
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
# ✅ FORMAL YEAR REPORT (TEXT)
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
# ✅ PDF EXPORT ENDPOINT (SAFE FOR RAILWAY)
# =====================================================

@app.post("/generate-annual-report-pdf")
def generate_report_pdf(data: AnnualReportRequest):

    result = generate_report(data)
    text = result["document_text"]

    # ✅ Railway-safe filesystem location
    filename = f"/tmp/jaarrekening_{uuid.uuid4().hex}.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for line in text.split("\n"):
        pdf.multi_cell(0, 7, line)

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
    temp_name = f"/tmp/upload_{uuid.uuid4().hex}.{ext}"

    with open(temp_name, "wb") as buffer:
        buffer.write(await file.read())

    # ✅ CSV
    if ext == "csv":
        df = pd.read_csv(temp_name)

    # ✅ Excel
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(temp_name)

    # ✅ MT940 optional
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


# =====================================================
# ✅ CSV → DIRECT YEAR REPORT GENERATOR
# Upload 1 CSV → return jaarrekening tekst
# =====================================================

@app.post(
    "/generate-from-csv",
    operation_id="generateAnnualReportFromCSV"
)
async def generate_from_csv(file: UploadFile = File(...)):
    """
    CSV bestand met kolommen:

    company_name,fiscal_year,
    fixed_assets,current_assets,equity,
    long_term_liabilities,short_term_liabilities,
    revenue,cost_of_sales,operating_expenses,
    personnel_costs,financial_result,net_profit
    """

    contents = await file.read()
    text_stream = io.StringIO(contents.decode("utf-8"))
    reader = csv.DictReader(text_stream)

    rows = list(reader)

    if len(rows) == 0:
        return {"error": "CSV bevat geen data"}

    row = rows[0]

    # ✅ Convert CSV row into request model
    data = AnnualReportRequest(
        company_name=row["company_name"],
        fiscal_year=row["fiscal_year"],
        balance_sheet=BalanceSheet(
            fixed_assets=float(row["fixed_assets"]),
            current_assets=float(row["current_assets"]),
            equity=float(row["equity"]),
            long_term_liabilities=float(row["long_term_liabilities"]),
            short_term_liabilities=float(row["short_term_liabilities"]),
        ),
        profit_and_loss=ProfitLoss(
            revenue=float(row["revenue"]),
            cost_of_sales=float(row["cost_of_sales"]),
            operating_expenses=float(row["operating_expenses"]),
            personnel_costs=float(row["personnel_costs"]),
            financial_result=float(row["financial_result"]),
            net_profit=float(row["net_profit"]),
        ),
    )

    # ✅ Generate report using the same function
    return generate_report(data)
