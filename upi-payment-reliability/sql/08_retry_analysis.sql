-- =============================================================================
-- FILE 08: RETRY BEHAVIOR & AUTO-RETRY CANDIDATE MODELING
-- Purpose: Analyze user retry chains using LEAD window functions, calculate retry
--          success rate by failure category, and identify auto-retry candidates.
-- =============================================================================

WITH SequentialTransactions AS (
    SELECT 
        transaction_id,
        user_id,
        amount,
        timestamp,
        final_status,
        failure_code,
        payer_bank_id,
        LEAD(transaction_id) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_txn_id,
        LEAD(final_status) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_txn_status,
        LEAD(failure_code) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_failure_code,
        LEAD(amount) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_amount,
        LEAD(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_timestamp
    FROM clean_transactions
),
RetryAttempts AS (
    SELECT 
        transaction_id AS initial_txn_id,
        user_id,
        failure_code AS initial_failure_code,
        amount AS initial_amount,
        final_status AS initial_status,
        next_txn_id,
        next_txn_status,
        EXTRACT(EPOCH FROM (CAST(next_timestamp AS TIMESTAMP) - CAST(timestamp AS TIMESTAMP))) AS retry_time_gap_seconds
    FROM SequentialTransactions
    WHERE final_status = 'FAILED'
      AND next_txn_id IS NOT NULL
      -- Retry window threshold: within 15 minutes (900 seconds) and similar amount range (+/- 10%)
      AND EXTRACT(EPOCH FROM (CAST(next_timestamp AS TIMESTAMP) - CAST(timestamp AS TIMESTAMP))) <= 900
      AND ABS(amount - next_amount) <= (0.1 * amount)
)
SELECT 
    e.error_category,
    e.error_code,
    e.error_description,
    e.technical_or_business_decline,
    COUNT(r.initial_txn_id) AS total_retried_failures,
    SUM(CASE WHEN r.next_txn_status = 'SUCCESS' THEN 1 ELSE 0 END) AS successful_retries,
    SUM(CASE WHEN r.next_txn_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_retries,
    ROUND(100.0 * SUM(CASE WHEN r.next_txn_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(r.initial_txn_id), 2) AS retry_success_rate_pct,
    ROUND(AVG(r.retry_time_gap_seconds), 1) AS avg_time_to_retry_seconds,
    CASE 
        WHEN e.error_category IN ('Technical Decline', 'Timeout/Network') AND (100.0 * SUM(CASE WHEN r.next_txn_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(r.initial_txn_id)) >= 50.0 
            THEN 'RECOMMENDED FOR AUTO-RETRY / SMART RETRY'
        WHEN e.error_code IN ('ERR_BD_01', 'ERR_BD_02', 'ERR_BD_03') 
            THEN 'DO NOT AUTO-RETRY (Hard Business Decline / Security / Balance)'
        ELSE 'MANUAL RETRY ONLY'
    END AS product_retry_policy
FROM RetryAttempts r
JOIN error_codes e ON r.initial_failure_code = e.error_code
GROUP BY e.error_category, e.error_code, e.error_description, e.technical_or_business_decline
ORDER BY total_retried_failures DESC;
