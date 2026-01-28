@app.post(
    "/generate-annual-report",
    operation_id="generateAnnualReport"
)
def generate_report(data: AnnualReportRequest):

    # Berekeningen
    total_assets = data.balance_sheet.fixed_assets + data.balance_sheet.current_assets
    total_liabilities = data.balance_sheet.long_term_liabilities + data.balance_sheet.short_term_liabilities

    profit_before_tax = data.profit_and_loss.net_profit
    corporate_tax = profit_before_tax * 0.19  # simpele VPB schatting 19%
    profit_after_tax = profit_before_tax - corporate_tax

    report_text = f"""
============================================================
                     JAARREKENING
============================================================

Onderneming:     {data.company_name}
Boekjaar:        {data.fiscal_year}

Opgesteld voor interne rapportagedoeleinden
============================================================


1. BALANS PER 31 DECEMBER {data.fiscal_year}
------------------------------------------------------------

ACTIVA

Vaste activa
  Materiële vaste activa            € {data.balance_sheet.fixed_assets:,.2f}

Vlottende activa
  Vorderingen en overlopende activa € {data.balance_sheet.current_assets:,.2f}

------------------------------------------------------------
TOTAAL ACTIVA                         € {total_assets:,.2f}


PASSIVA

Eigen vermogen
  Gestort en opgevraagd kapitaal     € {data.balance_sheet.equity:,.2f}

Langlopende schulden
  Leningen                           € {data.balance_sheet.long_term_liabilities:,.2f}

Kortlopende schulden
  Crediteuren en overlopende posten   € {data.balance_sheet.short_term_liabilities:,.2f}

------------------------------------------------------------
TOTAAL PASSIVA                        € {(data.balance_sheet.equity + total_liabilities):,.2f}


2. WINST- EN VERLIESREKENING {data.fiscal_year}
------------------------------------------------------------

Omzet                                   € {data.profit_and_loss.revenue:,.2f}

Bedrijfskosten                          € {(data.profit_and_loss.revenue - data.profit_and_loss.net_profit):,.2f}

------------------------------------------------------------
Resultaat vóór belasting                 € {profit_before_tax:,.2f}

Vennootschapsbelasting (indicatief)      € {corporate_tax:,.2f}

------------------------------------------------------------
Resultaat na belasting                   € {profit_after_tax:,.2f}


3. TOELICHTING
------------------------------------------------------------

Algemeen
De jaarrekening is opgesteld conform de in Nederland algemeen
aanvaarde grondslagen voor financiële verslaggeving.

Waarderingsgrondslagen
- Activa worden gewaardeerd tegen verkrijgingsprijs.
- Schulden worden opgenomen tegen nominale waarde.
- Resultaten worden toegerekend aan het boekjaar waarop
  zij betrekking hebben.

Continuïteit
De jaarrekening is opgesteld uitgaande van continuïteit
van de onderneming.


4. MUTATIE EIGEN VERMOGEN
------------------------------------------------------------

Eigen vermogen begin boekjaar            € 0,00
Resultaat boekjaar                       € {profit_after_tax:,.2f}

------------------------------------------------------------
Eigen vermogen einde boekjaar            € {data.balance_sheet.equity:,.2f}

============================================================
Einde Jaarrekening
============================================================
"""

    return {"document_text": report_text.strip()}
