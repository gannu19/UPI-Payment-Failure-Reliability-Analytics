-- =============================================================================
-- FILE 04: PAYER & PAYEE BANK RELIABILITY ANALYSIS
-- Purpose: Evaluate bank-level performance, payer vs payee bottleneck identification,
--          TD/BD split, and cross-bank pair failure matrices.
-- =============================================================================

-- 1. Payer Bank Reliability Ranking
SELECT 
    b.bank_name AS payer_bank_name,
    b.bank_type,
    COUNT(t.transaction_id) AS total_volume,
    SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_volume,
    SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS failure_volume,
    ROUND(100.0 * SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS bank_psr,
    ROUND(100.0 * SUM(CASE WHEN e.technical_or_business_decline = 'Technical Decline' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS technical_decline_rate,
    ROUND(100.0 * SUM(CASE WHEN e.technical_or_business_decline = 'Business Decline' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS business_decline_rate,
    RANK() OVER (ORDER BY (100.0 * SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(t.transaction_id)) ASC) AS reliability_rank_asc
FROM clean_transactions t
JOIN banks b ON t.payer_bank_id = b.bank_id
LEFT JOIN error_codes e ON t.failure_code = e.error_code
GROUP BY b.bank_name, b.bank_type
HAVING COUNT(t.transaction_id) >= 100
ORDER BY bank_psr ASC;

-- 2. Bank Pair Cross-Matrix Failure Rate (Payer Bank -> Payee Bank)
SELECT 
    b1.bank_name AS payer_bank,
    b2.bank_name AS payee_bank,
    COUNT(t.transaction_id) AS pair_volume,
    SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS pair_failures,
    ROUND(100.0 * SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS pair_failure_rate,
    ROUND(SUM(CASE WHEN t.final_status = 'FAILED' THEN t.amount ELSE 0 END), 2) AS pair_value_at_risk
FROM clean_transactions t
JOIN banks b1 ON t.payer_bank_id = b1.bank_id
JOIN banks b2 ON t.payee_bank_id = b2.bank_id
GROUP BY b1.bank_name, b2.bank_name
HAVING COUNT(t.transaction_id) >= 200
ORDER BY pair_failure_rate DESC
LIMIT 15;
