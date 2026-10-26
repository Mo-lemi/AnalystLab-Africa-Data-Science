// Business Understanding Report (Reports/Business_Understanding_Report.docx).
// Run from this folder: npm install, then npm run build.
const { p, h1, bullet, table, titleBlock, build } = require("./common");

const out = require("path").join(__dirname, "..", "Reports", "Business_Understanding_Report.docx");

const children = [
  ...titleBlock("Business Understanding Report", "Predicting heart disease from routine clinical measurements"),

  h1("1. Business problem"),
  p("Cardiovascular disease is the leading cause of death worldwide, responsible for an estimated 17.9 million deaths a year according to the World Health Organization. Heart failure is a common outcome. Many of these deaths are preventable when high-risk patients are identified early and referred for tests and treatment."),
  p("The problem is identifying those patients. Specialist diagnosis (angiography, echocardiography, cardiologist review) is expensive and in short supply, especially in African health systems, where WHO reports the highest prevalence of hypertension of any region. Clinics already collect basic measurements such as age, blood pressure, cholesterol, blood sugar, a resting ECG and an exercise test, but there is no consistent way to turn them into a risk decision. As a result, some high-risk patients are missed and some low-risk patients take up scarce specialist time."),

  h1("2. Project objective"),
  p("The Week 2 objective is to **prepare the Heart Failure Prediction dataset for machine learning**: clean it, engineer and encode features, scale them, treat outliers and select the most useful features, documenting every decision. The resulting dataset is the foundation for a classification model, to be built in a later stage, that predicts whether a patient has heart disease."),
  p("The dataset combines 918 unique patients from five hospital studies (Cleveland, Hungary, Switzerland, Long Beach VA and Stalog) and has 11 clinical features."),

  h1("3. Target variable"),
  table([
    ["Item", "Description"],
    ["Target column", "HeartDisease (renamed heart_disease)"],
    ["Type", "Binary classification: 1 = heart disease, 0 = normal"],
    ["Class balance", "508 positive (55.3%) and 410 negative (44.7%): mildly imbalanced, handled by a stratified train/test split"],
    ["Predictors", "Age, Sex, ChestPainType, RestingBP, Cholesterol, FastingBS, RestingECG, MaxHR, ExerciseAngina, Oldpeak, ST_Slope"],
  ], [0.25, 0.75]),
  p(""),
  p("The costs of the two kinds of error are not equal. A **false negative** (a sick patient labelled healthy) can mean a missed diagnosis and a preventable death; a **false positive** costs an extra test. A model built on this data should therefore be judged on recall (sensitivity) and ROC AUC as well as accuracy."),

  h1("4. Importance of predictive modelling"),
  bullet("**Consistency:** a model applies the same evidence-based rules to every patient, regardless of clinician workload or experience."),
  bullet("**Speed and cost:** it uses measurements that are already collected, so a risk score is available instantly at no extra cost."),
  bullet("**Hidden patterns:** it combines many weak signals. For example, the preparation found that patients with no recorded cholesterol have an 88% heart-disease rate, and that silent (asymptomatic) chest pain is a stronger warning sign than typical chest pain."),
  bullet("**Prioritisation:** a ranked risk list lets clinics send the right patients to specialists first."),

  h1("5. Expected business impact"),
  table([
    ["Stakeholder", "Expected impact"],
    ["Patients", "Earlier diagnosis and treatment, and fewer emergency admissions and deaths"],
    ["Clinics and hospitals", "Better use of specialists and diagnostic equipment, and lower cost per correct diagnosis"],
    ["Health funders and insurers", "Lower long-term treatment costs through prevention rather than emergency care"],
    ["Public health", "Data-driven screening programmes in areas with few cardiologists"],
  ], [0.3, 0.7]),
  p(""),
  p("**Risks to manage:** the model is a decision-support tool, not a diagnosis; final decisions stay with clinicians. Because the data pools five hospitals with different recording practices, any model must be validated on local patient data before use, and its performance should be monitored for bias, for example across sex, since 79% of the patients are male."),
];

build(children, out, "Business Understanding Report · Heart Disease Prediction");
