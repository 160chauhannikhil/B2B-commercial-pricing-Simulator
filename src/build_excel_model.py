"""
build_excel_model.py
---------------------
Builds excel/Commercial_Pricing_Model.xlsx with 8 sheets:
  1. Instructions
  2. Customers
  3. Products
  4. Historical Deals
  5. Pricing Calculator (live formulas)
  6. Scenario Analysis (live formulas)
  7. Risk Assessment (live formulas)
  8. Proposal Summary (live formulas, pulls from Pricing Calculator)

Color convention: blue = hardcoded input, black = formula, yellow fill = key
assumption / cell to edit.
"""

from pathlib import Path
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXCEL_PATH = BASE_DIR / "excel" / "Commercial_Pricing_Model.xlsx"

FONT_NAME = "Arial"
BLUE = Font(name=FONT_NAME, color="0000FF")
BLACK = Font(name=FONT_NAME, color="000000")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
YELLOW_FILL = PatternFill("solid", fgColor="FFFF00")
TITLE_FONT = Font(name=FONT_NAME, bold=True, size=14)
SECTION_FONT = Font(name=FONT_NAME, bold=True, size=11, color="1F4E78")
THIN = Side(style="thin", color="B7B7B7")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

CURRENCY_FMT = '$#,##0;($#,##0);-'
PCT_FMT = '0.0%'


def style_header_row(ws, row, n_cols, start_col=1):
    for c in range(start_col, start_col + n_cols):
        cell = ws.cell(row=row, column=c)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER


def write_dataframe(ws, df: pd.DataFrame, start_row=1, start_col=1):
    for j, col_name in enumerate(df.columns):
        ws.cell(row=start_row, column=start_col + j, value=col_name)
    style_header_row(ws, start_row, len(df.columns), start_col)
    for i, (_, row) in enumerate(df.iterrows()):
        for j, val in enumerate(row):
            cell = ws.cell(row=start_row + 1 + i, column=start_col + j, value=val)
            cell.font = BLACK
            cell.border = BORDER
    for j, col_name in enumerate(df.columns):
        col_letter = get_column_letter(start_col + j)
        max_len = max(len(str(col_name)), df[col_name].astype(str).map(len).max() if len(df) else 10)
        ws.column_dimensions[col_letter].width = min(max(max_len + 2, 10), 32)
    return start_row + 1 + len(df)


def build():
    customers = pd.read_csv(DATA_DIR / "customers.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    deals = pd.read_csv(DATA_DIR / "historical_deals.csv")

    wb = Workbook()

    # ---------------------------------------------------------------- Instructions
    ws = wb.active
    ws.title = "Instructions"
    ws["A1"] = "Commercial Proposal & Pricing Simulator — Excel Model"
    ws["A1"].font = TITLE_FONT
    lines = [
        "",
        "This workbook is a decision-support tool for evaluating B2B industrial sales proposals.",
        "It is built around a fictional company, InduTech Solutions, and a fully synthetic dataset.",
        "",
        "How to use this workbook:",
        "1. Go to the 'Pricing Calculator' sheet.",
        "2. Edit the YELLOW cells only (Customer, Product, Quantity, Discount, Competitor Price, "
        "Payment Terms, Expected Delivery Days, Target Margin).",
        "3. All other cells recalculate automatically using formulas (INDEX/MATCH lookups to "
        "Customers and Products, plus the pricing formulas below).",
        "4. Check 'Scenario Analysis' for a 5%/10%/15%/20% discount comparison.",
        "5. Check 'Risk Assessment' for the weighted commercial risk score.",
        "6. 'Proposal Summary' auto-builds a presentable summary from the Pricing Calculator inputs.",
        "",
        "Core formulas:",
        "  Revenue = Quantity x Quoted Unit Price",
        "  Total Cost = Base Cost + Installation + Maintenance + Warranty + Logistics + Other (x Quantity)",
        "  Gross Profit = Revenue - Total Cost",
        "  Gross Margin % = Gross Profit / Revenue",
        "  Minimum Price = Total Cost / (1 - Minimum Margin)",
        "  Target Price = Total Cost / (1 - Target Margin)",
        "",
        "Color legend:",
        "  Blue text   = hardcoded input / assumption",
        "  Black text  = formula (do not overwrite)",
        "  Yellow fill = cell you are expected to edit",
        "",
        "Limitations: dataset is synthetic; win probability and risk scores are simplified, "
        "configurable decision-support estimates, not guarantees or audited financial figures.",
    ]
    for i, line in enumerate(lines, start=2):
        cell = ws.cell(row=i, column=1, value=line)
        cell.font = BLACK if not line.startswith("Color") else BLACK
    ws.column_dimensions["A"].width = 110

    # ---------------------------------------------------------------- Customers
    ws = wb.create_sheet("Customers")
    write_dataframe(ws, customers)

    # ---------------------------------------------------------------- Products
    ws = wb.create_sheet("Products")
    write_dataframe(ws, products)

    # ---------------------------------------------------------------- Historical Deals
    ws = wb.create_sheet("Historical Deals")
    write_dataframe(ws, deals)

    n_customers = len(customers)
    n_products = len(products)

    # ---------------------------------------------------------------- Pricing Calculator
    ws = wb.create_sheet("Pricing Calculator")
    ws["A1"] = "Pricing Calculator"
    ws["A1"].font = TITLE_FONT

    labels_inputs = [
        ("Customer Name", customers["Customer_Name"].iloc[0]),
        ("Product Name", products["Product_Name"].iloc[0]),
        ("Quantity", 2),
        ("Other Cost (total)", 0),
        ("Discount %", 0.10),
        ("Competitor Price (total)", 250000),
        ("Payment Terms (days)", 45),
        ("Expected Delivery (days)", 50),
        ("Target Margin %", 0.25),
    ]
    row0 = 3
    for i, (label, val) in enumerate(labels_inputs):
        r = row0 + i
        ws.cell(row=r, column=1, value=label).font = SECTION_FONT
        cell = ws.cell(row=r, column=2, value=val)
        cell.font = BLUE
        cell.fill = YELLOW_FILL
        cell.border = BORDER
        if label == "Discount %" or label == "Target Margin %":
            cell.number_format = PCT_FMT

    # Named rows for readability
    (CUSTOMER_ROW, PRODUCT_ROW, QTY_ROW, OTHERCOST_ROW, DISC_ROW, COMP_ROW,
     PAYTERM_ROW, DELIVERY_ROW, TARGETMARGIN_ROW) = range(row0, row0 + 9)

    # Data validation dropdowns
    dv_cust = DataValidation(type="list", formula1=f"=Customers!$B$2:$B${n_customers + 1}", allow_blank=False)
    ws.add_data_validation(dv_cust)
    dv_cust.add(ws.cell(row=CUSTOMER_ROW, column=2))

    dv_prod = DataValidation(type="list", formula1=f"=Products!$B$2:$B${n_products + 1}", allow_blank=False)
    ws.add_data_validation(dv_prod)
    dv_prod.add(ws.cell(row=PRODUCT_ROW, column=2))

    # Lookup block (from Customers / Products sheets via INDEX/MATCH)
    lookup_start = row0 + 11
    ws.cell(row=lookup_start - 1, column=1, value="Looked-up Customer & Product Data").font = SECTION_FONT

    lookups = [
        ("Historical Win Rate", f"=INDEX(Customers!$I$2:$I${n_customers+1},MATCH($B${CUSTOMER_ROW},Customers!$B$2:$B${n_customers+1},0))", PCT_FMT),
        ("Relationship Years", f"=INDEX(Customers!$L$2:$L${n_customers+1},MATCH($B${CUSTOMER_ROW},Customers!$B$2:$B${n_customers+1},0))", None),
        ("Strategic Account (1/0)", f"=INDEX(Customers!$M$2:$M${n_customers+1},MATCH($B${CUSTOMER_ROW},Customers!$B$2:$B${n_customers+1},0))", None),
        ("Customer Risk Level", f"=INDEX(Customers!$N$2:$N${n_customers+1},MATCH($B${CUSTOMER_ROW},Customers!$B$2:$B${n_customers+1},0))", None),
        ("Base Cost (unit)", f"=INDEX(Products!$D$2:$D${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Standard Price (unit)", f"=INDEX(Products!$E$2:$E${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Installation Cost (unit)", f"=INDEX(Products!$F$2:$F${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Warranty Cost (unit)", f"=INDEX(Products!$G$2:$G${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Maintenance Cost (unit)", f"=INDEX(Products!$H$2:$H${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Logistics Cost (unit)", f"=INDEX(Products!$I$2:$I${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", CURRENCY_FMT),
        ("Minimum Margin %", f"=INDEX(Products!$J$2:$J${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", PCT_FMT),
        ("Maximum Discount %", f"=INDEX(Products!$K$2:$K${n_products+1},MATCH($B${PRODUCT_ROW},Products!$B$2:$B${n_products+1},0))", PCT_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(lookups):
        r = lookup_start + i
        ws.cell(row=r, column=1, value=label).font = BLACK
        cell = ws.cell(row=r, column=2, value=formula)
        cell.font = BLACK
        cell.border = BORDER
        if fmt:
            cell.number_format = fmt

    (WINRATE_ROW, RELYEARS_ROW, STRATEGIC_ROW, CUSTRISK_ROW, BASECOST_ROW, STDPRICE_ROW,
     INSTALL_ROW, WARRANTY_ROW, MAINT_ROW, LOGISTICS_ROW, MINMARGIN_ROW, MAXDISC_ROW) = range(
        lookup_start, lookup_start + 12)

    # Calculation block
    calc_start = lookup_start + 14
    ws.cell(row=calc_start - 1, column=1, value="Pricing Calculation").font = SECTION_FONT

    calcs = [
        ("Total Cost", f"=($B${BASECOST_ROW}+$B${INSTALL_ROW}+$B${MAINT_ROW}+$B${WARRANTY_ROW}+$B${LOGISTICS_ROW})*$B${QTY_ROW}+$B${OTHERCOST_ROW}", CURRENCY_FMT),
        ("List Price", f"=$B${STDPRICE_ROW}*$B${QTY_ROW}", CURRENCY_FMT),
        ("Discount Amount", None, CURRENCY_FMT),  # filled below, needs List Price row
        ("Quoted Price", None, CURRENCY_FMT),
        ("Revenue", None, CURRENCY_FMT),
        ("Gross Profit", None, CURRENCY_FMT),
        ("Gross Margin %", None, PCT_FMT),
        ("Minimum Acceptable Price", None, CURRENCY_FMT),
        ("Target Price", None, CURRENCY_FMT),
        ("Maximum Discount Allowed %", None, PCT_FMT),
        ("Expected Win Probability % (baseline)", None, PCT_FMT),
        ("Expected Revenue", None, CURRENCY_FMT),
        ("Expected Profit", None, CURRENCY_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(calcs):
        r = calc_start + i
        ws.cell(row=r, column=1, value=label).font = SECTION_FONT
        cell = ws.cell(row=r, column=2, value=formula)
        cell.font = BLACK
        cell.border = BORDER
        if fmt:
            cell.number_format = fmt

    (TOTALCOST_ROW, LISTPRICE_ROW, DISCAMT_ROW, QUOTED_ROW, REVENUE_ROW, GROSSPROFIT_ROW,
     MARGIN_ROW, MINPRICE_ROW, TARGETPRICE_ROW, MAXDISCALLOWED_ROW, WINPROB_ROW,
     EXPREV_ROW, EXPPROFIT_ROW) = range(calc_start, calc_start + 13)

    ws.cell(row=DISCAMT_ROW, column=2, value=f"=$B${LISTPRICE_ROW}*$B${DISC_ROW}")
    ws.cell(row=QUOTED_ROW, column=2, value=f"=$B${LISTPRICE_ROW}-$B${DISCAMT_ROW}")
    ws.cell(row=REVENUE_ROW, column=2, value=f"=$B${QUOTED_ROW}")
    ws.cell(row=GROSSPROFIT_ROW, column=2, value=f"=$B${REVENUE_ROW}-$B${TOTALCOST_ROW}")
    ws.cell(row=MARGIN_ROW, column=2, value=f"=IF($B${REVENUE_ROW}=0,0,$B${GROSSPROFIT_ROW}/$B${REVENUE_ROW})")
    ws.cell(row=MINPRICE_ROW, column=2, value=f"=$B${TOTALCOST_ROW}/(1-$B${MINMARGIN_ROW})")
    ws.cell(row=TARGETPRICE_ROW, column=2, value=f"=$B${TOTALCOST_ROW}/(1-$B${TARGETMARGIN_ROW})")
    ws.cell(row=MAXDISCALLOWED_ROW, column=2,
            value=f"=MAX(0,($B${LISTPRICE_ROW}-$B${MINPRICE_ROW})/$B${LISTPRICE_ROW})")
    # Baseline win probability formula (mirrors win_probability.py rule-based model)
    ws.cell(row=WINPROB_ROW, column=2, value=(
        f"=MIN(0.95,MAX(0.03, $B${WINRATE_ROW} + $B${DISC_ROW}*0.6 "
        f"- (($B${COMP_ROW}/$B${QUOTED_ROW})-1)*0.5 + MIN($B${RELYEARS_ROW},10)*0.005 "
        f"+ IF($B${STRATEGIC_ROW}=1,0.05,0) - MAX(0,$B${PAYTERM_ROW}-45)*0.0007))"
    ))
    ws.cell(row=EXPREV_ROW, column=2, value=f"=$B${REVENUE_ROW}*$B${WINPROB_ROW}")
    ws.cell(row=EXPPROFIT_ROW, column=2, value=f"=$B${GROSSPROFIT_ROW}*$B${WINPROB_ROW}")
    for r in [DISCAMT_ROW, QUOTED_ROW, REVENUE_ROW, GROSSPROFIT_ROW, MARGIN_ROW, MINPRICE_ROW,
              TARGETPRICE_ROW, MAXDISCALLOWED_ROW, WINPROB_ROW, EXPREV_ROW, EXPPROFIT_ROW]:
        c = ws.cell(row=r, column=2)
        c.font = BLACK
        c.border = BORDER
        fmt_map = {DISCAMT_ROW: CURRENCY_FMT, QUOTED_ROW: CURRENCY_FMT, REVENUE_ROW: CURRENCY_FMT,
                   GROSSPROFIT_ROW: CURRENCY_FMT, MARGIN_ROW: PCT_FMT, MINPRICE_ROW: CURRENCY_FMT,
                   TARGETPRICE_ROW: CURRENCY_FMT, MAXDISCALLOWED_ROW: PCT_FMT, WINPROB_ROW: PCT_FMT,
                   EXPREV_ROW: CURRENCY_FMT, EXPPROFIT_ROW: CURRENCY_FMT}
        c.number_format = fmt_map[r]

    # Pricing position / flags
    flag_start = calc_start + 15
    ws.cell(row=flag_start - 1, column=1, value="Commercial Flags").font = SECTION_FONT
    ws.cell(row=flag_start, column=1, value="Margin Position").font = BLACK
    ws.cell(row=flag_start, column=2, value=(
        f'=IF($B${QUOTED_ROW}<$B${MINPRICE_ROW},"Below Minimum Margin",'
        f'IF($B${QUOTED_ROW}<$B${TARGETPRICE_ROW},"Competitive",'
        f'IF($B${QUOTED_ROW}<=$B${TARGETPRICE_ROW}*1.05,"Target Margin Achieved","Premium Pricing")))'
    ))
    ws.cell(row=flag_start + 1, column=1, value="Discount Flag").font = BLACK
    ws.cell(row=flag_start + 1, column=2, value=(
        f'=IF($B${DISC_ROW}>$B${MAXDISC_ROW},"ESCALATION: Discount exceeds maximum allowed",'
        f'IF($B${DISC_ROW}>$B${MAXDISC_ROW}*0.6,"Manager approval recommended","Within normal range"))'
    ))
    ws.cell(row=flag_start + 2, column=1, value="Margin Flag").font = BLACK
    ws.cell(row=flag_start + 2, column=2, value=(
        f'=IF($B${MARGIN_ROW}<$B${MINMARGIN_ROW},"RED: Below minimum margin",'
        f'IF($B${MARGIN_ROW}<$B${TARGETMARGIN_ROW},"AMBER: Below target margin","GREEN: Target margin achieved"))'
    ))
    for r in [flag_start, flag_start + 1, flag_start + 2]:
        c = ws.cell(row=r, column=2)
        c.font = BLACK
        c.border = BORDER

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 48

    # Store row map for use in Scenario Analysis / Proposal Summary sheets
    pc_rows = dict(
        CUSTOMER_ROW=CUSTOMER_ROW, PRODUCT_ROW=PRODUCT_ROW, QTY_ROW=QTY_ROW, DISC_ROW=DISC_ROW,
        COMP_ROW=COMP_ROW, PAYTERM_ROW=PAYTERM_ROW, DELIVERY_ROW=DELIVERY_ROW,
        TARGETMARGIN_ROW=TARGETMARGIN_ROW, TOTALCOST_ROW=TOTALCOST_ROW, LISTPRICE_ROW=LISTPRICE_ROW,
        QUOTED_ROW=QUOTED_ROW, REVENUE_ROW=REVENUE_ROW, GROSSPROFIT_ROW=GROSSPROFIT_ROW,
        MARGIN_ROW=MARGIN_ROW, MINMARGIN_ROW=MINMARGIN_ROW, MAXDISC_ROW=MAXDISC_ROW,
        WINPROB_ROW=WINPROB_ROW, flag_start=flag_start,
    )

    # ---------------------------------------------------------------- Scenario Analysis
    ws2 = wb.create_sheet("Scenario Analysis")
    ws2["A1"] = "Scenario Analysis — Discount Scenarios"
    ws2["A1"].font = TITLE_FONT
    ws2["A3"] = "All scenarios below reference the Customer/Product/Quantity selected on the Pricing Calculator sheet."
    ws2["A3"].font = BLACK

    headers = ["Scenario", "Discount %", "Quoted Price", "Revenue", "Total Cost", "Gross Profit",
               "Margin %", "Win Probability", "Expected Revenue", "Expected Profit"]
    hdr_row = 5
    for j, h in enumerate(headers):
        ws2.cell(row=hdr_row, column=1 + j, value=h)
    style_header_row(ws2, hdr_row, len(headers))

    scenario_discounts = [0.05, 0.10, 0.15, 0.20]
    for i, d in enumerate(scenario_discounts):
        r = hdr_row + 1 + i
        ws2.cell(row=r, column=1, value=f"Scenario {chr(65+i)}").font = BLACK
        disc_cell = ws2.cell(row=r, column=2, value=d)
        disc_cell.font = BLUE
        disc_cell.number_format = PCT_FMT
        # Quoted Price = List Price (from Pricing Calculator) * (1 - this row's discount)
        ws2.cell(row=r, column=3, value=f"='Pricing Calculator'!$B${pc_rows['LISTPRICE_ROW']}*(1-B{r})").number_format = CURRENCY_FMT
        ws2.cell(row=r, column=4, value=f"=C{r}").number_format = CURRENCY_FMT
        ws2.cell(row=r, column=5, value=f"='Pricing Calculator'!$B${pc_rows['TOTALCOST_ROW']}").number_format = CURRENCY_FMT
        ws2.cell(row=r, column=6, value=f"=D{r}-E{r}").number_format = CURRENCY_FMT
        ws2.cell(row=r, column=7, value=f"=IF(D{r}=0,0,F{r}/D{r})").number_format = PCT_FMT
        # Win probability re-using the same formula structure as Pricing Calculator but with this row's discount
        ws2.cell(row=r, column=8, value=(
            f"=MIN(0.95,MAX(0.03, 'Pricing Calculator'!$B${pc_rows['WINPROB_ROW']} "
            f"+ (B{r}-'Pricing Calculator'!$B${pc_rows['DISC_ROW']})*0.6))"
        )).number_format = PCT_FMT
        ws2.cell(row=r, column=9, value=f"=D{r}*H{r}").number_format = CURRENCY_FMT
        ws2.cell(row=r, column=10, value=f"=F{r}*H{r}").number_format = CURRENCY_FMT
        for c in range(1, 11):
            ws2.cell(row=r, column=c).border = BORDER
            if c not in (1, 2):
                ws2.cell(row=r, column=c).font = BLACK

    for col, width in zip("ABCDEFGHIJ", [12, 11, 14, 14, 13, 13, 10, 13, 15, 14]):
        ws2.column_dimensions[col].width = width

    ws2.cell(row=hdr_row + 7, column=1,
             value="Note: Expected Revenue/Profit = Revenue or Gross Profit x Win Probability "
                   "(simplified expected-value approach).").font = BLACK

    # ---------------------------------------------------------------- Risk Assessment
    ws3 = wb.create_sheet("Risk Assessment")
    ws3["A1"] = "Commercial Risk Assessment"
    ws3["A1"].font = TITLE_FONT

    ws3["A3"] = "Risk Weights (editable, must total 100%)"
    ws3["A3"].font = SECTION_FONT
    weights = [
        ("Customer Risk", 0.15), ("Payment Risk", 0.15), ("Margin Risk", 0.20),
        ("Discount Risk", 0.15), ("Delivery Risk", 0.10), ("Warranty Risk", 0.10),
        ("Competitive Risk", 0.10), ("Contract Risk", 0.05),
    ]
    wrow0 = 4
    for i, (label, w) in enumerate(weights):
        r = wrow0 + i
        ws3.cell(row=r, column=1, value=label).font = BLACK
        c = ws3.cell(row=r, column=2, value=w)
        c.font = BLUE
        c.fill = YELLOW_FILL
        c.number_format = PCT_FMT
        c.border = BORDER
    total_row = wrow0 + len(weights)
    ws3.cell(row=total_row, column=1, value="Total").font = SECTION_FONT
    ws3.cell(row=total_row, column=2, value=f"=SUM(B{wrow0}:B{total_row-1})").number_format = PCT_FMT

    ws3.cell(row=wrow0, column=4, value="Score each dimension 0 (Low), 1 (Medium), 2 (High):").font = SECTION_FONT
    score_col_start = wrow0 + 1
    manual_scores = [1, 1, 1, 1, 0, 0, 1, 0]
    for i, s in enumerate(manual_scores):
        r = score_col_start + i
        c = ws3.cell(row=r, column=5, value=s)
        c.font = BLUE
        c.fill = YELLOW_FILL
        c.border = BORDER
        ws3.cell(row=r, column=4, value=weights[i][0]).font = BLACK

    ws3.cell(row=total_row + 2, column=1, value="Weighted Risk Score (0-100)").font = SECTION_FONT
    score_formula = "+".join([f"(E{score_col_start+i}/2)*100*B{wrow0+i}" for i in range(len(weights))])
    score_cell = ws3.cell(row=total_row + 2, column=2, value=f"={score_formula}")
    score_cell.font = BLACK
    score_cell.number_format = '0.0'
    ws3.cell(row=total_row + 3, column=1, value="Risk Classification").font = SECTION_FONT
    ws3.cell(row=total_row + 3, column=2, value=(
        f'=IF(B{total_row+2}<=30,"Low",IF(B{total_row+2}<=60,"Medium","High"))'
    )).font = BLACK

    ws3.column_dimensions["A"].width = 20
    ws3.column_dimensions["B"].width = 14
    ws3.column_dimensions["D"].width = 20
    ws3.column_dimensions["E"].width = 10

    # ---------------------------------------------------------------- Proposal Summary
    ws4 = wb.create_sheet("Proposal Summary")
    ws4["A1"] = "Proposal Summary"
    ws4["A1"].font = TITLE_FONT
    fields = [
        ("Customer", f"='Pricing Calculator'!$B${pc_rows['CUSTOMER_ROW']}"),
        ("Product", f"='Pricing Calculator'!$B${pc_rows['PRODUCT_ROW']}"),
        ("Quantity", f"='Pricing Calculator'!$B${pc_rows['QTY_ROW']}"),
        ("Quoted Price", f"='Pricing Calculator'!$B${pc_rows['QUOTED_ROW']}"),
        ("Discount %", f"='Pricing Calculator'!$B${pc_rows['DISC_ROW']}"),
        ("Total Contract Value", f"='Pricing Calculator'!$B${pc_rows['QUOTED_ROW']}"),
        ("Expected Margin %", f"='Pricing Calculator'!$B${pc_rows['MARGIN_ROW']}"),
        ("Payment Terms (days)", f"='Pricing Calculator'!$B${pc_rows['PAYTERM_ROW']}"),
        ("Expected Delivery (days)", f"='Pricing Calculator'!$B${pc_rows['DELIVERY_ROW']}"),
        ("Win Probability", f"='Pricing Calculator'!$B${pc_rows['WINPROB_ROW']}"),
        ("Margin Position", f"='Pricing Calculator'!$B${pc_rows['flag_start']}"),
        ("Margin Flag", f"='Pricing Calculator'!$B${pc_rows['flag_start']+2}"),
    ]
    frow0 = 3
    pct_fields = {"Discount %", "Expected Margin %", "Win Probability"}
    currency_fields = {"Quoted Price", "Total Contract Value"}
    for i, (label, formula) in enumerate(fields):
        r = frow0 + i
        ws4.cell(row=r, column=1, value=label).font = SECTION_FONT
        c = ws4.cell(row=r, column=2, value=formula)
        c.font = BLACK
        c.border = BORDER
        if label in pct_fields:
            c.number_format = PCT_FMT
        elif label in currency_fields:
            c.number_format = CURRENCY_FMT
    ws4.column_dimensions["A"].width = 26
    ws4.column_dimensions["B"].width = 40

    ws4.cell(row=frow0 + len(fields) + 2, column=1,
             value="This summary updates automatically when inputs on the Pricing Calculator sheet change.").font = BLACK

    wb.save(EXCEL_PATH)
    print(f"Saved: {EXCEL_PATH}")


if __name__ == "__main__":
    build()
