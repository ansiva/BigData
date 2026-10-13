-- File 1: Loading Data


-- 1. Keeping the original imported tables

CREATE TABLE IF NOT EXISTS orders_raw AS
SELECT * FROM orders;

CREATE TABLE IF NOT EXISTS order_products__prior_raw AS
SELECT * FROM order_products__prior;

CREATE TABLE IF NOT EXISTS order_products__train_raw AS
SELECT * FROM order_products__train;

CREATE TABLE IF NOT EXISTS products_raw AS
SELECT * FROM products;

CREATE TABLE IF NOT EXISTS aisles_raw AS
SELECT * FROM aisles;

CREATE TABLE IF NOT EXISTS departments_raw AS
SELECT * FROM departments;


-- 2. Drop old indexes first
-- This makes sure the before-index timing test starts without indexes.

DROP INDEX IF EXISTS idx_prior_order_id;
DROP INDEX IF EXISTS idx_prior_product_id;
DROP INDEX IF EXISTS idx_prior_order_product;

DROP INDEX IF EXISTS idx_train_order_id;
DROP INDEX IF EXISTS idx_train_product_id;
DROP INDEX IF EXISTS idx_train_order_product;

DROP INDEX IF EXISTS idx_orders_order_id;
DROP INDEX IF EXISTS idx_orders_user_order_number;

DROP INDEX IF EXISTS idx_products_product_id;
DROP INDEX IF EXISTS idx_products_aisle_id;
DROP INDEX IF EXISTS idx_products_department_id;

DROP INDEX IF EXISTS idx_aisles_aisle_id;
DROP INDEX IF EXISTS idx_departments_department_id;


-- 3. Remove old standardized views

DROP VIEW IF EXISTS std_orders;
DROP VIEW IF EXISTS std_order_products_prior;
DROP VIEW IF EXISTS std_order_products_train;
DROP VIEW IF EXISTS std_products;
DROP VIEW IF EXISTS std_aisles;
DROP VIEW IF EXISTS std_departments;


-- 4. Remove the old working tables
-- The *_raw tables are kept as the original audit copies.

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_products__prior;
DROP TABLE IF EXISTS order_products__train;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS aisles;
DROP TABLE IF EXISTS departments;


-- 5. Rebuild orders with the correct column names and data types

CREATE TABLE orders (
    order_id               INTEGER,
    user_id                INTEGER,
    eval_set               TEXT,
    order_number           INTEGER,
    order_dow              INTEGER,
    order_hour_of_day      INTEGER,
    days_since_prior_order REAL
);

INSERT INTO orders
SELECT
    CAST(column1 AS INTEGER),
    CAST(column2 AS INTEGER),
    TRIM(column3),
    CAST(column4 AS INTEGER),
    CAST(column5 AS INTEGER),
    CAST(column6 AS INTEGER),
    CASE
        WHEN TRIM(COALESCE(column7, '')) = '' THEN NULL
        ELSE CAST(column7 AS REAL)
    END
FROM orders_raw
WHERE column1 <> 'order_id';


-- 6. Rebuild prior order products

CREATE TABLE order_products__prior (
    order_id          INTEGER,
    product_id        INTEGER,
    add_to_cart_order INTEGER,
    reordered         INTEGER
);

INSERT INTO order_products__prior
SELECT
    CAST(column1 AS INTEGER),
    CAST(column2 AS INTEGER),
    CAST(column3 AS INTEGER),
    CAST(column4 AS INTEGER)
FROM order_products__prior_raw
WHERE column1 <> 'order_id';


-- 7. Rebuild train order products

CREATE TABLE order_products__train (
    order_id          INTEGER,
    product_id        INTEGER,
    add_to_cart_order INTEGER,
    reordered         INTEGER
);

INSERT INTO order_products__train
SELECT
    CAST(column1 AS INTEGER),
    CAST(column2 AS INTEGER),
    CAST(column3 AS INTEGER),
    CAST(column4 AS INTEGER)
FROM order_products__train_raw
WHERE column1 <> 'order_id';


-- 8. Rebuild products

CREATE TABLE products (
    product_id    INTEGER,
    product_name  TEXT,
    aisle_id      INTEGER,
    department_id INTEGER
);

INSERT INTO products
SELECT
    CAST(column1 AS INTEGER),
    TRIM(column2),
    CAST(column3 AS INTEGER),
    CAST(column4 AS INTEGER)
FROM products_raw
WHERE column1 <> 'product_id';


-- 9. Rebuild aisles

CREATE TABLE aisles (
    aisle_id INTEGER,
    aisle    TEXT
);

INSERT INTO aisles
SELECT
    CAST(column1 AS INTEGER),
    TRIM(column2)
FROM aisles_raw
WHERE column1 <> 'aisle_id';


-- 10. Rebuild departments

CREATE TABLE departments (
    department_id INTEGER,
    department    TEXT
);

INSERT INTO departments
SELECT
    CAST(column1 AS INTEGER),
    TRIM(column2)
FROM departments_raw
WHERE column1 <> 'department_id';


-- 11. Create standardized views for the later SQL files

CREATE VIEW std_orders AS
SELECT
    order_id,
    user_id,
    eval_set,
    order_number,
    order_dow,
    order_hour_of_day,
    days_since_prior_order
FROM orders;


CREATE VIEW std_order_products_prior AS
SELECT
    order_id,
    product_id,
    add_to_cart_order,
    reordered
FROM order_products__prior;


CREATE VIEW std_order_products_train AS
SELECT
    order_id,
    product_id,
    add_to_cart_order,
    reordered
FROM order_products__train;


CREATE VIEW std_products AS
SELECT
    product_id,
    product_name,
    aisle_id,
    department_id
FROM products;


CREATE VIEW std_aisles AS
SELECT
    aisle_id,
    aisle
FROM aisles;


CREATE VIEW std_departments AS
SELECT
    department_id,
    department
FROM departments;


-- 12. Index performance test
-- Index keys:
-- order_id supports joins between orders and order-product tables.
-- product_id supports product joins and product-frequency analysis.
-- user_id + order_number supports customer order history.
-- aisle_id and department_id support category joins.




SELECT
    product_id,
    COUNT(*) AS freq
FROM order_products__prior
GROUP BY product_id
ORDER BY freq DESC;


/*
I got the output for this in 12.3 seconds
*/


-- 13. Create indexes

CREATE INDEX idx_prior_order_id
ON order_products__prior(order_id);

CREATE INDEX idx_prior_product_id
ON order_products__prior(product_id);

CREATE INDEX idx_prior_order_product
ON order_products__prior(order_id, product_id);


CREATE INDEX idx_train_order_id
ON order_products__train(order_id);

CREATE INDEX idx_train_product_id
ON order_products__train(product_id);

CREATE INDEX idx_train_order_product
ON order_products__train(order_id, product_id);


CREATE INDEX idx_orders_order_id
ON orders(order_id);

CREATE INDEX idx_orders_user_order_number
ON orders(user_id, order_number);


CREATE INDEX idx_products_product_id
ON products(product_id);

CREATE INDEX idx_products_aisle_id
ON products(aisle_id);

CREATE INDEX idx_products_department_id
ON products(department_id);


CREATE INDEX idx_aisles_aisle_id
ON aisles(aisle_id);

CREATE INDEX idx_departments_department_id
ON departments(department_id);


-- 14. Running the same product-frequency query after creating the index

SELECT
    product_id,
    COUNT(*) AS freq
FROM order_products__prior
GROUP BY product_id
ORDER BY freq DESC;

/*
Before it took 12.3 seconds
After indexing took just 1.58 seconds, but index creation took a lot of time in comparison
*/


-- 15. Check that fixing the imported tables did not remove any real rows
-- Comparing the working tables with the original raw imports
-- To confirm that only the header rows were removed and all actual data was preserved.

DROP TABLE IF EXISTS submission_source_row_counts;

CREATE TABLE submission_source_row_counts AS

SELECT
    'orders' AS table_name,
    (SELECT COUNT(*)
     FROM orders_raw
     WHERE column1 <> 'order_id') AS raw_data_rows,
    COUNT(*) AS corrected_rows
FROM orders

UNION ALL

SELECT
    'order_products__prior',
    (SELECT COUNT(*)
     FROM order_products__prior_raw
     WHERE column1 <> 'order_id'),
    COUNT(*)
FROM order_products__prior

UNION ALL

SELECT
    'order_products__train',
    (SELECT COUNT(*)
     FROM order_products__train_raw
     WHERE column1 <> 'order_id'),
    COUNT(*)
FROM order_products__train

UNION ALL

SELECT
    'products',
    (SELECT COUNT(*)
     FROM products_raw
     WHERE column1 <> 'product_id'),
    COUNT(*)
FROM products

UNION ALL

SELECT
    'aisles',
    (SELECT COUNT(*)
     FROM aisles_raw
     WHERE column1 <> 'aisle_id'),
    COUNT(*)
FROM aisles

UNION ALL

SELECT
    'departments',
    (SELECT COUNT(*)
     FROM departments_raw
     WHERE column1 <> 'department_id'),
    COUNT(*)
FROM departments;


-- 16. Final row-count check
-- Expected difference = 0 for all six tables.

SELECT
    table_name,
    raw_data_rows,
    corrected_rows,
    raw_data_rows - corrected_rows AS difference
FROM submission_source_row_counts;


/*
Expected corrected row counts:

orders                   3,421,083
order_products__prior   32,434,489
order_products__train    1,384,617
products                    49,688
aisles                          134
departments                      21

What we found:
The imported CSVs had generic column names and their header rows inside the data.
The six working tables were rebuilt with correct names and data types.
All actual source rows were preserved. So we had to make the first row the headers in this loading process.
*/