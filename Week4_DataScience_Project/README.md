# Week 4: Consumer Complaint Patterns and Response Trends

**AnalystLab Africa Experience Lab, Data Science Track**
**Author:** Molemi Molokoane · **Data:** CFPB consumer complaint records about Bank of America, 1 May 2017 to 28 August 2023 (62,516 complaints), supplied by AnalystLab Africa

**Research question:** *How have complaint volumes, products, recorded company responses and CFPB forwarding intervals changed between 2017 and 2023, and which of these differences are statistically supported?*

> A complaint is an issue *reported by a consumer*. It does not establish misconduct, and a recorded company response is not proof that a complaint was resolved satisfactorily. Every finding below describes recorded data only.

## Key findings

| | Finding |
|---|---|
| 📈 | **Complaint volume nearly doubled and has not fallen back:** about 590 a month in 2019, 1,141 in 2023. Significant rises in 2020, 2021 and 2022 (Kruskal-Wallis ε² = 0.78; Sen's slope +102 a month per year) |
| 🏦 | **Two products account for two-thirds of complaints:** checking/savings 39.7%, credit/prepaid card 25.9%. "Managing an account" alone is 24.2% |
| 🔄 | **The mix is shifting:** mortgage share fell from 23% to 4%; credit reporting, fraud or scam, getting a credit card and opening an account gained share |
| ⏱️ | **Timeliness fell sharply in 2021:** the untimely rate went from 0.7% (2020) to 11.0% (2021), 16 times higher, across every product except mortgages. It was 4.4% in 2022 and is provisionally 6.8% in 2023 |
| 💵 | **Recorded response depends on product** (Cramér's V = 0.21): monetary relief closes 33% of checking/savings complaints but 4% of credit reporting ones, reflecting the remedy each product allows |
| 📨 | **CFPB forwarding is fast (79.4% same day), and its speed depends on channel, not product:** referrals are forwarded the same day only 22–46% of the time, against 87–93% for web complaints |
| ✅ | **Validated:** 38 of 38 key figures match an independent standard-library recalculation; 22 unit tests pass; conclusions hold with look-alike rows removed, without July 2023, and for web complaints only |

## Project structure

```
Week4_DataScience_Project/
├── Week4_Consumer_Complaints_Statistical_Analysis.ipynb   # full analysis, executed, with outputs
├── complaint_prep.py            # cleaning rules, KPI functions and statistics helpers (imported by the notebook)
├── tests/
│   └── test_complaint_prep.py   # 22 unit tests
├── Data/
│   ├── Consumer_Complaints.xlsx                 # raw data, never modified (SHA-256 checked)
│   ├── ConsumerComplaints_DataDictionary.csv
│   └── Cleaned/complaints_clean.csv             # NOT in the repository (34 MB); rebuilt by the notebook
├── Outputs/                     # result tables (CSV)
│   ├── kpi_definitions.csv, cleaning_log.csv, data_quality_summary.csv
│   ├── monthly_volume.csv, annual_volume.csv, product_share.csv, issue_share.csv, ...
│   ├── hypothesis_results.csv, h1_*.csv ... h4_*.csv, robustness_checks.csv
│   └── key_figures.csv          # figures checked by the independent reconciliation
├── Visualizations/              # 17 charts (PNG)
├── Reports/
│   └── Week4_Statistical_Analysis_Report.docx / .pdf
├── validation/
│   └── independent_check.py     # standard-library-only recalculation of the key figures
├── scripts/                     # rebuild the Word report from the charts (Node.js)
├── requirements.txt
└── README.md
```

### Notebook sections

1. Business understanding: hypotheses H1 to H4, the brief's data interpretation rules, success criteria
2. Data inspection: structure, ID uniqueness, look-alike rows, missing values and their meaning, dates, reporting months, category consistency
3. Data preparation: cleaning log, validation after cleaning, KPI definitions, exports
4. Exploratory data analysis (13 charts)
5. Hypothesis tests: assumptions, effect sizes, follow-up comparisons, Holm correction
6. Validation: robustness reruns, independent recalculation, unit tests, raw-file hash
7. Limitations and alternative explanations
8. Findings, recommendations, brief questions answered, contribution to the other tracks

### Visualizations

| # | Chart | # | Chart |
|---|---|---|---|
| 1 | Monthly complaints | 10 | Response by product |
| 2 | Average monthly complaints by year | 11 | Timely-response rate by year |
| 3 | Monthly counts within each year | 12 | Forwarding interval distribution |
| 4 | Complaints by product | 13 | Forwarding interval by product |
| 5 | Top 12 issues | 14 | H1: trend with Sen's slope |
| 6 | Issue mix within each product | 15 | H2: response × product residuals |
| 7 | Product mix by year | 16 | H3: untimely residuals by year |
| 8 | Issues whose share changed most | 17 | H4: same-day forwarding by product |
| 9 | Response mix by year | | |

## Method

| Hypothesis | Test | Result |
|---|---|---|
| **H1** Monthly volume changed across years | Kruskal-Wallis on 74 full months; Mann-Kendall trend with Sen's slope; adjacent-year Mann-Whitney (Holm) | Rejected H₀; large effect |
| **H2** Recorded response depends on product | Chi-square on 61,014 closed complaints; Cramér's V; adjusted residuals | Rejected H₀; medium effect |
| **H3** Timely rate changed over time (2017–2022) | Chi-square; residuals; 2020 vs 2021 rate difference with a Newcombe interval | Rejected H₀; large in practice (untimely ×16) |
| **H4** Forwarding interval differs by product | Kruskal-Wallis with ε²; chi-square on the same-day share; repeated within channel | Rejected H₀; small, and negligible within a channel |

With about 60,000 records almost every test is significant, so conclusions rest on effect sizes. Rank-based tests are used because monthly counts are few per year and forwarding intervals are highly skewed (79% zeros).

## How to reproduce

The raw data is in the repository. Use Python 3.13 and the pinned versions in `requirements.txt`. The command below runs the whole notebook headless and saves its outputs; opening it in Jupyter or VS Code and choosing Run All gives the same result.

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r Week4_DataScience_Project/requirements.txt
cd Week4_DataScience_Project
python -m nbconvert --to notebook --execute --inplace Week4_Consumer_Complaints_Statistical_Analysis.ipynb
```

A full run takes a few minutes. It rebuilds `Data/Cleaned/complaints_clean.csv`, every chart and every table. Random seeds are fixed, so repeated runs give identical charts. The run stops with an error if any validation check fails: cleaning counts, the independent recalculation, the unit tests or the raw-file hash.

**Unit tests:**

```bash
cd Week4_DataScience_Project
python -m pytest
```

Result: **22 passed**.

**Independent reconciliation** (needs only Python 3, no packages; run after the notebook so `Outputs/key_figures.csv` exists):

```bash
cd Week4_DataScience_Project
python validation/independent_check.py
```

It reads the raw `.xlsx` as XML without pandas or openpyxl, recomputes 38 figures (including the four main test statistics), and prints PASS or FAIL for each. It exits with status 1 if any fail. Result for the submitted run: **38 passed, 0 failed**.

**Rebuild the report** (needs Node.js; the PDF export needs Microsoft Word on Windows):

```bash
cd Week4_DataScience_Project/scripts
npm install
npm run build
powershell -File export_pdf.ps1
```

## Assumptions

- `Date submitted` is when the CFPB received the complaint and `Date received` is when it sent the complaint to the company, as defined in the brief. Their difference is the **CFPB forwarding interval**, not the company's response time.
- A blank `Timely response?` is **not** a "No". All 1,494 blanks are complaints still *In progress*. They are excluded from the timely-rate denominator and reported separately.
- Blank sub-issues, sub-products and public responses are labelled according to their meaning (for example, "Not recorded" for an optional public response), not imputed.
- The 2,784 rows identical except for `Complaint ID` are kept as separate complaints, because there is no consumer identifier to prove they are duplicates. Section 6.1 shows the conclusions are the same if they are removed.
- May 2017 and August 2023 are treated as partial months, and 2017 and 2023 as partial years. Year comparisons use per-month averages or shares.
- The 2023 timely rate is provisional, because recent complaints are still in progress.

## Limitations

- Complaints are unverified consumer reports. Nothing here establishes misconduct.
- There are no customer or account counts, so complaint **rates** cannot be calculated. Growth in volume may reflect a growing customer base.
- Recorded responses are set by the company. The data has no consumer feedback, no relief amounts and no actual response times.
- Only complaints sent to the CFPB are included, for one company, with no complaint narratives.
- All results are associations from observational data, not causes. Monthly counts are serially correlated, and product and issue cannot be separated.

The full discussion, with alternative explanations for each finding, is in notebook Section 7 and report Section 7.

## Contribution to the other Week 4 tracks

- **Data Analytics (dashboard):** `Data/Cleaned/complaints_clean.csv` (rebuilt by the notebook) and `Outputs/kpi_definitions.csv` provide shared definitions for total complaints, timely rate (pending excluded), in-progress count, forwarding interval and year-over-year change.
- **Machine Learning (forecasting):** `Outputs/monthly_volume.csv` has all 76 months with no gaps and the partial first and last months identified. H1 documents the 2020 change in trend and the July 2023 outlier.
- **Generative AI (assistant):** `Outputs/key_figures.csv` is an independently verified answer key for testing numerical answers. Section 7 lists the limitations the assistant should state.
- **Project Management:** the robustness and reconciliation results are evidence for acceptance criteria and for the risks of incorrect counts, date calculations and misread responses.

## Revision log

Changes made after reviewing each stage of the analysis:

| Stage | Change |
|---|---|
| EDA review | Corrected the 2023 timeliness statement: pending complaints can still close either way, so the rate is *more likely* to fall, not certain to |
| EDA review | Fixed chart issues: the 2021 point was cut off by the axis, duplicate outlier markers, unreadable labels on light colours, cluttered 0% heatmap cells; fixed the random seed for chart 03 so reruns are identical |
| H4 review | Added a channel-stratified follow-up after finding that referrals are forwarded more slowly. This changed the H4 conclusion from "product matters a little" to "channel, not product" |
| H3 review | Reported the rate difference and ratio alongside Cramér's V, because V understates effects when the outcome is rare |
| H1 review | Added an annual-level trend test because monthly counts are serially correlated |

## Responsible data handling

- The dataset contains no consumer names, contact details or complaint narratives. `State` is the only location field, and it is not analysed at a level that could identify anyone.
- The raw file is never modified. Its SHA-256 hash is checked at the start and end of every notebook run.
- No finding is presented as evidence of misconduct, and recorded responses are not treated as proof of resolution.

## Attribution

- **Data:** consumer complaint records about Bank of America from the Consumer Financial Protection Bureau (CFPB), with a data dictionary, supplied by AnalystLab Africa for the Week 4 assignment.
- **Tools:** Python, pandas, NumPy, SciPy, Matplotlib, seaborn and pytest; the report is generated with [docx](https://www.npmjs.com/package/docx) for Node.js. The statistical methods are standard, and no external code was copied.
