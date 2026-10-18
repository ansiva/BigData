/* FILE 2: DATA QUALITY CHECKS

   File 1 corrected the CSV loading issue:

   These checks confirm the corrected data is reliable for analysis.

 
*/


/* CHECK 0 — FILE 1 Correction
   Confirms all real rows were kept after fixing the imports.
   Expected: difference = 0 for all six tables. */

SELECT
  table_name,
  raw_data_rows,
  corrected_rows,
  raw_data_rows - corrected_rows AS difference,
  CASE
    WHEN raw_data_rows = corrected_rows THEN 'NO'
    ELSE 'YES'
  END AS needs_review
FROM submission_source_row_counts;

/* Finding: corrected tables matched the original data row counts;
   no rows were lost while fixing the column names and header rows. */


/* CHECK 1 — DUPLICATE BUSINESS KEYS
   Expected: 0 for every key. */

SELECT 'orders.order_id' AS item_checked, COUNT(*) AS issue_count,
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END AS needs_review
FROM (
  SELECT order_id
  FROM orders
  GROUP BY order_id
  HAVING COUNT(*)>1
)

UNION ALL

SELECT 'prior (order_id, product_id)', COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END
FROM (
  SELECT order_id, product_id
  FROM order_products__prior
  GROUP BY order_id, product_id
  HAVING COUNT(*)>1
)

UNION ALL

SELECT 'train (order_id, product_id)', COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END
FROM (
  SELECT order_id, product_id
  FROM order_products__train
  GROUP BY order_id, product_id
  HAVING COUNT(*)>1
)

UNION ALL

SELECT 'products.product_id', COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END
FROM (
  SELECT product_id
  FROM products
  GROUP BY product_id
  HAVING COUNT(*)>1
)

UNION ALL

SELECT 'aisles.aisle_id', COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END
FROM (
  SELECT aisle_id
  FROM aisles
  GROUP BY aisle_id
  HAVING COUNT(*)>1
)

UNION ALL

SELECT 'departments.department_id', COUNT(*),
       CASE WHEN COUNT(*)=0 THEN 'NO' ELSE 'YES' END
FROM (
  SELECT department_id
  FROM departments
  GROUP BY department_id
  HAVING COUNT(*)>1
);

/* Finding: no duplicate business keys were found;
   no correction was needed. */


/* CHECK 2 — ORPHANED FOREIGN KEYS
   Checks whether referenced orders and products exist.
   Expected: all counts = 0. */

SELECT
  SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END)
    AS prior_missing_product,

  SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)
    AS prior_missing_order,

  CASE
    WHEN
      SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END)=0
      AND
      SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)=0
    THEN 'NO'
    ELSE 'YES'
  END AS needs_review

FROM order_products__prior op

LEFT JOIN products p
  ON p.product_id = op.product_id

LEFT JOIN orders o
  ON o.order_id = op.order_id;


/* Train order-product relationships. */

SELECT
  SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END)
    AS train_missing_product,

  SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)
    AS train_missing_order,

  CASE
    WHEN
      SUM(CASE WHEN p.product_id IS NULL THEN 1 ELSE 0 END)=0
      AND
      SUM(CASE WHEN o.order_id IS NULL THEN 1 ELSE 0 END)=0
    THEN 'NO'
    ELSE 'YES'
  END AS needs_review

FROM order_products__train op

LEFT JOIN products p
  ON p.product_id = op.product_id

LEFT JOIN orders o
  ON o.order_id = op.order_id;


/* Product aisle and department relationships. */

SELECT
  SUM(CASE WHEN a.aisle_id IS NULL THEN 1 ELSE 0 END)
    AS products_missing_aisle,

  SUM(CASE WHEN d.department_id IS NULL THEN 1 ELSE 0 END)
    AS products_missing_department,

  CASE
    WHEN
      SUM(CASE WHEN a.aisle_id IS NULL THEN 1 ELSE 0 END)=0
      AND
      SUM(CASE WHEN d.department_id IS NULL THEN 1 ELSE 0 END)=0
    THEN 'NO'
    ELSE 'YES'
  END AS needs_review

FROM products p

LEFT JOIN aisles a
  ON a.aisle_id = p.aisle_id

LEFT JOIN departments d
  ON d.department_id = p.department_id;

/* Finding: no orphaned foreign keys were found;
   no correction was needed. */


/* CHECK 3 — EVAL_SET RECONCILIATION
   Prior and train order counts should match their product files.
   Test is informational because no test product table was supplied. */

SELECT
  'prior' AS eval_set,

  (SELECT COUNT(*)
   FROM orders
   WHERE eval_set='prior') AS headers,

  (SELECT COUNT(DISTINCT order_id)
   FROM order_products__prior) AS detail_orders,

  (SELECT COUNT(*)
   FROM orders
   WHERE eval_set='prior')
  -
  (SELECT COUNT(DISTINCT order_id)
   FROM order_products__prior) AS difference,

  CASE
    WHEN
      (SELECT COUNT(*)
       FROM orders
       WHERE eval_set='prior')
      =
      (SELECT COUNT(DISTINCT order_id)
       FROM order_products__prior)
    THEN 'NO'
    ELSE 'YES'
  END AS needs_review

UNION ALL

SELECT
  'train',

  (SELECT COUNT(*)
   FROM orders
   WHERE eval_set='train'),

  (SELECT COUNT(DISTINCT order_id)
   FROM order_products__train),

  (SELECT COUNT(*)
   FROM orders
   WHERE eval_set='train')
  -
  (SELECT COUNT(DISTINCT order_id)
   FROM order_products__train),

  CASE
    WHEN
      (SELECT COUNT(*)
       FROM orders
       WHERE eval_set='train')
      =
      (SELECT COUNT(DISTINCT order_id)
       FROM order_products__train)
    THEN 'NO'
    ELSE 'YES'
  END;


/* Test orders are expected to have no supplied product-detail file. */

SELECT
  COUNT(*) AS test_orders,
  'INFORMATIONAL - no test product-detail table supplied' AS note
FROM orders
WHERE eval_set='test';

/* Finding: prior and train reconciled exactly.
   Test orders were retained as an expected holdout,
   not treated as missing data. */


/* CHECK 4 — AISLE / DEPARTMENT QUALITY
   Checks blank names and placeholder categories.
   Blank names should be 0. */

SELECT
  (SELECT COUNT(*)
   FROM aisles
   WHERE aisle IS NULL OR TRIM(aisle)='')
    AS blank_aisles,

  (SELECT COUNT(*)
   FROM departments
   WHERE department IS NULL OR TRIM(department)='')
    AS blank_departments,

  (SELECT COUNT(*)
   FROM products
   WHERE product_name IS NULL OR TRIM(product_name)='')
    AS blank_products;


/* Shows placeholder categories instead of deleting them. */

SELECT
  TRIM(a.aisle) AS aisle,
  TRIM(d.department) AS department,
  COUNT(*) AS product_count,
  'RETAIN' AS treatment

FROM products p

JOIN aisles a
  ON a.aisle_id = p.aisle_id

JOIN departments d
  ON d.department_id = p.department_id

WHERE
  LOWER(TRIM(a.aisle)) IN ('missing','other')
  OR
  LOWER(TRIM(d.department)) IN ('missing','other')

GROUP BY
  TRIM(a.aisle),
  TRIM(d.department)

ORDER BY product_count DESC;

/* Finding: no blank names were found.
   Placeholder categories were retained so totals and denominators
   were not changed. */


/* CHECK 5 — RANGE / VALIDITY
   Checks whether important numeric values are valid.
   Expected: all invalid counts = 0. */

SELECT
  SUM(CASE WHEN order_dow NOT BETWEEN 0 AND 6
           THEN 1 ELSE 0 END) AS invalid_dow,

  SUM(CASE WHEN order_hour_of_day NOT BETWEEN 0 AND 23
           THEN 1 ELSE 0 END) AS invalid_hour,

  SUM(CASE WHEN days_since_prior_order < 0
           THEN 1 ELSE 0 END) AS negative_gap,

  SUM(CASE WHEN order_number < 1
           THEN 1 ELSE 0 END) AS invalid_order_number

FROM orders;


/* Prior order-product values. */

SELECT
  SUM(CASE WHEN reordered NOT IN (0,1)
           THEN 1 ELSE 0 END) AS invalid_prior_reordered,

  SUM(CASE WHEN add_to_cart_order < 1
           THEN 1 ELSE 0 END) AS invalid_prior_cart_position

FROM order_products__prior;


/* Train order-product values. */

SELECT
  SUM(CASE WHEN reordered NOT IN (0,1)
           THEN 1 ELSE 0 END) AS invalid_train_reordered,

  SUM(CASE WHEN add_to_cart_order < 1
           THEN 1 ELSE 0 END) AS invalid_train_cart_position

FROM order_products__train;

/* Finding: no invalid ranges or codes were found;
   no correction was needed. */


/* CHECK 6 — DAYS_SINCE_PRIOR_ORDER
   First-order NULLs are valid.
   Later orders should have a recorded gap.
   Also checks how often the gap reaches the 30-day recording limit. */

SELECT
  SUM(CASE
        WHEN order_number=1
         AND days_since_prior_order IS NOT NULL
        THEN 1 ELSE 0
      END) AS first_nonnull,

  SUM(CASE
        WHEN order_number>1
         AND days_since_prior_order IS NULL
        THEN 1 ELSE 0
      END) AS later_missing,

  SUM(CASE
        WHEN order_number=1
         AND days_since_prior_order IS NULL
        THEN 1 ELSE 0
      END) AS first_nulls,

  COUNT(DISTINCT user_id) AS distinct_users,

  SUM(CASE
        WHEN days_since_prior_order=30
        THEN 1 ELSE 0
      END) AS gaps_at_30,

  ROUND(
    100.0 *
    SUM(CASE
          WHEN days_since_prior_order=30
          THEN 1 ELSE 0
        END)
    /
    COUNT(days_since_prior_order),
    2
  ) AS pct_measured_gaps_at_30

FROM orders;

/* First-order NULL gaps were valid and were kept as NULL.
   No later-order gaps were unexpectedly missing.
   11.49% of all measured order gaps were recorded at the 30-day limit,. */


/* CHECK 7 — ORDER SEQUENCE INTEGRITY
   Checks that every customer's order sequence starts at 1
   and continues without gaps or duplicate order numbers.
   Expected: 0 users with sequence issues. */

SELECT
  COUNT(*) AS users_with_sequence_issue,

  CASE
    WHEN COUNT(*)=0 THEN 'NO'
    ELSE 'YES'
  END AS needs_review

FROM (
  SELECT user_id

  FROM orders

  GROUP BY user_id

  HAVING
       MIN(order_number)<>1
    OR MAX(order_number)<>COUNT(*)
    OR COUNT(DISTINCT order_number)<>COUNT(*)
);

/* No customer order-sequence issues were found;
   no correction was needed. */


/* 

  Overall finding:
   No duplicate keys, orphan keys, reconciliation errors,
   invalid values, unexpected NULL patterns, or order-sequence issues were found.
   
   



   Placeholder categories were retained rather than deleted.
   First-order NULL gaps were kept because they are structurally valid.
   Test orders were treated as an expected holdout.
   The 30-day order-gap limit was carried forward as a quality flag
   in the engagement analysis.
*/