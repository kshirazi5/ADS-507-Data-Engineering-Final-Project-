-- ============================================================================
-- E-Commerce Data Pipeline - Database Schema (Updated with Enriched Features)
-- ============================================================================

-- Drop existing tables 
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS fact_transactions;
DROP TABLE IF EXISTS fact_customer_behavior;
DROP TABLE IF EXISTS fact_economic_indicators;
DROP TABLE IF EXISTS customer_metrics;
DROP TABLE IF EXISTS dim_customers;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS pipeline_logs;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Customers dimension (Updated with segments and tiers)
CREATE TABLE dim_customers (
    customer_key INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT UNIQUE NOT NULL,
    gender VARCHAR(10),
    age INT,
    age_segment VARCHAR(50),      
    city VARCHAR(50),
    membership_type VARCHAR(20),
    spending_tier VARCHAR(20),     
    engagement_score DECIMAL(4,2), 
    is_valid_record BOOLEAN,       
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customer_id (customer_id),
    INDEX idx_age_segment (age_segment),
    INDEX idx_spending_tier (spending_tier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Products dimension
CREATE TABLE dim_products (
    product_key INT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    unit_price DECIMAL(10,2),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_code (stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Date dimension
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    week_of_year INT NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    INDEX idx_full_date (full_date),
    INDEX idx_year_month (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Transactions fact (Updated for Returns and Outliers)
CREATE TABLE fact_transactions (
    transaction_key INT AUTO_INCREMENT PRIMARY KEY,
    invoice_no VARCHAR(50) NOT NULL,
    customer_key INT,
    product_key INT NOT NULL,
    date_key INT NOT NULL,
    transaction_date DATETIME NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_value DECIMAL(10,2),   
    is_return BOOLEAN,            
    is_price_outlier BOOLEAN,      
    country VARCHAR(50),
    FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    INDEX idx_invoice (invoice_no),
    INDEX idx_is_return (is_return)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Economic Indicators fact (Updated for Quarters and Momentum)
CREATE TABLE fact_economic_indicators (
    indicator_key INT AUTO_INCREMENT PRIMARY KEY,
    date_key INT NOT NULL,
    observation_date DATE NOT NULL UNIQUE,
    pce_value DECIMAL(10,2) NOT NULL,
    pce_mom_change_pct DECIMAL(5,2), 
    quarter_label VARCHAR(5),        
    econ_status VARCHAR(20),         
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    INDEX idx_date_key (date_key),
    INDEX idx_econ_status (econ_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- MONITORING & ANALYTICS
-- ============================================================================

-- Pipeline Logs for Monitoring Requirement
CREATE TABLE pipeline_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'SUCCESS', 'FAILURE'
    records_processed INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Practical Output View (Spend vs Economy Trend)
CREATE OR REPLACE VIEW view_spending_trends AS
SELECT 
    d.year,
    d.quarter,
    e.econ_status,
    COUNT(t.transaction_key) as total_sales_volume,
    SUM(t.total_value) as total_revenue
FROM fact_transactions t
JOIN dim_date d ON t.date_key = d.date_key
JOIN fact_economic_indicators e ON d.date_key = e.date_key
WHERE t.is_return = FALSE
GROUP BY d.year, d.quarter, e.econ_status;

-- ============================================================================
-- STORED PROCEDURES & POPULATION
-- ============================================================================

DELIMITER //
CREATE PROCEDURE populate_date_dimension(IN start_date DATE, IN end_date DATE)
BEGIN
    DECLARE v_current_date DATE;
    DECLARE date_key_val INT;
    SET v_current_date = start_date;
    WHILE v_current_date <= end_date DO
        SET date_key_val = YEAR(v_current_date) * 10000 + MONTH(v_current_date) * 100 + DAY(v_current_date);
        INSERT IGNORE INTO dim_date (
            date_key, full_date, year, quarter, month, month_name,
            day, day_of_week, day_name, week_of_year, is_weekend
        ) VALUES (
            date_key_val, v_current_date, YEAR(v_current_date), QUARTER(v_current_date),
            MONTH(v_current_date), DATE_FORMAT(v_current_date, '%M'), DAY(v_current_date),
            DAYOFWEEK(v_current_date), DATE_FORMAT(v_current_date, '%W'), WEEK(v_current_date, 3),
            CASE WHEN DAYOFWEEK(v_current_date) IN (1, 7) THEN TRUE ELSE FALSE END
        );
        SET v_current_date = DATE_ADD(v_current_date, INTERVAL 1 DAY);
    END WHILE;
END//
DELIMITER ;

CALL populate_date_dimension('1959-01-01', '2026-12-31');
