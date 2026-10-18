BANA 5090 Capstone - Python README

Purpose

This Python work takes the final SQL output and prepares it for Tableau.

The SQL work already created the customer decision table and the supporting segment and validation tables. In Python, we load those SQL exports, check them, standardize the fields, handle the known limitations, validate the SQL results, merge, and then export clean Tableau-ready files.

Input files from SQL

1. submission_customer_decision.csv
   This is the main final SQL decision table.
   It has one row per customer and contains the customer segments, historical behavior,
   latest and expected order gaps, engagement status, and the assessment flags.

2. submission_segment_context.csv
   This is the segment-level supporting table.
   It has one row for each basket x frequency segment and gives the customer count,
   share of the customer base, and at-risk percentage for the segment.

3. python_validation_input.csv
   This contains the customer-level totals needed to independently recalculate
   the main SQL measures in Python.

4. sql_validation_reference.csv
   This contains the SQL values that the Python calculations are checked against.

Important:
The SQL export files do not have a header row. The first row is actual data.
We therefore load them with header=None and use names= to assign the exact SQL column names.
This keeps the first data row and gives the files the correct field names in Python.


Eight-step Python process

1. Load

We set the project, Input, and Output folders with Path and load the four SQL export files with pd.read_csv().
Because the SQL exports are headerless, we use header=None and names= with the exact SQL column names.
After the correct load, the main customer table has 206,209 rows and 16 columns, the segment table has 9 rows,
the validation table has 206,209 rows, and the SQL reference table has 4 rows.

2. Profile

We profile submission_customer_decision using .shape, .dtypes, .isna(), duplicated(), nunique(), and value_counts().
This confirms 206,209 customers, 206,209 unique user IDs, 0 duplicate customers, and 0 missing source values.
We also review the basket_segment, frequency_segment, and engagement_status counts so the main classifications
are visible before cleaning or merging.

As part of validation, Python independently recalculates four SQL results from python_validation_input:
3,214,874 total prior orders, 10.09 weighted average basket size, 10.71 average days between orders,
and 58.97% overall reorder rate. np.isclose() is used to compare the Python values with sql_validation_reference,
and all four checks must pass.

3. Structure

The four SQL CSV exports do not contain column headers, so we explicitly provide CUSTOMER_COLS, SEGMENT_COLS,
VALIDATION_COLS, and REFERENCE_COLS when reading the files.
This gives each file the same field names used in SQL and prevents the first data row from being treated as a header.
We also confirm the main decision table stays at one row per customer and do not drop valid customer rows.

4. Types

We standardized the numeric fields before using them for calculations or Tableau.
Customer IDs, counts, and flags are converted with .astype(int), while averages, percentages,
expected order gap, and gap ratio fields are converted with pd.to_numeric().
This keeps the number fields consistent for validation, aggregation, merge checks, and export.

5. Standardize

We standardized the main category fields used in the analysis:
basket_segment, frequency_segment, and engagement_status.
We use .str.strip() to remove leading or trailing spaces without changing the meaning of the categories.
We then use assertions to confirm the expected Small / Medium / Large basket groups and
Frequent / Regular / Infrequent frequency groups are present.

6. Missing and invalid / known limitations

We keep customers instead of deleting them when the data has a known limitation.
A latest observed gap of 30 is a recording cap and may mean 30 or more days, so we use .mask()
to create gap_vs_expected_ratio_clean and do not use the capped ratio as an exact slowdown value.
Customers with insufficient history are also kept in the customer base and are identified with
insufficient_history_flag and assessed_flag rather than being removed.

7. Enrich and validate the merge

We independently recalculated the segment at-risk percentage in Python and compared it with the SQL segment result.
The segment result is joined to submission_segment_context and checked with np.isclose() so the Python and SQL
segment-risk values match.

We then merged the 9-row segment context into the customer-level table using:
validate="many_to_one" and indicator=True.
We checked the row count before and after the merge, confirmed it remains 206,209 customers,
confirmed there are exactly 9 segment rows, and confirmed every customer matched a segment.
This prevents an unexpected fan-out, lost rows, or duplicate customers.

8. Aggregate and export for Tableau

The final customer-level Tableau table is created by selecting the 13 fields needed for the business question.
We confirm it has exactly 206,209 rows, one unique user_id per row, and no duplicated columns.
It is exported with .to_csv(..., index=False) as:

final_customer_decision_tableau.csv

This is the main Tableau file and is used for engagement status, customer behavior,
latest versus expected cadence, assessed customers, and at-risk analysis.

We also create:

segment_summary_tableau.csv

This is an optional supporting Tableau file with 9 rows, one for each basket x frequency segment.
It gives the segment label, customer count, share of the customer base, and at-risk percentage,
so the segment results can be shown more clearly in Tableau.
It is also exported with index=False so no extra pandas index column is added.


Main Tableau output

final_customer_decision_tableau.csv
- Main output
- 206,209 rows
- One row per customer
- 13 columns
- Used for the main customer engagement analysis in Tableau

Optional supporting Tableau output

segment_summary_tableau.csv
- Supporting output
- 9 rows
- One row per basket x frequency segment
- 6 columns
- Used for a simple segment-level comparison and better analysis in Tableau




How to run

1. Keep the Input and Output folders inside the project folder.

2. Change PROJECT_DIR only if the project folder is saved in a different location, or you can just uncomment the first block of our code and comment the second block of code, and that gives you a default loading function.

3. Run the notebook from top to bottom.



Dependencies

pandas
numpy
