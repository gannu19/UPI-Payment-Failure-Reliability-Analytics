import os
import csv
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

print("Running Data Quality Audit & Cleaning Pipeline...")

# Load static reference mapping
bank_name_to_id = {
    "SBI": "BNK001",
    "STATE BANK OF INDIA": "BNK001",
    "HDFC BANK": "BNK002",
    "HDFC": "BNK002",
    "ICICI_BANK": "BNK003",
    "ICICI": "BNK003"
}

audit_summary = {
    "raw_transaction_count": 0,
    "duplicate_transactions_removed": 0,
    "inconsistent_bank_names_standardized": 0,
    "invalid_amounts_dropped": 0,
    "missing_values_imputed": 0,
    "processed_transaction_count": 0
}

# 1. Process Banks, Devices, Users, Error Codes (Copy/validate)
for static_file in ["banks.csv", "error_codes.csv", "devices.csv", "users.csv"]:
    raw_path = os.path.join(RAW_DIR, static_file)
    proc_path = os.path.join(PROC_DIR, static_file)
    with open(raw_path, "r", encoding="utf-8") as rf, open(proc_path, "w", newline="", encoding="utf-8") as pf:
        pf.write(rf.read())

# 2. Process Transactions
tx_raw_path = os.path.join(RAW_DIR, "transactions.csv")
tx_proc_path = os.path.join(PROC_DIR, "transactions.csv")

seen_tx_ids = set()
clean_transactions = []

with open(tx_raw_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        audit_summary["raw_transaction_count"] += 1
        tx_id = row["transaction_id"]
        
        # Check Duplicate ID
        if tx_id in seen_tx_ids:
            audit_summary["duplicate_transactions_removed"] += 1
            continue
        
        # Check Amount validity
        try:
            amt = float(row["amount"])
            if amt <= 0:
                audit_summary["invalid_amounts_dropped"] += 1
                continue
        except (ValueError, TypeError):
            audit_summary["invalid_amounts_dropped"] += 1
            continue
        
        # Check Inconsistent Bank Name
        payer_bank = row["payer_bank_id"].strip()
        if payer_bank.upper() in bank_name_to_id:
            payer_bank = bank_name_to_id[payer_bank.upper()]
            audit_summary["inconsistent_bank_names_standardized"] += 1
        
        row["payer_bank_id"] = payer_bank
        
        # Impute missing network_type
        if not row["network_type"]:
            row["network_type"] = "4G" # Default mode
            audit_summary["missing_values_imputed"] += 1
            
        seen_tx_ids.add(tx_id)
        clean_transactions.append(row)

audit_summary["processed_transaction_count"] = len(clean_transactions)

with open(tx_proc_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = [
        "transaction_id", "user_id", "payer_bank_id", "payee_bank_id", "amount",
        "timestamp", "transaction_type", "device_id", "network_type",
        "payment_app", "final_status", "failure_code"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(clean_transactions)

# 3. Process Stage Events (keep events corresponding to clean_transactions)
se_raw_path = os.path.join(RAW_DIR, "stage_events.csv")
se_proc_path = os.path.join(PROC_DIR, "stage_events.csv")

clean_stage_events = []
with open(se_raw_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["transaction_id"] in seen_tx_ids:
            clean_stage_events.append(row)

with open(se_proc_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["transaction_id", "stage_id", "event_timestamp", "stage_status", "error_code"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(clean_stage_events)

# Write audit summary JSON
with open(os.path.join(PROC_DIR, "data_quality_summary.json"), "w", encoding="utf-8") as f:
    json.dump(audit_summary, f, indent=2)

print(f"Data Quality Audit Completed successfully!")
print(json.dumps(audit_summary, indent=2))
