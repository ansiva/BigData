
-- File 5: Engagement Analysis and Final Output


-- This file compares each customer's latest observed order gap with the
-- expected cadence for customers with similar historical shopping behavior.
-- It then creates the final customer-level decision table used by Python.


-- 1. slowdown_thresholds
-- Stores the validated historical thresholds used to classify slowdown severity.
-- P75 = 1.176471 and P90 = 1.743017.

DROP TABLE IF EXISTS slowdown_thresholds;

CREATE TABLE slowdown_thresholds AS
SELECT
    117064 AS calibration_customers,
    1.176471 AS p75_ratio,
    1.743017 AS p90_ratio,
    29404 AS excluded_capped_customers,
    59741 AS excluded_short_history_customers,
    0 AS excluded_invalid_customers;

SELECT *
FROM slowdown_thresholds;


-- 2. latest_customer_order
-- One row per customer containing the most recent observed order and order gap.

DROP TABLE IF EXISTS latest_customer_order;

CREATE TABLE latest_customer_order AS
SELECT
    o.user_id,
    o.eval_set AS latest_eval_set,
    o.order_number AS latest_order_number,
    o.days_since_prior_order AS latest_observed_gap
FROM std_orders o
JOIN (
    SELECT
        user_id,
        MAX(order_number) AS latest_order_number
    FROM std_orders
    GROUP BY user_id
) m
    ON o.user_id = m.user_id
   AND o.order_number = m.latest_order_number;

DROP INDEX IF EXISTS idx_latest_customer_order_user;

CREATE UNIQUE INDEX idx_latest_customer_order_user
ON latest_customer_order(user_id);

SELECT *
FROM latest_customer_order
LIMIT 10;


-- 3. Business Query 4
-- Compares each customer's latest observed gap with the expected gap
-- for their basket-size and ordering-cadence segment.

DROP TABLE IF EXISTS engagement_scoring;

CREATE TABLE engagement_scoring AS
SELECT
    s.user_id,
    s.basket_segment,
    s.frequency_segment,
    c.total_prior_orders,
    c.total_items,
    c.prior_gap_count,
    c.avg_basket_size,
    c.avg_days_between_orders,
    c.reorder_rate_pct,
    l.latest_eval_set,
    l.latest_observed_gap,
    e.expected_order_gap,
    ROUND(
        1.0 * l.latest_observed_gap / NULLIF(e.expected_order_gap, 0),
        6
    ) AS gap_vs_expected_ratio
FROM customer_segments s
JOIN m_customer_behavior c
    ON s.user_id = c.user_id
JOIN latest_customer_order l
    ON s.user_id = l.user_id
LEFT JOIN segment_expected_cadence e
    ON s.basket_segment = e.basket_segment
   AND s.frequency_segment = e.frequency_segment;

DROP INDEX IF EXISTS idx_engagement_scoring_user;

CREATE UNIQUE INDEX idx_engagement_scoring_user
ON engagement_scoring(user_id);


-- 4. customer_engagement
-- One row per customer with the final engagement status based on history,
-- the 30-day cap, and the validated slowdown thresholds.

DROP TABLE IF EXISTS customer_engagement;

CREATE TABLE customer_engagement AS
SELECT
    e.*,
    CASE
        WHEN e.total_prior_orders < 5
          OR e.prior_gap_count < 4
            THEN 'Insufficient History'

        WHEN e.latest_observed_gap = 30
            THEN 'Capped Gap - Review'

        WHEN e.latest_observed_gap IS NULL
          OR e.expected_order_gap IS NULL
          OR e.expected_order_gap <= 0
            THEN 'Not Assessable'

        WHEN e.gap_vs_expected_ratio <=
             (SELECT p75_ratio FROM slowdown_thresholds)
            THEN 'Stable'

        WHEN e.gap_vs_expected_ratio <=
             (SELECT p90_ratio FROM slowdown_thresholds)
            THEN 'Weakening'

        ELSE 'High Concern'
    END AS engagement_status
FROM engagement_scoring e;

DROP INDEX IF EXISTS idx_customer_engagement_user;

CREATE UNIQUE INDEX idx_customer_engagement_user
ON customer_engagement(user_id);


-- 5. submission_customer_decision
-- Final SQL decision table at one row per customer.
-- Includes customer segment dimensions, behavioral KPIs, latest-vs-expected cadence,
-- engagement status, and quality flags carried into the Python step.

DROP TABLE IF EXISTS submission_customer_decision;

CREATE TABLE submission_customer_decision AS
SELECT
    user_id,
    basket_segment,
    frequency_segment,
    total_prior_orders,
    prior_gap_count,
    avg_basket_size,
    avg_days_between_orders,
    reorder_rate_pct,
    latest_observed_gap,
    expected_order_gap,
    gap_vs_expected_ratio,
    engagement_status,

    CASE
        WHEN latest_observed_gap = 30 THEN 1
        ELSE 0
    END AS latest_gap_capped_flag,

    CASE
        WHEN engagement_status = 'Insufficient History' THEN 1
        ELSE 0
    END AS insufficient_history_flag,

    CASE
        WHEN engagement_status IN (
            'Stable',
            'Weakening',
            'High Concern'
        ) THEN 1
        ELSE 0
    END AS assessed_flag,

    CASE
        WHEN engagement_status IN (
            'Weakening',
            'High Concern'
        ) THEN 1
        ELSE 0
    END AS at_risk_flag

FROM customer_engagement;

DROP INDEX IF EXISTS idx_submission_customer_decision_user;

CREATE UNIQUE INDEX idx_submission_customer_decision_user
ON submission_customer_decision(user_id);


-- 6. submission_segment_risk
-- One row per basket x cadence segment showing status counts and
-- the share of assessed customers classified as Weakening or High Concern.

DROP TABLE IF EXISTS submission_segment_risk;

CREATE TABLE submission_segment_risk AS
SELECT
    basket_segment,
    frequency_segment,
    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN engagement_status = 'Stable' THEN 1
            ELSE 0
        END
    ) AS stable_customers,

    SUM(
        CASE
            WHEN engagement_status = 'Weakening' THEN 1
            ELSE 0
        END
    ) AS weakening_customers,

    SUM(
        CASE
            WHEN engagement_status = 'High Concern' THEN 1
            ELSE 0
        END
    ) AS high_concern_customers,

    SUM(
        CASE
            WHEN engagement_status = 'Capped Gap - Review' THEN 1
            ELSE 0
        END
    ) AS capped_review_customers,

    SUM(
        CASE
            WHEN engagement_status = 'Insufficient History' THEN 1
            ELSE 0
        END
    ) AS insufficient_history_customers,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN engagement_status IN (
                    'Weakening',
                    'High Concern'
                ) THEN 1
                ELSE 0
            END
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN engagement_status IN (
                        'Stable',
                        'Weakening',
                        'High Concern'
                    ) THEN 1
                    ELSE 0
                END
            ),
            0
        ),
        2
    ) AS pct_at_risk_among_assessed

FROM submission_customer_decision
GROUP BY
    basket_segment,
    frequency_segment;

SELECT *
FROM submission_segment_risk
ORDER BY
    frequency_segment,
    basket_segment;


-- 7. submission_engagement_status_summary
-- One row per engagement status summarizing customer count, share of the
-- customer base, latest observed gap, and expected gap.

DROP TABLE IF EXISTS submission_engagement_status_summary;

CREATE TABLE submission_engagement_status_summary AS
SELECT
    engagement_status,
    COUNT(*) AS customer_count,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM submission_customer_decision),
        2
    ) AS pct_of_customers,
    ROUND(AVG(latest_observed_gap), 2) AS avg_latest_gap,
    ROUND(AVG(expected_order_gap), 2) AS avg_expected_gap
FROM submission_customer_decision
GROUP BY engagement_status;

SELECT *
FROM submission_engagement_status_summary
ORDER BY
    CASE engagement_status
        WHEN 'Stable' THEN 1
        WHEN 'Weakening' THEN 2
        WHEN 'High Concern' THEN 3
        WHEN 'Capped Gap - Review' THEN 4
        WHEN 'Insufficient History' THEN 5
        ELSE 6
    END;


-- 8. submission_segment_context
-- One row per basket x cadence segment combining segment size,
-- share of the customer base, and at-risk rate among assessed customers.

DROP TABLE IF EXISTS submission_segment_context;

CREATE TABLE submission_segment_context AS
SELECT
    b.basket_segment,
    b.frequency_segment,
    b.basket_segment || ' / ' || b.frequency_segment AS segment_label,
    b.customer_count AS segment_customer_count,
    b.pct_of_customers AS pct_of_customer_base,
    r.pct_at_risk_among_assessed AS segment_pct_at_risk_among_assessed
FROM business_query_1_segments b
JOIN submission_segment_risk r
    ON b.basket_segment = r.basket_segment
   AND b.frequency_segment = r.frequency_segment;

SELECT *
FROM submission_segment_context
ORDER BY
    basket_segment,
    frequency_segment;


-- 9. submission_calibration_thresholds
-- Keeps the final calibration values in a simple table for reporting and export.

DROP TABLE IF EXISTS submission_calibration_thresholds;

CREATE TABLE submission_calibration_thresholds AS
SELECT *
FROM slowdown_thresholds;

SELECT *
FROM submission_calibration_thresholds;


-- 10. python_validation_input
-- One row per customer containing additive SQL totals that Python can
-- independently recompute and compare with the SQL results.

DROP TABLE IF EXISTS python_validation_input;

CREATE TABLE python_validation_input AS
SELECT
    user_id,
    COUNT(*) AS prior_orders,
    SUM(basket_size) AS total_items,
    COUNT(days_since_prior_order) AS valid_gap_count,
    SUM(days_since_prior_order) AS total_gap_days,
    SUM(reordered_items) AS reordered_items
FROM order_fact
GROUP BY user_id;

DROP INDEX IF EXISTS idx_python_validation_input_user;

CREATE UNIQUE INDEX idx_python_validation_input_user
ON python_validation_input(user_id);


-- 11. sql_validation_reference
-- Stores four headline SQL measures that are independently recalculated in Python.

DROP TABLE IF EXISTS sql_validation_reference;

CREATE TABLE sql_validation_reference AS
SELECT
    'total_prior_orders' AS metric,
    1.0 * SUM(prior_orders) AS sql_value
FROM python_validation_input

UNION ALL

SELECT
    'weighted_avg_basket_size',
    1.0 * SUM(total_items) / SUM(prior_orders)
FROM python_validation_input

UNION ALL

SELECT
    'avg_days_between_orders',
    1.0 * SUM(total_gap_days) / SUM(valid_gap_count)
FROM python_validation_input

UNION ALL

SELECT
    'overall_reorder_rate_pct',
    100.0 * SUM(reordered_items) / SUM(total_items)
FROM python_validation_input;

SELECT *
FROM sql_validation_reference;


-- 12. Final check
-- Confirms that the final decision table has exactly one row per customer.

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT user_id) AS unique_customers,
    COUNT(*) - COUNT(DISTINCT user_id) AS duplicate_customers
FROM submission_customer_decision;
