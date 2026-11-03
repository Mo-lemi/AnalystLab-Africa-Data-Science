# Week 3: Healthcare Operations, Statistical Investigation & Insight Discovery

**AnalystLab Africa Experience Lab, Data Science Track (Track B)**
**Author:** Molemi Molokoane · **Data:** healthcare dataset pack supplied by AnalystLab Africa (Massachusetts General Hospital, January 2011 to February 2022; appears to be synthetic, Synthea-style)

**Research question:** *How do recorded total claim costs vary across encounter classes, and is encounter duration associated with cost?*

The analysis covers 27,891 encounters for 974 patients. Because a handful of patients generate a large share of encounters, every hypothesis is tested both per encounter and per patient, with confidence intervals from a bootstrap that resamples patients. The key figures are then reconciled against an independent, pandas-free recalculation.

## Key findings

| | Finding |
|---|---|
| 💲 | **Claim costs are extremely skewed:** mean $3,640 vs median $279, largest claim $641,883. Averages misrepresent typical cost |
| 🏥 | **Encounter class has a large effect on cost** (Kruskal-Wallis on patient-level values, H = 363, p ≈ 3 × 10⁻⁷⁶, ε² = 0.15). Emergency, wellness and inpatient claims are reliably higher than ambulatory, outpatient and urgent care claims |
| 🔧 | **Procedures drive the high claims:** urgent care median $22,598 with a procedure vs $143 without; urgent care is 13% of encounters but 23% of claim value |
| 🔁 | **A few patients dominate volume:** 5% of emergency patients make 62% of emergency visits, so the typical ER *visit* costs $146 while the typical ER *patient's* claim is $2,758 |
| ⏱️ | **Duration is a weak cost signal:** Spearman ρ = 0.48 in ambulatory care (0.53 within the same encounter type), mostly explained by encounter type in outpatient care, and not established for emergency. Recorded durations are mostly fixed templates |
| ✅ | **Validated:** 29 of 29 key figures match an independent standard-library recalculation, which also caught and fixed two real tolerance errors |

## Project structure

```
Week3_DataScience_Project/
├── Week3_Healthcare_Statistical_Investigation.ipynb   # full analysis, executed in Colab, with outputs
├── Data/                        # raw dataset pack: NOT in the repository (contains patient names/addresses)
├── Outputs/                     # aggregate result tables (no patient-level data)
│   ├── data_quality_summary.csv
│   ├── class_cost_summary.csv
│   ├── frequent_user_effect.csv
│   ├── h1_class_medians_ci.csv
│   ├── h1_pairwise_tests.csv
│   ├── h2_duration_cost_correlations.csv
│   └── key_figures.csv          # figures checked by the independent reconciliation
├── Visualizations/              # 12 charts from the notebook (PNG)
├── Reports/
│   └── Week3_Statistical_Analysis_Report.docx / .pdf
├── validation/
│   ├── independent_check.py     # pandas-free recalculation of the key figures
│   └── privacy_check.py         # scans published files for patient IDs, names and addresses
├── scripts/                     # rebuild the Word report from the charts (Node.js)
├── requirements.txt
└── README.md
```

### Notebook sections

1. Business understanding and success criteria
2. Data inspection: structure, missing values, dictionary vs CSV, privacy, duplicates, table relationships
3. Data preparation: dates and durations, implausible durations, cost composition, zero claims, confounders, data-quality summary
4. Exploratory data analysis (9 charts)
5. Hypothesis 1: Kruskal-Wallis, bootstrap confidence intervals, pairwise tests, frequent-user effect
6. Hypothesis 2: within-class Spearman correlations with an encounter-type confounding check
7. Validation: sanity tests, encounter vs patient agreement, key-figure export, privacy check
8. Limitations
9. Findings and recommendations

### Visualizations

| # | Chart | # | Chart |
|---|---|---|---|
| 1 | Encounters by class | 7 | Claim cost with and without procedures |
| 2 | Claim cost distribution | 8 | Payer mix by class |
| 3 | Claim cost by class | 9 | Encounters per year |
| 4 | Encounters per patient | 10 | H1: class medians with bootstrap CIs |
| 5 | Duration by class | 11 | H1: pairwise probability of superiority |
| 6 | Duration vs claim cost | 12 | H2: duration–cost correlations |

## How to reproduce

The raw data pack is **not** in this repository because `patients.csv` contains names and addresses. Get the six CSV files from the AnalystLab Africa Week 3 dataset pack: `encounters.csv`, `procedures.csv`, `patients.csv`, `payers.csv`, `organizations.csv` and `data_dictionary.csv`.

**Google Colab (how the submitted notebook was run):**
1. Open [colab.research.google.com](https://colab.research.google.com) → File → Upload notebook → `Week3_Healthcare_Statistical_Investigation.ipynb`.
2. Runtime → Run all.
3. When the upload dialog appears, select the six CSV files.
4. The last cell downloads `week3_outputs.zip` containing the `Visualizations` and `Outputs` folders.

A full run takes about two minutes; the bootstrap cells take the longest. The random seed is fixed (`RANDOM_STATE = 42`), so every run gives identical results.

**Locally:**

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r Week3_DataScience_Project/requirements.txt
# copy the six CSV files into Week3_DataScience_Project/Data/
cd Week3_DataScience_Project
jupyter notebook Week3_Healthcare_Statistical_Investigation.ipynb
```

**Independent reconciliation** (needs only Python 3, no packages; run after the notebook so `Outputs/key_figures.csv` exists):

```bash
cd Week3_DataScience_Project
python validation/independent_check.py
```

It prints PASS or FAIL for each of the 29 figures and exits with status 1 if any fail. Result for the submitted run: **29 passed, 0 failed**.

**Privacy check before publishing** (also standard library only; needs `Data/patients.csv`):

```bash
cd Week3_DataScience_Project
python validation/privacy_check.py
```

It checks the notebook, README, result tables and report source against every patient ID, name, maiden name and address in the raw data, printing only counts, never the values. Result for the submitted files: **0 found**.

**Rebuild the report** (needs Node.js; the PDF export needs Microsoft Word on Windows):

```bash
cd Week3_DataScience_Project/scripts
npm install
npm run build
powershell -File export_pdf.ps1
```

## Responsible data handling

- Identifying patient columns (names, addresses, birthplace, coordinates and others) are dropped as soon as the data is loaded, and are never displayed, charted or exported.
- The raw data pack is excluded from git (`.gitignore`).
- An automated check at the end of the notebook confirms that no exported file contains an identifying column or a patient ID, and `validation/privacy_check.py` scans everything that is published, including the notebook itself.
- No clinical claims are made. Recommendations are operational and based on recorded claim amounts, which are not the hospital's actual cost of care.

## Attribution

- **Data:** healthcare dataset pack and data dictionary supplied by AnalystLab Africa. Field descriptions match the documentation of [Synthea](https://github.com/synthetichealth/synthea) (MITRE), an open-source synthetic patient generator.
- **Tools:** Python, pandas, NumPy, SciPy, Matplotlib, seaborn; the report is generated with [docx](https://www.npmjs.com/package/docx) for Node.js.
