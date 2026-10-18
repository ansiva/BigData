-- File 3: Descriptive Statistics


-- This file creates descriptive measures that summarize
-- customer ordering behavior before the engagement analysis begins.


-- Base Table 1: One row per prior order
-- Used to calculate basket size, reorder behavior, order timing,
-- and customer shopping history.

DROP TABLE IF EXISTS order_fact;

CREATE TABLE order_fact AS
SELECT
    o.order_id,
    o.user_id,
    o.order_number,
    o.order_dow,
    o.order_hour_of_day,
    o.days_since_prior_order,
    COUNT(op.product_id) AS basket_size,
    SUM(op.reordered) AS reordered_items
FROM orders o
JOIN order_products__prior op
    ON o.order_id = op.order_id
WHERE o.eval_set = 'prior'
GROUP BY
    o.order_id,
    o.user_id,
    o.order_number,
    o.order_dow,
    o.order_hour_of_day,
    o.days_since_prior_order;


DROP INDEX IF EXISTS idx_order_fact_order;

CREATE UNIQUE INDEX idx_order_fact_order
ON order_fact(order_id);


DROP INDEX IF EXISTS idx_order_fact_user_order;

CREATE INDEX idx_order_fact_user_order
ON order_fact(user_id, order_number);


-- Check the order-level table.
-- Expected: 3,214,874 prior orders.

SELECT
    COUNT(*) AS order_fact_rows,
    COUNT(DISTINCT user_id) AS distinct_customers
FROM order_fact;



-- Base Table 2: One row per product purchased in a prior order
-- Used for product, aisle, department, and reorder-rate measures.

DROP TABLE IF EXISTS line_item_fact;

CREATE TABLE line_item_fact AS
SELECT
    op.order_id,
    op.product_id,
    p.aisle_id,
    p.department_id,
    op.reordered
FROM order_products__prior op
JOIN products p
    ON op.product_id = p.product_id;


DROP INDEX IF EXISTS idx_lif_product;

CREATE INDEX idx_lif_product
ON line_item_fact(product_id);


DROP INDEX IF EXISTS idx_lif_aisle;

CREATE INDEX idx_lif_aisle
ON line_item_fact(aisle_id);


DROP INDEX IF EXISTS idx_lif_department;

CREATE INDEX idx_lif_department
ON line_item_fact(department_id);


-- Check the product-level table.
-- Expected: 32,434,489 prior-order product rows.

SELECT COUNT(*) AS line_item_fact_rows
FROM line_item_fact;



-- Measure 1: Total prior orders and distinct customers
-- Describes the overall size of the historical customer base.
-- Also shows total purchased items and average prior orders per customer.

DROP VIEW IF EXISTS m_totals;

CREATE VIEW m_totals AS
SELECT
    COUNT(*) AS total_orders,
    COUNT(DISTINCT user_id) AS distinct_users,
    SUM(basket_size) AS total_line_items,
    ROUND(
        1.0 * COUNT(*) / COUNT(DISTINCT user_id),
        2
    ) AS avg_orders_per_user
FROM order_fact;

SELECT * FROM m_totals;


-- 3214874 total orders and 206209 users 


-- Measure 2: Average basket size
-- Shows how many products customers purchase in a typical prior order.

DROP VIEW IF EXISTS m_basket_size;

CREATE VIEW m_basket_size AS
SELECT
    ROUND(AVG(basket_size), 2) AS avg_basket_size,
    MIN(basket_size) AS min_basket_size,
    MAX(basket_size) AS max_basket_size
FROM order_fact;

SELECT * FROM m_basket_size;

-- Basket_Size: 10.09

-- Measure 3A: Overall reorder rate
-- Reordered products divided by all purchased products.
-- This shows how much prior shopping consists of repeat purchases.

DROP VIEW IF EXISTS m_reorder_rate;

CREATE VIEW m_reorder_rate AS
SELECT
    SUM(reordered_items) AS reordered_items,
    SUM(basket_size) AS total_items,
    ROUND(
        100.0 * SUM(reordered_items) / SUM(basket_size),
        2
    ) AS reorder_rate_pct
FROM order_fact;

SELECT * FROM m_reorder_rate;

--Reorder Rate: 58.97%

-- Measure 3B: Reorder rate by department
-- Shows which departments contain more repeat purchasing behavior.

DROP VIEW IF EXISTS m_reorder_by_department;

CREATE VIEW m_reorder_by_department AS
SELECT
    d.department,
    COUNT(*) AS line_items,
    ROUND(
        100.0 * SUM(l.reordered) / COUNT(*),
        2
    ) AS reorder_rate_pct
FROM line_item_fact l
JOIN departments d
    ON l.department_id = d.department_id
GROUP BY d.department;

SELECT *
FROM m_reorder_by_department
ORDER BY reorder_rate_pct DESC;



-- Measure 3C: Reorder rate by aisle
-- Gives a more detailed view of repeat purchasing within departments.

DROP VIEW IF EXISTS m_reorder_by_aisle;

CREATE VIEW m_reorder_by_aisle AS
SELECT
    a.aisle,
    d.department,
    COUNT(*) AS line_items,
    ROUND(
        100.0 * SUM(l.reordered) / COUNT(*),
        2
    ) AS reorder_rate_pct
FROM line_item_fact l
JOIN aisles a
    ON l.aisle_id = a.aisle_id
JOIN departments d
    ON l.department_id = d.department_id
GROUP BY
    a.aisle,
    d.department;

SELECT *
FROM m_reorder_by_aisle
ORDER BY reorder_rate_pct DESC;



-- Measure 4: Average days between orders
-- Describes the historical ordering cadence of prior orders.
-- First-order NULL gaps are excluded automatically.
-- pct_at_cap_30 refers only to the prior-order analytical history.
-- The full orders-table data-quality check in File 2 showed 11.49% at the 30-day limit.

DROP VIEW IF EXISTS m_days_between_orders;

CREATE VIEW m_days_between_orders AS
SELECT
    COUNT(days_since_prior_order) AS gaps_measured,
    ROUND(
        AVG(days_since_prior_order),
        2
    ) AS avg_days_between_orders,
    MIN(days_since_prior_order) AS min_gap,
    MAX(days_since_prior_order) AS max_gap,
    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN days_since_prior_order = 30 THEN 1
                ELSE 0
            END
        )
        /
        COUNT(days_since_prior_order),
        2
    ) AS pct_at_cap_30
FROM order_fact;

SELECT * FROM m_days_between_orders;



-- Measure 5A: Order volume by day of week
-- Shows when customers place prior orders during the week.
-- order_dow uses the source values 0 through 6.

DROP VIEW IF EXISTS m_volume_by_dow;

CREATE VIEW m_volume_by_dow AS
SELECT
    order_dow,
    COUNT(*) AS orders,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM order_fact),
        2
    ) AS pct_of_orders,
    ROUND(
        AVG(basket_size),
        2
    ) AS avg_basket_size
FROM order_fact
GROUP BY order_dow;

SELECT *
FROM m_volume_by_dow
ORDER BY order_dow;



-- Measure 5B: Order volume by hour of day
-- Shows the hours when customers most often place orders.

DROP VIEW IF EXISTS m_volume_by_hour;

CREATE VIEW m_volume_by_hour AS
SELECT
    order_hour_of_day,
    COUNT(*) AS orders,
    ROUND(
        100.0 * COUNT(*) /
        (SELECT COUNT(*) FROM order_fact),
        2
    ) AS pct_of_orders,
    ROUND(
        AVG(basket_size),
        2
    ) AS avg_basket_size
FROM order_fact
GROUP BY order_hour_of_day;

SELECT *
FROM m_volume_by_hour
ORDER BY order_hour_of_day;



-- Measure 6: Top products by prior-order frequency
-- Shows the most frequently purchased products and their share of all prior orders.
-- Reorder rate is included to show whether these products are also commonly repurchased.

DROP VIEW IF EXISTS m_top_products;

CREATE VIEW m_top_products AS
SELECT
    p.product_name,
    d.department,
    COUNT(DISTINCT l.order_id) AS orders_containing_product,
    ROUND(
        100.0 * COUNT(DISTINCT l.order_id)
        / (SELECT COUNT(*) FROM order_fact),
        3
    ) AS pct_of_all_prior_orders,
    ROUND(
        100.0 * SUM(l.reordered) / COUNT(*),
        2
    ) AS reorder_rate_pct
FROM line_item_fact l
JOIN products p
    ON l.product_id = p.product_id
JOIN departments d
    ON p.department_id = d.department_id
GROUP BY
    l.product_id,
    p.product_name,
    d.department;

SELECT *
FROM m_top_products
ORDER BY orders_containing_product DESC
LIMIT 10;



-- Measure 7: Customer shopping summary
-- One row per customer showing their usual historical shopping behavior.
-- This measure is reused in File 4 for segmentation and expected cadence.

DROP VIEW IF EXISTS m_customer_behavior;

CREATE VIEW m_customer_behavior AS
SELECT
    user_id,
    COUNT(*) AS total_prior_orders,
    SUM(basket_size) AS total_items,
    COUNT(days_since_prior_order) AS prior_gap_count,
    ROUND(
        AVG(basket_size),
        2
    ) AS avg_basket_size,
    ROUND(
        AVG(days_since_prior_order),
        2
    ) AS avg_days_between_orders,
    ROUND(
        100.0 * SUM(reordered_items) /
        NULLIF(SUM(basket_size), 0),
        2
    ) AS reorder_rate_pct
FROM order_fact
GROUP BY user_id;

SELECT *
FROM m_customer_behavior
ORDER BY user_id
LIMIT 10;



-- Measure 8: Customer basket-size distribution
-- Supports the Small / Medium / Large basket thresholds used in File 4.
-- Percentiles show how average basket size is distributed across customers.

DROP VIEW IF EXISTS m_basket_distribution;

CREATE VIEW m_basket_distribution AS
WITH ranked AS (
    SELECT
        avg_basket_size,
        NTILE(100) OVER (
            ORDER BY avg_basket_size
        ) AS percentile
    FROM m_customer_behavior
)
SELECT
    ROUND(MIN(avg_basket_size), 2) AS minimum,
    ROUND(AVG(avg_basket_size), 2) AS mean,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 25 THEN avg_basket_size
            END
        ),
        2
    ) AS p25,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 50 THEN avg_basket_size
            END
        ),
        2
    ) AS median,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 75 THEN avg_basket_size
            END
        ),
        2
    ) AS p75,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 90 THEN avg_basket_size
            END
        ),
        2
    ) AS p90,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 95 THEN avg_basket_size
            END
        ),
        2
    ) AS p95,
    ROUND(MAX(avg_basket_size), 2) AS maximum
FROM ranked;

SELECT * FROM m_basket_distribution;



-- Measure 9: Customer ordering-cadence distribution
-- Supports the Frequent / Regular / Infrequent thresholds used in File 4.
-- Percentiles show how average days between orders vary across customers.

DROP VIEW IF EXISTS m_cadence_distribution;

CREATE VIEW m_cadence_distribution AS
WITH ranked AS (
    SELECT
        avg_days_between_orders,
        NTILE(100) OVER (
            ORDER BY avg_days_between_orders
        ) AS percentile
    FROM m_customer_behavior
    WHERE avg_days_between_orders IS NOT NULL
)
SELECT
    ROUND(MIN(avg_days_between_orders), 2) AS minimum,
    ROUND(AVG(avg_days_between_orders), 2) AS mean,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 25 THEN avg_days_between_orders
            END
        ),
        2
    ) AS p25,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 50 THEN avg_days_between_orders
            END
        ),
        2
    ) AS median,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 75 THEN avg_days_between_orders
            END
        ),
        2
    ) AS p75,
    ROUND(
        AVG(
            CASE
                WHEN percentile = 90 THEN avg_days_between_orders
            END
        ),
        2
    ) AS p90,
    ROUND(MAX(avg_days_between_orders), 2) AS maximum
FROM ranked;

SELECT * FROM m_cadence_distribution;



-- Final expected headline values:
--
-- Total prior orders:      3,214,874
-- Distinct customers:        206,209
-- Total prior line items:  32,434,489
-- Average basket size:          10.09
-- Average days between orders:  10.71
-- Overall reorder rate:         58.97%