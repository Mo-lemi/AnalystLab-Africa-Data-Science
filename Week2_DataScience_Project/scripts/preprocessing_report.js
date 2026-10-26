// Data Preprocessing Report (Reports/Data_Preprocessing_Report.docx).
// Run from this folder: npm install, then npm run build. Charts are read from ../Visualizations,
// so run the notebook first.
const path = require("path");
const { p, h1, h2, bullet, numbered, table, image, caption, titleBlock, build } = require("./common");

const out = path.join(__dirname, "..", "Reports", "Data_Preprocessing_Report.docx");
const viz = (name) => path.join(__dirname, "..", "Visualizations", `${name}.png`);

const children = [
  ...titleBlock("Data Preprocessing Report", "From raw patient records to a machine-learning-ready dataset"),

  h1("1. Summary"),
  p("This report documents every step taken to prepare the Heart Failure Prediction dataset (918 patients, 11 clinical features) for a model that predicts heart disease. The full code and outputs are in Week2_Feature_Engineering.ipynb."),
  table([
    ["Raw data", "Final ML-ready data"],
    ["918 rows, 12 columns, 5 text columns", "918 rows (734 train / 184 test), 14 numeric features + target"],
    ["172 cholesterol and 1 blood-pressure values hidden as 0", "No missing values; missingness kept as a flag"],
    ["Outliers in blood pressure, cholesterol and ST depression", "Capped at the IQR fences, no patients removed"],
    ["Features on scales from −2 to 600", "Continuous features robust-scaled (median 0, IQR 1)"],
  ], [0.5, 0.5]),
  p(""),
  p("**Key principle: no data leakage.** The data was split into training and test sets before any step that learns from the data. Imputation medians, outlier fences, encoders and the scaler were all fitted on the training set only and then applied unchanged to the test set, so test results will reflect performance on genuinely unseen patients."),

  h1("2. Business problem"),
  p("Heart disease is the world's leading cause of death, and early identification of high-risk patients saves lives and specialist time. The goal is a dataset from which a model can flag likely heart-disease patients (target heart_disease: 1 = disease, 0 = normal) using routine measurements. Because a missed diagnosis is far more costly than an extra test, preprocessing aimed to preserve every patient and every warning signal. The Business Understanding Report covers this in detail."),

  h1("3. Data inspection: key observations"),
  bullet("**Structure:** 918 rows × 12 columns: 6 numeric (one of them, FastingBS, a 0/1 flag), 5 text categories and the binary target. Data types were correct on load."),
  bullet("**Missing values:** no NaNs, but 172 patients (18.7%) have Cholesterol = 0 and one has RestingBP = 0, which is physically impossible. **88.4% of the patients with missing cholesterol have heart disease, against 47.7% of the rest**, so the missingness itself is informative."),
  bullet("**Duplicates:** none."),
  bullet("**Target balance:** 55.3% heart disease, 44.7% normal: mildly imbalanced, so stratified splitting is sufficient."),
  bullet("**Strongest raw signals:** a flat ST slope (83% disease vs 20% for an upward slope), asymptomatic chest pain (79%), exercise-induced angina (85% vs 35%) and male sex (63% vs 26%). Resting ECG separates the classes only weakly (52% to 66%)."),
  image(viz("02_numeric_histograms")),
  caption("Figure 1. Continuous features by diagnosis. Note the spike of impossible zeros in Cholesterol."),

  h1("4. Data cleaning"),
  table([
    ["Step", "Decision", "Justification"],
    ["Rename columns", "e.g. Oldpeak → st_depression, FastingBS → fasting_blood_sugar", "Descriptive snake_case names make the dataset self-explanatory"],
    ["Hidden missing values", "Cholesterol and RestingBP zeros → NaN; flag cholesterol_missing created first", "A value of 0 is impossible; the flag keeps the strong signal carried by missingness"],
    ["Duplicates", "Checked and removed: 0 found", "The check stays in the pipeline for future data"],
    ["Data types", "Text → category; flags → 0/1 integers", "Documents meaning and reduces memory use"],
    ["Range validation", "All values within clinical limits; 13 negative st_depression values kept", "Negative ST depression means ST elevation, a real clinical finding"],
  ], [0.2, 0.42, 0.38]),

  h1("5. Feature engineering"),
  table([
    ["New feature", "Definition", "Outcome"],
    ["cholesterol_missing", "1 if cholesterol was not recorded", "Kept: r = 0.32 with the target, more signal than cholesterol itself"],
    ["hr_pct_of_predicted", "max heart rate ÷ (220 − age)", "Removed in selection: r = 0.95 with max_heart_rate"],
    ["has_st_depression", "1 if st_depression > 0", "Kept: 70% vs 35% disease rate; r = 0.76 with st_depression, below the 0.8 cutoff"],
    ["age_group", "<45, 45–54, 55–64, 65+", "Removed in selection: r = 0.94 with age"],
  ], [0.24, 0.33, 0.43]),
  p(""),
  p("The dataset has no identifier, name or date columns, so no feature was removed purely as irrelevant; removals were decided with evidence during feature selection (section 10)."),
  image(viz("05_engineered_features")),
  caption("Figure 2. Engineered features against the diagnosis."),

  h1("6. Train/test split"),
  p("A stratified 80/20 split (random_state = 42) gave 734 training and 184 test patients, both with 55.3%/55.4% heart disease. Splitting first prevents information about test patients from leaking into the preprocessing statistics."),

  h1("7. Missing-value imputation"),
  p("Missing resting_bp and cholesterol values were filled with the **training-set median for the patient's sex** (cholesterol: 250 for women, 235 for men; resting_bp: 130 for both)."),
  bullet("**Dropping rows was rejected:** it would lose 19% of the data, mostly heart-disease patients, biasing the sample."),
  bullet("**The mean was rejected:** cholesterol is right-skewed, so the median is more representative."),
  bullet("**Per-sex medians** reflect that cholesterol levels differ between men and women."),
  image(viz("06_cholesterol_imputation"), 560),
  caption("Figure 3. Cholesterol before and after imputation (training set)."),

  h1("8. Outlier detection and treatment"),
  p("Outliers were detected on the training set with boxplots, the IQR rule (outside Q1 − 1.5×IQR or Q3 + 1.5×IQR) and Z-scores (|z| > 3). The IQR rule flagged 20 resting_bp, 33 cholesterol, 13 st_depression, 2 max_heart_rate and 2 hr_pct_of_predicted values; the Z-score flagged fewer (6, 10, 6, 0 and 1), because it assumes a normal distribution and its own mean and standard deviation are inflated by the outliers."),
  p("**Treatment: capping (winsorising) at the training-set IQR fences.** The values are clinically plausible (a cholesterol of 500 mg/dl does occur), so deleting those patients would discard real, often high-risk, cases. Capping keeps every patient while stopping extreme values from dominating distance- and gradient-based models. The IQR rule was preferred to the Z-score because several features are skewed."),
  image(viz("07_outlier_boxplots")),
  caption("Figure 4. Boxplots before (top) and after (bottom) capping."),

  h1("9. Encoding and scaling"),
  h2("9.1 Encoding"),
  table([
    ["Variable", "Technique", "Why"],
    ["sex, exercise_angina", "Label encoding (0/1)", "Binary: a single 0/1 column loses nothing and implies no false order"],
    ["age_group", "Ordinal encoding (0–3)", "The age bands have a natural order"],
    ["chest_pain_type, resting_ecg, st_slope", "One-hot encoding, dropping one reference level", "Nominal categories: label codes would invent an order. ST slope risk is not monotonic (Flat 83%, Down 78%, Up 20%)"],
  ], [0.28, 0.27, 0.45]),
  p(""),
  p("The reference levels are the clinically normal or lowest-risk categories (ATA chest pain, Normal ECG, Up slope). Dropping one level per feature avoids the dummy-variable trap (perfect multicollinearity in linear models), and choosing these levels means each remaining column reads as “risk relative to normal”."),
  h2("9.2 Scaling"),
  p("StandardScaler, MinMaxScaler and RobustScaler were compared. **RobustScaler** was chosen for the six continuous features because it uses the median and IQR, which are not distorted by the remaining skew (st_depression) or by the cluster of imputed cholesterol values at the median. MinMaxScaler was rejected because it depends on the single most extreme values. The 0/1 columns were not scaled, to keep them interpretable. The scaler was fitted on the training set only."),
  image(viz("08_scaler_comparison")),
  caption("Figure 5. The three scalers change the axis, not the shape of the distribution."),

  h1("10. Feature selection"),
  p("Three methods were combined on the training set: a correlation heatmap, mutual information and random-forest importance. Two rules were fixed **before** looking at the results:"),
  numbered("**Redundancy:** for any pair of features correlated above |0.8|, remove the one with lower mutual information."),
  numbered("**Low relevance:** remove a feature only if both methods rate it as uninformative (mutual information < 0.01 and random-forest importance < 0.02)."),
  image(viz("09_correlation_heatmap"), 560),
  caption("Figure 6. Correlation heatmap of the encoded features and the target (training set)."),
  image(viz("10_feature_importance")),
  caption("Figure 7. Mutual information and random-forest importance."),
  table([
    ["Removed feature", "Reason"],
    ["hr_pct_of_predicted", "Redundant with max_heart_rate (r = 0.95), lower mutual information (0.059 vs 0.081)"],
    ["age_group", "Redundant with age (r = 0.94), lower mutual information"],
    ["resting_ecg_LVH, resting_ecg_ST", "Both methods near zero, so resting ECG is removed entirely"],
    ["chest_pain_type_TA", "Both methods near zero (only 46 patients); grouped with the ATA reference level"],
  ], [0.35, 0.65]),
  p(""),
  p("**Most important features:** st_slope_Flat, chest_pain_type_ASY, exercise_angina, st_depression and max_heart_rate, which rank in the top six for both methods. Two engineered features did not beat the raw columns they were derived from, and the rule was applied as written rather than adjusted after seeing the result. Cholesterol was kept although its linear correlation is only 0.06, because its mutual information ranks 6th, which points to a non-linear relationship."),
  p("**Validation:** a 5-fold cross-validated logistic regression scored ROC AUC **0.930** with all 19 features and **0.930** with the 14 selected ones, so the selection removed 5 columns without any loss of predictive power."),

  h1("11. Final dataset and readiness"),
  table([
    ["File", "Contents"],
    ["Data/heart.csv", "Original Kaggle dataset, unchanged"],
    ["Data/heart_cleaned.csv", "Cleaned, imputed, capped, with engineered features; human-readable, with a split column"],
    ["Data/heart_ml_ready_train.csv", "734 rows: 14 encoded, scaled features + heart_disease"],
    ["Data/heart_ml_ready_test.csv", "184 rows, same columns, transformed with training-set statistics"],
    ["Data/heart_ml_ready.csv", "Both parts combined, with a split column"],
  ], [0.38, 0.62]),
  p(""),
  p("Final features: age, sex, resting_bp, cholesterol, fasting_blood_sugar, max_heart_rate, exercise_angina, st_depression, cholesterol_missing, has_st_depression, chest_pain_type_ASY, chest_pain_type_NAP, st_slope_Down, st_slope_Flat."),
  p("**Is the dataset ready for machine learning? Yes.** It has no missing values, only numeric features on comparable scales, no redundant features, a stratified split with an identical class balance, and every learned transformation fitted on training data alone. All automated readiness checks in the notebook pass."),
  h2("Limitations and recommendations"),
  bullet("The data pools five hospitals with different recording practices (one did not record cholesterol). A model should be validated on local patient data before use."),
  bullet("79% of the patients are male, so model performance should be checked separately for women."),
  bullet("Because missed diagnoses are costly, the modelling stage should prioritise recall and ROC AUC over plain accuracy."),
];

build(children, out, "Data Preprocessing Report · Heart Disease Prediction");
