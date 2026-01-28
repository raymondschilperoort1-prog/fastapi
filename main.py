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
    version="4.0.0",
    description="Accountant-grade jaarrekening PDF met tabellen + cover + inhoud + toelichting."
)

# =====================================================
# ✅ BASIC ENDPOINTS
# =====================================================

@app.get("/")
def home():
    return {"status": "Accountant API draait ✅ (v4.0)"}


@app.get("/version")
def version():
    return {"version": "Accountant API v4.0 ✅ PDF met tabellen"}


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
# ✅ PDF BUILDER HELPERS (TABLE STYLE)
# =====================================================

class AccountantPDF(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "Jaarrekening (Accountant Style)", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 10, f"Pagina {self.page_no()}", align="C")


def table_row(pdf, col1, col2):
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(110, 8, col1, border=0)
    pdf.cell(60, 8, col2, border=0, ln=True, align="R")


def section_title(pdf, title):
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_draw_color(0)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)


# =====================================================
# ✅ PDF GENERATOR v4.0 (EXACT ACCOUNTANT STYLE)
# =====================================================

@app.post("/generate-annual-report-pdf")
def generate_report_pdf(data: AnnualReportRequest):

    filename = f"/tmp/jaarrekening_{uuid.uuid4().hex}.pdf"

    pdf = AccountantPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =====================================================
    # ✅ COVER PAGE
    # =====================================================

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 20, "JAARREKENING", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, data.company_name, ln=True, align="C")
    pdf.cell(0, 10, f"Boekjaar {data.fiscal_year}", ln=True, align="C")

    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Opgesteld conform RJ Microrechtspersonen", ln=True, align="C")

    # =====================================================
    # ✅ PAGE 2 — INHOUDSOPGAVE LOOK
    # =====================================================

    pdf.add_page()
    section_title(pdf, "INHOUDSOPGAVE")

    table_row(pdf, "1. Samenstellingsverklaring", "Pagina 3")
    table_row(pdf, "2. Balans", "Pagina 4")
    table_row(pdf, "3. Winst- en verliesrekening", "Pagina 5")
    table_row(pdf, "4. Grondslagen", "Pagina 6")
    table_row(pdf, "5. Toelichting balansposten", "Pagina 7")
    table_row(pdf, "6. Overige gegevens", "Pagina 8")
    table_row(pdf, "7. Ondertekening", "Pagina 9")

    # =====================================================
    # ✅ PAGE 3 — SAMENSTELLINGSVERKLARING
    # =====================================================

    pdf.add_page()
    section_title(pdf, "1. SAMENSTELLINGSVERKLARING")

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        f"De jaarrekening van {data.company_name} over boekjaar {data.fiscal_year} "
        "is samengesteld op basis van de door de directie verstrekte gegevens.\n\n"
        "Er is geen accountantscontrole toegepast.\n\n"
        "Deze jaarrekening is bedoeld voor interne rapportage."
    )

    # =====================================================
    # ✅ PAGE 4 — BALANS MET TABELLEN
    # =====================================================

    pdf.add_page()
    section_title(pdf, f"2. BALANS PER 31-12-{data.fiscal_year}")

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "ACTIVA", ln=True)

    table_row(pdf, "Vaste activa", f"€ {data.balance_sheet.fixed_assets:,.2f}")
    table_row(pdf, "Vlottende activa", f"€ {data.balance_sheet.current_assets:,.2f}")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 8, "Totaal activa", border="T")
    pdf.cell(
        60, 8,
        f"€ {(data.balance_sheet.fixed_assets + data.balance_sheet.current_assets):,.2f}",
        border="T",
        ln=True,
        align="R"
    )

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "PASSIVA", ln=True)

    table_row(pdf, "Eigen vermogen", f"€ {data.balance_sheet.equity:,.2f}")
    table_row(pdf, "Langlopende schulden", f"€ {data.balance_sheet.long_term_liabilities:,.2f}")
    table_row(pdf, "Kortlopende schulden", f"€ {data.balance_sheet.short_term_liabilities:,.2f}")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(110, 8, "Totaal passiva", border="T")
    pdf.cell(
        60, 8,
        f"€ {(data.balance_sheet.equity + data.balance_sheet.long_term_liabilities + data.balance_sheet.short_term_liabilities):,.2f}",
        border="T",
        ln=True,
        align="R"
    )

    # =====================================================
    # ✅ PAGE 5 — WINST & VERLIES TABELLEN
    # =====================================================

    pdf.add_page()
    section_title(pdf, "3. WINST- EN VERLIESREKENING")

    table_row(pdf, "Omzet", f"€ {data.profit_and_loss.revenue:,.2f}")
    table_row(pdf, "Kostprijs omzet", f"€ {data.profit_and_loss.cost_of_sales:,.2f}")

    brutowinst = data.profit_and_loss.revenue - data.profit_and_loss.cost_of_sales
    pdf.set_font("Helvetica", "B", 10)
    table_row(pdf, "Brutowinst", f"€ {brutowinst:,.2f}")

    pdf.ln(4)
    table_row(pdf, "Operationele kosten", f"€ {data.profit_and_loss.operating_expenses:,.2f}")
    table_row(pdf, "Personeelskosten", f"€ {data.profit_and_loss.personnel_costs:,.2f}")
    table_row(pdf, "Financieel resultaat", f"€ {data.profit_and_loss.financial_result:,.2f}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 11)
    table_row(pdf, "Nettoresultaat", f"€ {data.profit_and_loss.net_profit:,.2f}")

    # =====================================================
    # ✅ PAGE 6 — GRONDSLAGEN
    # =====================================================

    pdf.add_page()
    section_title(pdf, "4. GRONDSLAGEN")

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0, 7,
        "De jaarrekening is opgesteld overeenkomstig de Richtlijnen voor de Jaarverslaggeving "
        "voor microrechtspersonen.\n\n"
        "Activa en passiva worden gewaardeerd tegen verkrijgingsprijs.\n\n"
        "Materiële vaste activa worden lineair afgeschreven."
    )

    # =====================================================
    # ✅ PAGE 7 — TOELICHTING
    # =====================================================

    pdf.add_page()
    section_title(pdf, "5. TOELICHTING BALANSPOSTEN")

    pdf.multi_cell(
        0, 7,
        f"Eigen vermogen per balansdatum bedraagt € {data.balance_sheet.equity:,.2f}.\n\n"
        f"Langlopende schulden: € {data.balance_sheet.long_term_liabilities:,.2f}\n"
        f"Kortlopende schulden: € {data.balance_sheet.short_term_liabilities:,.2f}"
    )

    # =====================================================
    # ✅ PAGE 8 — OVERIGE
    # =====================================================

    pdf.add_page()
    section_title(pdf, "6. OVERIGE GEGEVENS")

    pdf.multi_cell(
        0, 7,
        "Gedurende het boekjaar waren er geen werknemers in dienst.\n\n"
        "Er hebben zich geen materiële gebeurtenissen voorgedaan na balansdatum."
    )

    # =====================================================
    # ✅ PAGE 9 — SIGNATURE
    # =====================================================

    pdf.add_page()
    section_title(pdf, "7. ONDERTEKENING")

    pdf.ln(15)
    pdf.cell(0, 10, "Opgemaakt te: ____________________", ln=True)
    pdf.cell(0, 10, "Datum: _________________________", ln=True)
    pdf.cell(0, 10, "Directie: _______________________", ln=True)

    # ✅ Save PDF
    pdf.output(filename)

    return FileResponse(
        filename,
        media_type="application/pdf",
        filename="jaarrekening_v4_accountant.pdf"
    )
