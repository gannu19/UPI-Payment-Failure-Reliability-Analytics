-- =============================================================================
-- FILE 05: HOURLY, PEAK VS NON-PEAK & TEMPORAL RELIABILITY ANALYSIS
-- Purpose: Analyze system capacity during peak traffic hours, day of week patterns,
--          and calculate 3-hour rolling average failure rates.
-- =============================================================================

-- 1. Hourly Transaction Volume & Failure Rate Breakdown
WITH HourlyAggregates AS (
    SELECT 
        EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) AS hour_of_day,
        COUNT(*) AS total_txns,
        SUM(CASE WHEN final_status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_txns,
        SUM(CASE WHEN final_status = 'FAILED' THEN 1 ELSE 0 END) AS failed_txns,
        SUM(CASE WHEN failure_code LIKE 'ERR_TD%' THEN 1 ELSE 0 END) AS technical_failures
    FROM clean_transactions
    GROUP BY EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP))
)
SELECT 
    hour_of_day,
    total_txns,
    success_txns,
    failed_txns,
    ROUND(100.0 * success_txns / total_txns, 2) AS psr_percentage,
    ROUND(100.0 * failed_txns / total_txns, 2) AS failure_rate_percentage,
    ROUND(100.0 * technical_failures / total_txns, 2) AS td_rate_percentage,
    CASE 
        WHEN hour_of_day BETWEEN 19 AND 21 THEN 'Evening Peak (19:00-21:00)'
        WHEN hour_of_day BETWEEN 12 AND 14 THEN 'Afternoon Peak (12:00-14:00)'
        WHEN hour_of_day BETWEEN 1 AND 5 THEN 'Off-Peak Night'
        ELSE 'Normal Hours'
    END AS time_window_type
FROM HourlyAggregates
ORDER BY hour_of_day ASC;

-- 2. Peak vs Non-Peak Comparative Summary
SELECT 
    CASE 
        WHEN EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) BETWEEN 19 AND 21 THEN 'Evening Peak Hours (7 PM - 9 PM)'
        ELSE 'Non-Peak Hours'
    END AS period_type,
    COUNT(*) AS total_volume,
    ROUND(100.0 * SUM(CASE WHEN final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS psr_percentage,
    ROUND(100.0 * SUM(CASE WHEN failure_code LIKE 'ERR_TD%' THEN 1 ELSE 0 END) / COUNT(*), 2) AS td_rate_percentage,
    ROUND(100.0 * SUM(CASE WHEN failure_code LIKE 'ERR_BD%' THEN 1 ELSE 0 END) / COUNT(*), 2) AS bd_rate_percentage,
    ROUND(AVG(amount), 2) AS avg_txn_amount
FROM clean_transactions
GROUP BY CASE 
    WHEN EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) BETWEEN 19 AND 21 THEN 'Evening Peak Hours (7 PM - 9 PM)'
    ELSE 'Non-Peak Hours'
END;
