# Week 2: Feature Engineering & Data Preprocessing for Machine Learning

**AnalystLab Africa Experience Lab, Data Science Track**
**Author:** Molemi Molokoane · **Dataset:** [Heart Failure Prediction](https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction) (fedesoriano, Kaggle, ODbL)

This project turns 918 raw patient records into a clean, encoded, scaled, machine-learning-ready dataset for predicting heart disease, and documents every preprocessing decision. Every step that learns from the data (imputation, outlier fences, encoders, scaler, feature selection) is fitted on the training set only, so there is no data leakage.

## Key findings

| | Finding |
|---|---|
| 🩺 | **172 cholesterol values (19%) were hidden as 0.** Those patients have an **88% heart-disease rate vs 48%**, so the gaps were imputed *and* kept as a `cholesterol_missing` flag |
| 📈 | Strongest predictors: **flat ST slope** (83% disease vs 20% for upward), **asymptomatic chest pain** (79%), **exercise angina** (85% vs 35%), ST depression and low max heart rate |
| ✂️ | Outliers are clinically plausible, so they were **capped at the IQR fences** instead of deleted: every patient kept |
| 🔁 | Two engineered features were **redundant** with their source columns (r = 0.95, 0.94) and were removed; **resting ECG** carried almost no signal and was dropped |
| ✅ | **19 → 14 features with no loss of signal:** baseline logistic regression ROC AUC 0.930 → 0.930 (5-fold CV) |

## Pipeline

1. **Inspection:** shape, types, missing values (including hidden zeros), duplicates, summary statistics
2. **Cleaning:** descriptive column names, zeros → NaN with a missing flag, duplicate check, type and range validation
3. **Feature engineering:** `cholesterol_missing`, `hr_pct_of_predicted`, `has_st_depression`, `age_group`
4. **Stratified 80/20 train/test split** (734 / 184)
5. **Imputation:** training-set median per sex
6. **Outliers:** detected with boxplots, IQR and Z-score; capped at the IQR fences
7. **Encoding:** label (binary), ordinal (`age_group`), one-hot with a clinically "normal" reference level (nominal)
8. **Scaling:** RobustScaler on continuous features, chosen after comparing Standard, MinMax and Robust scalers
9. **Feature selection:** correlation heatmap, mutual information, random-forest importance, two pre-stated drop rules

## Project structure

```
Week2_DataScience_Project/
├── Week2_Feature_Engineering.ipynb   # full workflow, executed, with outputs
├── Data/
│   ├── heart.csv                     # original Kaggle dataset
│   ├── heart_cleaned.csv             # cleaned, imputed, capped, engineered (human-readable)
│   ├── heart_ml_ready_train.csv      # 734 rows, 14 encoded + scaled features + target
│   ├── heart_ml_ready_test.csv       # 184 rows, transformed with training-set statistics
│   └── heart_ml_ready.csv            # both parts with a split column
├── Visualizations/                   # 10 charts from the notebook (PNG)
├── Reports/
│   ├── Business_Understanding_Report.docx / .pdf
│   └── Data_Preprocessing_Report.docx / .pdf
├── scripts/                          # rebuild the Word reports from the charts (Node.js)
├── requirements.txt
└── README.md
```

### Visualizations

| # | Chart | # | Chart |
|---|---|---|---|
| 1 | Target distribution (count plot) | 6 | Cholesterol before/after imputation |
| 2 | Continuous features by diagnosis (histograms) | 7 | Outlier boxplots before/after capping |
| 3 | Categorical features by diagnosis (count plots) | 8 | Scaler comparison |
| 4 | Age vs max heart rate (scatter plot) | 9 | Correlation heatmap |
| 5 | Engineered features vs diagnosis | 10 | Feature importance (MI and random forest) |

## How to run

**Google Colab (how this notebook was run):** File → Upload notebook → `Week2_Feature_Engineering.ipynb` → Runtime → Run all. The dataset is read from this repository on GitHub, and the last cell downloads the generated CSVs and charts as a zip.

**Locally:**

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r Week2_DataScience_Project/requirements.txt
cd Week2_DataScience_Project
jupyter notebook Week2_Feature_Engineering.ipynb
```

**Rebuild the reports** (needs Node.js; PDF export needs Microsoft Word on Windows):

```bash
cd Week2_DataScience_Project/scripts
npm install
npm run build
powershell -File export_pdf.ps1
```
