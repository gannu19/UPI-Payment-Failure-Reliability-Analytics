-- =============================================================================
-- FILE 02: CORE BUSINESS KPIs & OVERALL RELIABILITY METRICS
-- Purpose: Calculate system-level Payment Success Rate (PSR), Technical Decline
--          (TD) Rate, Business Decline (BD) Rate, Value at Risk, and Latencies.
-- =============================================================================

WITH OverallMetrics AS (
    SELECT 
        COUNT(*) AS total_transactions,
        SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_transactions,
        SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_transactions,
        
        -- Categorized Declines
        SUM(CASE WHEN e.technical_or_business_decline = 'Technical Decline' THEN 1 ELSE 0 END) AS technical_declines,
        SUM(CASE WHEN e.technical_or_business_decline = 'Business Decline' THEN 1 ELSE 0 END) AS business_declines,
        SUM(CASE WHEN e.error_category = 'Timeout/Network' THEN 1 ELSE 0 END) AS timeout_declines,
        
        -- Monetary Values
        SUM(t.amount) AS total_transaction_value,
        SUM(CASE WHEN t.final_status = 'SUCCESS' THEN t.amount ELSE 0 END) AS successful_transaction_value,
        SUM(CASE WHEN t.final_status = 'FAILED' THEN t.amount ELSE 0 END) AS transaction_value_at_risk,
        AVG(t.amount) AS avg_transaction_amount
    FROM clean_transactions t
    LEFT JOIN error_codes e ON t.failure_code = e.error_code
)
SELECT 
    total_transactions,
    successful_transactions,
    failed_transactions,
    
    -- Primary KPI: PSR
    ROUND(100.0 * successful_transactions / total_transactions, 2) AS psr_percentage,
    ROUND(100.0 * failed_transactions / total_transactions, 2) AS failure_rate_percentage,
    
    -- Granular Decline Rates
    ROUND(100.0 * technical_declines / total_transactions, 2) AS technical_decline_rate,
    ROUND(100.0 * business_declines / total_transactions, 2) AS business_decline_rate,
    ROUND(100.0 * timeout_declines / total_transactions, 2) AS timeout_decline_rate,
    
    -- Monetary Metrics
    ROUND(total_transaction_value, 2) AS total_value_inr,
    ROUND(successful_transaction_value, 2) AS successful_value_inr,
    ROUND(transaction_value_at_risk, 2) AS value_at_risk_inr,
    ROUND(100.0 * transaction_value_at_risk / total_transaction_value, 2) AS pct_value_at_risk,
    ROUND(avg_transaction_amount, 2) AS avg_txn_amount_inr
FROM OverallMetrics;
