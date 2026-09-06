-- =============================================================================
-- FILE 09: SYSTEM SEGMENTATION & PLATFORM PERFORMANCE
-- Purpose: Evaluate reliability across device OS, network type (5G/4G/3G/WiFi),
--          transaction category (P2P vs P2M), and transaction amount buckets.
-- =============================================================================

-- 1. Device OS & Network Type Performance
SELECT 
    d.operating_system,
    t.network_type,
    COUNT(t.transaction_id) AS total_volume,
    ROUND(100.0 * SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS psr_percentage,
    ROUND(100.0 * SUM(CASE WHEN e.error_category = 'Timeout/Network' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS network_timeout_rate,
    ROUND(100.0 * SUM(CASE WHEN e.technical_or_business_decline = 'Technical Decline' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS technical_decline_rate
FROM clean_transactions t
JOIN devices d ON t.device_id = d.device_id
LEFT JOIN error_codes e ON t.failure_code = e.error_code
GROUP BY d.operating_system, t.network_type
ORDER BY d.operating_system, total_volume DESC;

-- 2. Transaction Type & Amount Bucket Reliability Matrix
WITH CategorizedTransactions AS (
    SELECT 
        transaction_id,
        transaction_type,
        amount,
        final_status,
        failure_code,
        CASE 
            WHEN amount < 100 THEN '1. Micro (< Rs 100)'
            WHEN amount BETWEEN 100 AND 500 THEN '2. Small (Rs 100 - 500)'
            WHEN amount BETWEEN 501 AND 2000 THEN '3. Medium (Rs 501 - 2000)'
            WHEN amount BETWEEN 2001 AND 10000 THEN '4. High (Rs 2001 - 10000)'
            ELSE '5. Very High (> Rs 10000)'
        END AS amount_bucket
    FROM clean_transactions
)
SELECT 
    transaction_type,
    amount_bucket,
    COUNT(*) AS transaction_volume,
    SUM(CASE WHEN final_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_volume,
    ROUND(100.0 * SUM(CASE WHEN final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS psr_percentage,
    SUM(CASE WHEN final_status = 'FAILED' THEN amount ELSE 0 END) AS value_at_risk_inr
FROM CategorizedTransactions
GROUP BY transaction_type, amount_bucket
ORDER BY transaction_type, amount_bucket ASC;
