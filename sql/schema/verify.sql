-- 1. Show all tables
SHOW TABLES;

-- 2. Count dates (should be ~24,837 dates from 1959-2026)
SELECT COUNT(*) as total_dates FROM dim_date;

-- 3. Check sample dates
SELECT * FROM dim_date 
WHERE year = 2026 
ORDER BY full_date 
LIMIT 5;

-- 4. Verify all tables are empty (ready for data)
SELECT 
    'dim_customers' as table_name, COUNT(*) as row_count FROM dim_customers
UNION ALL
SELECT 'dim_products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'fact_customer_behavior', COUNT(*) FROM fact_customer_behavior
UNION ALL
SELECT 'fact_transactions', COUNT(*) FROM fact_transactions
UNION ALL
SELECT 'fact_economic_indicators', COUNT(*) FROM fact_economic_indicators
UNION ALL
SELECT 'customer_metrics', COUNT(*) FROM customer_metrics;

