-- =============================================================================
-- FILE 06: PAYMENT FUNNEL & STAGE LATENCY ANALYSIS
-- Purpose: Model the 7-stage payment journey, track conversion & drop-offs,
--          calculate inter-stage latency, and pinpoint the biggest bottleneck stage.
-- =============================================================================

WITH StageNames AS (
    SELECT 1 AS stage_id, '1. INITIATED' AS stage_name UNION ALL
    SELECT 2, '2. REQUEST_SENT' UNION ALL
    SELECT 3, '3. AUTHENTICATION' UNION ALL
    SELECT 4, '4. BANK_PROCESSING' UNION ALL
    SELECT 5, '5. AUTHORIZATION' UNION ALL
    SELECT 6, '6. CONFIRMATION' UNION ALL
    SELECT 7, '7. COMPLETED'
),
StageCounts AS (
    SELECT 
        stage_id,
        COUNT(DISTINCT transaction_id) AS transactions_entering_stage,
        SUM(CASE WHEN stage_status = 'FAILED' THEN 1 ELSE 0 END) AS stage_failures
    FROM stage_events
    GROUP BY stage_id
),
TotalInitiated AS (
    SELECT COUNT(DISTINCT transaction_id) AS total_initiations FROM clean_transactions
)
SELECT 
    sn.stage_name,
    sc.stage_id,
    sc.transactions_entering_stage,
    sc.stage_failures,
    
    -- Conversion relative to top of funnel
    ROUND(100.0 * sc.transactions_entering_stage / ti.total_initiations, 2) AS overall_conversion_pct,
    
    -- Drop-off rate at this specific stage
    ROUND(100.0 * sc.stage_failures / sc.transactions_entering_stage, 2) AS stage_dropoff_rate_pct,
    
    -- Stage latency relative to previous stage timestamp
    LAG(sc.transactions_entering_stage) OVER (ORDER BY sc.stage_id) - sc.transactions_entering_stage AS absolute_dropoff_volume
FROM StageNames sn
JOIN StageCounts sc ON sn.stage_id = sc.stage_id
CROSS JOIN TotalInitiated ti
ORDER BY sc.stage_id ASC;
