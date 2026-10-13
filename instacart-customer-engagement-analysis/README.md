# Instacart Customer Engagement Analysis

A Group 11 data architecture capstone for BANA 5090 that uses **SQLite, Python, and Tableau** to identify customers returning more slowly than customers with similar historical shopping behavior.

## Business question

**Which customers are starting to shop less often than normal for customers with similar historical shopping behavior?**

The project turns Instacart order history into a customer-level engagement decision table. It combines data-quality checks, behavioral segmentation, historical cadence benchmarks, independent Python validation, and dashboard-ready outputs.

## Workflow

1. **Prepare and validate data in SQLite.** Standardize six imported source tables, preserve raw copies, create indexes, and check duplicate keys, referential integrity, numeric ranges, and order sequences.
2. **Summarize shopping behavior.** Build order and line-item facts and calculate basket size, reorder rate, order timing, and historical order gaps.
3. **Create nine behavior segments.** Combine three basket-size groups with three ordering-frequency groups. Use customers with at least five prior orders and four measured gaps to calculate each segment's median expected order gap.
4. **Assess engagement.** Compare the latest observed order gap with the expected gap and assign a status using historical slowdown thresholds.
5. **Validate and prepare outputs in Python.** Recalculate SQL metrics, standardize fields, handle capped gaps, validate segment risk, and enrich customers through a checked many-to-one merge.
6. **Visualize in Tableau.** Export customer-level and segment-level CSVs for engagement and segment comparisons.

## Findings

The supplied customer output contains **206,209 unique customers**.

| Engagement status | Customers |
| --- | ---: |
| Stable | 90,281 |
| Weakening | 17,678 |
| High Concern | 12,034 |
| Capped Gap - Review | 42,640 |
| Insufficient History | 43,576 |

Of the **119,993 assessed customers**, **29,712 (24.76%)** are classified as Weakening or High Concern. The submission also reports 3,214,874 prior orders, a weighted average basket size of 10.09 items, an average order gap of 10.71 days, and an overall reorder rate of 58.97%.

These classifications can support a controlled retention pilot, with outcomes measured through repeat orders, time to next order, basket size, and changes in engagement status. They do not establish that an incentive will work.

## Engagement rules

The slowdown ratio is `latest_observed_gap / expected_order_gap`.

| Status | Rule |
| --- | --- |
| Insufficient History | Fewer than 5 prior orders or 4 measured historical gaps |
| Capped Gap - Review | Latest recorded gap is 30 days, after the history check |
| Stable | Ratio ≤ 1.176471 |
| Weakening | 1.176471 < ratio ≤ 1.743017 |
| High Concern | Ratio > 1.743017 |

The ratio thresholds represent historical P75 and P90 alert thresholds, not predicted churn probabilities. Basket segments use historical average basket size: Small ≤ 8, Medium > 8 and < 18, and Large ≥ 18. Frequency segments use historical average order gaps: Frequent ≤ 9 days, Regular > 9 and ≤ 20 days, and Infrequent > 20 days.

## Project files

```text
instacart-customer-engagement-analysis/
├── README.md
├── requirements.txt
├── SQL_Group_11_Capstone/
│   ├── SQL_Scripts/                 # Five ordered SQL scripts
│   ├── SQL_Data_Dictionary.xlsx
│   ├── SQL_Schema.pdf
│   └── SQL_README.txt
├── Python_Group_11_Capstone/
│   ├── Group_11Capstone.ipynb
│   ├── Csv_Files/                   # Four SQL exports; no header row
│   ├── Output_Tableau_CSVs/         # Generated CSVs with headers
│   ├── Dependency_List.txt
│   └── Python_README.txt
├── Tableau_Ready_Extract/
│   ├── final_customer_decision_tableau.csv
│   ├── segment_summary_tableau.csv
│   ├── Tableau_Extract.jpeg
│   ├── Tableau_README.txt
│   └── Optional_Dashboard/          # Packaged Tableau workbook (.twbx)
└── Slides/                         # Original capstone presentation
```

Original component documentation is retained as submission context. The instructions below reflect the portable notebook in this repository; the original Python README describes its earlier Google Colab setup.

## Run the Python workflow

The included SQL exports let you run the Python analysis without rebuilding the full database.

From this project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
jupyter lab Python_Group_11_Capstone/Group_11Capstone.ipynb
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Run the notebook from top to bottom. It resolves inputs from `Python_Group_11_Capstone/Csv_Files` when launched from the project root or notebook folder, and writes to `Python_Group_11_Capstone/Output_Tableau_CSVs`. Adjust `PROJECT_DIR` if using a different working directory. The four input CSVs are **headerless**; the notebook supplies their column names explicitly.

The notebook checks customer uniqueness, row counts, source completeness, four SQL/Python metric comparisons, segment-risk agreement, and merge integrity. Its final outputs are:

- `final_customer_decision_tableau.csv`: 206,209 rows and 13 columns, one row per customer.
- `segment_summary_tableau.csv`: 9 rows and 6 columns, one row per behavioral segment.

## Rebuild the SQL analysis

Use a **separate working SQLite database**: the setup script replaces working tables and retains raw audit copies. The six original Instacart source CSVs are not included here: `orders.csv`, `order_products__prior.csv`, `order_products__train.csv`, `products.csv`, `aisles.csv`, and `departments.csv`.

The setup script was written for the submission's imported table layout. Review its expected source columns and header-row handling before importing data through a different tool. Run the actual files in this order:

1. `01_setup_and_indexes.sql`
2. `02_data_quality.sql`
3. `03_descriptive_statistics.sql`
4. `04_customer_segmentation.sql`
5. `05_engagement_analysis_and_final_output.sql`

Review each script's checkpoints, then export `submission_customer_decision`, `submission_segment_context`, `python_validation_input`, and `sql_validation_reference` as headerless CSVs into the notebook's `Csv_Files` folder.

The original submission's database archive is approximately **2.65 GB** and expands to a roughly **7.45 GB** SQLite database. It remains outside this GitHub package. Use the original archive locally if available; the included exports are sufficient for the Python workflow.

## View the Tableau deliverables

Connect Tableau to the two CSVs in `Tableau_Ready_Extract`, or open the packaged workbook in `Optional_Dashboard` with a compatible Tableau application. Local file connections may need to be updated. The JPEG documents the submitted Tableau work; this folder does not contain a standalone `.hyper` extract.

## Limitations

- Recorded order gaps stop at 30 days; a value of 30 can mean 30 or more days. The cleaned slowdown ratio is left missing for capped gaps.
- The latest gap is observed only when a subsequent order occurs. This analysis measures historically slower returns; it cannot identify customers currently overdue.
- Customers with insufficient history remain in the customer base but are excluded from the assessed-risk denominator.
- Placeholder aisle and department categories are retained to preserve totals.
- This is a descriptive, rule-based analysis, not a validated predictive churn model or causal study.

## Credits and repository scope

Created as the **Group 11 BANA 5090 capstone submission**. SQL, notebook, presentation, and Tableau deliverables are retained from the group project. The notebook's loading setup has been adapted for local execution, and stored notebook outputs have been cleared for a clean rerun.

Peer-review documents and the large database archive are excluded from this portfolio folder. No additional software or dataset license is asserted by this README; review the original dataset terms before redistributing source data.
