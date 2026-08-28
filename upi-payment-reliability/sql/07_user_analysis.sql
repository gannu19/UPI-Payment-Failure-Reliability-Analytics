-- =============================================================================
-- FILE 07: USER COHORT & REPEATED FAILURE FRICTION ANALYSIS
-- Purpose: Evaluate user-level failure distribution, identify power users 
--          suffering high failure frequency, and measure cohort friction.
-- =============================================================================

-- 1. Distribution of Failure Frequency Per User
WITH UserFailureSummary AS (
    SELECT 
        u.user_id,
        u.user_segment,
        COUNT(t.transaction_id) AS user_total_txns,
        SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) AS user_success_txns,
        SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS user_failed_txns
    FROM users u
    JOIN clean_transactions t ON u.user_id = t.user_id
    GROUP BY u.user_id, u.user_segment
)
SELECT 
    user_segment,
    COUNT(user_id) AS total_users_in_segment,
    SUM(user_total_txns) AS segment_txn_volume,
    SUM(user_failed_txns) AS segment_failed_volume,
    ROUND(100.0 * SUM(user_success_txns) / SUM(user_total_txns), 2) AS segment_psr,
    ROUND(1.0 * SUM(user_failed_txns) / COUNT(user_id), 2) AS avg_failures_per_user,
    SUM(CASE WHEN user_failed_txns >= 3 THEN 1 ELSE 0 END) AS users_with_3plus_failures,
    ROUND(100.0 * SUM(CASE WHEN user_failed_txns >= 3 THEN 1 ELSE 0 END) / COUNT(user_id), 2) AS pct_users_severely_impacted
FROM UserFailureSummary
GROUP BY user_segment
ORDER BY segment_txn_volume DESC;

-- 2. Top Power Users Impacted by Repeated Technical Declines
SELECT 
    u.user_id,
    u.user_segment,
    u.state,
    COUNT(t.transaction_id) AS total_attempts,
    SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_attempts,
    SUM(CASE WHEN t.failure_code LIKE 'ERR_TD%' THEN 1 ELSE 0 END) AS technical_declines,
    ROUND(100.0 * SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS user_psr,
    ROUND(SUM(CASE WHEN t.final_status = 'FAILED' THEN t.amount ELSE 0 END), 2) AS user_failed_value_inr
FROM clean_transactions t
JOIN users u ON t.user_id = u.user_id
GROUP BY u.user_id, u.user_segment, u.state
HAVING COUNT(t.transaction_id) >= 10 AND SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) >= 3
ORDER BY failed_attempts DESC
LIMIT 20;
