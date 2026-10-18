
Project Question

Which customers are starting to shop less often than normal for customers with similar historical shopping behavior?

Purpose

The SQL work prepares the Instacart data, checks data quality, creates the descriptive statistics,
builds customer behavior segments, calculates the expected ordering cadence for each segment,
and creates the final customer-level decision table used by Python.

Run Order

Run the five SQL files in numeric order on the SQLite database after the six source CSVs have been imported.

1. 01_load_setup.sql
   - Preserves the original imported tables as *_raw copies.
   - Rebuilds the six working tables with the correct column names and data types.
   - Removes the imported header row that had been loaded as data.
   - Creates the standard working views and the indexes used by later files.
   - Confirms the corrected tables retain all real source rows.
   - Index timing check: product-frequency query improved from 12.30 seconds to 1.55 seconds.

2. 02_data_quality.sql
   - Runs the required data-quality checks before analysis.
   - Checks duplicate business keys, orphaned foreign keys, prior/train reconciliation,
     aisle and department quality, numeric ranges, order-gap NULL patterns, and order-sequence integrity.
   - No duplicate keys, orphaned keys, reconciliation errors, invalid ranges, unexpected later-order NULLs,
     or order-sequence issues were found.
   - Placeholder categories are retained instead of deleted.
   - First-order NULL gaps are retained because they are structurally valid.
   - 11.49% of all measured order gaps in the full orders table are recorded at the 30-day limit,
     so the 30-day value is treated as a data limitation.

3. 03_descriptive_statistics.sql
   - Creates order_fact with one row per prior order.
   - Creates line_item_fact with one row per product purchased in a prior order.
   - Builds the reusable descriptive measures required by the rubric:
     total orders and customers, basket size, reorder rate, days between orders,
     order volume by day and hour, and top products.
   - Creates m_customer_behavior with one row per customer.
   - Creates the basket-size and cadence distributions used to support the segment cutoffs.

4. 04_customer_segmentation_and_expected_cadence.sql
   - Assigns every customer to a basket-size segment and an ordering-cadence segment.
   - Basket segments: Small <= 8, Medium 9-17, Large >= 18.
   - Cadence segments: Frequent <= 9 days, Regular 10-20 days, Infrequent > 20 days.
   - Creates the 9 basket x cadence behavior groups.
   - Keeps customers with at least 5 prior orders and at least 4 measured gaps as benchmark customers.
   - Calculates the median expected order gap for each of the 9 behavior groups.
   - Customers with less history are not deleted; they are handled later as Insufficient History.

5. 05_engagement_analysis_and_final_output.sql
   - Uses the validated historical slowdown thresholds:
     P75 = 1.176471 and P90 = 1.743017.
   - Finds the latest observed order gap for each customer.
   - Compares the latest observed gap with the expected gap for the customer's behavior segment.
   - Classifies customers as Stable, Weakening, High Concern, Capped Gap - Review,
     or Insufficient History.
   - Creates the final customer decision table and the supporting segment/status summaries.
   - Creates the SQL outputs used for independent Python validation.

Main Final SQL Table

submission_customer_decision

Grain:
One row per customer.

Main fields:
- basket_segment
- frequency_segment
- total_prior_orders
- prior_gap_count
- avg_basket_size
- avg_days_between_orders
- reorder_rate_pct
- latest_observed_gap
- expected_order_gap
- gap_vs_expected_ratio
- engagement_status
- latest_gap_capped_flag
- insufficient_history_flag
- assessed_flag
- at_risk_flag

The final table contains the customer dimensions, more than five behavioral KPIs,
the engagement decision, and the quality flags required for the Python handoff.

Engagement Status Rules

1. Insufficient History
   Fewer than 5 prior orders or fewer than 4 measured prior gaps.

2. Capped Gap - Review
   Latest observed gap equals 30 days.
   The source records gaps only up to 30 days, so this is not treated as an exact slowdown value.

3. Stable
   gap_vs_expected_ratio <= 1.176471

4. Weakening
   1.176471 < gap_vs_expected_ratio <= 1.743017

5. High Concern
   gap_vs_expected_ratio > 1.743017

The thresholds are historical alert-policy thresholds, not churn probabilities.

Headline Results

Total customer base: 206,209

Final engagement status:
- Stable: 90,281
- Weakening: 17,678
- High Concern: 12,034
- Capped Gap - Review: 42,640
- Insufficient History: 43,576

Assessed customers:
119,993

Weakening + High Concern:
29,712 customers

At-risk share among assessed customers:
24.76%

SQL Outputs Exported to Python

The following File 5 tables are exported as CSV files for the Python work:

1. submission_customer_decision
   Main customer-level SQL decision table.

2. submission_segment_context
   Segment-level supporting context.

3. python_validation_input
   Additive customer totals used to independently recalculate SQL results in Python.

4. sql_validation_reference
   SQL reference values used to confirm the Python calculations.

The current SQLite exports are headerless, so the Python notebook reads them with header=None
and assigns the exact SQL column names with names=.

Important Data Limitations

- The source records days_since_prior_order only up to 30 days.
- A recorded value of 30 may mean 30 or more days.
- The latest observed gap exists only when another order is observed.
  The analysis therefore identifies historically slower observed returns;
  it does not identify who is currently overdue.
- Customers with insufficient history are retained rather than deleted.
- Placeholder aisle/department categories are retained so totals and denominators are not changed.
- The analysis describes customer behavior; it does not prove churn or the effect of a future incentive.

Re-running the SQL

1. Import the six source CSVs into a clean SQLite database.
2. Run Files 01 through 05 in numeric order.
3. Review the checkpoints and final row counts after each file.
4. Confirm submission_customer_decision has 206,209 rows,
   206,209 unique customers, and 0 duplicate customers.
5. Export the four File 5 Python handoff tables to CSV.
