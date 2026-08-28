-- =============================================================================
-- FILE 03: FAILURE CATEGORY & REASON DEEP DIVE
-- Purpose: Break down payment failures by technical, business, and network 
--          reasons, calculating contribution % and total value affected.
-- =============================================================================

WITH FailedTransactions AS (
    SELECT 
        t.transaction_id,
        t.amount,
        t.failure_code,
        COALESCE(e.error_category, 'Unknown') AS error_category,
        COALESCE(e.error_description, 'Unclassified Error') AS error_description,
        COALESCE(e.technical_or_business_decline, 'Other') AS decline_type
    FROM clean_transactions t
    LEFT JOIN error_codes e ON t.failure_code = e.error_code
    WHERE t.final_status = 'FAILED'
),
CategoryTotals AS (
    SELECT COUNT(*) AS total_failed_txns FROM FailedTransactions
)
SELECT 
    f.decline_type,
    f.error_category,
    f.failure_code,
    f.error_description,
    COUNT(*) AS failure_count,
    ROUND(100.0 * COUNT(*) / c.total_failed_txns, 2) AS pct_contribution_to_failures,
    SUM(f.amount) AS total_failed_value_inr,
    ROUND(AVG(f.amount), 2) AS avg_failed_amount_inr,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS failure_rank
FROM FailedTransactions f
CROSS JOIN CategoryTotals c
GROUP BY f.decline_type, f.error_category, f.failure_code, f.error_description, c.total_failed_txns
ORDER BY failure_count DESC;
