-- =============================================================================
-- FILE 01: DATA QUALITY AUDIT & ANOMALY DETECTION
-- Purpose: Inspect relational raw datasets, identify duplicates, missing values,
--          inconsistent bank names, invalid amounts, and document cleaning rules.
-- =============================================================================

-- 1. Identify Duplicate Transaction Records
WITH DuplicateTransactions AS (
    SELECT 
        transaction_id,
        COUNT(*) AS occurrence_count
    FROM raw_transactions
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
)
SELECT 
    'Duplicate Transactions' AS anomaly_type,
    COUNT(*) AS affected_records,
    'De-duplicate by taking FIRST_VALUE by timestamp' AS recommended_action
FROM DuplicateTransactions;

-- 2. Audit Inconsistent Bank Names & Unmapped IDs
SELECT 
    payer_bank_id,
    COUNT(*) AS transaction_count,
    CASE 
        WHEN payer_bank_id IN ('SBI', 'State Bank Of India') THEN 'Map to BNK001 (State Bank of India)'
        WHEN payer_bank_id IN ('HDFC BANK', 'hdfc bank') THEN 'Map to BNK002 (HDFC Bank)'
        WHEN payer_bank_id IN ('ICICI_BANK') THEN 'Map to BNK003 (ICICI Bank)'
        WHEN payer_bank_id NOT LIKE 'BNK%' THEN 'Unknown Bank Alias'
        ELSE 'Valid Bank ID'
    END AS data_quality_status
FROM raw_transactions
WHERE payer_bank_id NOT LIKE 'BNK%'
GROUP BY payer_bank_id;

-- 3. Detect Invalid Transaction Amounts (Negative, Zero, or Outlier Values)
SELECT 
    COUNT(*) AS invalid_amount_records,
    MIN(amount) AS min_amount_found,
    MAX(amount) AS max_amount_found,
    'Filter out amount <= 0' AS cleaning_rule
FROM raw_transactions
WHERE amount <= 0;

-- 4. Check Missing/Null Values Across Core Fields
SELECT 
    SUM(CASE WHEN user_id IS NULL OR user_id = '' THEN 1 ELSE 0 END) AS missing_users,
    SUM(CASE WHEN payer_bank_id IS NULL OR payer_bank_id = '' THEN 1 ELSE 0 END) AS missing_payer_banks,
    SUM(CASE WHEN payee_bank_id IS NULL OR payee_bank_id = '' THEN 1 ELSE 0 END) AS missing_payee_banks,
    SUM(CASE WHEN network_type IS NULL OR network_type = '' THEN 1 ELSE 0 END) AS missing_networks,
    SUM(CASE WHEN final_status IS NULL OR final_status = '' THEN 1 ELSE 0 END) AS missing_statuses
FROM raw_transactions;

-- 5. Clean Transactions CTE View (Gold Standard Dataset for Analysis)
CREATE VIEW clean_transactions_view AS
WITH DedupedTransactions AS (
    SELECT 
        transaction_id,
        user_id,
        CASE 
            WHEN UPPER(TRIM(payer_bank_id)) IN ('SBI', 'STATE BANK OF INDIA') THEN 'BNK001'
            WHEN UPPER(TRIM(payer_bank_id)) IN ('HDFC BANK', 'HDFC') THEN 'BNK002'
            WHEN UPPER(TRIM(payer_bank_id)) IN ('ICICI_BANK', 'ICICI') THEN 'BNK003'
            ELSE payer_bank_id
        END AS payer_bank_id,
        payee_bank_id,
        amount,
        timestamp,
        transaction_type,
        device_id,
        COALESCE(NULLIF(network_type, ''), '4G') AS network_type,
        payment_app,
        final_status,
        failure_code,
        ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY timestamp ASC) AS row_num
    FROM raw_transactions
    WHERE amount > 0
)
SELECT 
    transaction_id,
    user_id,
    payer_bank_id,
    payee_bank_id,
    amount,
    timestamp,
    transaction_type,
    device_id,
    network_type,
    payment_app,
    final_status,
    failure_code
FROM DedupedTransactions
WHERE row_num = 1;
