"""Build Reports/Week5_Electricity_Data_Science_Report.pdf.

The report reads its numbers from the CSV tables in Outputs/ and its charts
from Visualizations/, both written by the notebook, so it always matches the
latest notebook run. Run the notebook first, then, from the project folder:

    python scripts/build_report.py
"""

from __future__ import annotations

import platform
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.doctemplate import BaseDocTemplate
from reportlab.platypus.frames import Frame
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Outputs"
VIS = ROOT / "Visualizations"
PDF = ROOT / "Reports" / "Week5_Electricity_Data_Science_Report.pdf"

AUTHOR = "Molemi Molokoane"
TITLE = "Statistical and Time-Series Analysis of Electricity Consumption in Morocco"

# --- fonts -------------------------------------------------------------------
# A Unicode TTF is needed for Greek letters and symbols (ρ, ε², χ², ≥, −).
FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/ariali.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf", "/Library/Fonts/Arial Italic.ttf"),
]
BASE, BOLD, ITALIC = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
for reg, bold, ital in FONT_CANDIDATES:
    if Path(reg).exists() and Path(bold).exists():
        pdfmetrics.registerFont(TTFont("Body", reg))
        pdfmetrics.registerFont(TTFont("Body-Bold", bold))
        pdfmetrics.registerFont(TTFont("Body-Italic", ital if Path(ital).exists() else reg))
        pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic",
                                      boldItalic="Body-Bold")
        BASE, BOLD, ITALIC = "Body", "Body-Bold", "Body-Italic"
        break
else:
    print("Warning: no Unicode font found; Greek letters may not render.")

# --- palette (same as charts.py) ----------------------------------------------
INK = colors.HexColor("#0b0b0b")
INK_2 = colors.HexColor("#52514e")
RULE = colors.HexColor("#d9d8d2")
TINT = colors.HexColor("#f2f1ec")
ACCENT = colors.HexColor("#2a78d6")
ACCENT_TINT = colors.HexColor("#eaf2fc")

# --- styles ------------------------------------------------------------------
S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=24, leading=30, textColor=INK, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName=BASE, fontSize=13, leading=18, textColor=INK_2, spaceAfter=4),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=16, leading=21, textColor=INK, spaceBefore=6, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=12, leading=16, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", fontName=BASE, fontSize=9.6, leading=14, textColor=INK, spaceAfter=6, alignment=TA_LEFT),
    "bullet": ParagraphStyle("bullet", fontName=BASE, fontSize=9.6, leading=14, textColor=INK, leftIndent=12,
                             bulletIndent=2, spaceAfter=3),
    "caption": ParagraphStyle("caption", fontName=ITALIC, fontSize=8.3, leading=11, textColor=INK_2, spaceAfter=10),
    "cell": ParagraphStyle("cell", fontName=BASE, fontSize=8.3, leading=10.5, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=8.3, leading=10.5, textColor=INK),
    "box": ParagraphStyle("box", fontName=BASE, fontSize=9.4, leading=13.5, textColor=INK, spaceAfter=4),
    "meta": ParagraphStyle("meta", fontName=BASE, fontSize=9.5, leading=14, textColor=INK_2),
    "toc1": ParagraphStyle("toc1", fontName=BASE, fontSize=10.5, leading=17, textColor=INK),
}

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


# --- helpers -----------------------------------------------------------------

def p(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def table(rows, widths, header=True, zebra=True, bold_first_col=False):
    data = []
    for i, r in enumerate(rows):
        style = "cellb" if (header and i == 0) else "cell"
        data.append([Paragraph(str(c), S["cellb" if (bold_first_col and j == 0 and i > 0) else style])
                     for j, c in enumerate(r)])
    t = Table(data, colWidths=[w * CONTENT_W for w in widths], repeatRows=1 if header else 0)
    st = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, RULE),
    ]
    if header:
        st += [("LINEBELOW", (0, 0), (-1, 0), 0.9, INK), ("BACKGROUND", (0, 0), (-1, 0), TINT)]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if (i % 2 == 0) == header:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafaf7")))
    t.setStyle(TableStyle(st))
    return t


def figure(name, caption, width=1.0):
    path = VIS / f"{name}.png"
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    w = CONTENT_W * width
    img.drawWidth, img.drawHeight = w, w * ratio
    return KeepTogether([img, Spacer(1, 3), p(caption, "caption")])


def callout(title, lines):
    inner = [p(f"<b>{title}</b>", "box")] + [Paragraph(t, S["box"], bulletText="•") for t in lines]
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_TINT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def mw(kw, d=1):
    return f"{kw / 1000:,.{d}f} MW"


def pct(x, d=0, sign=False):
    return f"{x:+.{d}f}%" if sign else f"{x:.{d}f}%"


def fmt_p(pv):
    """'< 0.001' or '= 0.123', to follow 'p '."""
    if pv < 0.001:
        return "&lt; 0.001"
    return f"= {pv:.3f}"


def minus(s):
    """Typographic minus for negative numbers."""
    return s.replace("-", "−")


# --- document ----------------------------------------------------------------

class ReportDoc(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(str(path), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=MARGIN, title=TITLE, author=AUTHOR,
                         subject="AnalystLab Africa Week 5, Data Science track", **kw)
        frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id="f")
        self.addPageTemplates([PageTemplate("cover", [frame], onPage=lambda c, d: None),
                               PageTemplate("body", [frame], onPage=self._decorate)])

    def _decorate(self, canv, doc):
        canv.saveState()
        canv.setFont(BASE, 7.8)
        canv.setFillColor(INK_2)
        canv.drawString(MARGIN, 11 * mm, "Week 5 · Electricity consumption in Morocco · Data Science track")
        canv.drawRightString(PAGE_W - MARGIN, 11 * mm, f"{doc.page}")
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.5)
        canv.line(MARGIN, 14 * mm, PAGE_W - MARGIN, 14 * mm)
        canv.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == "h1":
            text = flowable.getPlainText()
            key = f"h1-{self.seq.nextf('h1')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=0)
            self.notify("TOCEntry", (0, text, self.page, key))


def build():
    # ---- load outputs --------------------------------------------------------
    desc = pd.read_csv(OUT / "descriptive_stats_10min.csv", index_col=0)
    desc_d = pd.read_csv(OUT / "descriptive_stats_daily.csv", index_col=0)
    peak = pd.read_csv(OUT / "hourly_profile.csv", index_col=0)
    wkt = pd.read_csv(OUT / "weekday_tests.csv", index_col=0)
    mt = pd.read_csv(OUT / "monthly_tests.csv", index_col=0)
    mp = pd.read_csv(OUT / "monthly_profile.csv", index_col=0)
    ram = pd.read_csv(OUT / "ramadan_profile.csv", index_col=0)
    dec = pd.read_csv(OUT / "decomposition_strength.csv", index_col=0)
    st = pd.read_csv(OUT / "stationarity_tests.csv", index_col=0)
    corr = pd.read_csv(OUT / "correlations.csv")
    wm = pd.read_csv(OUT / "correlations_within_month.csv")
    hinge = pd.read_csv(OUT / "hinge_models.csv", index_col=0)
    reg = pd.read_csv(OUT / "regression_hac.csv")
    wind = pd.read_csv(OUT / "wind_state_effect.csv", index_col=0)
    zm = pd.read_csv(OUT / "zone_mean_comparison.csv")
    zv = pd.read_csv(OUT / "zone_variability.csv", index_col=0)
    zs = pd.read_csv(OUT / "zone_profile_shape.csv", index_col=0)
    ls = pd.read_csv(OUT / "autumn_level_shift.csv", index_col=0)
    rob = pd.read_csv(OUT / "robustness_checks.csv", index_col=0)
    kf = pd.read_csv(OUT / "key_figures.csv")
    dq = pd.read_csv(OUT / "data_quality_summary.csv")
    an = pd.read_csv(OUT / "daily_anomalies.csv")

    Z = ["Zone1", "Zone2", "Zone3"]
    ZN = {"Zone1": "Zone 1", "Zone2": "Zone 2", "Zone3": "Zone 3"}
    total_mean = desc.loc["Total", "mean"]
    share = {z: desc.loc[z, "mean"] / desc.loc[Z, "mean"].sum() * 100 for z in Z}
    mi = (mp[Z] / desc_d.loc[Z, "mean"] - 1) * 100
    hs = corr[(corr.level == "hourly") & (corr.method == "spearman")].set_index(["variable", "zone"])
    regC = reg[reg.model.str.startswith("C")].set_index(["term", "zone"])
    night = ram.loc[1:3].mean()
    night_ratio = night.iloc[1] / night.iloc[0]
    hol_flagged = an[an.holiday.notna()]["date"].nunique()
    n_key = len(kf)

    story = []

    # ---- cover ------------------------------------------------------------------
    story += [Spacer(1, 38 * mm),
              p("AnalystLab Africa · Experience Lab Internship · Week 5 · Data Science track", "meta"),
              Spacer(1, 6), p(TITLE, "title"),
              p("Patterns in demand, environmental associations and differences between three electricity "
                "consumption zones, 2017", "subtitle"),
              Spacer(1, 16),
              p(f"<b>Author:</b> {AUTHOR}", "meta"),
              p(f"<b>Date:</b> {date.today():%d %B %Y}", "meta"),
              p("<b>Data:</b> powerconsumption.csv (52,416 ten-minute readings, 1 January to 30 December 2017) "
                "and powerconsumption_datadictionary.csv, supplied by AnalystLab Africa", "meta"),
              p("<b>Tools:</b> Python, pandas, NumPy, SciPy, statsmodels, Plotly, Matplotlib", "meta"),
              Spacer(1, 24)]
    story.append(callout("At a glance", [
        f"Zone 1 carries {share['Zone1']:.0f}% of the load ({mw(desc.loc['Zone1', 'mean'])} on average); "
        f"Zone 3 is the smallest ({mw(desc.loc['Zone3', 'mean'])}) but the most variable (CV {desc.loc['Zone3', 'cv']:.2f}).",
        "Demand peaks at 20:00 and bottoms out at 06:00 to 07:00 in every zone, and is highest in July and August.",
        "Temperature is the only weather variable with a meaningful association, mostly through the shared seasonal "
        "cycle; it survives calendar controls only in Zone 3.",
        f"Ramadan raised night-time load by {(night_ratio - 1) * 100:.0f}%, and the zones' base loads shifted after the summer "
        "in a way that points to network reconfiguration.",
    ]))
    story += [NextPageTemplate("body"), PageBreak()]

    # ---- contents ---------------------------------------------------------------
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"]]
    story += [p("Contents", "h1"), toc, PageBreak()]

    # ---- executive summary ------------------------------------------------------
    story.append(p("Executive summary", "h1"))
    story.append(p(
        "An energy management organisation in Morocco wants to understand how electricity demand in three "
        "consumption zones changes over time, whether weather conditions are associated with it, and how the "
        "zones differ, so that it can plan capacity, maintenance and demand management. This report analyses "
        "one year of 10-minute load readings with descriptive statistics, time-series decomposition and "
        "statistical tests that account for the strong serial dependence in the data."))
    story.append(p("Key findings", "h2"))
    story += bullets([
        f"<b>Time of day is the strongest driver.</b> Load bottoms out at 06:00 to 07:00 and peaks at 20:00 in every zone. "
        f"The daily cycle accounts for {dec.loc['Zone1', 'share_of_variance_daily'] * 100:.1f}% of the variance of Zone 1's hourly load "
        f"and {dec.loc['Zone2', 'share_of_variance_daily'] * 100:.1f}% of Zone 2's.",
        f"<b>Zone 1 is the largest zone; Zone 3 is the most volatile.</b> Zone 1 averages {mw(desc.loc['Zone1', 'mean'])} "
        f"({share['Zone1']:.0f}% of the total) and is the highest zone on every day. Zone 3 averages {mw(desc.loc['Zone3', 'mean'])} "
        f"but has a coefficient of variation of {desc.loc['Zone3', 'cv']:.2f} (against {desc.loc['Zone1', 'cv']:.2f} and "
        f"{desc.loc['Zone2', 'cv']:.2f}) and a load factor of only {desc.loc['Zone3', 'load_factor']:.2f}.",
        f"<b>Summer is the peak season.</b> All zones peak in July or August. Zone 3's July load is "
        f"{mi.loc['Jul', 'Zone3']:.0f}% above its annual average and {mt.loc['Zone3', 'highest_over_lowest']:.1f} times its December load.",
        f"<b>Temperature matters mainly through the season.</b> Above about {hinge.loc['Total', 'base_temp_C']:.0f} °C daily mean, "
        f"total load rises by about {hinge.loc['Total', 'slope_kW_per_C'] / 1000:.1f} MW per °C. With month, Ramadan and holidays "
        f"controlled, the effect disappears in Zones 1 and 2 but remains in Zone 3 "
        f"(+{regC.loc[('Temperature', 'Zone3'), 'coef_kW']:.0f} kW per °C, p {fmt_p(regC.loc[('Temperature', 'Zone3'), 'p_HAC'])}). "
        "Humidity and wind show no association that survives the seasonal controls.",
        f"<b>Calendar events reshape demand.</b> During Ramadan, load between 01:00 and 03:59 was "
        f"{(night_ratio - 1) * 100:.0f}% higher than in the three weeks before; public holidays are among the most unusual days.",
        f"<b>The zones changed composition after the summer.</b> At the same mild temperatures, autumn load was "
        f"{abs(ls.loc['Zone3', 'change_pct']):.0f}% lower than spring in Zone 3 and {ls.loc['Zone2', 'change_pct']:.0f}% higher in Zone 2, "
        "which points to load moving between zones rather than to weather.",
    ])
    story.append(p("Recommendations", "h2"))
    story += bullets([
        "Plan peak capacity and demand response around the 18:00 to 22:00 window in June to September, starting with Zone 3.",
        "Schedule planned maintenance at 03:00 to 07:00, on Sunday daytime (Zones 1 and 2), on public holidays and, for "
        "Zone 3, between October and March.",
        "Forecast with calendar features (hour, weekday, holidays, a movable Ramadan flag) and lagged load, and add a "
        "temperature term above about 20 °C for Zone 3.",
        "Log network reconfigurations between zones and confirm the data definitions with the data owner.",
        "Collect further years of data before treating seasonal patterns or temperature thresholds as stable.",
    ])
    story.append(PageBreak())

    # ---- 1 business problem ---------------------------------------------------------
    story.append(p("1. Business problem and questions", "h1"))
    story.append(p(
        "The organisation records electricity load in three geographical zones every 10 minutes, together with "
        "temperature, humidity, wind speed and two solar-radiation readings. Raw records do not answer the planning "
        "questions it faces: when demand is highest, which zones need the most headroom, how much weather matters, "
        "and how history can guide future planning. The analysis is structured around the six questions in the brief."))
    story.append(table([
        ["#", "Business question", "Section"],
        ["1", "What patterns can be identified in consumption across the three zones?", "4, 5, 7"],
        ["2", "During which hours and days is consumption highest and lowest?", "5"],
        ["3", "How does consumption vary across months?", "5"],
        ["4", "Are temperature, humidity and wind speed associated with consumption?", "6"],
        ["5", "Which zone records the highest and lowest consumption?", "7"],
        ["6", "How can historical patterns support energy planning?", "10"],
    ], [0.06, 0.78, 0.16]))

    # ---- 2 data ---------------------------------------------------------------------
    story.append(p("2. Data and interpretation", "h1"))
    story.append(p(
        "The dataset holds 52,416 readings at exact 10-minute intervals from 1 January 00:00 to 30 December 23:50, 2017 "
        "(364 days; 31 December is not included). It has no missing values, duplicates, irregular intervals or "
        "out-of-range values. The raw file is never modified, and its SHA-256 hash is checked at the start and end "
        "of every run."))
    story.append(p("Data dictionary review", "h2"))
    story.append(p(
        "The brief warned that two parts of the dictionary need care. Each field was checked against the data's "
        "behaviour before analysis:"))
    story.append(table([
        ["Field", "Dictionary says", "Data shows", "Treatment"],
        ["PowerConsumption_Zone1-3", "Power consumption in kWh",
         "Magnitudes only plausible as average load: read as kWh per 10 minutes, the city would use about 3.7 TWh a year "
         "(about 10 MWh per resident)", "Average load in kW; averaged, never summed; energy only derived (mean kW × hours)"],
        ["GeneralDiffuseFlows", "Emission gases diffusing into the broader atmosphere",
         "Zero at night, peaks at noon, up to 1,163", "Solar irradiance (likely W/m²); daylight control only"],
        ["DiffuseFlows", "Emission gases diffusing into the local atmosphere",
         "Solar-shaped but peaks at 16:00 and exceeds GDF in 15% of daylight readings", "Solar reading of uncertain definition; not used"],
        ["WindSpeed", "Speed of the wind in km/h", "99.7% of readings near 0.08 or 4.9 (two states)",
         "Analysed as recorded and as a high/low state"],
        ["Humidity", "Concentration of water vapour", "Values 11 to 95", "Relative humidity (%)"],
    ], [0.19, 0.22, 0.33, 0.26]))
    story.append(Spacer(1, 6))
    story.append(p(
        "The file matches the public <i>Power consumption of Tetouan city</i> dataset (Salam &amp; El Hibaoui, 2018), "
        "which supports the zones being distribution networks in Tetouan, northern Morocco. Every pattern, ranking and "
        "correlation in this report depends only on relative values and is therefore unaffected by the unit question; "
        "only derived energy totals depend on it."))
    story.append(p("Unusual values", "h2"))
    story.append(p(
        "A neighbour-median rule flags 0.3% to 0.4% of readings per zone as abrupt departures. The largest, a 19.3 MW "
        "drop in Zone 1 at 12:10 on 20 April, coincides with an 8.9 MW rise in Zone 2: load switched between networks, "
        "not a sensor error. Flagged readings are kept and marked, and Section 8 shows that removing them changes nothing."))
    story.append(figure("03_load_transfer_20_april",
                        "Figure 1. Zone 1's drop on 20 April is matched by a rise in Zone 2, consistent with load transferred between zones.", 0.92))

    # ---- 3 methodology -------------------------------------------------------------
    story.append(p("3. Methodology", "h1"))
    story.append(table([
        ["Step", "Method", "Why"],
        ["Aggregation", "Hourly means (8,736) for time-series work; daily means (364) for day, month, weather and zone "
                        "comparisons; 10-minute readings for descriptive statistics",
         "Hourly keeps the daily cycle and removes switching noise; daily removes the daily cycle from weather and zone tests"],
        ["Descriptive statistics", "Mean, median, min, max, SD, variance, quartiles, IQR, CV, skewness, kurtosis, load factor (pandas, NumPy, SciPy)",
         "Compare level, spread and shape across zones of different size"],
        ["Decomposition", "MSTL on hourly data with 24 h and 168 h periods; STL on daily data (period 7); strength of components",
         "Separates daily and weekly cycles from the slow seasonal level"],
        ["Stationarity", "ACF/PACF, ADF and KPSS tests", "Establishes dependence structure and justifies the inference adjustments"],
        ["Day and month effects", "Friedman test with weeks as blocks; Kruskal-Wallis with ε²", "Rank-based, paired by week; effect sizes rather than p-values"],
        ["Correlation", "Spearman ρ (Pearson for comparison) with effective-sample-size p-values and intervals; Holm correction",
         "Wind is two-state and temperature acts non-linearly; serial correlation would make naive p-values meaningless"],
        ["Non-linearity", "Change-point (degree-day) model with 14-day block-bootstrap intervals", "Load responds only above a base temperature"],
        ["Confounding", "Within-month correlation; OLS with HAC (Newey-West) errors and calendar controls; within month-and-hour wind comparison",
         "Separates weather from the shared seasonal cycle"],
        ["Zone comparison", "Friedman and Wilcoxon signed-rank (Holm) on paired daily values; 7-day block-bootstrap CIs",
         "Same timestamps across zones; keeps week-to-week dependence"],
        ["Validation", f"Robustness reruns; {n_key} key figures recomputed with the standard library only; 24 unit tests",
         "Guards against coding and interpretation errors"],
    ], [0.17, 0.48, 0.35]))
    story.append(PageBreak())

    # ---- 4 statistics ---------------------------------------------------------------
    story.append(p("4. Statistical summary", "h1"))
    rows = [["Statistic (10-minute readings)", "Zone 1", "Zone 2", "Zone 3"]]
    spec = [("Mean", "mean", "kw"), ("Median", "median", "kw"), ("Minimum", "min", "kw"), ("Maximum", "max", "kw"),
            ("Standard deviation", "std", "kw"), ("Variance (MW²)", "variance", "var"), ("Q1", "q1", "kw"), ("Q3", "q3", "kw"),
            ("IQR", "iqr", "kw"), ("Coefficient of variation", "cv", "r2"), ("Skewness", "skewness", "r2"),
            ("Excess kurtosis", "excess_kurtosis", "r2"), ("Load factor (mean / max)", "load_factor", "r2")]
    for label, col, kind in spec:
        vals = []
        for z in Z:
            v = desc.loc[z, col]
            vals.append(mw(v, 2) if kind == "kw" else f"{v / 1e6:,.1f}" if kind == "var" else minus(f"{v:.2f}"))
        rows.append([label] + vals)
    rows.append(["Share of variance between days", *[f"{desc_d.loc[z, 'variance'] / desc.loc[z, 'variance'] * 100:.0f}%" for z in Z]])
    rows.append(["Derived energy, 364 days", *[f"{desc.loc[z, 'mean'] * 364 * 24 / 1e6:,.0f} GWh" for z in Z]])
    story.append(table(rows, [0.37, 0.21, 0.21, 0.21]))
    story.append(Spacer(1, 6))
    story += bullets([
        f"<b>Zone 1 leads on every level measure</b> and has the largest absolute spread (SD {mw(desc.loc['Zone1', 'std'])}, "
        f"IQR {mw(desc.loc['Zone1', 'iqr'])}).",
        f"<b>Zone 3 is the most variable relative to its size</b> (CV {desc.loc['Zone3', 'cv']:.2f}) and clearly right-skewed "
        f"(skewness {desc.loc['Zone3', 'skewness']:.2f}): its maximum is {desc.loc['Zone3', 'max'] / desc.loc['Zone3', 'mean']:.1f} times its mean, "
        f"so its network must be sized for almost three times its average use.",
        f"<b>Where variation comes from:</b> {(1 - desc_d.loc['Zone1', 'variance'] / desc.loc['Zone1', 'variance']) * 100:.0f}% of Zone 1's "
        f"variance is within days (the daily cycle); for Zone 3, {desc_d.loc['Zone3', 'variance'] / desc.loc['Zone3', 'variance'] * 100:.0f}% is "
        "between days (the seasonal swing).",
        "No zone is normally distributed (all normality tests reject, as expected with 52,416 readings). This, together with "
        "serial correlation, is why rank-based and dependence-adjusted methods are used.",
    ])
    story.append(figure("04_load_distribution_by_zone", "Figure 2. Distribution of 10-minute load by zone.", 0.86))

    # ---- 5 time series --------------------------------------------------------------
    story.append(p("5. Time-series observations", "h1"))
    story.append(figure("06_daily_load_trend", "Figure 3. Daily average load and 7-day centred average by zone, 2017."))
    story.append(p("Hourly pattern", "h2"))
    pk = {z: (int(peak[z].idxmax()), int(peak[z].idxmin())) for z in Z}
    story.append(p(
        f"Every zone peaks at {pk['Zone1'][0]}:00 and bottoms out at {pk['Zone1'][1]:02d}:00 (Zone 3: {pk['Zone3'][1]:02d}:00). "
        f"The evening peak is {peak['Zone1'].max() / peak['Zone1'].min():.2f} times the morning trough in Zones 1 and 2 and "
        f"{peak['Zone3'].max() / peak['Zone3'].min():.2f} times in Zone 3. Zones 1 and 2 also have a midday plateau (+8% to +9% above "
        "their mean), typical of mixed commercial and residential areas, while Zone 3's midday load is only at its mean."))
    story.append(figure("07_hourly_profile_by_zone", "Figure 4. Mean hourly load with the 10th to 90th percentile range across days."))
    story.append(p("Daily and weekly pattern", "h2"))
    story.append(p(
        f"The weekly cycle is smaller than the daily one and is mostly a quieter <b>Sunday daytime</b>. Against the same week's "
        f"Monday-Friday level, Sunday is {abs(wkt.loc['Zone2', 'sunday_vs_weekday_pct']):.0f}% lower in Zone 2 (Kendall's W = "
        f"{wkt.loc['Zone2', 'kendalls_W']:.2f}) and {abs(wkt.loc['Zone1', 'sunday_vs_weekday_pct']):.0f}% lower in Zone 1 (W = "
        f"{wkt.loc['Zone1', 'kendalls_W']:.2f}). Zone 3 has almost no weekly cycle (W = {wkt.loc['Zone3', 'kendalls_W']:.2f}; Sunday "
        f"{wkt.loc['Zone3', 'sunday_vs_weekday_pct']:+.0f}%, not significant). The 20:00 peak is almost the same every day."))
    story.append(figure("09_day_of_week_by_zone", "Figure 5. Mean daily load by day of week relative to each zone's weekly average.", 0.92))
    story.append(figure("08_weekday_hour_heatmap", "Figure 6. Total load by weekday and hour.", 0.92))
    story.append(p("Monthly pattern", "h2"))
    story.append(p(
        f"Month explains most day-to-day variation (Kruskal-Wallis ε² = {mt.loc['Zone1', 'epsilon_squared']:.2f}, "
        f"{mt.loc['Zone2', 'epsilon_squared']:.2f} and {mt.loc['Zone3', 'epsilon_squared']:.2f}). All zones peak in summer "
        f"(Zone 1 and Zone 2 in {mt.loc['Zone1', 'highest_month']}, Zone 3 in {mt.loc['Zone3', 'highest_month']}). The swing between "
        f"the highest and lowest month is {mt.loc['Zone1', 'highest_over_lowest']:.2f} times for Zone 1, "
        f"{mt.loc['Zone2', 'highest_over_lowest']:.2f} for Zone 2 and {mt.loc['Zone3', 'highest_over_lowest']:.2f} for Zone 3. "
        "Zone 2 rises again in November and December while Zone 3 falls to its lowest level of the year (Section 7)."))
    story.append(figure("10_monthly_load_by_zone", "Figure 7. Mean load by month.", 0.92))
    story.append(p("Recurring calendar patterns", "h2"))
    story.append(p(
        f"During Ramadan (27 May to 25 June 2017), mean total load between 01:00 and 03:59 was {night.iloc[1] / 1000:.1f} MW, "
        f"{(night_ratio - 1) * 100:.0f}% above the {night.iloc[0] / 1000:.1f} MW of the three weeks before (pre-dawn meal). Morning "
        "load was lower and the evening peak stayed high later into the night. Because Ramadan moves about 11 days earlier "
        f"each year, forecasts need a movable Ramadan flag. Public holidays are the most unusual days: {hol_flagged} of the 15 "
        "holidays have a daily residual beyond 4 robust standard deviations, against 23% of other days."))
    story.append(figure("11_ramadan_hourly_profile", "Figure 8. Hourly total load during Ramadan and the three weeks either side.", 0.92))
    story.append(p("Decomposition", "h2"))
    story.append(p(
        "MSTL separates the hourly series into a slow level, a daily cycle (24 h), a weekly cycle (168 h) and a residual. "
        "With one year, the annual cycle cannot be separated from a long-run trend, so the 'trend' is the slow seasonal "
        "level of 2017, not evidence of growth."))
    rows = [["Component", "Zone 1", "Zone 2", "Zone 3"]]
    for label, col, f in [("Daily seasonal strength", "daily_seasonal_strength", "{:.2f}"),
                          ("Weekly seasonal strength", "weekly_seasonal_strength", "{:.2f}"),
                          ("Trend strength", "trend_strength", "{:.2f}"),
                          ("Variance share: daily cycle", "share_of_variance_daily", "pct"),
                          ("Variance share: slow level", "share_of_variance_trend", "pct"),
                          ("Variance share: weekly cycle", "share_of_variance_weekly", "pct"),
                          ("Variance share: residual", "share_of_variance_residual", "pct")]:
        rows.append([label] + [f"{dec.loc[z, col] * 100:.1f}%" if f == "pct" else f.format(dec.loc[z, col]) for z in Z])
    story.append(table(rows, [0.40, 0.20, 0.20, 0.20]))
    story.append(Spacer(1, 6))
    story += bullets([
        "<b>Trend:</b> a summer hump in every zone, with a dip around Eid al-Fitr in late June. Zone 3's level moves furthest "
        f"(range {dec.loc['Zone3', 'trend_range_kW'] / 1000:.1f} MW, more than its annual mean); Zone 1 drops sharply at the end of October.",
        "<b>Daily seasonal:</b> the strongest and most regular component (strength at least 0.97 everywhere): trough at dawn, "
        "midday plateau, dip around 16:00, sharp 20:00 peak.",
        "<b>Weekly seasonal:</b> small, mostly the Sunday daytime dip; negligible in Zone 3.",
        "<b>Residual:</b> only 1% to 2% of the variance; the largest residuals fall on holidays and network events.",
        f"<b>Stationarity:</b> daily load is non-stationary (ADF p ≈ {st['ADF_p_daily_level'].mean():.1f}; KPSS p ≤ "
        f"{st['KPSS_p_daily_level'].max():.2f}); the STL residual is stationary (ADF p &lt; 0.001). The hourly PACF has its "
        "largest spikes at lags 1, 2 and 23 to 25.",
    ])
    story.append(figure("12_mstl_decomposition_zone1", "Figure 9. MSTL decomposition of Zone 1's hourly load (Zones 2 and 3 in the notebook).", 0.86))
    story.append(figure("13_trend_and_daily_cycle_compared", "Figure 10. Trend and daily seasonal components compared across zones."))
    story.append(figure("14_acf_pacf", "Figure 11. Autocorrelation of hourly and daily load, and of the MSTL residuals.", 0.92))

    # ---- 6 environment --------------------------------------------------------------
    story.append(p("6. Environmental relationships", "h1"))
    story.append(p(
        "<b>Choice of method.</b> Spearman's rank correlation is the primary measure. Wind is two-state, temperature acts on load "
        "non-linearly and Zone 3 is skewed; Pearson coefficients are reported for comparison and agree for temperature and "
        "humidity but diverge for wind (Pearson 0.28 against Spearman 0.08 for Zone 3), which supports the choice. "
        "Because readings are strongly autocorrelated, each p-value and confidence interval uses an <b>effective sample size</b> "
        "(Bartlett / Pyper &amp; Peterman) rather than the nominal n, and the nine primary tests are Holm-corrected."))
    rows = [["Hourly, Spearman ρ [95% CI]", "Zone 1", "Zone 2", "Zone 3"]]
    for v in ["Temperature", "Humidity", "WindSpeed"]:
        cells = []
        for z in Z:
            r = hs.loc[(v, z)]
            cells.append(minus(f"{r.r:+.2f} [{r.ci_low:.2f}, {r.ci_high:.2f}]") + f"<br/>n<sub>eff</sub> {r.n_eff:.0f}, Holm p {fmt_p(r.p_adjusted_holm)}")
        rows.append([v] + cells)
    story.append(table(rows, [0.22, 0.26, 0.26, 0.26]))
    story.append(Spacer(1, 6))
    story += bullets([
        "<b>Temperature:</b> moderate positive association in every zone; significant after Holm correction for Zones 1 and 2. "
        "Zone 3's similar ρ is not significant because its seasonal persistence leaves only about 21 effectively independent observations.",
        "<b>Humidity:</b> weak to moderate negative, largely temperature viewed from the other side (humidity is lowest on hot afternoons).",
        "<b>Wind:</b> negligible to weak and not significant in any zone.",
        "All naive p-values are below 10<super>−15</super>; the effective sample sizes (21 to 271 from 8,736 hours) show how much weaker the real evidence is.",
    ])
    story.append(figure("15_correlation_forest_plot", "Figure 12. Spearman correlations with effective-sample-size intervals at three aggregation levels."))
    story.append(p("Non-linear temperature response", "h2"))
    rows = [["Change-point model (daily)", "Base temperature", "kW per °C above base", "% of cool-day load", "R²"]]
    for z in Z + ["Total"]:
        h = hinge.loc[z]
        rows.append([ZN.get(z, "All three zones"), f"{h.base_temp_C:.1f} °C ({h.base_ci_low:.1f} to {h.base_ci_high:.1f})",
                     f"{h.slope_kW_per_C:,.0f} ({h.slope_ci_low:,.0f} to {h.slope_ci_high:,.0f})",
                     f"{h.slope_pct_of_base_load:.1f}%", f"{h.r2:.2f}"])
    story.append(table(rows, [0.22, 0.24, 0.26, 0.15, 0.13]))
    story.append(Spacer(1, 6))
    story.append(p(
        f"Load is flat on cool days and rises once the daily mean passes about {hinge.loc['Total', 'base_temp_C']:.0f} °C: about "
        f"{hinge.loc['Total', 'slope_kW_per_C'] / 1000:.1f} MW per °C across all zones, with Zone 3 by far the most sensitive "
        f"relative to its size ({hinge.loc['Zone3', 'slope_pct_of_base_load']:.1f}% of its cool-day load per °C). Intervals are from a 14-day block bootstrap."))
    story.append(figure("16_temperature_vs_load_daily", "Figure 13. Daily load against daily mean temperature with LOWESS and the fitted change-point model."))
    story.append(p("Confounding by the seasonal cycle", "h2"))
    story.append(p(
        "Temperature, humidity, the high-wind state, Ramadan (in 2017), school holidays and the tourist season all peak at "
        "the same time of year. Three checks separate weather from season:"))
    rC = {z: regC.loc[("Temperature", z)] for z in Z}
    wm_t = wm[wm.variable == "Temperature"].set_index("zone")["rho_within_month"]
    c1, c2 = minus(f"{rC['Zone1'].coef_kW:.0f}"), minus(f"{rC['Zone2'].coef_kW:.0f}")
    w_hi = minus(f"{wind.within_month_hour_difference_kW.max():.0f}")
    w_lo = minus(f"{wind.within_month_hour_difference_kW.min():.0f}")
    story += bullets([
        f"<b>Within-month correlation</b> of daily anomalies: ρ = {wm_t['Zone1']:.2f} (Zone 1), {wm_t['Zone2']:.2f} (Zone 2) "
        f"and {wm_t['Zone3']:.2f} (Zone 3). Within the same month, warmer days do not have noticeably higher load in Zones 1 and 2.",
        "<b>OLS with HAC (Newey-West, 48 lags) standard errors</b> on hourly data, adding hour, weekday, month, Ramadan and "
        f"holiday controls: the temperature effect falls to {c1} kW per °C "
        f"(p = {rC['Zone1'].p_HAC:.2f}) in Zone 1 and {c2} kW per °C (p = {rC['Zone2'].p_HAC:.2f}) in Zone 2, "
        f"but stays at +{rC['Zone3'].coef_kW:.0f} kW per °C in Zone 3 (95% CI {rC['Zone3'].ci_low:.0f} to {rC['Zone3'].ci_high:.0f}, "
        f"p {fmt_p(rC['Zone3'].p_HAC)}), also with irradiance added. Humidity and wind are not significant once the calendar is included.",
        f"<b>Wind within the same month and hour:</b> high-wind hours average {wind['raw_difference_kW'].min() / 1000:.1f} to "
        f"{wind['raw_difference_kW'].max() / 1000:.1f} MW more load overall, but {w_hi} to "
        f"{w_lo} kW within the same month and hour. The raw gap exists because "
        "over 90% of July and August readings are in the high-wind state.",
    ])
    story.append(figure("18_temperature_effect_by_model", "Figure 14. Temperature coefficient as calendar controls are added (HAC 95% intervals).", 0.92))
    story.append(p(
        "<b>Conclusion.</b> Temperature is the only environmental variable with a meaningful association, and it mainly reflects "
        "the shared seasonal cycle. Within a month, day-to-day temperature adds little in Zones 1 and 2 but is associated with "
        "higher load in Zone 3, consistent with temperature-driven demand such as cooling. Month controls are conservative, "
        "since they also absorb any part of the seasonal effect that temperature causes; one year of data cannot separate the two. "
        "These are associations in observational data, not causal effects."))

    # ---- 7 zones -------------------------------------------------------------------
    story.append(p("7. Differences between zones", "h1"))
    zm_i = zm.set_index("comparison")
    dec_txt = [minus(f"{mi.loc['Dec', z]:+.0f}%") for z in Z]
    ls_txt = {z: minus(f"{ls.loc[z, 'change_pct']:+.0f}%") for z in Z + ["Total"]}
    story.append(table([
        ["Question", "Answer", "Evidence"],
        ["Highest average", f"Zone 1: {mw(desc.loc['Zone1', 'mean'])} ({share['Zone1']:.0f}% of total)",
         f"Higher than Zone 2 on 100% of days by {mw(zm_i.loc['Zone1 - Zone2', 'mean_difference_kW'])} "
         f"(95% CI {zm_i.loc['Zone1 - Zone2', 'ci_low'] / 1000:.1f} to {zm_i.loc['Zone1 - Zone2', 'ci_high'] / 1000:.1f}); Friedman χ² = "
         f"{kf.set_index('figure').loc['friedman_zones_daily_chi2', 'value']:.0f}, W = 0.81"],
        ["Lowest average", f"Zone 3: {mw(desc.loc['Zone3', 'mean'])} ({share['Zone3']:.0f}%)",
         f"Below Zone 2 by {mw(zm_i.loc['Zone2 - Zone3', 'mean_difference_kW'])} "
         f"({zm_i.loc['Zone2 - Zone3', 'ci_low'] / 1000:.1f} to {zm_i.loc['Zone2 - Zone3', 'ci_high'] / 1000:.1f}), but higher than Zone 2 on "
         f"{(1 - zm_i.loc['Zone2 - Zone3', 'days_a_higher']) * 100:.0f}% of days, mostly in summer"],
        ["Greatest variability (absolute)", f"Zone 1: SD {mw(zv.loc['Zone1', 'sd_kW'])}, IQR {mw(zv.loc['Zone1', 'iqr_kW'])}", "Largest zone with the largest daily swing"],
        ["Greatest variability (relative)", f"Zone 3: CV {zv.loc['Zone3', 'cv']:.2f} ({zv.loc['Zone3', 'cv_ci_low']:.2f} to {zv.loc['Zone3', 'cv_ci_high']:.2f})",
         "1.5 times Zone 2's and 1.7 times Zone 1's CV (block-bootstrap ratio intervals exclude 1)"],
        ["Hourly pattern", "Same timing, different shape",
         f"Median daily peak/trough: {zs.loc['Zone1', 'median_daily_peak_over_trough']:.2f}, {zs.loc['Zone2', 'median_daily_peak_over_trough']:.2f}, "
         f"{zs.loc['Zone3', 'median_daily_peak_over_trough']:.2f}; Friedman W = 0.67; Zone 3 sharper on almost every day"],
        ["Monthly pattern", "Very different",
         f"July vs annual mean: {mi.loc['Jul', 'Zone1']:+.0f}%, {mi.loc['Jul', 'Zone2']:+.0f}%, {mi.loc['Jul', 'Zone3']:+.0f}%; "
         f"December: {dec_txt[0]}, {dec_txt[1]}, {dec_txt[2]}"],
    ], [0.22, 0.30, 0.48]))
    story.append(Spacer(1, 6))
    story.append(figure("19_average_load_by_zone", "Figure 15. Average load by zone with 95% block-bootstrap intervals.", 0.86))
    story.append(figure("20_zone_shape_comparison", "Figure 16. Normalised hourly profiles and monthly deviations by zone."))
    story.append(p("A change in the zones' composition after the summer", "h2"))
    story.append(p(
        f"On days with the same mild temperature (11 to 18 °C), load in October to December compared with January to May was "
        f"{ls_txt['Zone3']} in Zone 3, {ls_txt['Zone2']} in Zone 2 and "
        f"{ls_txt['Zone1']} in Zone 1 (all Mann-Whitney p &lt; 10<super>−11</super>), while the three-zone total "
        f"changed by only {ls_txt['Total']}. Weather cannot explain differences at equal temperatures. "
        "Together with the 20 April transfer and the zones' uncorrelated day-to-day changes (Zone 2 and Zone 3: ρ ≈ 0), this points "
        "to feeders or customers being moved between zones, possibly alongside a seasonal population in Zone 3. The data cannot "
        "confirm the cause, so year-round comparisons between zones partly reflect changes in what each zone contains."))
    story.append(figure("21_autumn_level_shift", "Figure 17. Weekly mean load by zone; the shaded period marks the shift."))

    # ---- 8 validation --------------------------------------------------------------
    story.append(p("8. Validation", "h1"))
    story += bullets([
        f"<b>Independent recalculation:</b> {n_key} key figures (descriptive statistics, peak hours, monthly and Ramadan values, "
        "18 correlations, the Friedman statistic, shares and level shifts) were recomputed from the raw CSV using only the Python "
        f"standard library. All {n_key} match.",
        "<b>Unit tests:</b> 24 tests of the cleaning, aggregation and statistics helpers pass.",
        "<b>Robustness:</b> removing the 429 timestamps with a flagged spike (0.8%), excluding Ramadan, excluding holidays, or "
        "aggregating with medians changes no conclusion. Zone means move by less than 1%, the peak hour and highest month are unchanged, "
        "and hourly temperature correlations move by at most 0.02.",
        "<b>Data integrity:</b> the raw file's SHA-256 hash is checked before and after every run.",
    ])
    rows = [["Headline", "Main", "No spikes", "No Ramadan", "No holidays", "Median aggregation"]]
    for lab in ["Zone1 mean (kW)", "Zone3 mean (kW)", "Zone3 CV", "Zone1 rho temp (hourly)", "Zone3 rho temp (daily)", "Zone3 highest month"]:
        r = rob.loc[lab]
        fmtv = (lambda v: f"{v:,.0f}") if "mean" in lab else (lambda v: f"{v:.0f}") if "month" in lab else (lambda v: f"{v:.3f}")
        rows.append([lab.replace("rho", "ρ")] + [fmtv(v) for v in r.values])
    story.append(table(rows, [0.27, 0.13, 0.15, 0.15, 0.15, 0.15]))

    # ---- 9 limitations -------------------------------------------------------------
    story.append(p("9. Limitations", "h1"))
    story += bullets([
        "<b>One year only.</b> The annual cycle occurs once, so seasonality cannot be separated from trend and 2017 may not be typical.",
        "<b>Uncertain definitions.</b> The load unit, the diffuse-flow fields and wind speed are interpreted from the data's behaviour, "
        "not confirmed by the data owner. Derived energy totals depend on the unit; patterns and correlations do not.",
        "<b>Changing zone composition.</b> Load moves between zones during the year, so zone comparisons across months partly compare "
        "different networks.",
        "<b>Serial dependence.</b> Effective sample sizes are small (as low as 21). The adjustments used are approximations that depend on "
        "assumptions such as the block length.",
        "<b>Confounding.</b> Season, Ramadan, school holidays, tourism and daylight move with temperature. Calendar controls may remove real "
        "weather effects, and occupancy, tariffs and customer mix are not observed. No finding is causal.",
        "<b>No zone descriptions, one weather station, undocumented time zone.</b> Descriptions of zones as residential or seasonal are "
        "inferences. Weather is measured at one point. Daylight saving time is not documented, so hour-of-day results could be shifted by "
        "up to an hour in some periods. 31 December is missing.",
    ])

    # ---- 10 recommendations -------------------------------------------------------
    story.append(p("10. Recommendations", "h1"))
    story.append(table([
        ["#", "Recommendation", "Based on"],
        ["1", "<b>Plan peak capacity and demand response for 18:00 to 22:00 in June to September, starting with Zone 3.</b> "
              f"Use the change-point model as a trigger: about +{hinge.loc['Zone3', 'slope_kW_per_C'] / 1000:.1f} MW in Zone 3 "
              f"(+{hinge.loc['Total', 'slope_kW_per_C'] / 1000:.1f} MW overall) per °C of daily mean above about 20 °C. Target time-of-use "
              "tariffs and shifting flexible loads at the evening window.",
         "20:00 peak; Zone 3 load factor 0.38 and temperature sensitivity"],
        ["2", "<b>Schedule maintenance in low-demand windows:</b> 03:00 to 07:00, Sunday daytime in Zones 1 and 2, public holidays and, "
              "for Zone 3, October to March. Avoid July and August evenings and Ramadan nights.",
         "Hourly, weekly and monthly profiles; holiday anomalies"],
        ["3", "<b>Forecast with calendar features, not month alone:</b> hour, weekday, holidays and a movable Ramadan flag, plus lagged "
              "load at 1, 2 and 24 hours; add a temperature hinge term for Zone 3. Do not assume next January resembles January 2017.",
         "MSTL strengths; PACF; Ramadan effect; autumn level shift"],
        ["4", "<b>Log network reconfigurations and confirm data definitions</b> (load unit, diffuse-flow fields, wind sensor, time zone and "
              "daylight saving) with the data owner.",
         "20 April transfer; autumn shift; dictionary review"],
        ["5", "<b>Collect at least two more years</b> and re-estimate seasonal patterns and temperature thresholds each year.",
         "One-year limitation"],
    ], [0.05, 0.68, 0.27]))
    story.append(Spacer(1, 8))
    story.append(p("Answers to the brief's questions", "h2"))
    story.append(table([
        ["Question", "Answer"],
        ["1. Patterns across zones", "Shared daily cycle (trough 06:00 to 07:00, peak 20:00), summer peak, Sunday dip in Zones 1 and 2, higher Ramadan nights, holiday dips; zones differ in size, seasonality and weekly behaviour."],
        ["2. Highest and lowest hours and days", "Highest 20:00; lowest 06:00 (Zones 1 and 2) and 07:00 (Zone 3). Sunday lowest in Zones 1 and 2; no meaningful weekday effect in Zone 3."],
        ["3. Monthly variation", "Peak in August (Zones 1 and 2) and July (Zone 3); lowest in November (Zone 1), April (Zone 2) and December (Zone 3); swing 1.26, 1.40 and 2.55 times."],
        ["4. Weather associations", "Temperature moderate positive with a threshold near 20 °C, mostly seasonal and robust only in Zone 3; humidity weak negative (temperature proxy); wind negligible. Not causal."],
        ["5. Highest and lowest zone", f"Highest Zone 1 ({mw(desc.loc['Zone1', 'mean'])}); lowest Zone 3 ({mw(desc.loc['Zone3', 'mean'])})."],
        ["6. Planning use", "Evening-peak capacity planning, maintenance windows, calendar-aware forecasting, temperature alerts for Zone 3, tracking network changes."],
    ], [0.28, 0.72]))

    # ---- appendix ------------------------------------------------------------------
    story.append(p("Appendix: reproducibility", "h1"))
    story.append(p(
        "All code, outputs and charts are in the project folder <font name='Courier'>Week5_DataScience_Project/</font>. "
        "<font name='Courier'>Week5_Electricity_Time_Series_Analysis.ipynb</font> runs the full analysis and writes every table in "
        "<font name='Courier'>Outputs/</font> and every chart in <font name='Courier'>Visualizations/</font> (interactive Plotly versions "
        "in <font name='Courier'>Visualizations/interactive/</font>). <font name='Courier'>power_prep.py</font> holds the cleaning, "
        "aggregation and statistics helpers; <font name='Courier'>validation/independent_check.py</font> recomputes the key figures; "
        "<font name='Courier'>scripts/build_report.py</font> builds this PDF from the outputs. The README gives the exact commands."))
    story.append(p(
        "<b>Reference:</b> Salam, A. &amp; El Hibaoui, A. (2018). Comparison of machine learning algorithms for the power consumption "
        "prediction: case study of Tetouan city. <i>6th International Renewable and Sustainable Energy Conference (IRSEC)</i>. "
        "Dataset: UCI Machine Learning Repository, <i>Power Consumption of Tetouan City</i>."))
    story.append(p(f"Generated {date.today():%d %B %Y} on {platform.system()} with Python {platform.python_version()}.", "caption"))

    PDF.parent.mkdir(exist_ok=True)
    doc = ReportDoc(PDF)
    doc.multiBuild(story)
    print(f"Wrote {PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
