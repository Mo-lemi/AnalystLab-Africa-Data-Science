# Week 1: Exploratory Data Analysis on ShopSmart Retail Data

**Mission DS01** · AnalystLab Africa Experience Lab, Data Science Track
**Author:** Molemi Molokoane · **Client:** ShopSmart Retail Ltd. (fictional)

An end-to-end exploratory analysis of ShopSmart's 2025 retail data: nine related tables, 50,000 orders,
5,000 customers, 500 products and 25 stores across Nigeria. It covers loading, cleaning, KPIs,
visualisation, correlation, feature engineering, ten business questions and a bonus K-Means customer
segmentation.

## Key findings

| | Finding |
|---|---|
| 💰 | **₦2.25B revenue** from 16,529 completed orders (AOV ₦136K), but **only 1 in 3 orders completes**. Cancelled and pending orders hold ₦4.57B. |
| 📉 | **27% of completed order lines sold below cost**, losing ₦226M. The top 10 products by revenue and by profit have no products in common. |
| 🏬 | Stores, categories, months and customer segments perform **very evenly**. The best store (Lagos STR003) leads mainly because it completes more of its orders. |
| 👥 | Gold, Silver and Bronze members **spend the same**. RFM segmentation shows that purchase frequency is what drives customer value. |
| 📦 | **₦3.17B of stock at cost**: 417 of 500 items are overstocked, and only 21 need restocking. |
| ⚠️ | The data is complete but **inconsistent**: discounts were misapplied, regions contradict states, and half the returns are dated before their order. |

## Project structure

```
Week1_DataScience_Project/
├── Week1_EDA.ipynb          # the full analysis (executed, with outputs)
├── Cleaned_Data/            # cleaned tables, engineered features, cleaning log, KPIs
├── Visualizations/          # every chart from the notebook (PNG)
├── EDA_Report.pdf           # written report for ShopSmart management
├── Presentation.pptx        # 13-slide findings deck with speaker notes
├── scripts/
│   └── build_report.py      # regenerates EDA_Report.pdf from the notebook outputs
├── requirements.txt
└── README.md
```

The raw CSVs live in [`../data/`](../data) at the repository root, so later weeks can reuse them.

### Cleaned_Data contents

| File | Description |
|---|---|
| `*_clean.csv` | One cleaned file per source table (Order_Items is dropped because it duplicates Orders) |
| `sales_master.csv` | Orders joined to products, customers, stores and the return flag |
| `sales_features.csv` | `sales_master` plus profit, margin, below-cost flag, calendar and age-group features |
| `customer_features.csv` | Customer-level RFM, CLV estimate, days since last purchase, completion and return rates |
| `inventory_features.csv` | Stock cover, Low/Medium/High status and days of supply |
| `customer_segments.csv` | K-Means RFM segment for each customer |
| `restock_list.csv` | Inventory items at or below their reorder level |
| `cleaning_log.csv` | Every cleaning step, with the number of rows affected |
| `kpis.json`, `insights.json` | Headline numbers used by the report |

## How to run

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate                 # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r Week1_DataScience_Project/requirements.txt

cd Week1_DataScience_Project
jupyter notebook Week1_EDA.ipynb       # run all cells to regenerate Cleaned_Data/ and Visualizations/
python scripts/build_report.py         # rebuild EDA_Report.pdf from those outputs
```

Tested with Python 3.13, pandas 3.0, scikit-learn 1.9 and matplotlib 3.11.

## Key analysis decisions

- **Revenue = Completed orders only.** Pending and cancelled orders are reported separately as unrealised demand.
- **Discount is a percentage.** The source `line_total` subtracted 0–20 as naira. Net sales were recomputed as `qty × price × (1 − discount/100)`.
- **Region comes from state.** The source `region` field puts Lagos in all four regions, so stores are mapped to Nigeria's six geopolitical zones instead.
- **Impossible records are flagged, not deleted.** For example, returns dated before their order are kept, with flags, so analyses can include or exclude them.
- **Products are linked to suppliers by brand.** Every supplier is named "<Brand> Supplies", which gives a 100% match.

## Assignment checklist

| Part | Section in the notebook |
|---|---|
| 1. Environment setup (10) | Part 1 · `requirements.txt` |
| 2. Load the data (15) | Part 2: head, tail, shape, columns, dtypes, missing values, missingno |
| 3. Data cleaning (20) | Part 3: duplicates, missing values, types, dates, renaming, inconsistent values, cleaning log |
| 4. EDA KPIs (30) | Part 4: all ten KPIs, saved to `kpis.json` |
| 5. Visualisation (30) | Part 5: all ten required charts (`Visualizations/01–10`) |
| 6. Correlation (20) | Part 6: matrices, heatmaps, pair plot, interpretation |
| 7. Feature engineering (20) | Part 7: all eight requested features plus extras, with reasons |
| 8. Business questions (30) | Part 8: Q1–Q10, each with a table or chart |
| 9. Report (25) | `EDA_Report.pdf` |
| 10. Code quality (10) | Markdown throughout, docstrings, reusable functions |
| Bonus (20) | K-Means customer segmentation, with limitations |

## Limitations

The dataset appears to be synthetic. Distributions are very uniform, and names often contradict the
recorded gender. As a result, differences between groups are small and every finding should be
validated on production data. There is only one year of sales, so growth and seasonality cannot be
confirmed year on year.
