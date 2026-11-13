// Statistical Analysis Report (Reports/Week4_Statistical_Analysis_Report.docx).
// Run from this folder: npm install, then npm run build. Charts are read from ../Visualizations,
// so run the notebook first. Every figure quoted here comes from the executed notebook.
const path = require("path");
const { p, h1, h2, bullet, table, image, caption, titleBlock, build } = require("./common");

const out = path.join(__dirname, "..", "Reports", "Week4_Statistical_Analysis_Report.docx");
const viz = (name) => path.join(__dirname, "..", "Visualizations", `${name}.png`);

const children = [
  ...titleBlock(
    "Statistical Analysis Report",
    "Consumer complaints about Bank of America: trends, products, recorded responses and CFPB forwarding, 2017–2023",
    "Author: Molemi Molokoane  ·  Data: CFPB complaint records supplied by AnalystLab Africa (62,516 complaints, 1 May 2017 – 28 August 2023)  ·  November 2026"),

  h1("Executive summary"),
  p("**Research question:** how have complaint volumes, products, recorded company responses and CFPB forwarding intervals changed between 2017 and 2023, and which of these differences are statistically supported? A complaint is an issue reported by a consumer. It does not establish misconduct, and a recorded response is not proof of satisfactory resolution."),
  table([
    ["Finding", "Evidence"],
    ["Complaint volume nearly doubled from 2019 to 2023 and has not fallen back", "Per month: 590 in 2019, 1,141 in 2023. Kruskal-Wallis ε² = 0.78; Sen's slope +102 per month per year"],
    ["Two products account for two-thirds of complaints", "Checking/savings 39.7%, credit/prepaid card 25.9%; “Managing an account” alone 24.2%"],
    ["The complaint mix is shifting", "Mortgage share 23% → 4%; credit reporting, fraud or scam, getting a credit card and opening an account rising"],
    ["Response timeliness fell sharply in 2021 and has not fully recovered", "Untimely rate 0.7% (2020) → 11.0% (2021) → 4.4% (2022); 2023 provisional 6.8%"],
    ["Recorded response type depends on product", "Monetary relief: 33% of checking/savings vs 4% of credit reporting; Cramér's V = 0.21"],
    ["CFPB forwarding is fast; its speed depends on channel, not product", "79.4% same day. Same-day share is 87–93% for web complaints but only 22–46% for referrals"],
  ], [0.48, 0.52]),
  p(""),
  p("**Main recommendations:** review complaint-handling capacity from Q2 2021 and monitor the untimely rate monthly; plan capacity for the current volume level, with an alert for sudden bursts; focus root-cause work on account management and the growing onboarding and fraud issues; count response targets from the date the company receives a complaint. All findings are associations in recorded data, not causal conclusions."),

  h1("1. Research question and objectives"),
  p("Bank of America's complaint and compliance teams need to know where consumers report problems, whether that is changing, and how recorded responses and timeliness have developed. This analysis answers the Data Science questions in the Week 4 brief. Its cleaned dataset, KPI definitions and verified figures are also inputs for the dashboard, forecasting and AI-assistant tracks."),
  table([
    ["", "Question", "Null hypothesis", "Test"],
    ["H1", "Did monthly volume change across years?", "Same distribution every year; no monotonic trend", "Kruskal-Wallis; Mann-Kendall with Sen's slope"],
    ["H2", "Is the recorded response associated with product?", "Response independent of product", "Chi-square, Cramér's V, adjusted residuals"],
    ["H3", "Did the timely-response rate change over time?", "Same timely share every year (2017–2022)", "Chi-square, residuals, rate difference"],
    ["H4", "Do CFPB forwarding intervals differ by product?", "Same distribution for every product", "Kruskal-Wallis with ε²; chi-square on the same-day share"],
  ], [0.06, 0.32, 0.32, 0.30]),
  h2("Success criteria"),
  table([
    ["#", "Criterion", "Result"],
    ["1", "Every data-preparation step in the brief is done and documented; raw file provably unchanged", "Met: SHA-256 identical before and after the notebook run"],
    ["2", "Each hypothesis is tested with assumptions checked and interpreted with an effect size", "Met, with robustness reruns"],
    ["3", "Key figures reconcile with an independent recalculation", "Met: 38 of 38 figures match (validation/independent_check.py)"],
    ["4", "At least three findings are supported by evidence, with limitations stated", "Met: six findings"],
  ], [0.05, 0.6, 0.35]),

  h1("2. Data and data quality"),
  p("The file Consumer_Complaints.xlsx has 62,516 records and 12 columns, matching the brief and the data dictionary. Following the brief's definitions, “Date submitted” is when the CFPB received a complaint and “Date received” is when it sent the complaint to the company. The difference between them is the CFPB forwarding interval, not the company's response time. No rows were deleted: cleaned and derived values were added as new columns next to the unchanged raw ones."),
  table([
    ["Check", "Result", "Decision"],
    ["Complaint ID uniqueness", "62,516 unique IDs; 0 exact duplicate rows", "Valid primary key"],
    ["Rows identical except Complaint ID", "2,784 rows in 1,290 groups", "Kept and flagged: no consumer identifier, so two consumers can file identical-looking complaints. Robustness check confirms no effect"],
    ["Blank “Timely response?”", "1,494, all “In progress” (May–Aug 2023)", "Labelled Pending; excluded from the timely-rate denominator, never counted as “No”"],
    ["Blank public response", "1,494 in progress, 681 closed", "Labelled Pending / Not recorded: a public response is optional"],
    ["Blank sub-issue / sub-product", "10,858 / 7", "Labelled, not imputed: not every issue has a sub-issue"],
    ["Dates", "1 May 2017 – 28 Aug 2023; no time components; no negative intervals", "Valid. 435 intervals over 30 days flagged, not removed"],
    ["Reporting months", "76 of 76 months present; August 2023 partial", "First and last months excluded from month-level tests"],
    ["Category consistency", "No spelling, case or spacing variants", "No standardisation needed"],
    ["July 2023", "1,749 complaints; 537 of them on 11–14 July", "Kept as recorded; treated as an outlier in interpretation"],
  ], [0.26, 0.34, 0.40]),
  p(""),
  p("Cleaning is done by a tested Python module (complaint_prep.py, 22 unit tests). The cleaned dataset and the KPI definitions are exported for the other tracks. Headline KPIs: timely-response rate **96.06%** (58,619 of 61,022 Yes/No records, 1,494 pending excluded); forwarding interval mean **1.22 days**, median 0, **79.4%** same day."),

  h1("3. Exploratory findings"),
  image(viz("01_monthly_volume"), 600),
  caption("Figure 1. Monthly complaints, May 2017 to August 2023, with a 12-month average."),
  p("Monthly volume was flat to slightly falling from 2017 to 2019 (about 590–675 a month), then rose by 16–26% a year from 2020 to 2022. Raw annual totals mislead at the edges: 2023 looks like a 29.5% fall, but it covers only eight months, and per month it is a 5.7% rise. The lowest month is February 2019 (356). The highest is July 2023 (1,749), driven by a four-day burst of mostly web complaints about checking and savings accounts."),
  image(viz("04_complaints_by_product"), 540),
  caption("Figure 2. Complaints by financial product."),
  p("Checking/savings and credit/prepaid card complaints make up two-thirds of the total. The issue list is product-specific, because the CFPB form offers different issues for each product. “Managing an account” (24.2% of all complaints) appears only under checking/savings. For this reason the analysis compares responses across products, not issues: an issue-by-product test would only restate the design of the form."),
  image(viz("07_product_mix_by_year"), 580),
  caption("Figure 3. Product mix by year."),
  p("Mortgage complaints fell from 23% of the total in 2017 to 4% in 2023, from about 155 to 45 a month. Credit reporting rose from 9% to 14%. Between 2018 and 2022 the issues gaining most share were getting a credit card (+4.8 points), opening an account (+3.6) and fraud or scam (+3.3). Because total volume nearly doubled, a stable share still means a rising count: checking/savings complaints roughly doubled while keeping a share of about 40%."),
  image(viz("11_timely_rate_by_year"), 560),
  caption("Figure 4. Recorded timely-response rate by year with 95% Wilson intervals (y-axis starts at 86%)."),
  p("The response mix of closed complaints was stable over time: “closed with explanation” stayed between 65% and 69% every year. Timeliness was not stable. It was 99.3–99.9% from 2017 to 2020, then fell to 89.0% in 2021, starting in Q2 2021 and across every product except mortgages. The 2023 rate is provisional: complaints from Q3 2023 are still in progress, and those already closed are the quickest ones, so the final 2023 rate is more likely to fall than rise."),

  h1("4. Hypotheses and statistical methods"),
  p("With about 60,000 records, almost any difference is statistically significant, so each test is reported with an effect size and interpreted on that basis. Thresholds: ε² 0.01 / 0.08 / 0.26 and Cramér's V 0.10 / 0.30 / 0.50 (two columns) or 0.07 / 0.21 / 0.35 (three columns) for small / medium / large. The significance level is 5%, with Holm correction within follow-up comparisons and across the six primary tests. Vehicle loans, payday/personal loans and student loans (1,005 complaints in total) are pooled as “Other loans” in H2 and H4 so that every expected chi-square count is at least 5."),
  bullet("**H1:** the unit of analysis is the 74 full months, because volume exists only as a count per period. Each year has only 7–12 months and 2023 contains the July outlier (Shapiro-Wilk p = 0.005), so rank-based tests are used. Spreads are similar across years (Brown-Forsythe p = 0.29). Adjacent years are compared with Mann-Whitney U tests (Holm-corrected). Monthly counts are serially correlated (lag-1 autocorrelation 0.57), so the trend test is repeated on the seven annual averages."),
  bullet("**H2:** 61,014 closed complaints in the three main response categories. In-progress complaints have no outcome, and the 8 “Closed” records are too few to form a category. The smallest expected count is 85."),
  bullet("**H3:** Yes/No records for 2017–2022 (53,385). 2023 is excluded from the test because it is right-censored, and reported separately. Because the untimely outcome is rare, the 2020-to-2021 change is also given as a difference in rates with a Newcombe 95% interval."),
  bullet("**H4:** all 62,516 complaints. The interval is highly skewed (skewness 11.8) with 79% zeros, so Kruskal-Wallis replaces ANOVA, and the same-day share gives a second, easier-to-read view. The test is repeated within the web and referral channels, because the channels forward at very different speeds."),

  h1("5. Results and interpretation"),
  table([
    ["Hypothesis", "Test", "Statistic", "p (Holm)", "Effect size"],
    ["H1", "Kruskal-Wallis, monthly counts by year", "H = 57.0, df 6", "< 0.001", "ε² = 0.78 (large)"],
    ["H1", "Mann-Kendall trend", "τ = 0.61", "< 0.001", "Sen +102 / month per year (95% CI 83–124)"],
    ["H2", "Chi-square, response × product", "χ² = 5,426, df 12", "< 0.001", "V = 0.21 (medium)"],
    ["H3", "Chi-square, timely × year 2017–2022", "χ² = 2,747, df 5", "< 0.001", "V = 0.23; untimely rate ×16 in 2021"],
    ["H4", "Kruskal-Wallis, forwarding days × product", "H = 1,508, df 6", "< 0.001", "ε² = 0.024 (small)"],
    ["H4", "Chi-square, same-day × product", "χ² = 1,657, df 6", "< 0.001", "V = 0.16 (small)"],
  ], [0.11, 0.33, 0.18, 0.12, 0.26]),
  p(""),
  h2("5.1 H1: complaint volume rose, mostly in 2020–2022"),
  image(viz("14_h1_trend"), 580),
  caption("Figure 5. Full-month complaint counts with the Sen's slope trend line."),
  p("**H₀ is rejected.** Years differ strongly and the trend is upward. The trend test on annual averages, which is not affected by serial correlation, agrees (τ = 0.71, p = 0.030). The growth is not linear. Adjacent-year comparisons are significant for 2019→2020, 2020→2021 and 2021→2022 (rank-biserial r 0.64–0.81), but not for 2017→2018, 2018→2019 or 2022→2023, when volume levelled off at around 1,100 a month. The data has no customer counts, so it cannot show whether the complaint rate rose or the customer base grew."),
  h2("5.2 H2: recorded response depends on product"),
  image(viz("15_h2_response_residuals"), 540),
  caption("Figure 6. Share of each product's closed complaints by response, with adjusted residuals (red = more than expected under independence)."),
  p("**H₀ is rejected,** with a medium association. Checking/savings (33%, residual +43) and card complaints (30%, +22) close with monetary relief far more often than expected. Credit reporting almost never does (4%, −44) but often closes with non-monetary relief (16%, +23), such as a corrected record. Debt collection (88%) and money transfer (80%) mostly close with an explanation. **Interpretation:** the response follows the remedy each product allows. A disputed fee can be refunded; a credit report error is corrected, not paid. This is not evidence that any product is handled better or worse. Monetary relief is not an admission of fault, and part of the product effect is an issue effect that the data cannot separate."),
  h2("5.3 H3: timeliness dropped in 2021"),
  p("**H₀ is rejected.** Cramér's V (0.23) counts as small, but V stays low when one outcome is rare, so it understates this change. The untimely rate rose from 0.69% in 2020 to 10.98% in 2021, an increase of **10.3 percentage points (95% CI 9.7–10.9), about 16 times** the 2020 rate. 2021 is far above expectation (adjusted residual +48), and 2022 is still above the earlier years (4.4%, +6). The 2023 rate so far, 93.2% timely (95% CI 92.6–93.7), is already below 2022. This is the only measure in the data that directly describes the company's handling. The drop is spread across products and coincides with a 25% rise in volume, a pattern that fits a capacity or process issue more than a product-specific problem. The cause cannot be confirmed from this data."),
  h2("5.4 H4: forwarding speed depends on channel, not product"),
  image(viz("17_h4_same_day_by_product"), 560),
  caption("Figure 7. Share forwarded by the CFPB on the day received, by product, with 95% intervals."),
  p("**H₀ is rejected, but the effect is small.** Same-day forwarding ranges from 71.9% (mortgage) to 91.9% (credit reporting), and the product means differ by only about one day. Most of this difference comes from the submission channel. Mortgage and checking/savings complaints arrive as referrals from other agencies about a quarter of the time, against 1.5% for credit reporting, and referrals are forwarded the same day only 22–46% of the time. Within each channel the product effect is negligible: V = 0.06 for web complaints and 0.08 for referrals."),

  h1("6. Validation"),
  bullet("**Independent reconciliation:** a separate script using only Python's standard library reads the raw .xlsx file as XML and recomputes 38 key figures, including counts, rates, forwarding statistics and all four main test statistics (with its own tie-corrected Kruskal-Wallis and chi-square code). **All 38 match** the notebook. The notebook runs this check itself and stops if any figure fails."),
  bullet("**Robustness:** removing the 1,494 extra look-alike rows changes every effect size by 0.006 or less. Removing July 2023 leaves H1 unchanged (ε² 0.77, τ 0.60). Restricting to web complaints keeps H2 and H3 (V 0.22, 0.23) and confirms that H4's product effect disappears (V 0.06)."),
  bullet("**Unit tests:** 22 tests cover the cleaning rules, KPI functions and statistical helpers (Wilson interval, Holm correction, adjusted residuals, ε²). All pass, and the notebook runs them as part of its validation."),
  bullet("**Raw data preserved:** the SHA-256 hash of the raw file is recorded at the start of the notebook and is identical at the end. The notebook gives byte-identical charts on repeated runs."),

  h1("7. Limitations and alternative explanations"),
  bullet("**Complaints are unverified consumer reports.** Nothing here establishes misconduct."),
  bullet("**No denominator:** there are no customer or account counts, so complaint rates cannot be calculated. Growth may reflect a larger customer base."),
  bullet("**Recorded responses are not outcomes:** the categories are set by the company. There is no consumer-feedback field, no relief amount and no actual response time. “Timely” is a Yes/No flag, and the 2023 rate is provisional."),
  bullet("**Coverage:** only complaints sent to the CFPB, for one company, May 2017 – August 2023. There are no narratives, so root causes and severity cannot be analysed."),
  bullet("**Statistical:** the data is observational (association, not causation). Large samples make significance trivial. Monthly counts are serially correlated. Product and issue cannot be separated."),
  p("**Alternative explanations the data cannot rule out:**"),
  table([
    ["Finding", "Alternative explanations"],
    ["Volume rise (H1)", "Customer growth; wider awareness of the CFPB; consumers choosing the CFPB over the bank's own channels; pandemic-era changes in banking"],
    ["Mortgage decline", "Pandemic forbearance programmes; the refinancing period; a smaller mortgage book"],
    ["Response depends on product (H2)", "Issue mix within each product; different recording practices across business units"],
    ["Timeliness drop (H3)", "A change in how timeliness was recorded or in CFPB processes; one large batch of late responses"],
    ["July 2023 burst", "An external trigger; a reporting artefact; a coordinated submission campaign"],
  ], [0.3, 0.7]),

  h1("8. Recommendations"),
  p("These recommendations are based on recorded complaint data and identify where to look, not who is at fault."),
  table([
    ["Recommendation", "Supporting finding", "Benefit", "Limitation / information needed"],
    ["1. Review complaint-handling capacity from Q2 2021, and report the untimely rate monthly by product with a 1% alert threshold", "Untimely rate below 1% every year to 2020; 11.0% in 2021; 4.4% in 2022", "The 2021 drop would have been flagged within weeks, and timeliness becomes a tracked KPI", "Actual response times and staffing data needed to confirm the cause"],
    ["2. Plan capacity for about 1,100–1,200 complaints a month, with a daily alert at twice the recent median", "Volume nearly doubled and levelled off; 11–14 July 2023 reached 183 a day against a typical 53", "Staffing matches current demand; bursts are detected while they happen", "No customer base, so growth vs complaint rate is unknown; use the ML track's forecast"],
    ["3. Focus root-cause work on account management and on the growing onboarding and fraud issues; report issue shares quarterly", "“Managing an account” is 24% of complaints; card acquisition, account opening and fraud gained the most share", "Effort goes where volume is largest and growing; shows whether fixes work", "No narratives: the actual root causes need case reviews"],
    ["4. Count response targets from the date the company receives a complaint; report referrals separately", "Referrals are forwarded the same day only 22–46% of the time, against 87–93% for web", "Teams are not penalised for CFPB and agency routing delays", "Forwarding measures the CFPB, not the bank"],
    ["5. Add customer counts by product, actual response times and relief amounts to the complaint data", "Limitations of the current fields", "Turns counts into rates and recorded categories into measurable outcomes", "Needs internal data access and privacy review"],
  ], [0.28, 0.27, 0.22, 0.23]),

  h1("9. Reproducibility and attribution"),
  p("The full analysis is in Week4_Consumer_Complaints_Statistical_Analysis.ipynb, which runs top to bottom with fixed random seeds. The README gives setup and run instructions, including the independent check and the unit tests. Tools: Python, pandas, NumPy, SciPy, Matplotlib and seaborn; this report was generated with the docx library for Node.js. Data: CFPB consumer complaint records for Bank of America, supplied by AnalystLab Africa with a data dictionary. The statistical methods are standard, and no external code was copied."),
];

build(children, out, "Week 4 · Statistical Analysis Report");
