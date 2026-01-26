from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

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


@app.get("/")
def home():
    return {"status": "Accountant API draait ✅"}


@app.post("/generate-annual-report")
def generate_report(data: AnnualReportRequest):

    report_text = f"""
JAARREKENING {data.company_name}
Boekjaar: {data.fiscal_year}

BALANS PER 31-12-{data.fiscal_year}
Vaste activa: {data.balance_sheet.fixed_assets:.2f}
Vlottende activa: {data.balance_sheet.current_assets:.2f}

Eigen vermogen: {data.balance_sheet.equity:.2f}
Langlopende schulden: {data.balance_sheet.long_term_liabilities:.2f}
Kortlopende schulden: {data.balance_sheet.short_term_liabilities:.2f}

WINST- EN VERLIESREKENING
Omzet: {data.profit_and_loss.revenue:.2f}
Nettoresultaat: {data.profit_and_loss.net_profit:.2f}
"""
    return {"document_text": report_text}
# ✅ Privacy endpoint moet hier staan (helemaal buiten)
@app.get("/privacy")
def privacy():
    return {
        "policy": "Deze API verwerkt alleen boekhoudgegevens voor rapportage en slaat niets permanent op."
    }
