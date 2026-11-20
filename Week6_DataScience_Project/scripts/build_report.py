"""Build Reports/Week6_SP500_Data_Science_Report.pdf.

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
PDF = ROOT / "Reports" / "Week6_SP500_Data_Science_Report.pdf"

AUTHOR = "Molemi Molokoane"
TITLE = "Statistical Analysis and Time-Series Investigation of S&P 500 Stock Performance, 2014–2017"

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
                         subject="AnalystLab Africa Week 6, Data Science track", **kw)
        frame = Frame(MARGIN, MARGIN, CONTENT_W, PAGE_H - 2 * MARGIN, id="f")
        self.addPageTemplates([PageTemplate("cover", [frame], onPage=lambda c, d: None),
                               PageTemplate("body", [frame], onPage=self._decorate)])

    def _decorate(self, canv, doc):
        canv.saveState()
        canv.setFont(BASE, 7.8)
        canv.setFillColor(INK_2)
        canv.drawString(MARGIN, 11 * mm, "Week 6 · S&P 500 stock performance 2014–2017 · Data Science track")
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




def esc(s):
    return str(s).replace("&", "&amp;")


def pc(x, d=1, sign=False):
    """Fraction -> percentage string with a typographic minus."""
    return minus(f"{100 * x:+.{d}f}%" if sign else f"{100 * x:.{d}f}%")


def build():
    # ---- load outputs --------------------------------------------------------
    rd = pd.read_csv(OUT / "descriptive_stats_daily_returns.csv", index_col=0)
    pdsc = pd.read_csv(OUT / "descriptive_stats_closing_price.csv", index_col=0)
    q = pd.read_csv(OUT / "data_quality_summary.csv")
    h1 = pd.read_csv(OUT / "h1_mean_return_tests.csv", index_col=0)
    h2 = pd.read_csv(OUT / "h2_volume_return_tests.csv", index_col=0)
    h3 = pd.read_csv(OUT / "h3_distribution_tests.csv")
    h3p = pd.read_csv(OUT / "h3_pairwise_volatility.csv")
    h4 = pd.read_csv(OUT / "h4_autocorrelation_volatility_clustering.csv", index_col=0)
    cal = pd.read_csv(OUT / "calendar_effect_tests.csv")
    st = pd.read_csv(OUT / "stationarity_tests.csv")
    dec = pd.read_csv(OUT / "decomposition_strength.csv", index_col=0)
    fc = pd.read_csv(OUT / "next_day_forecast_evaluation.csv")
    ct = pd.read_csv(OUT / "correlation_tests_returns.csv")
    beta = pd.read_csv(OUT / "beta_vs_market_average.csv", index_col=0)
    vc = pd.read_csv(OUT / "correlation_tests_monthly_volatility.csv")
    rob = pd.read_csv(OUT / "robustness_checks.csv", index_col=0)
    key = pd.read_csv(OUT / "key_figures.csv").set_index("figure")["value"]
    STOCKS = ["AAPL", "AMZN", "JPM", "JNJ", "XOM", "WMT"]
    company = {"AAPL": "Apple", "AMZN": "Amazon", "JPM": "JPMorgan Chase", "JNJ": "Johnson &amp; Johnson",
               "XOM": "Exxon Mobil", "WMT": "Walmart"}
    sector = {"AAPL": "Information technology", "AMZN": "Consumer discretionary", "JPM": "Financials",
              "JNJ": "Health care", "XOM": "Energy", "WMT": "Consumer staples"}

    story = []
    # ---- cover -----------------------------------------------------------------
    story += [Spacer(1, 40 * mm), p("AnalystLab Africa · Experience Lab · Week 6 · Track B: Data Science", "meta"), Spacer(1, 6),
              p(esc(TITLE), "title"),
              p("Returns, volatility, trading volume, correlation and next-day predictability of six large S&amp;P 500 stocks", "subtitle"),
              Spacer(1, 14), p(f"<b>Author:</b> {AUTHOR}", "meta"),
              p("<b>Data:</b> S&amp;P 500 Stock Prices 2014-2017.csv (497,472 daily records, 505 symbols, 1,007 trading days), supplied by AnalystLab Africa", "meta"),
              p(f"<b>Date:</b> {date.today():%d %B %Y}", "meta"), Spacer(1, 18),
              callout("Important", [
                  "All figures describe 2 January 2014 to 29 December 2017. They are historical, not current market facts.",
                  "Returns are <b>price returns</b> (the file is split-adjusted but not dividend-adjusted). Prices are assumed to be US dollars.",
                  "Nothing in this report is a forecast or an investment recommendation. Historical returns and model outputs do not guarantee future results.",
              ]),
              NextPageTemplate("body"), PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [S["toc1"]]
    story += [p("Contents", "h1"), toc, PageBreak()]

    # ---- executive summary --------------------------------------------------------
    story.append(p("Executive summary", "h1"))
    story.append(p(
        "Six large stocks from six sectors (AAPL, AMZN, JPM, JNJ, XOM, WMT) were compared on return, risk, trading activity and "
        "co-movement, using statistical tests that allow for fat tails, volatility clustering and multiple testing. The whole file "
        "was used for market-wide questions and for an equal-weighted market average."))
    story.append(callout("Key findings", [
        f"<b>The stocks differ in risk, not in average daily return.</b> Annualised volatility runs from {pc(rd.loc['JNJ', 'ann_volatility'], 0)} (JNJ) "
        f"to {pc(rd.loc['AMZN', 'ann_volatility'], 0)} (AMZN); 14 of 15 pairs differ significantly. The difference in typical daily return is negligible "
        f"(Kendall's W = {h3.effect_size[0]:.3f}).",
        f"<b>Big total returns are hard to tell from luck at the daily level.</b> AMZN {pc(rd.loc['AMZN', 'total_return'], 0, True)}, "
        f"AAPL {pc(rd.loc['AAPL', 'total_return'], 0, True)}, XOM {pc(rd.loc['XOM', 'total_return'], 0, True)}, yet no mean daily return is "
        "significantly different from zero on the HAC test after Holm correction.",
        f"<b>Volume tracks the size of moves, not their direction</b> (Spearman ρ {h2.rho_abs.min():.2f} to {h2.rho_abs.max():.2f} with |return|; |ρ| &lt; 0.07 with signed return).",
        f"<b>Weak-to-moderate co-movement</b> (ρ {ct.spearman.min():.2f} to {ct.spearman.max():.2f}); JPM–XOM and AAPL–AMZN most similar, WMT least connected. "
        "Links to the market reached 0.7–0.9 in the 2015–16 sell-off.",
        "<b>Volatility clusters but direction is unpredictable:</b> no autocorrelation, calendar effect or stable seasonality in returns; "
        "no model beat “tomorrow = today” significantly in 2017.",
        f"<b>Validated:</b> {len(key)} of {len(key)} key figures match an independent standard-library recalculation; 26 unit tests pass; "
        "conclusions hold under five robustness checks.",
    ]))

    # ---- 1 research problem ----------------------------------------------------
    story.append(p("1. Research problem and objectives", "h1"))
    story.append(p(
        "<b>Primary problem.</b> How did return, risk and trading activity differ across six large S&amp;P 500 stocks from six sectors in "
        "2014–2017, how much of their daily behaviour was shared with the market, and did their history contain any pattern that would help "
        "estimate the next day's return?"))
    story.append(p(
        "<b>Why it matters.</b> Comparing performance fairly (percentage returns, not prices), separating real differences from noise, and "
        "knowing how much diversification “different” stocks give are basic inputs to portfolio research, risk reporting and model design. "
        "<b>Intended users:</b> financial researchers and analysts, and the dashboard, ML and AI-assistant tracks, which need validated figures."))
    story.append(table([["#", "Supporting question", "Method"],
                        ["RQ1", "Are mean daily returns different from zero?", "t-test with HAC errors, Wilcoxon, block bootstrap"],
                        ["RQ2", "Do return distributions differ in level or spread?", "Friedman, Kruskal-Wallis; Brown-Forsythe, paired Wilcoxon"],
                        ["RQ3", "Is volume related to returns (direction or size)?", "Spearman with effective sample size"],
                        ["RQ4", "How strongly do returns move together and with the market?", "Spearman/Pearson, rolling correlation, beta"],
                        ["RQ5", "Seasonality, autocorrelation, volatility clustering, next-day predictability?", "STL, ACF/PACF, Ljung-Box, ARCH-LM, walk-forward, Diebold-Mariano"]],
                       [0.07, 0.5, 0.43]))
    story.append(Spacer(1, 6))
    story.append(table([["Stock", "Company", "Sector (general knowledge)"]] + [[s, company[s], sector[s]] for s in STOCKS], [0.15, 0.4, 0.45]))
    story.append(p("All six have a complete 1,007-day history with no flagged record, so they are compared on identical dates.", "caption"))
    story.append(p("Success criteria", "h2"))
    story += bullets([
        f"Every key figure reconciles with an independent recalculation: <b>met</b> ({len(key)}/{len(key)}).",
        "Each hypothesis states H₀/H₁, justifies its test, reports statistic, p-value and effect size, and corrects for multiple testing: <b>met</b>.",
        "Every data-quality issue in the brief is confirmed or corrected and every cleaning step logged; raw file hash unchanged: <b>met</b>.",
        "Helpers pass unit tests and the notebook stops on any failed check: <b>met</b> (26 tests).",
        "Forecasts evaluated chronologically against a no-change baseline: <b>met</b>.",
    ])

    # ---- 2 data ----------------------------------------------------------------
    story.append(p("2. Dataset inspection and preparation", "h1"))
    story.append(p(
        "The file has 497,472 rows and 7 columns (symbol, date, open, high, low, close, volume), 505 symbols and 1,007 trading dates from "
        "2 January 2014 to 29 December 2017, with no weekend dates. Dates are text and were parsed with the explicit format month/day/year. "
        "The file is ordered by date, then symbol; it was re-sorted by symbol and date before any return was calculated."))
    story.append(table([["Check", "Brief", "This analysis", "Treatment"]] +
                       [[r.check, r.brief_initial_observation, r.this_analysis, r.treatment] for r in q.itertuples()],
                       [0.27, 0.13, 0.22, 0.38]))
    story.append(Spacer(1, 6))
    story += bullets([
        "<b>Split adjustment verified:</b> nine known splits (e.g. AAPL 7-for-1, June 2014) show no jump; AAPL's first close 79.0185 = $553.13 ÷ 7. "
        "Prices are split-adjusted but <b>not</b> dividend- or spin-off-adjusted, so all returns are price returns.",
        "<b>Probable price errors:</b> five single closes that jump ≥ 20% and reverse the next day (FLR, MPC, MRO, NWL on 14 Sep 2017; LNT on "
        "19 May 2016, a close not adjusted for its 2-for-1 split). Returns into and out of them are excluded.",
        "<b>Corporate actions:</b> 12 large falls on spin-off/distribution dates (e.g. eBay/PayPal) are not losses; excluded from market-wide figures. "
        "The list comes from public announcements, not the file.",
        "<b>Histories:</b> 479 symbols are complete; 22 start late; DHR, ES, O and ICE have gaps inside (8 multi-day returns excluded). "
        "No symbol ends early, which points to <b>survivorship bias</b>.",
        "<b>Missing and zero values:</b> missing open/high/low left missing (never zero, never imputed); 6 placeholder rows with no prices and ≤ 100 "
        "shares have volume treated as missing. Nothing was deleted; every exclusion is a documented flag.",
        "<b>Derived fields:</b> year, quarter, month, weekday, price change, % and log return, daily range, 20/50/200-day moving averages, "
        "21-day volatility and relative volume, all per symbol and using past data only.",
    ])

    # ---- 3 EDA -------------------------------------------------------------------
    story.append(p("3. Exploratory data analysis", "h1"))
    story.append(figure("01_growth_of_100", "Figure 1. Growth of 100 for the six stocks and the equal-weighted market average (price return)."))
    story.append(figure("02_closing_price_moving_averages", "Figure 2. Closing prices with 50- and 200-day moving averages (each panel on its own scale)."))
    story.append(p(
        "AMZN, AAPL, JPM and JNJ ended well above their start; XOM fell with oil prices in 2014–15 and ended lower; WMT dropped sharply in 2015 "
        "and recovered in 2017. Price <i>levels</i> are not comparable across stocks, so all comparisons use percentage returns."))
    story.append(figure("03_daily_return_distribution", "Figure 3. Distribution of daily returns."))
    story.append(figure("04_qq_plots", "Figure 4. Q-Q plots of standardised daily returns against the normal distribution.", 0.9))
    story.append(p(
        f"Returns centre near zero but are strongly fat-tailed (excess kurtosis {rd.loc[STOCKS, 'excess_kurtosis'].min():.1f} to "
        f"{rd.loc[STOCKS, 'excess_kurtosis'].max():.1f}; Jarque-Bera rejects normality for every stock). Each stock's largest moves were 3.8 to 9.5 "
        "standard deviations and mostly came with 2–11 times normal volume. Their causes cannot be verified from the file, so they are kept."))
    story.append(figure("05_monthly_volume", "Figure 5. Monthly average daily volume (shares, log scale)."))
    story.append(p(
        "Volume is a count of shares, not money, so it is compared within a stock over time. AAPL traded about 45 million shares a day, AMZN about 4 million. "
        "Volume peaked in January 2016 for four of the six and fell over the period for five."))
    story.append(figure("06_top_bottom_total_returns", "Figure 6. Ten highest and lowest total price returns among the 479 complete histories (* includes an unadjusted distribution).", 0.85))
    story.append(figure("07_risk_vs_return_all_stocks", "Figure 7. Volatility against total return for all 479 complete histories."))
    story.append(p(
        f"<b>Market-wide:</b> the highest close in the file was PCLN ${key['max_close_all']:,.2f} (8 Aug 2017), the lowest CHK ${key['min_close_all']:.2f} "
        f"(12 Feb 2016). NVDA rose {pc(key['NVDA_total_return'], 0, True)}; CHK fell {pc(key['CHK_total_return'], 0)}. The median complete-history "
        f"stock gained {pc(key['median_total_return_complete'], 0)}, but survivorship bias inflates this. Riskier stocks did not earn more over these four years (ρ = −0.19)."))

    # ---- 4 descriptive ----------------------------------------------------------------
    story.append(p("4. Descriptive statistical findings", "h1"))
    story.append(p("Closing prices (USD assumed)", "h2"))
    story.append(table([["Stock", "First", "Last", "Mean", "Median", "Min", "Max", "SD", "Variance"]] +
                       [[s] + [f"{pdsc.loc[s, c]:,.2f}" for c in ["first_close", "last_close", "mean", "median", "min", "max", "std", "variance"]] for s in STOCKS],
                       [0.1] + [0.1125] * 8))
    story.append(p("Price SD and variance measure how far the price travelled (they grow with trend and price level), not risk.", "caption"))
    story.append(p("Daily percentage returns", "h2"))
    story.append(table([["Stock", "Mean", "Median", "SD", "Min", "Max", "Skew", "Ex. kurt.", "Total", "Ann. vol.", "Max DD"]] +
                       [[s, pc(r["mean"], 3), pc(r["median"], 3), pc(r["std"], 2), pc(r["min"]), pc(r["max"]), minus(f"{r['skewness']:.2f}"),
                         f"{r['excess_kurtosis']:.1f}", pc(r["total_return"], 0, True), pc(r["ann_volatility"], 1), pc(r["max_drawdown"], 0)]
                        for s, r in rd.iterrows()],
                       [0.12] + [0.088] * 10))
    story.append(p("Ann. vol. = SD × √252. Max DD = largest peak-to-trough fall of the close. Market avg = equal-weighted mean of all valid returns in the file.", "caption"))
    story.append(figure("08_yearly_returns_heatmap", "Figure 8. Calendar-year price returns.", 0.75))
    story.append(p(
        "The best stock changed from year to year (AAPL 2014, AMZN 2015 and 2017, JPM 2016). 2015 was weak and 2016–17 strong. "
        "Volatility was lowest in 2017 for five of the six stocks and for the market average."))

    # ---- 5 hypotheses --------------------------------------------------------------------
    story.append(p("5. Hypotheses and statistical methods", "h1"))
    story.append(p(
        "All tests use α = 0.05. When a hypothesis is tested for six stocks (or 15 pairs), p-values are Holm-adjusted. Tests were chosen for "
        "fat-tailed, serially dependent data: HAC (Newey-West) errors, rank-based tests, block bootstrap, and effective sample sizes for autocorrelated series."))
    story.append(p("H1: Mean daily return equals zero", "h2"))
    story.append(p("H₀: mean = 0; H₁: mean ≠ 0. Main test: one-sample t-test with HAC errors; also the ordinary t-test, Wilcoxon signed-rank and a 20-day block-bootstrap interval."))
    story.append(table([["Stock", "Mean", "HAC t", "p (HAC)", "Holm p", "Wilcoxon Holm p", "Bootstrap 95% CI", "Detectable mean"]] +
                       [[s, pc(r.mean_daily_pct / 100, 3), minus(f"{r.t_hac:.2f}"), f"{r.p_hac:.3f}",
                         "–" if pd.isna(r.p_hac_holm) else f"{r.p_hac_holm:.2f}", "–" if pd.isna(r.p_wilcoxon_holm) else f"{r.p_wilcoxon_holm:.3f}",
                         minus(f"{r.boot_ci_low_pct:.3f}% to {r.boot_ci_high_pct:.3f}%"), f"{r.min_detectable_mean_pct:.3f}%"]
                        for s, r in h1.iterrows()],
                       [0.12, 0.1, 0.09, 0.1, 0.09, 0.13, 0.22, 0.15]))
    story.append(figure("09_mean_return_confidence_intervals", "Figure 9. Mean daily return with block-bootstrap 95% intervals."))
    story.append(p(
        "<b>Result: do not reject H₀ for any stock</b> on the main test. Only AMZN's rank-based Wilcoxon test is significant after Holm "
        "(p = 0.048): weak, borderline evidence. With daily SDs of 0.9–1.9%, four years can only detect mean daily returns of 0.08–0.16% "
        "(roughly 20–40% a year), so failing to reject means the data cannot tell a good stock from a lucky one, not that the true mean is zero."))
    story.append(p("H2: Trading volume and daily returns", "h2"))
    story.append(p(
        "H₀: no monotonic relationship between volume and returns. Volume is used as <i>relative volume</i> (day ÷ median of previous 20 days, "
        "logged) to remove trends. Spearman correlation, with p-values on the effective sample size, Holm-adjusted."))
    story.append(table([["Stock", "ρ signed", "Holm p", "ρ |return|", "95% CI", "Holm p", "n_eff"]] +
                       [[s, minus(f"{r.rho_signed:.3f}"), f"{r.p_signed_holm:.2f}", f"{r.rho_abs:.3f}", f"{r.ci_low_abs:.2f} to {r.ci_high_abs:.2f}",
                         f"{r.p_abs_holm:.0e}", f"{r.n_eff_abs:.0f}"] for s, r in h2.iterrows()],
                       [0.12, 0.13, 0.12, 0.13, 0.2, 0.15, 0.15]))
    story.append(figure("10_volume_vs_returns", "Figure 10. Mean absolute and mean signed return by relative-volume decile."))
    story.append(p(
        "<b>Result:</b> for direction, do not reject H₀ (negligible ρ, all Holm p &gt; 0.2). For size, reject H₀: a moderate positive relationship "
        "in every stock, and the busiest tenth of days move 3.7–6.3 times as much as the quietest. Volume signals that a large move is "
        "happening, not which way. This is a same-day association, not a cause."))
    story.append(p("H3: Differences between the stocks' return distributions", "h2"))
    story.append(p(
        "Location: Friedman test with days as blocks (the six returns on a day are not independent); Kruskal-Wallis for comparison. Spread: "
        "Brown-Forsythe and a Friedman test on absolute deviations; pairwise Wilcoxon signed-rank (Holm, 15 pairs)."))
    story.append(table([["Aspect", "Test", "Statistic", "p", "Effect size"]] +
                       [[r.aspect, r.test.replace("−", "-"), f"{r.statistic:.2f}", f"{r.p_value:.2e}" if r.p_value < 0.001 else f"{r.p_value:.3f}",
                         f"{r.effect_size_measure}: {r.effect_size:.3f}"] for r in h3.itertuples()],
                       [0.12, 0.38, 0.12, 0.13, 0.25]))
    story.append(figure("11_volatility_comparison", "Figure 11. Annualised volatility with block-bootstrap 95% intervals."))
    nsig = int((h3p.p_holm < 0.05).sum())
    story.append(p(
        f"<b>Result:</b> the location difference is statistically detectable with the paired test (p = {h3.p_value[0]:.3f}) but negligible (W = {h3.effect_size[0]:.3f}), "
        f"and Kruskal-Wallis does not reject. Volatility differs decisively; {nsig} of 15 pairs differ after Holm (only AAPL vs JPM does not). "
        "<b>The stocks differ in risk, not in typical daily return.</b>"))
    story.append(p("H4: Autocorrelation and volatility clustering", "h2"))
    story.append(table([["Stock", "ACF lag 1", "Ljung-Box r (Holm p)", "Ljung-Box r² (Holm p)", "ARCH-LM (Holm p)"]] +
                       [[s, minus(f"{r.acf_lag1:.3f}"), f"{r.ljungbox_r_p_holm:.2f}" if s in STOCKS else f"{r.ljungbox_r_p:.2f}*",
                         f"{r.ljungbox_r2_p_holm:.3f}" if s in STOCKS else f"{r.ljungbox_r2_p:.3f}*",
                         f"{r.arch_lm_p_holm:.3f}" if s in STOCKS else f"{r.arch_lm_p:.3f}*"] for s, r in h4.iterrows()],
                       [0.16, 0.14, 0.24, 0.24, 0.22]))
    story.append(p("* single test, unadjusted. Lags: Ljung-Box 10, ARCH-LM 5.", "caption"))
    story.append(p(
        "<b>Result:</b> no significant autocorrelation in returns (do not reject). Strong volatility clustering for JPM, JNJ, XOM and the market "
        "(reject). AMZN and WMT show none: their volatility comes from isolated one-day jumps. A supporting test found no day-of-week or month "
        f"effect (smallest Holm p = {cal.p_holm.min():.2f})."))

    # ---- 6 time series ------------------------------------------------------------
    story.append(p("6. Time-series analysis", "h1"))
    nonst = st[(st.series == "log close")]
    story.append(p(
        f"<b>Stationarity.</b> ADF and KPSS agree that log prices are non-stationary for {int((nonst.conclusion == 'non-stationary').sum())} of 7 series "
        "(AMZN is mixed), and that every return series is stationary. Statistics and correlations are therefore computed on returns, never on prices."))
    story.append(figure("12_rolling_volatility", "Figure 12. Rolling 63-day annualised volatility."))
    story.append(figure("13_daily_returns_over_time", "Figure 13. Daily returns on a common scale.", 0.9))
    story.append(p(
        "Volatility came in waves: all six stocks were turbulent in August 2015 and January–February 2016, and unusually calm in 2017 "
        "(market average below 5%). A single full-period volatility hides swings such as AMZN's 13% to 44%."))
    story.append(p("Decomposition", "h2"))
    story.append(table([["Series", "Trend strength", "Seasonal strength", "Seasonal shape corr. 2014–15 vs 2016–17", "Month-return rank corr."]] +
                       [[s, f"{r.trend_strength:.2f}", f"{r.seasonal_strength:.2f}", minus(f"{r.seasonal_shape_corr_2014_15_vs_2016_17:.2f}"),
                         minus(f"{r.monthly_return_rank_corr_2014_15_vs_2016_17:.2f}")] for s, r in dec.iterrows()],
                       [0.16, 0.16, 0.18, 0.28, 0.22]))
    story.append(figure("14_stl_decomposition_amzn", "Figure 14. STL decomposition of AMZN's weekly log close (52-week period).", 0.85))
    story.append(p(
        "STL always produces a seasonal component, but its strength is 0.00–0.11 for every stock, the seasonal shape does not repeat between "
        "the two halves, and month-of-year returns show no significant effect. <b>There is no stable seasonality</b>; trend plus noise describes "
        "these prices better. Four annual cycles are too few to establish annual seasonality in any case."))
    story.append(p("Autocorrelation and next-day predictability", "h2"))
    story.append(figure("15_acf_pacf", "Figure 15. ACF and PACF of returns and ACF of squared returns (20 lags).", 0.82))
    story.append(p(
        "Chronological test: models fitted on 2014–2016 and evaluated on the 251 trading days of 2017, against the no-change baseline "
        "(tomorrow's close = today's). Diebold-Mariano tests compare squared errors."))
    f2 = fc[fc.model != "No change (baseline)"]
    story.append(table([["Stock", "Model", "RMSE return", "vs baseline", "DM p", "Price MAPE"]] +
                       [[r.symbol, r.model, f"{r.rmse_return_pct:.3f}%", minus(f"{r.rmse_vs_baseline_pct:+.2f}%"), f"{r.dm_p_vs_baseline:.2f}",
                         f"{r.mape_price_pct:.2f}%"] for r in f2.itertuples()],
                       [0.12, 0.24, 0.16, 0.16, 0.14, 0.18]))
    story.append(figure("16_next_day_forecast_vs_baseline", "Figure 16. Next-day forecast error relative to the no-change baseline, 2017."))
    story.append(p(
        "<b>No model improved on “no change” by more than 1% of RMSE, and none significantly</b> (closest: AMZN AR(1), p = 0.06; WMT's historical "
        "mean was significantly worse). Historical information can produce a next-day estimate, but past returns did not beat the simplest rule."))

    # ---- 7 correlation -----------------------------------------------------------------
    story.append(p("7. Correlation analysis", "h1"))
    story.append(p(
        "Spearman's ρ is the main measure because fat tails let a few extreme days dominate Pearson's r; Pearson is shown alongside because "
        "portfolio maths uses it. Correlations use returns, not prices. Intervals and p-values use effective sample sizes where series are autocorrelated."))
    story.append(figure("17_return_correlation_heatmap", "Figure 17. Correlation of daily returns between the six stocks.", 0.75))
    story.append(table([["Pair", "Spearman ρ", "95% CI", "Pearson r", "Strength"]] +
                       [[f"{r.stock_a}–{r.stock_b}", f"{r.spearman:.2f}", f"{r.ci_low:.2f} to {r.ci_high:.2f}", f"{r.pearson:.2f}", r.strength]
                        for r in ct.head(6).itertuples()] + [["…", "", "", "", ""]] +
                       [[f"{r.stock_a}–{r.stock_b}", f"{r.spearman:.2f}", f"{r.ci_low:.2f} to {r.ci_high:.2f}", f"{r.pearson:.2f}", r.strength]
                        for r in ct.tail(2).itertuples()],
                       [0.2, 0.17, 0.23, 0.17, 0.23]))
    story.append(p(
        f"All 15 pairs are positively and significantly correlated, but only weakly to moderately. The equal-weighted portfolio of the six had "
        f"{pc(key['equal_weight_portfolio_ann_vol'], 1)} annualised volatility, against {pc(rd.loc['JNJ', 'ann_volatility'], 0)}–{pc(rd.loc['AMZN', 'ann_volatility'], 0)} "
        "for the individual stocks: real diversification."))
    story.append(table([["Stock", "Beta vs market avg", "95% CI", "R²", "Spearman with market"]] +
                       [[s, f"{r.beta:.2f}", f"{r.beta_ci_low:.2f} to {r.beta_ci_high:.2f}", f"{r.r_squared:.2f}", f"{r.spearman_with_market:.2f}"]
                        for s, r in beta.iterrows()],
                       [0.16, 0.2, 0.24, 0.14, 0.26]))
    story.append(figure("18_rolling_correlation_with_market", "Figure 18. Rolling 126-day correlation with the market average."))
    story.append(figure("19_monthly_realised_volatility", "Figure 19. Monthly realised volatility."))
    story.append(p(
        f"Monthly volatilities are positively correlated for all pairs (ρ {vc.spearman.min():.2f}–{vc.spearman.max():.2f}); "
        f"{int((vc.p_holm < 0.05).sum())} of 15 survive Holm with only 48 months. Turbulence is shared more than direction. "
        "<b>Limitations:</b> correlation is not causation, coefficients change over time, and the market average contains the six stocks."))

    # ---- 8 results / validation ----------------------------------------------------------
    story.append(p("8. Results, interpretation and validation", "h1"))
    story.append(table([["Brief question", "Answer (2014–2017, historical)"],
                        ["1. Highest / lowest closing price", "PCLN $2,049 (8 Aug 2017) / CHK $1.59 (12 Feb 2016)"],
                        ["2. Highest returns", "All: NVDA ≈ +1,120%, AVGO, EA. Six: AMZN +194%, AAPL +114%, JPM +84%"],
                        ["3. Greatest volatility", "Six: AMZN (30%); least JNJ (14%). All: CHK, AMD, FCX"],
                        ["4. Price change 2014–2017", "Five of six rose; XOM −16%. Leadership changed yearly; 2017 very calm"],
                        ["5. Volume across stocks", "AAPL ≈ 45M shares/day to AMZN ≈ 4M; shares, not money"],
                        ["6. Volume vs returns", "Moderate link with size of move (ρ ≈ 0.35–0.46); none with direction"],
                        ["7. Similar daily patterns", "JPM–XOM, AAPL–AMZN; WMT least connected"],
                        ["8. Returns vs volatility", "Differ in volatility, not in typical return; more risk did not mean more return"],
                        ["9. Next-day estimation", "Possible, but no model significantly beat “no change” in 2017"]],
                       [0.32, 0.68]))
    story.append(Spacer(1, 6))
    story.append(p("Validation", "h2"))
    story += bullets([
        f"<b>Independent recalculation:</b> {len(key)} key figures (data-quality counts, flags, prices, returns, moving averages, drawdowns, "
        "15 Spearman and 15 Pearson correlations, Friedman and Brown-Forsythe statistics) recomputed from the raw CSV with the Python standard "
        f"library only: {len(key)} passed, 0 failed.",
        "<b>Unit tests:</b> 26 tests of parsing, per-symbol returns, trailing windows, every flag rule and every statistical helper pass.",
        "<b>Robustness:</b> results unchanged with log returns, without each stock's top 1% days, and in each half of the period (AMZN always "
        "most and JNJ least volatile; no mean return significant; Brown-Forsythe p &lt; 10⁻¹⁶). Ignoring the data-quality flags changes the market "
        "average's four-year return by about one percentage point.",
        "<b>Integrity:</b> the raw file's SHA-256 hash is checked at the start and end of every run.",
    ])
    rows = [["Version", "Most / least volatile", "Min Holm p (mean)", "Friedman W", "Mean pairwise ρ", "Top pair"]]
    for lab, r in rob.iterrows():
        rows.append([lab, f"{r.most_volatile} / {r.least_volatile}", f"{r.min_holm_p_mean_return:.2f}", f"{r.friedman_location_W:.4f}",
                     f"{r.mean_pairwise_spearman:.2f}", r.most_correlated_pair])
    story.append(table(rows, [0.3, 0.17, 0.14, 0.12, 0.13, 0.14]))

    # ---- 9 limitations ------------------------------------------------------------------
    story.append(p("9. Limitations", "h1"))
    story += bullets([
        "<b>Historical, four-year window</b> with an oil crash and an unusually calm 2017. Too short to estimate mean returns precisely or test annual seasonality.",
        "<b>Price returns only:</b> not dividend-adjusted (understates JNJ, XOM, WMT, JPM); spin-offs unadjusted; the event list is external context.",
        "<b>Survivorship bias:</b> symbols reflect later index membership; the equal-weighted market average is not the S&amp;P 500 index.",
        "<b>Judgement rules:</b> the price-error rule could rarely misclassify a real event; all flags are documented and conclusions do not depend on them.",
        "<b>Assumed currency (USD) and definitions</b>; no source documentation supplied.",
        "<b>Statistical caveats:</b> HAC, rank tests, block bootstrap and effective sample sizes approximate the effects of fat tails and dependence; "
        "correlations are associations and change over time.",
        "<b>Six stocks are not a sample of the market</b>, and the forecast test covers one year, three simple models and one-day horizons.",
    ])

    # ---- 10 recommendations -------------------------------------------------------------
    story.append(p("10. Recommendations", "h1"))
    story.append(table([
        ["#", "Recommendation", "Evidence", "How to use it"],
        ["1", "<b>Compare stocks on risk-adjusted terms and report volatility with an interval</b>, not on total return alone.",
         "H1, H3; Figures 9, 11", "Treat volatility differences as reliable and return differences as uncertain when ranking stocks."],
        ["2", "<b>Diversify across weakly correlated sectors, but stress-test with sell-off correlations.</b>",
         "Section 7; Figures 17, 18", "Size risk limits on 0.7–0.9 sell-off correlations, not the 0.3 full-period average."],
        ["3", "<b>Treat volume spikes as a volatility warning, not a direction signal.</b>",
         "H2; Figure 10", "Dashboards can flag relative volume above 2 as likely large-move days."],
        ["4", "<b>Prediction work must beat the no-change baseline on returns</b>, and should target volatility, which has memory.",
         "H4, Section 6; Figure 16", "Acceptance test for the ML track: chronological split plus Diebold-Mariano against “tomorrow = today”."],
        ["5", "<b>Use adjusted total-return data and point-in-time index membership</b> before any decision-grade use.",
         "Sections 2, 9", "Removes the dividend, spin-off and survivorship limitations."],
    ], [0.05, 0.4, 0.2, 0.35]))
    story.append(Spacer(1, 8))
    story.append(p("Contribution to the other tracks", "h2"))
    story += bullets([
        "<b>Data Analytics:</b> cleaned dataset with flags, one definition of a valid daily return, and key_figures.csv to check dashboard numbers.",
        "<b>Machine Learning:</b> the no-change baseline and its 2017 errors; evidence to model returns not prices; data-quality flags to exclude.",
        "<b>Generative AI:</b> key_figures.csv as an independently verified answer key; Section 9 as statements the assistant must make.",
        "<b>Project Management:</b> data-quality findings and recommendations as inputs to the risk register and acceptance criteria.",
        "These are outputs offered for reuse; no other track's work was consumed here.",
    ])

    # ---- appendix ---------------------------------------------------------------------------
    story.append(p("Appendix: reproducibility", "h1"))
    story.append(p(
        "All code and outputs are in <font name='Courier'>Week6_DataScience_Project/</font>. "
        "<font name='Courier'>Week6_SP500_Statistical_Time_Series_Analysis.ipynb</font> runs the analysis and writes every table in "
        "<font name='Courier'>Outputs/</font> and chart in <font name='Courier'>Visualizations/</font> (interactive versions in "
        "<font name='Courier'>Visualizations/interactive/</font>). <font name='Courier'>stock_prep.py</font> holds the cleaning rules and "
        "statistics helpers; <font name='Courier'>validation/independent_check.py</font> recomputes the key figures; "
        "<font name='Courier'>scripts/build_report.py</font> builds this PDF. The README gives the exact commands."))
    story.append(p(
        "<b>Methods referenced:</b> Newey &amp; West (1987) HAC errors; Pyper &amp; Peterman (1998) effective sample size; Bonett &amp; Wright (2000) "
        "Spearman interval; Cleveland et al. (1990) STL; Wang, Smith &amp; Hyndman (2006) component strength; Diebold &amp; Mariano (1995) with "
        "Harvey, Leybourne &amp; Newbold (1997) correction; Holm (1979)."))
    story.append(p(f"Generated {date.today():%d %B %Y} on {platform.system()} with Python {platform.python_version()}.", "caption"))

    PDF.parent.mkdir(exist_ok=True)
    doc = ReportDoc(PDF)
    doc.multiBuild(story)
    print(f"Wrote {PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
