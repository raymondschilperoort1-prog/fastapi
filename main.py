from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os
from fpdf import FPDF

app = FastAPI(
    title="Accountant Jaarstukken API",
    version="2.0.0"
)

# -----------------------------
# Input modellen
# -----------------------------

class BalanceSheet(BaseModel):
    fixed_assets: float
    current_assets: float
    equity_start: float
    long_term_liabilities: float
    short_term_liabilities: float


class ProfitLoss(BaseModel):
    revenue: float
    cost_of_sales: float
    operating_expenses: float
    personnel_costs: float
    financial_result: float
    tax_rate: float  # VPB percentage


class AnnualReportRequest(BaseModel):
    company_name: str
    fiscal_year: str
    balance_sheet: BalanceSheet
    profit_and_loss: ProfitLoss


# -----------------------------
# Jaarrekening tekst (NL Model)
# -----------------------------

@app.post("/generate-annual-report")
def generate_report(data: AnnualReportRequest):

    # Resultaat berekenen
    gross_profit = data.profit_and_loss.revenue - data.profit_and_loss.cost_of_sales
    profit_before_tax = (
        gross_profit
        - data.profit_and_loss.operating_expenses
        - data.profit_and_loss.personnel_costs
        + data.profit_and_loss.financial_result
    )

    tax = profit_before_tax * (data.profit_and_loss.tax_rate / 100)
    net_profit = profit_before_tax - tax

    # EV mutatie
    equity_end = data.balance_sheet.equity_start + net_profit

    report_text = f"""
JAARREKENING {data.company_name}
Boekjaar: {data.fiscal_year}

==============================
BALANS PER 31-12-{data.fiscal_year}
==============================

ACTIVA
Vaste activa:                 € {data.balance_sheet.fixed_assets:,.2f}
Vlottende activa:             € {data.balance_sheet.current_assets:,.2f}

PASSIVA
Eigen vermogen begin:         € {data.balance_sheet.equity_start:,.2f}
Resultaat boekjaar:           € {net_profit:,.2f}
Eigen vermogen einde:         € {equity_end:,.2f}

Langlopende schulden:         € {data.balance_sheet.long_term_liabilities:,.2f}
Kortlopende schulden:         € {data.balance_sheet.short_term_liabilities:,.2f}

==============================
WINST- EN VERLIESREKENING
==============================

Omzet:                        € {data.profit_and_loss.revenue:,.2f}
Kostprijs omzet:              € {data.profit_and_loss.cost_of_sales:,.2f}
Brutowinst:                   € {gross_profit:,.2f}

Operationele kosten:          € {data.profit_and_loss.operating_expenses:,.2f}
Personeelskosten:             € {data.profit_and_loss.personnel_costs:,.2f}
Financieel resultaat:         € {data.profit_and_loss.financial_result:,.2f}

Winst vóór belasting:         € {profit_before_tax:,.2f}
Vennootschapsbelasting ({data.profit_and_loss.tax_rate}%): € {tax:,.2f}

NETTO RESULTAAT:              € {net_profit:,.2f}

==============================
TOELICHTING
==============================
Deze jaarrekening is opgesteld op basis van aangeleverde cijfers.
De onderneming hanteert continuïteitsveronderstelling.
"""

    return {
        "document_text": report_text,
        "net_profit": net_profit,
        "equity_end": equity_end
    }


# -----------------------------
# PDF generatie endpoint
# -----------------------------

@app.post("/generate-annual-report-pdf")
def generate_report_pdf(data: AnnualReportRequest):

    result = generate_report(data)
    text = result["document_text"]

    filename = "jaarrekening.pdf"

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.cell(0, 8, line, ln=True)

    pdf.output(filename)

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename=filename
    )


# -----------------------------
# Privacy endpoint
# -----------------------------

@app.get("/privacy")
def privacy():
    return {
        "policy": "Deze API verwerkt uitsluitend boekhoudgegevens voor rapportage en slaat niets permanent op."
    }

