# Week 5: Statistical and Time-Series Analysis of Electricity Consumption in Morocco

**AnalystLab Africa Experience Lab, Data Science Track (Track 2)**
**Author:** Molemi Molokoane · **Data:** 52,416 electricity load readings taken every 10 minutes for three consumption zones in Morocco, 1 January to 30 December 2017, with weather readings, supplied by AnalystLab Africa

**Research question:** *How does electricity load in the three zones vary by hour, day of week and month, how strongly is it associated with temperature, humidity and wind speed once the shared daily and seasonal cycles are accounted for, and which differences between the zones are statistically supported?*

> The load readings are treated as **average load in kW** for each 10-minute interval, not as energy per interval (see [Data interpretation](#data-interpretation)). All relationships with weather are **associations**, not causes.

## Key findings

| | Finding |
|---|---|
| 🕗 | **The time of day is the strongest driver of load.** Every zone bottoms out at 06:00 to 07:00 and peaks at **20:00**. The daily cycle accounts for 84% of the variation in Zone 1's hourly load and 70% in Zone 2's (MSTL seasonal strength ≥ 0.97) |
| ⚡ | **Zone 1 is the largest zone; Zone 3 is the most volatile.** Zone 1 averages 32.3 MW (45% of the total) and is the highest zone on all 364 days. Zone 3 averages 17.8 MW, but its CV of 0.37 is 1.5 to 1.7 times the others' and its load factor is only 0.38 |
| ☀️ | **Summer is the peak season.** All zones peak in July or August. Zone 3's July load is 58% above its annual average and 2.6 times its December load |
| 🌡️ | **Temperature matters mainly through the season.** Above a daily mean of about 20 °C, total load rises about 2.6 MW per °C. With month, Ramadan and holidays controlled (OLS with HAC errors), the effect disappears in Zones 1 and 2 but remains in **Zone 3 (+100 kW per °C, p < 0.001)**. Humidity and wind show no association that survives the seasonal controls |
| 🌙 | **Ramadan reshapes the day.** Night-time load (01:00 to 03:59) was 45% higher during Ramadan than in the three weeks before. Public holidays are among the most unusual days (80% flagged, against 23% of other days) |
| 🔀 | **The zones changed composition after the summer.** At the same mild temperatures, autumn load was 34% lower than spring in Zone 3 and 26% higher in Zone 2. Together with a visible load transfer on 20 April, this points to load being moved between zones, not to weather |
| ✅ | **Validated:** 88 of 88 key figures match an independent standard-library recalculation; 24 unit tests pass; conclusions hold with spike readings removed, without Ramadan, without holidays and with median aggregation |

## Project structure

```
Week5_DataScience_Project/
├── Week5_Electricity_Time_Series_Analysis.ipynb   # full analysis, executed, with outputs
├── power_prep.py                # loading, cleaning rules, aggregation, statistics helpers (imported by the notebook)
├── charts.py                    # shared Plotly/Matplotlib style; saves each chart as PNG + interactive HTML
├── tests/
│   └── test_power_prep.py       # 24 unit tests
├── Data/
│   ├── powerconsumption.csv                     # raw data, never modified (SHA-256 checked)
│   ├── powerconsumption_datadictionary.csv
│   └── Cleaned/power_clean_10min.csv            # NOT in the repository (~9 MB); rebuilt by the notebook
├── Outputs/                     # result tables (CSV)
│   ├── data_dictionary_review.csv, data_quality_summary.csv
│   ├── hourly_consumption.csv, daily_consumption.csv          # aggregated datasets
│   ├── descriptive_stats_10min/hourly/daily.csv
│   ├── hourly_profile.csv, weekday_profile.csv, weekday_tests.csv, monthly_profile.csv, monthly_tests.csv
│   ├── ramadan_profile.csv, decomposition_strength.csv, stationarity_tests.csv, daily_anomalies.csv
│   ├── correlations.csv, correlations_within_month.csv, hinge_models.csv, regression_hac.csv, wind_state_effect.csv
│   ├── zone_mean_comparison.csv, zone_variability.csv, zone_profile_shape.csv, autumn_level_shift.csv
│   ├── robustness_checks.csv
│   └── key_figures.csv          # figures checked by the independent reconciliation
├── Visualizations/              # 23 charts (PNG)
│   └── interactive/             # the same Plotly charts as interactive HTML (hover for values)
├── Reports/
│   └── Week5_Electricity_Data_Science_Report.pdf
├── validation/
│   └── independent_check.py     # standard-library-only recalculation of the key figures
├── scripts/
│   └── build_report.py          # builds the PDF report from Outputs/ and Visualizations/
├── requirements.txt
└── README.md
```

### Notebook sections

1. Data dictionary review and interpretation rules (load unit, diffuse flows, wind)
2. Data inspection (Task 1): structure, types, missing values, duplicates, interval regularity, unusual values
3. Data preparation and aggregation: time features, calendar flags, hourly and daily series, and why
4. Statistical summary (Task 2): mean, median, min, max, SD, variance, quartiles, IQR, CV, skewness, kurtosis, load factor
5. Time-series analysis (Task 3): hourly, daily/weekly and monthly patterns, Ramadan and holidays, MSTL and STL decomposition, ACF/PACF, ADF/KPSS
6. Environmental statistical analysis (Task 4): choice of correlation method, correlations with effective sample sizes, change-point model, confounding checks (within-month correlation, HAC regression, wind within month and hour)
7. Comparative zone analysis (Task 5): level, variability, hourly and monthly shape, the autumn level shift
8. Validation: robustness reruns, independent recalculation, unit tests, raw-file hash
9. Limitations
10. Findings, recommendations, the brief's questions answered, contribution to the other tracks

### Visualizations

| # | Chart | # | Chart |
|---|---|---|---|
| 01 | Diffuse-flow fields by hour | 12 | MSTL decomposition (one per zone) |
| 02 | Wind speed distribution | 13 | Trend and daily cycle compared |
| 03 | Load transfer on 20 April | 14 | ACF and PACF |
| 04 | Load distribution by zone | 15 | Correlation forest plot |
| 05 | Q-Q plots | 16 | Temperature vs load with change-point model |
| 06 | Daily load trend | 17 | Humidity and wind vs load |
| 07 | Hourly profile by zone | 18 | Temperature effect as controls are added |
| 08 | Weekday × hour heatmap | 19 | Average load by zone |
| 09 | Day of week by zone | 20 | Zone shape comparison (hour and month) |
| 10 | Monthly load by zone | 21 | Autumn level shift |
| 11 | Ramadan hourly profile | | |

Charts 01 to 04, 06 to 13 and 15 to 21 are made with **Plotly** and are also saved as interactive HTML in `Visualizations/interactive/`. The ACF/PACF and Q-Q plots use statsmodels and SciPy with Matplotlib. The three zones always have the same colours (blue, orange and aqua), which are distinguishable with common colour-vision deficiencies.

## Method

| Task | Method | Why |
|---|---|---|
| Aggregation | **Hourly means** for time-series work, **daily means** for day, month, weather and zone tests, 10-minute readings for descriptive statistics | Hourly keeps the daily cycle and removes switching noise; daily takes the daily cycle out of weather and zone comparisons. Readings are averages, so they are averaged, never summed |
| Decomposition | **MSTL** (statsmodels) with 24 h and 168 h periods; STL on daily data; seasonal and trend strength | Two seasonal cycles; one year cannot separate the annual cycle from trend, so "trend" is the 2017 seasonal level |
| Day/month effects | Friedman test with weeks as blocks (Kendall's W); Kruskal-Wallis (ε²) | Rank-based; paired by week; effect sizes carry the conclusion |
| Correlation | **Spearman** (Pearson for comparison) with p-values and intervals based on an **effective sample size**; Holm correction | Wind is two-state, temperature acts non-linearly, Zone 3 is skewed; serial correlation makes naive p-values meaningless (n_eff is 21 to 271 out of 8,736 hours) |
| Non-linearity | Change-point (degree-day) model, 14-day block bootstrap | Load responds only above a base temperature |
| Confounding | Within-month correlation; **OLS with HAC (Newey-West) errors** adding hour, weekday, month, Ramadan, holiday and irradiance; wind compared within month and hour | Weather, Ramadan, holidays and tourism share the seasonal cycle |
| Zone comparison | Friedman and Wilcoxon signed-rank (Holm, rank-biserial) on paired days; 7-day **block-bootstrap** intervals | Same timestamps across zones; keeps week-to-week dependence |

## Data interpretation

The brief asked for the dictionary to be checked carefully. The decisions, with evidence, are in notebook Section 1 and `Outputs/data_dictionary_review.csv`:

- **Load (`PowerConsumption_Zone1-3`)**: the dictionary says "kWh". Read as kWh per 10 minutes, the city would use about 3.7 TWh a year, about 10 MWh per resident, which is not plausible. The values are treated as **average load in kW**. They are averaged when aggregated, and energy is only derived as mean kW × hours (622 GWh over 364 days for all three zones). Patterns, rankings and correlations do not depend on this choice.
- **`GeneralDiffuseFlows` / `DiffuseFlows`**: the dictionary says "emission gases". Both fields are zero at night and follow the sun, so they are **solar-radiation readings**. `DiffuseFlows` does not behave exactly like diffuse irradiance (it peaks at 16:00 and sometimes exceeds the general value), so neither field is interpreted physically. `GeneralDiffuseFlows` is used only as a daylight control.
- **`WindSpeed`**: 99.7% of values are about 0.08 or about 4.9, two states rather than a continuous speed. It is analysed both as recorded and as a high/low state.
- **`Humidity`** is relative humidity (%). **31 December is not in the file** (364 days).

## How to reproduce

The raw data is in the repository. Use Python 3.12 or later (tested with 3.14) and the pinned versions in `requirements.txt`. Static chart export uses kaleido, which needs Google Chrome or Chromium. If neither is installed, run `plotly_get_chrome` once after installing the requirements.

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r Week5_DataScience_Project/requirements.txt
cd Week5_DataScience_Project
python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 Week5_Electricity_Time_Series_Analysis.ipynb
```

A full run takes about 7 minutes; most of the time goes on the 12 HAC regressions and the bootstrap. It rebuilds `Data/Cleaned/power_clean_10min.csv`, every table in `Outputs/` and every chart. Random seeds are fixed, so repeated runs give identical results. The run stops with an error if any validation check fails: the raw-file hash, complete hours and days, the independent recalculation or the unit tests.

**Build the PDF report** (after the notebook):

```bash
cd Week5_DataScience_Project
python scripts/build_report.py
```

**Unit tests:**

```bash
cd Week5_DataScience_Project
python -m pytest
```

Result: **24 passed**.

**Independent reconciliation** (needs only Python 3, no packages; run after the notebook so `Outputs/key_figures.csv` exists):

```bash
cd Week5_DataScience_Project
python validation/independent_check.py
```

It reads the raw CSV with the `csv` module, without pandas, NumPy or SciPy. It recomputes 88 figures: descriptive statistics, peak hours, monthly and Ramadan values, 18 correlations, the Friedman statistic, zone shares and the autumn level shift. It prints PASS or FAIL for each and exits with status 1 if any fail. Result for the submitted run: **88 passed, 0 failed**.

## Libraries

| Library | Used for |
|---|---|
| pandas, NumPy | Loading, cleaning, aggregation, descriptive statistics |
| SciPy | Spearman/Pearson correlation, Friedman, Kruskal-Wallis, Wilcoxon, Mann-Whitney, Brown-Forsythe, skewness and kurtosis, normality tests |
| statsmodels | MSTL and STL decomposition, ACF/PACF, ADF and KPSS tests, OLS with HAC standard errors, LOWESS |
| Plotly (+ kaleido) | Charts, saved as interactive HTML and static PNG |
| Matplotlib | ACF/PACF and Q-Q diagnostic plots |
| reportlab | PDF report |
| pytest | Unit tests |

## Assumptions

- Each load reading is the **average load (kW)** in its 10-minute interval (see above).
- Each timestamp marks the start of its interval. The time zone and daylight saving treatment are not documented and are taken as recorded.
- Ramadan 1438 ran from 27 May to 25 June 2017 in Morocco. The data confirms this: night-time load steps up on 27 May and back down on 27 June. Public holidays are Morocco's 2017 fixed and religious holidays, listed in `power_prep.py`.
- Abrupt jumps in load are kept as real network events (for example load switched between zones), not removed as errors. Section 8 shows that removing them changes nothing.
- Wind speed above 2 is the "high" state.

## Limitations

- **One year only**: seasonality cannot be separated from trend, and 2017 may not be typical.
- **Definitions** of the load unit, the diffuse-flow fields and wind speed are inferred from the data, not confirmed by the data owner.
- **Zone composition changes** during the year (load moved between zones), so zone comparisons across months partly compare different networks.
- **Serial dependence**: effective sample sizes are small, and the adjustments used are approximations.
- **Confounding**: season, Ramadan, holidays, tourism and daylight move together with temperature; occupancy, tariffs and customer mix are not observed. No finding is causal.
- No descriptions of the zones, one weather station, an undocumented time zone, and 31 December missing.

The full discussion is in notebook Section 9 and report Section 9.

## Contribution to the other Week 5 tracks

- **Data Analytics:** `Outputs/hourly_consumption.csv` and `daily_consumption.csv`, plus the hourly, weekday and monthly profiles, give consistent aggregates (average kW, never summed).
- **Machine Learning:** hourly aggregation with every hour complete; lags 1, 2 and 24 suggested by the PACF; Ramadan and holiday flags; the temperature change-point term; and a warning about Zone 3's autumn level shift for chronological train/test splits.
- **Generative AI:** `Outputs/key_figures.csv` is an independently verified answer key for numerical questions, and notebook Sections 1 and 9 list the interpretation notes and limitations an assistant should state.
- **Project Management:** the dictionary issues and the network reconfiguration risk are open items to take up with the data owner.

## Responsible data handling

- The dataset contains no personal data: it is aggregated load for three network zones and weather readings.
- The raw file is never modified. Its SHA-256 hash is checked at the start and end of every notebook run.
- Associations with weather are not presented as causes, and interpretations of what the zones contain are labelled as inferences.

## Attribution

- **Data:** supplied by AnalystLab Africa for the Week 5 assignment. It matches the public *Power Consumption of Tetouan City* dataset (UCI Machine Learning Repository; Salam, A. & El Hibaoui, A., 2018, "Comparison of machine learning algorithms for the power consumption prediction: case study of Tetouan city", *IRSEC 2018*).
- **Tools:** Python, pandas, NumPy, SciPy, statsmodels, Plotly, Matplotlib, reportlab and pytest. The statistical methods are standard (MSTL: Bandara, Hyndman & Bergmeir 2021; seasonal strength: Wang, Smith & Hyndman 2006; effective sample size: Pyper & Peterman 1998; HAC: Newey & West 1987), and no external code was copied.
