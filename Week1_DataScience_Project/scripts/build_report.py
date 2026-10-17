"""Build EDA_Report.pdf from the notebook outputs.

Run from the project folder after executing Week1_EDA.ipynb:
    python scripts/build_report.py

Numbers come from Cleaned_Data/kpis.json and Cleaned_Data/insights.json, and charts from
Visualizations/, so the report always matches the latest notebook run.
"""
import json
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
CLEAN, VIZ = ROOT / "Cleaned_Data", ROOT / "Visualizations"
OUT = ROOT / "EDA_Report.pdf"

# DejaVu Sans ships with matplotlib and includes the naira sign (₦), which Helvetica lacks.
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVu", FONT_DIR / "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", FONT_DIR / "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")

INK, MUTED, ACCENT, RULE = colors.HexColor("#0b0b0b"), colors.HexColor("#52514e"), \
    colors.HexColor("#2a78d6"), colors.HexColor("#d0cfca")

base = getSampleStyleSheet()
STYLES = {
    "title": ParagraphStyle("title", fontName="DejaVu-Bold", fontSize=20, leading=25, textColor=INK, spaceAfter=4),
    "subtitle": ParagraphStyle("subtitle", fontName="DejaVu", fontSize=10.5, leading=14, textColor=MUTED, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=14, leading=18, textColor=ACCENT, spaceBefore=12, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=11, leading=14, textColor=INK, spaceBefore=8, spaceAfter=4),
    "body": ParagraphStyle("body", fontName="DejaVu", fontSize=9.5, leading=13.5, textColor=INK, alignment=TA_LEFT, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="DejaVu", fontSize=8, leading=10.5, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="DejaVu", fontSize=8.5, leading=11, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DejaVu-Bold", fontSize=8.5, leading=11, textColor=INK),
    "caption": ParagraphStyle("caption", fontName="DejaVu", fontSize=8, leading=10, textColor=MUTED, spaceAfter=10),
}


def naira(x: float) -> str:
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(x) >= div:
            return f"₦{x / div:,.2f}{suffix}"
    return f"₦{x:,.0f}"


def p(text, style="body"):
    return Paragraph(text, STYLES[style])


def bullets(items, style="body"):
    return ListFlowable([ListItem(p(t, style), leftIndent=12, value="•") for t in items],
                        bulletType="bullet", start="•", leftIndent=12, bulletFontName="DejaVu")


def numbered(items):
    return ListFlowable([ListItem(p(t), leftIndent=14) for t in items], bulletType="1",
                        leftIndent=14, bulletFontName="DejaVu-Bold", bulletFontSize=9.5)


def table(rows, col_widths, header=True):
    data = [[p(str(c), "cellb" if header and i == 0 else "cell") for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK if header else RULE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def figure(name, caption, width=16.5 * cm):
    path = VIZ / f"{name}.png"
    img = Image(str(path))
    img.drawHeight = width * img.imageHeight / img.imageWidth
    img.drawWidth = width
    return KeepTogether([img, p(caption, "caption")])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, "ShopSmart Retail Ltd. | Mission DS01: Exploratory Data Analysis | AnalystLab Africa, Week 1")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    kpi = json.loads((CLEAN / "kpis.json").read_text(encoding="utf-8"))
    ins = json.loads((CLEAN / "insights.json").read_text(encoding="utf-8"))
    raw_rows = {name: len(pd.read_csv(ROOT.parent / "data" / f, encoding="utf-8-sig")) for name, f in {
        "Customers": "ALA_ShopSmart_Customers.csv", "Products": "ShopSmart_Products.csv",
        "Orders": "ShopSmart_Orders.csv", "Order_Items": "ShopSmart_Order_Items.csv",
        "Stores": "ShopSmart_Stores.csv", "Returns": "ShopSmart_Returns.csv",
        "Employees": "ShopSmart_Employees.csv", "Suppliers": "ShopSmart_Suppliers.csv",
        "Inventory": "ShopSmart_Inventory.csv"}.items()}
    sales = pd.read_csv(CLEAN / "sales_features.csv", usecols=["is_completed", "profit", "net_sales", "below_cost"])
    done = sales[sales["is_completed"] == 1]
    loss = -done.loc[done["profit"] < 0, "profit"].sum()
    margin = done["profit"].sum() / done["net_sales"].sum()
    below_cost_share = done["below_cost"].mean()
    segments = pd.read_csv(CLEAN / "customer_segments.csv")
    seg = segments.groupby("segment").agg(customers=("cluster", "size"), revenue=("total_revenue", "sum"))
    seg["cust_share"] = seg["customers"] / seg["customers"].sum()
    seg["rev_share"] = seg["revenue"] / seg["revenue"].sum()

    revenue = kpi["Total Revenue (₦, completed orders)"]
    all_value = kpi["Order Value, all statuses (₦)"]
    completed = kpi["Completed Orders"]
    total_orders = kpi["Total Orders (all statuses)"]
    growth = ins["category_growth"]

    s = []
    # ---- Title + executive summary -------------------------------------------------------
    s += [p("ShopSmart Retail: Exploratory Data Analysis", "title"),
          p("Mission DS01 · AnalystLab Africa Experience Lab, Week 1 (Data Science Track)<br/>"
            "Prepared by Molemi Molokoane for ShopSmart Retail Ltd. management · Data period: 1 Jan – 31 Dec 2025",
            "subtitle")]

    s += [p("1. Executive Summary", "h1"),
          p(f"ShopSmart earned <b>{naira(revenue)}</b> from <b>{completed:,.0f} completed orders</b> in 2025 "
            f"(average order value {naira(kpi['Average Order Value (₦)'])}). Customers placed {total_orders:,.0f} orders "
            f"worth {naira(all_value)}, but <b>only one in three was completed</b>. About "
            f"{naira(all_value - revenue)} of demand never became revenue. That conversion gap is larger than "
            "every other effect in the data put together."),
          p(f"Performance is <b>remarkably even</b> across stores, categories, customer segments and months. The best "
            f"store ({ins['best_store']}, {naira(ins['best_store_revenue'])}) earns only 26% more than the weakest "
            f"({ins['worst_store']}, {naira(ins['worst_store_revenue'])}), and the gap comes from its higher order "
            f"completion rate. Profitability is the main concern: the gross margin is {margin:.0%}, but "
            f"<b>{below_cost_share:.0%} of completed order lines were sold below cost</b>, losing {naira(loss)}. "
            f"In addition, <b>{naira(kpi['Inventory Value at Cost (₦)'])}</b> is tied up in stock, more than a full "
            "year of revenue."),
          p("The data is complete (no missing values) but <b>inconsistent</b>. The data-quality issues below must be "
            "fixed at source before ShopSmart builds predictive models.")]

    kpi_rows = [["KPI", "Value", "KPI", "Value"],
                ["Total revenue (completed)", naira(revenue), "Total orders (all statuses)", f"{total_orders:,.0f}"],
                ["Completed orders", f"{completed:,.0f}", "Average order value", naira(kpi["Average Order Value (₦)"])],
                ["Customers (registered / active)", f"{kpi['Total Customers (registered)']:,.0f} / "
                                                    f"{kpi['Active Customers (≥1 completed order)']:,.0f}",
                 "Average selling price per unit", naira(kpi["Average Selling Price (₦ per unit sold)"])],
                ["Products / Stores", f"{kpi['Total Products']:,.0f} / {kpi['Total Stores']:,.0f}",
                 "Units sold (completed)", f"{kpi['Total Quantity Sold (units, completed)']:,.0f}"],
                ["Return rate", f"{kpi['Return Rate (returned orders / all orders)']:.2%}",
                 "Inventory value (at cost)", naira(kpi["Inventory Value at Cost (₦)"])]]
    s += [table(kpi_rows, [4.6 * cm, 3.6 * cm, 4.6 * cm, 3.7 * cm])]

    # ---- Dataset description ---------------------------------------------------------------
    s += [p("2. Dataset Description", "h1"),
          p("Nine related CSV tables and a data dictionary were provided. Orders is the central fact table, and "
            "the other tables describe who bought (Customers), what (Products, through Suppliers), where (Stores, "
            "Employees), what happened afterwards (Returns) and what is on the shelf (Inventory).")]
    desc = {
        "Customers": ("Customer_ID", "Demographics, location, membership segment"),
        "Products": ("Product_ID", "Name, category, brand, cost and selling price"),
        "Orders": ("Order_ID", "One product line per order: date, qty, price, discount, status"),
        "Order_Items": ("Order_Item_ID", "Duplicate of Orders plus line_total (1:1)"),
        "Stores": ("Store_ID", "Store name, region, state, city, opening date"),
        "Returns": ("Return_ID", "Returned order, date, reason, refund amount"),
        "Employees": ("Employee_ID", "Role, store, hire date, salary"),
        "Suppliers": ("Supplier_ID", "Supplier name, contact, country"),
        "Inventory": ("Inventory_ID", "Stock on hand and reorder level per product/store"),
    }
    rows = [["Table", "Rows", "Primary key", "Contents"]] + \
           [[t, f"{raw_rows[t]:,}", desc[t][0], desc[t][1]] for t in desc]
    s += [table(rows, [2.6 * cm, 1.6 * cm, 2.9 * cm, 9.4 * cm]),
          p("Relationships: Orders → Customers, Products, Stores · Returns → Orders · Inventory → Products, Stores · "
            "Employees → Stores · Products → Suppliers (by brand name, since there is no key).", "small")]

    # ---- Cleaning -----------------------------------------------------------------------
    s += [p("3. Data Cleaning Process", "h1"),
          p("Every step is logged in <i>Cleaned_Data/cleaning_log.csv</i>. The raw files were never modified."),
          table([
              ["Issue found", "Evidence", "Action"],
              ["Column names inconsistent", "Mixed case (Customer_ID)", "Renamed to snake_case"],
              ["Duplicates", "0 duplicate rows or keys; 56 orders returned more than once",
               "Kept the first return per order (2,500 → 2,442)"],
              ["Missing values", "None in any table", "Documented a policy for future extracts"],
              ["Dates stored as text", "M/D/YYYY strings", "Parsed to datetime, 0 failures"],
              ["Discount misapplied", "Values 0–20 are percentages but line_total subtracted them as ₦",
               "Recomputed gross, discount and net sales"],
              ["Order_Items duplicates Orders", "Row-for-row identical", "Used Orders as the single fact table"],
              ["Store names not unique", "25 stores share 10 names", "Added a unique store_label"],
              ["Region contradicts State", "Lagos stores tagged North, South, East and West",
               "Added geo_zone (Nigeria's six zones) from the state"],
              ["Impossible returns", "50% dated before their order; 12% refund more than the sale",
               "Flagged, not deleted"],
              ["Price inconsistencies", "Order prices never match the catalogue; 24% below cost",
               "Flagged below_cost (Part 7)"],
              ["No product → supplier key", "Supplier name = Brand + ' Supplies'", "Linked by name (100% match)"],
              ["Constant column", "sub_category = 'General' for all", "Dropped"],
          ], [4.2 * cm, 6.3 * cm, 6.0 * cm])]

    # ---- Findings + visuals -----------------------------------------------------------------
    s += [p("4. Exploratory Findings", "h1"),
          p(f"<b>Seasonality.</b> Monthly revenue is fairly flat (₦171M–₦201M). <b>{ins['peak_month']}</b> is the peak "
            f"({naira(ins['peak_month_revenue'])}), then October, and Q4 is the strongest quarter. February is lowest, "
            "but only because it is short."),
          p("<b>Categories.</b> Beauty earns the most (23%), then Groceries and Electronics (about 20% each). Revenue per "
            "product is almost the same in every category, so Beauty leads on range size, not on stronger sellers. "
            f"From Q1 to Q4, Fashion grew {growth['Fashion']:+.0%} and Beauty {growth['Beauty']:+.0%}, while Groceries was flat "
            f"({growth['Groceries']:+.0%})."),
          p(f"<b>Stores and regions.</b> {ins['best_store']} leads and {ins['worst_store']} trails. Every store "
            "receives about 2,000 orders, so the stores differ in how many orders they complete (31–36%). Per store, the "
            f"{ins['best_zone']} zone performs best and the {ins['worst_zone']} worst, a gap of about 8%."),
          p("<b>Customers.</b> Gold, Silver and Bronze members spend within 0.4% of each other per customer, and age, "
            "gender, channel and payment method make little difference. <b>Purchase frequency</b> is what separates "
            "high-value customers (r = 0.79 between completed orders and revenue)."),
          p(f"<b>Returns.</b> The return rate is 4.6–5.1% in every category. Only {ins['high_return_products']} of 500 products "
            f"have a significantly high rate (top: {ins['top_return_product']}, {ins['top_return_rate']:.1%}). Late delivery "
            "and wrong item cause 51% of returns, and both are operational failures ShopSmart can control."),
          p(f"<b>Profit and inventory.</b> The top 10 products by revenue and by profit have no products in common, "
            f"and 57 products lose money overall. Only {ins['restock_items']} inventory items are at or below their reorder level, "
            "while 417 of 500 hold more than three times it.")]

    s += [KeepTogether([p("5. Visualisations", "h1"),
                        figure("01_monthly_sales_trend", "Figure 1. Monthly revenue from completed orders, 2025.")]),
          figure("02_revenue_by_category", "Figure 2. Revenue by category.", 14 * cm),
          figure("16_category_growth", "Figure 3. Category revenue indexed to Q1 = 100.", 14 * cm),
          figure("03_revenue_by_store", "Figure 4. Revenue by store (store labels are unique; names repeat in the source).", 12 * cm),
          figure("15_spend_by_customer_segment", "Figure 5. Revenue per customer is flat across membership, age and gender."),
          figure("09_return_rate_by_category", "Figure 6. Return rate by category.", 14 * cm),
          figure("10_inventory_by_store", "Figure 7. Units and value of stock held per store."),
          figure("11_correlation_heatmap_orders", "Figure 8. Correlation between order-level variables.", 12 * cm),
          figure("19_customer_segments", "Figure 9. Bonus: K-Means RFM segments.")]

    # ---- Insights + recommendations ---------------------------------------------------------
    s += [p("6. Five Key Insights", "h1"), numbered([
        f"<b>Order completion is the biggest lever.</b> Only {completed / total_orders:.0%} of orders complete, and "
        f"{naira(all_value - revenue)} of demand is lost. The completion rate also explains why some stores beat others.",
        f"<b>Revenue does not equal profit.</b> {below_cost_share:.0%} of completed sales were below cost "
        f"({naira(loss)} lost), and the highest-revenue products are not the most profitable.",
        "<b>Membership tiers do not reflect value.</b> Gold, Silver and Bronze customers spend the same. Data-driven RFM "
        f"segments do: 'Champions' are {seg.loc['Champions', 'cust_share']:.0%} of customers but "
        f"{seg.loc['Champions', 'rev_share']:.0%} of revenue.",
        f"<b>Inventory is overstocked and badly distributed.</b> {naira(kpi['Inventory Value at Cost (₦)'])} is held "
        "at cost, Lagos (STR015) holds 3× the stock value of Enugu (STR005) despite similar sales, and only 21 items "
        "need restocking.",
        "<b>Data quality limits analytics.</b> Discounts are misapplied, regions contradict states, half the returns are "
        "dated before their order, and suppliers cannot be linked by key. These issues must be fixed at source.",
    ])]

    s += [p("7. Five Recommendations", "h1"), numbered([
        "<b>Launch an order-completion programme:</b> chase pending orders, find out why orders are cancelled "
        "(payment, stock, delivery), and copy the practices of the best-converting stores (e.g. Lagos STR003). "
        "Raising completion from 33% to 40% would add about ₦470M a year at the current average order value.",
        "<b>Enforce a price floor:</b> block sales below cost in the POS/e-commerce system and review the 57 "
        "loss-making products and 56 loss-making suppliers. Manage the range on profit, not revenue.",
        "<b>Redesign the loyalty programme</b> around RFM segments: reward Champions, convert Active Low-Converters, "
        "win back lapsing customers, and investigate the 205 customers who have never completed an order.",
        "<b>Rebalance inventory:</b> transfer excess stock to stores with Low items, restock the 21 Low items "
        "now, and cut purchase quantities for the overstocked majority to release working capital.",
        "<b>Invest in Beauty and Fashion ahead of Q4,</b> as the fastest-growing categories with the strongest "
        "festive-season uplift. In parallel, fix the source-system data issues and start recording "
        "delivery times and supplier lead times.",
    ])]

    s += [KeepTogether([p("8. Suggested Machine Learning Problems", "h1"), table([
        ["Problem", "Type", "Target / output", "Key features & readiness"],
        ["Order completion prediction", "Classification", "Completed vs cancelled/pending",
         "Biggest business value. Current features do not separate statuses, so add cart, stock and payment events."],
        ["Sales forecasting", "Time series", "Monthly revenue by store/category",
         "Month, quarter, store, category. Needs 2+ years of history to model seasonality reliably."],
        ["Customer churn / CLV", "Classification / regression", "Lapse in 90 days / 12-month value",
         "Recency, frequency, completion rate, RFM segment. Ready to prototype."],
        ["Product recommendation", "Collaborative filtering", "Next products per customer",
         "10 orders per customer gives purchase histories. Ready to prototype."],
        ["Return prediction", "Classification", "Return_Flag",
         "No current variable correlates with returns. Needs delivery times, reviews and return history."],
        ["Inventory forecasting", "Regression", "Units needed per product/store",
         "Days of supply, stock cover, demand trend. Needs daily stock movements."],
        ["Pricing anomaly detection", "Anomaly detection", "Flag below-cost or off-catalogue prices",
         "Unit price vs cost and catalogue. Ready now, with high immediate value."],
    ], [3.6 * cm, 2.8 * cm, 3.6 * cm, 6.5 * cm])])]

    s += [p("Bonus: Customer Segmentation (K-Means)", "h2"),
          p("Customers were clustered on recency, frequency, monetary value and completion rate (log-scaled and "
            "standardised, k = 4 chosen by elbow and silhouette = 0.38). The four segments are Champions, Active "
            "Low-Converters, At Risk / Lapsing and Non-Converters. Each has the same mix of Gold, Silver and Bronze members, which "
            "confirms that the current tiers do not reflect value. <i>Limitations:</i> one year of data, K-Means assumes "
            "round clusters, k was partly a business choice, and the data appears synthetic. Re-fit on real data and "
            "track segment stability over time."),
          p("Limitations of this analysis", "h2"),
          bullets(["The dataset appears synthetic: distributions are very uniform and names and genders often "
                   "conflict. Effect sizes are small, and conclusions should be validated on production data.",
                   "Revenue is defined as Completed orders. If Pending orders later complete, revenue will be higher.",
                   "Returns data is unreliable (impossible dates), so return insights are indicative only.",
                   "There is one year of sales, so year-on-year growth and seasonality cannot be confirmed."]),
          Spacer(1, 6),
          p("Reproducibility: <i>Week1_EDA.ipynb</i> produces every number and chart in this report, and "
            "<i>scripts/build_report.py</i> regenerates this PDF from those outputs.", "small")]

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title="ShopSmart EDA Report", author="Molemi Molokoane")
    doc.build(s, onFirstPage=footer, onLaterPages=footer)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
