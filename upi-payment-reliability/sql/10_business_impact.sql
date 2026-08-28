-- =============================================================================
-- FILE 10: BUSINESS IMPACT ESTIMATION & VALUE RECOVERY MODELING
-- Purpose: Estimate potential transaction value recovered under Conservative,
--          Base-case, and Optimistic product intervention adoption scenarios.
-- =============================================================================

WITH RecoverableFailures AS (
    SELECT 
        SUM(t.amount) AS total_failed_value_inr,
        
        -- Recoverable segment: Technical Declines + Network Timeouts
        SUM(CASE WHEN e.technical_or_business_decline = 'Technical Decline' OR e.error_category = 'Timeout/Network' THEN t.amount ELSE 0 END) AS recoverable_technical_value_inr,
        
        -- Unrecoverable segment: Hard Business Declines (Insufficient Balance / Account Frozen)
        SUM(CASE WHEN e.error_code IN ('ERR_BD_01', 'ERR_BD_05') THEN t.amount ELSE 0 END) AS hard_business_decline_value_inr,
        
        -- Addressable Business Declines (e.g. Wrong PIN via instant retry prompt)
        SUM(CASE WHEN e.error_code IN ('ERR_BD_02') THEN t.amount ELSE 0 END) AS soft_business_decline_value_inr
    FROM clean_transactions t
    JOIN error_codes e ON t.failure_code = e.error_code
    WHERE t.final_status = 'FAILED'
)
SELECT 
    ROUND(total_failed_value_inr, 2) AS total_transaction_value_at_risk_inr,
    ROUND(recoverable_technical_value_inr, 2) AS recoverable_technical_value_inr,
    ROUND(soft_business_decline_value_inr, 2) AS soft_business_decline_value_inr,
    
    -- Scenario 1: Conservative (15% Technical Recovery + 10% Soft BD Recovery)
    ROUND((0.15 * recoverable_technical_value_inr) + (0.10 * soft_business_decline_value_inr), 2) AS conservative_recovered_value_inr,
    ROUND(100.0 * ((0.15 * recoverable_technical_value_inr) + (0.10 * soft_business_decline_value_inr)) / total_failed_value_inr, 2) AS conservative_recovery_pct,
    
    -- Scenario 2: Base-Case (35% Technical Recovery + 25% Soft BD Recovery)
    ROUND((0.35 * recoverable_technical_value_inr) + (0.25 * soft_business_decline_value_inr), 2) AS base_case_recovered_value_inr,
    ROUND(100.0 * ((0.35 * recoverable_technical_value_inr) + (0.25 * soft_business_decline_value_inr)) / total_failed_value_inr, 2) AS base_case_recovery_pct,
    
    -- Scenario 3: Optimistic (60% Technical Recovery + 45% Soft BD Recovery)
    ROUND((0.60 * recoverable_technical_value_inr) + (0.45 * soft_business_decline_value_inr), 2) AS optimistic_recovered_value_inr,
    ROUND(100.0 * ((0.60 * recoverable_technical_value_inr) + (0.45 * soft_business_decline_value_inr)) / total_failed_value_inr, 2) AS optimistic_recovery_pct
FROM RecoverableFailures;
