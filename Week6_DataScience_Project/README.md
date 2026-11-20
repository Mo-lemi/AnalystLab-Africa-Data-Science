# Week 6: Statistical Analysis and Time-Series Investigation of S&P 500 Stock Performance, 2014–2017

**AnalystLab Africa Experience Lab, Data Science Track (Track B)**
**Author:** Molemi Molokoane · **Data:** `S&P 500 Stock Prices 2014-2017.csv`, 497,472 daily records (open, high, low, close, volume) for 505 symbols over 1,007 trading days, 2 January 2014 to 29 December 2017, supplied by AnalystLab Africa

**Research problem:** *How did return, risk and trading activity differ across six large S&P 500 stocks from six different sectors in 2014–2017, how much of their daily behaviour was shared with the rest of the market, and did their history contain any pattern (seasonal or serial) that would help estimate the next day's return?*

**Stocks studied:** AAPL (Apple), AMZN (Amazon), JPM (JPMorgan Chase), JNJ (Johnson & Johnson), XOM (Exxon Mobil) and WMT (Walmart). They come from six different sectors, and each has a complete 1,007-day history with no flagged record. The whole file is used for the market-wide questions and for an equal-weighted market average.

> **Historical data only.** Every figure describes 2014 to 2017 and is not a current market fact. Returns are **price returns**, because the file is split-adjusted but not dividend-adjusted. Nothing here is a forecast or an investment recommendation.

## Key findings

| | Finding |
|---|---|
| ⚖️ | **The stocks differ in risk, not in average daily return.** Annualised volatility runs from 14% (JNJ) to 30% (AMZN), and 14 of 15 pairs differ significantly (Brown-Forsythe p < 10⁻⁴⁰). The paired test can detect a difference in typical daily return, but it is negligible (Kendall's W = 0.003) |
| 🎲 | **Large total returns are hard to tell from luck at the daily level.** AMZN +194%, AAPL +114%, JPM +84%, JNJ +53%, WMT +25% and XOM −16%, yet no mean daily return differs from zero on the HAC t-test after Holm correction (only AMZN's rank-based test is borderline, p = 0.048). Four years can only detect mean daily returns of 0.08% to 0.16% |
| 📊 | **Volume goes with the size of moves, not their direction.** Relative volume and absolute return: Spearman ρ = 0.35 to 0.46, all p < 10⁻²⁵, and the busiest tenth of days move 3.7 to 6.3 times as much as the quietest. Relative volume and signed return: \|ρ\| < 0.07, not significant |
| 🔗 | **Weak-to-moderate co-movement that rises in sell-offs.** Pairwise ρ = 0.23 to 0.47. JPM–XOM and AAPL–AMZN are the most similar pairs, and WMT is the least connected. Correlation with the market peaked at 0.7 to 0.9 in the 2015–16 sell-off and fell to 0.1 to 0.2 for four stocks in calm 2017 |
| 🌊 | **Volatility clusters, but direction is unpredictable.** Strong ARCH effects for JPM, JNJ, XOM and the market. Returns show no significant autocorrelation, no day-of-week or month effect, and no stable seasonality (STL seasonal strength ≤ 0.11). In 2017, out of sample, no model significantly beat "tomorrow = today" |
| 🏛️ | **Market-wide:** the highest close was PCLN \$2,049 and the lowest CHK \$1.59. Among the 479 complete histories, NVDA had the highest return (+1,120%) and CHK the lowest (−85%). Riskier stocks did **not** earn more over these four years (ρ = −0.19) |
| 🧹 | **Data quality:** every check in the brief was confirmed (11/8/8 missing open/high/low, 4 zero-volume rows, 0 duplicates, 26 incomplete histories). Five further issue types were found and handled: price errors on 14 Sep 2017 and LNT's unadjusted split, inconsistent OHLC rows, gaps inside histories, unadjusted spin-offs, and survivorship bias |
| ✅ | **Validated:** 172 of 172 key figures match an independent standard-library recalculation, 26 unit tests pass, and the conclusions hold with log returns, without extreme days and in each half of the period |

## Project structure

```
Week6_DataScience_Project/
├── Week6_SP500_Statistical_Time_Series_Analysis.ipynb   # full analysis, executed, with outputs
├── stock_prep.py                # loading, cleaning and flag rules, derived fields, statistics helpers
├── charts.py                    # shared Plotly/Matplotlib style; saves each chart as PNG + interactive HTML
├── tests/
│   └── test_stock_prep.py       # 26 unit tests
├── Data/
│   ├── S&P 500 Stock Prices 2014-2017.csv      # raw data, never modified (SHA-256 checked)
│   └── Cleaned/sp500_clean.csv                  # NOT in the repository (~134 MB); rebuilt by the notebook
├── Outputs/                     # 31 result tables (CSV), including:
│   ├── data_quality_summary.csv, cleaning_log.csv, flagged_records.csv, history_coverage.csv, split_adjustment_check.csv
│   ├── descriptive_stats_closing_price.csv, descriptive_stats_daily_returns.csv, yearly_performance.csv
│   ├── h1_mean_return_tests.csv, h2_volume_return_tests.csv, h3_distribution_tests.csv, h3_pairwise_volatility.csv
│   ├── h4_autocorrelation_volatility_clustering.csv, calendar_effect_tests.csv
│   ├── stationarity_tests.csv, decomposition_strength.csv, next_day_forecast_evaluation.csv
│   ├── correlation_returns_spearman/pearson.csv, correlation_tests_returns.csv, beta_vs_market_average.csv
│   ├── correlation_tests_monthly_volatility.csv, cross_section_correlations.csv
│   ├── market_total_returns_complete_histories.csv, market_closing_price_extremes.csv
│   ├── robustness_checks.csv
│   └── key_figures.csv          # 172 figures checked by the independent reconciliation
├── Visualizations/              # 19 charts (PNG)
│   └── interactive/             # the Plotly charts as interactive HTML (hover for values)
├── Reports/
│   └── Week6_SP500_Data_Science_Report.pdf      # 20-page Data Science report
├── validation/
│   └── independent_check.py     # standard-library-only recalculation of the key figures
├── scripts/
│   └── build_report.py          # builds the PDF from Outputs/ and Visualizations/
├── requirements.txt
└── README.md
```

### Notebook sections

0. Research problem, stock selection and measurable success criteria
1. Setup and data integrity (raw-file hash)
2. Dataset inspection and preparation: structure, types, missing values, duplicates, zero volume, OHLC consistency, extreme moves and price errors, split-adjustment check, currency, incomplete histories, data-quality summary and cleaning log
3. Exploratory data analysis: price trends and moving averages, return distributions, Q-Q plots, unusual moves, volume, market-wide extremes and risk against return
4. Descriptive statistics: closing prices, daily returns, year by year
5. Hypothesis testing: H1 mean returns, H2 volume and returns, H3 distribution differences (level and spread), H4 autocorrelation and volatility clustering, calendar effects
6. Time-series analysis: stationarity, rolling volatility, STL decomposition with a seasonality check, ACF/PACF, walk-forward next-day forecasts against a no-change baseline
7. Correlation analysis: returns, beta and rolling correlation with the market, volatility co-movement, cross-section
8. Validation: robustness reruns, key figures with independent recalculation, unit tests, raw-file hash
9. Limitations
10. Findings, recommendations, the brief's questions answered, contribution to the other tracks

### Visualizations

| # | Chart | # | Chart |
|---|---|---|---|
| 01 | Growth of 100 | 11 | Volatility comparison with bootstrap intervals |
| 02 | Closing prices with 50/200-day moving averages | 12 | Rolling 63-day volatility |
| 03 | Daily return distribution | 13 | Daily returns over time |
| 04 | Q-Q plots | 14 | STL decomposition (AMZN) |
| 05 | Monthly volume | 15 | ACF and PACF |
| 06 | Top and bottom total returns (all symbols) | 16 | Next-day forecasts against the baseline |
| 07 | Risk against return (all symbols) | 17 | Return correlation heatmap |
| 08 | Yearly returns heatmap | 18 | Rolling correlation with the market |
| 09 | Mean return confidence intervals | 19 | Monthly realised volatility |
| 10 | Volume against returns by decile | | |

All charts except 04 and 15 (Matplotlib, for SciPy and statsmodels diagnostics) are made with **Plotly** and are also saved as interactive HTML. Each stock always has the same colour, from a palette checked for colour-vision deficiency. The market average is always grey. Line charts carry direct labels, and every value is also in `Outputs/`.

## Method

| Task | Method | Why |
|---|---|---|
| Returns | Simple daily % return `close_t / close_{t-1} − 1` per symbol in date order; log returns as a robustness check | The brief's definition; percentage returns make stocks comparable |
| Valid return | One-day return with no flag on either day (gaps, price errors and corporate actions excluded) | One definition used by every statistic |
| H1 mean = 0 | t-test with **HAC (Newey-West)** errors; Wilcoxon; 20-day block bootstrap; minimum detectable effect; Holm | Fat tails and volatility clustering break the plain t-test's assumptions |
| H2 volume and returns | **Spearman** between log relative volume and signed and absolute returns; **effective sample size** | Non-linear, fat-tailed; relative volume removes trends; volume is autocorrelated |
| H3 distributions | **Friedman** (days as blocks) for level; **Brown-Forsythe** and paired Wilcoxon on absolute deviations for spread | The six returns on a day are not independent; robust to fat tails |
| H4 dependence | Ljung-Box on r and r², ARCH-LM | Separates predictability of direction from predictability of volatility |
| Stationarity | ADF and KPSS together | Complementary null hypotheses |
| Decomposition | **STL** (robust) on weekly log close, 52-week period; component strength; stability across halves | The brief warns that a decomposition is not proof of seasonality |
| Predictability | Train 2014–16, test 2017; no-change, historical mean and AR(1); **Diebold-Mariano** | Chronological, no leakage, baseline first |
| Correlation | Spearman (main) and Pearson; Fisher-z intervals with effective n; rolling 126-day; beta with HAC | Robust to extreme days; shows how correlation changes over time |

## Data decisions

The details and evidence are in notebook Section 2, `Outputs/data_quality_summary.csv` and `Outputs/cleaning_log.csv`. **No row is deleted and no price is imputed or set to zero.** Suspect values are flagged, and every exclusion is a filter on a documented flag.

- **Adjustment:** nine known splits (AAPL 7-for-1 in June 2014, NFLX, V and others) show no jump, and AAPL's first close equals \$553.13 ÷ 7. Prices are therefore **split-adjusted but not dividend- or spin-off-adjusted**.
- **Price errors:** five single closes jump at least 20% and reverse the next day. Four are on 14 Sep 2017 (FLR, MPC, MRO, NWL); the fifth is LNT on 19 May 2016, a close not adjusted for its 2-for-1 split. Returns into and out of them are excluded.
- **Corporate actions:** 12 one-day falls on spin-off or distribution dates (eBay/PayPal, Baxter/Baxalta, NiSource and others) are excluded from market-wide figures. The list is external context from public announcements (`stock_prep.CORPORATE_ACTIONS`). None affects the six stocks.
- **Histories:** 479 of 505 symbols are complete. DHR, ES, O and ICE have gaps inside their histories, so 8 multi-day returns are excluded. No symbol ends early, which means **survivorship bias**.
- **Missing and zero values:** missing open/high/low stay missing and are left out of the daily range only. On 6 placeholder rows (no open/high/low and at most 100 shares), volume is treated as missing.
- **Currency:** none is given in the file. All symbols are US-listed, and the AAPL check matches its USD price, so prices are **assumed to be US dollars**.
- **Volume** is shares traded, not money.

## How to reproduce

Use Python 3.12 or later (tested with 3.14) and the pinned versions in `requirements.txt`. Static chart export uses kaleido, which needs Google Chrome or Chromium. If neither is installed, run `plotly_get_chrome` once.

```bash
# from the repository root
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r Week6_DataScience_Project/requirements.txt
cd Week6_DataScience_Project
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1800 Week6_SP500_Statistical_Time_Series_Analysis.ipynb
python scripts/build_report.py         # builds Reports/Week6_SP500_Data_Science_Report.pdf
```

A full run takes about 4 minutes. It rebuilds `Data/Cleaned/sp500_clean.csv`, every table in `Outputs/` and every chart. Random seeds are fixed. **The run stops with an error if any validation fails:** the raw-file hash (checked at the start and the end), the selected stocks' completeness, the independent recalculation or the unit tests.

**Unit tests:** `python -m pytest tests` gives **26 passed**.

**Independent reconciliation** (needs only Python 3, no packages; run after the notebook):

```bash
python validation/independent_check.py
```

It reads the raw CSV with the `csv` module and re-implements, from their definitions, the parsing, sorting, returns, the gap, price-error and corporate-action flags, descriptive statistics, skewness and kurtosis, moving averages, drawdowns, all 30 pairwise correlations, and the Friedman and Brown-Forsythe statistics. It uses no pandas, NumPy, SciPy or `stock_prep`. Result: **172 passed, 0 failed**.

## Libraries

| Library | Used for |
|---|---|
| pandas, NumPy | Loading, cleaning, per-symbol calculations, descriptive statistics |
| SciPy | t-test, Wilcoxon, Friedman, Kruskal-Wallis, Levene/Brown-Forsythe, Spearman/Pearson, Jarque-Bera, skewness and kurtosis |
| statsmodels | HAC regression, ADF and KPSS, STL, ACF/PACF, Ljung-Box, ARCH-LM, AutoReg |
| Plotly (+ kaleido) | Charts as interactive HTML and static PNG |
| Matplotlib | Q-Q and ACF/PACF diagnostic plots |
| reportlab | PDF report |
| pytest | Unit tests |

## Assumptions

- Prices are US dollars, split-adjusted and not dividend-adjusted (verified as far as the data allows).
- Annualisation uses 252 trading days. Volatility is the SD of daily returns × √252.
- The market average is the equal-weighted mean of all valid daily returns in the file. It is not the cap-weighted S&P 500 index.
- Moves that are not flagged by a rule are real moves.
- Sector labels for the six stocks are general knowledge, not from the file.

## Limitations

- **A four-year historical window** that includes an oil crash and an unusually calm 2017. It is too short to estimate mean returns precisely or to test annual seasonality.
- **Price returns only**, so total return is understated for dividend payers. Spin-offs are unadjusted.
- **Survivorship bias:** companies that left the index before 2018 are missing.
- **Judgement rules** for price errors, and an **assumed currency**.
- **Statistical approximations** for fat tails and dependence. Correlations are associations and change over time.
- **Six stocks are not a sample of the market.** The forecast test covers one year, three simple models and a one-day horizon.

The full discussion is in notebook Section 9 and report Section 9.

## Contribution to the other Week 6 tracks

- **Data Analytics:** the cleaned dataset with flags, one definition of a valid daily return, and `key_figures.csv` for checking dashboard numbers.
- **Machine Learning:** the no-change baseline and its 2017 error levels (`next_day_forecast_evaluation.csv`), evidence to model returns rather than prices, and the observation that volatility has memory while direction does not.
- **Generative AI:** `key_figures.csv` as an independently verified answer key, and the limitations as statements the assistant must make.
- **Project Management:** the data-quality findings and recommendations as inputs to the risk register and the acceptance criteria.

These are outputs offered for reuse. No other track's work was consumed.

## Responsible data handling

- The dataset contains no personal data.
- The raw file is never modified, and its SHA-256 hash is checked at the start and the end of every run.
- Historical results are not presented as current facts or as investment advice, and associations are not presented as causes.

## Attribution

- **Data:** supplied by AnalystLab Africa for the Week 6 assignment. No source documentation was supplied with the file.
- **Methods:** Newey & West (1987); Pyper & Peterman (1998); Bonett & Wright (2000); Cleveland et al. (1990, STL); Wang, Smith & Hyndman (2006); Diebold & Mariano (1995) with Harvey, Leybourne & Newbold (1997); Holm (1979). Corporate-action dates are from public company announcements. No external code was copied.
- **Tools:** Python, pandas, NumPy, SciPy, statsmodels, Plotly, Matplotlib, reportlab and pytest.
