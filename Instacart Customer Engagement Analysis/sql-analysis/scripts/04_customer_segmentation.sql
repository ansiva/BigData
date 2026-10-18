
-- File 4: Customer Segmentation and Expected Cadence
-- Run after File 3.

-- Customer segments:
-- Basket size: Small <= 8, Medium 9-17, Large >= 18
-- Ordering cadence: Frequent <= 9 days, Regular 10-20 days, Infrequent > 20 days




-- Business Query 1: How are customers distributed across the 9 behavior groups?
-- Business Query 2: How does basket size compare with ordering cadence?
-- Business Query 3: What is the expected order gap for each behavior group?


--1. Create Customer Segments
-- Grain: one row per customer.
--
-- Each customer is assigned one basket-size segment and one
-- ordering-cadence segment using their historical averages from File 3.

-- customer_segments: One row per customer, assigning a basket-size segment and ordering-cadence segment from historical behavior.
DROP TABLE IF EXISTS customer_segments;

CREATE TABLE customer_segments AS
SELECT
    user_id,
    CASE
        WHEN avg_basket_size <= 8 THEN 'Small'
        WHEN avg_basket_size < 18 THEN 'Medium'
        ELSE 'Large'
    END AS basket_segment,
    CASE
        WHEN avg_days_between_orders IS NULL THEN 'Unknown'
        WHEN avg_days_between_orders <= 9 THEN 'Frequent'
        WHEN avg_days_between_orders <= 20 THEN 'Regular'
        ELSE 'Infrequent'
    END AS frequency_segment
FROM m_customer_behavior;

DROP INDEX IF EXISTS idx_customer_segments_user;
CREATE UNIQUE INDEX idx_customer_segments_user
ON customer_segments(user_id);

DROP INDEX IF EXISTS idx_customer_segments_group;
CREATE INDEX idx_customer_segments_group
ON customer_segments(basket_segment, frequency_segment);

SELECT *
FROM customer_segments
ORDER BY user_id
LIMIT 10;


-- Business Query 1: Customer Distribution Across Behavior Groups
--
-- Shows the number and percentage of customers in each basket x cadence group.
-- Additional averages help describe the behavior of customers inside each group.
--
-- This helps us understand the size and characteristics of the segments
-- before using them as comparison groups.

-- business_query_1_segments: One row per basket x cadence group, summarizing the size and average behavior of the 9 customer segments.
DROP TABLE IF EXISTS business_query_1_segments;

CREATE TABLE business_query_1_segments AS
SELECT
    s.basket_segment,
    s.frequency_segment,
    COUNT(*) AS customer_count,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM customer_segments),
        2
    ) AS pct_of_customers,
    ROUND(AVG(c.avg_basket_size), 2) AS avg_basket_size,
    ROUND(AVG(c.avg_days_between_orders), 2) AS avg_days_between_orders,
    ROUND(AVG(c.total_prior_orders), 2) AS avg_prior_orders_per_customer,
    ROUND(AVG(c.reorder_rate_pct), 2) AS avg_reorder_rate_pct
FROM customer_segments s
JOIN m_customer_behavior c
    ON s.user_id = c.user_id
GROUP BY
    s.basket_segment,
    s.frequency_segment;

SELECT *
FROM business_query_1_segments
ORDER BY
    basket_segment,
    frequency_segment;


-- Business Query 2: Compare basket size with ordering cadence
-- Shows the number and percentage of customers in each basket x cadence group.
-- Additional averages help describe the behavior of customers inside each group.

-- This helps us understand the size and characteristics of the segments
-- before using them as comparison groups.

-- business_query_2_basket_cadence: One row per basket-size group, comparing ordering cadence and other customer behavior across Small, Medium, and Large baskets.
DROP TABLE IF EXISTS business_query_2_basket_cadence;

CREATE TABLE business_query_2_basket_cadence AS
SELECT
    s.basket_segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(c.avg_basket_size), 2) AS avg_basket_size,
    ROUND(AVG(c.avg_days_between_orders), 2) AS avg_days_between_orders,
    ROUND(AVG(c.total_prior_orders), 2) AS avg_prior_orders_per_customer,
    ROUND(AVG(c.reorder_rate_pct), 2) AS avg_reorder_rate_pct,
    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN s.frequency_segment = 'Frequent' THEN 1
                ELSE 0
            END
        ) / COUNT(*),
        2
    ) AS pct_frequent_customers
FROM customer_segments s
JOIN m_customer_behavior c
    ON s.user_id = c.user_id
GROUP BY s.basket_segment;

SELECT *
FROM business_query_2_basket_cadence
ORDER BY basket_segment;


--Business Query 3: Expected Cadence by Behavior Group
--
-- Creates one benchmark row for each of the 9 basket x cadence groups.
--
-- Expected order gap is the MEDIAN of customer historical average gaps
-- within the eligible comparison group.
--
-- Median is used instead of the mean for the final benchmark because
-- it is less affected by unusually short or long customer ordering gaps.
--
-- The two middle observations are averaged so the calculation works
-- correctly for groups with either an odd or even number of customers.
--
-- UNION ALL is used to calculate the same benchmark separately
-- for each of the 9 defined behavior groups.



--Select Customers With Enough History for the Benchmark
--
-- Expected cadence should be based on customers with enough historical
-- behavior to represent a meaningful shopping pattern.
--
-- Eligibility:
--   At least 5 prior orders
--   At least 4 measured prior-order gaps
--   A valid historical average order gap
--
-- Customers who do not meet these requirements are not deleted.
-- They remain in the customer base and are handled later as
-- Insufficient History in File 5.

-- eligible_segment_customers: One row per customer with enough historical orders and measured gaps to contribute to the expected-cadence benchmark.
DROP TABLE IF EXISTS eligible_segment_customers;

CREATE TABLE eligible_segment_customers AS
SELECT
    s.user_id,
    s.basket_segment,
    s.frequency_segment,
    c.avg_basket_size,
    c.avg_days_between_orders,
    c.total_prior_orders
FROM customer_segments s
JOIN m_customer_behavior c
    ON s.user_id = c.user_id
WHERE c.total_prior_orders >= 5
  AND c.prior_gap_count >= 4
  AND c.avg_days_between_orders IS NOT NULL;

DROP INDEX IF EXISTS idx_eligible_segment_gap;
CREATE INDEX idx_eligible_segment_gap
ON eligible_segment_customers(
    basket_segment,
    frequency_segment,
    avg_days_between_orders
);




-- segment_expected_cadence: One row per behavior group, storing the benchmark metrics and median expected order gap used in File 5.
DROP TABLE IF EXISTS segment_expected_cadence;

CREATE TABLE segment_expected_cadence AS
SELECT
    'Small' AS basket_segment,
    'Frequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Frequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Frequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Small'
  AND frequency_segment = 'Frequent'

UNION ALL

SELECT
    'Small' AS basket_segment,
    'Regular' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Regular'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Regular'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Small'
  AND frequency_segment = 'Regular'

UNION ALL

SELECT
    'Small' AS basket_segment,
    'Infrequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Infrequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Small'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Small'
                      AND frequency_segment = 'Infrequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Small'
  AND frequency_segment = 'Infrequent'

UNION ALL

SELECT
    'Medium' AS basket_segment,
    'Frequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Frequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Frequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Medium'
  AND frequency_segment = 'Frequent'

UNION ALL

SELECT
    'Medium' AS basket_segment,
    'Regular' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Regular'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Regular'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Medium'
  AND frequency_segment = 'Regular'

UNION ALL

SELECT
    'Medium' AS basket_segment,
    'Infrequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Infrequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Medium'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Medium'
                      AND frequency_segment = 'Infrequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Medium'
  AND frequency_segment = 'Infrequent'

UNION ALL

SELECT
    'Large' AS basket_segment,
    'Frequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Frequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Frequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Frequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Large'
  AND frequency_segment = 'Frequent'

UNION ALL

SELECT
    'Large' AS basket_segment,
    'Regular' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Regular'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Regular'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Regular'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Large'
  AND frequency_segment = 'Regular'

UNION ALL

SELECT
    'Large' AS basket_segment,
    'Infrequent' AS frequency_segment,
    COUNT(*) AS benchmark_customers,
    ROUND(AVG(avg_basket_size), 2) AS segment_avg_basket_size,
    ROUND(AVG(total_prior_orders), 2) AS segment_avg_orders,
    ROUND(AVG(avg_days_between_orders), 2) AS mean_order_gap,
    ROUND(
        (
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT (COUNT(*) - 1) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Infrequent'
                )
            )
            +
            (
                SELECT avg_days_between_orders
                FROM eligible_segment_customers
                WHERE basket_segment = 'Large'
                  AND frequency_segment = 'Infrequent'
                ORDER BY avg_days_between_orders
                LIMIT 1
                OFFSET (
                    SELECT COUNT(*) / 2
                    FROM eligible_segment_customers
                    WHERE basket_segment = 'Large'
                      AND frequency_segment = 'Infrequent'
                )
            )
        ) / 2.0,
        2
    ) AS expected_order_gap
FROM eligible_segment_customers
WHERE basket_segment = 'Large'
  AND frequency_segment = 'Infrequent';


SELECT *
FROM segment_expected_cadence
ORDER BY
    CASE basket_segment
        WHEN 'Small' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Large' THEN 3
        ELSE 4
    END,
    CASE frequency_segment
        WHEN 'Frequent' THEN 1
        WHEN 'Regular' THEN 2
        WHEN 'Infrequent' THEN 3
        ELSE 4
    END;


/* File 4 output:
   customer_segments = one row per customer
   business_query_1_segments = 9 customer behavior groups
   business_query_2_basket_cadence = basket-level comparison
   segment_expected_cadence = expected order gap for each of the 9 groups
*/
