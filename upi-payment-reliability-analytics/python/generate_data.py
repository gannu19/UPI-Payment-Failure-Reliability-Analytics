import os
import random
import csv
from datetime import datetime, timedelta

# Define target paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DATA_DIR, exist_ok=True)

print(f"Generating synthetic UPI transaction data in {RAW_DATA_DIR}...")

random.seed(42)

# 1. Banks
banks_data = [
    ("BNK001", "State Bank of India", "PSU"),
    ("BNK002", "HDFC Bank", "Private"),
    ("BNK003", "ICICI Bank", "Private"),
    ("BNK004", "Axis Bank", "Private"),
    ("BNK005", "Bank of Baroda", "PSU"),
    ("BNK006", "Punjab National Bank", "PSU"),
    ("BNK007", "Paytm Payments Bank", "Payments Bank"),
    ("BNK008", "Airtel Payments Bank", "Payments Bank"),
    ("BNK009", "Canara Bank", "PSU"),
    ("BNK010", "Kotak Mahindra Bank", "Private")
]

with open(os.path.join(RAW_DATA_DIR, "banks.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["bank_id", "bank_name", "bank_type"])
    writer.writerows(banks_data)

# 2. Error Codes
error_codes_data = [
    ("ERR_SUCCESS", "Success", "Transaction completed successfully", "N/A"),
    ("ERR_TD_01", "Technical Decline", "Core Banking Server (CBS) Timeout / Unresponsive", "Technical Decline"),
    ("ERR_TD_02", "Technical Decline", "NPCI Switch Timeout", "Technical Decline"),
    ("ERR_TD_03", "Technical Decline", "Bank CBS Connection Failure", "Technical Decline"),
    ("ERR_BD_01", "Business Decline", "Insufficient Balance in Account", "Business Decline"),
    ("ERR_BD_02", "Business Decline", "Invalid UPI PIN / Incorrect MPIN", "Business Decline"),
    ("ERR_BD_03", "Business Decline", "Daily Transaction Amount Limit Exceeded", "Business Decline"),
    ("ERR_BD_04", "Business Decline", "Daily Transaction Count Limit Exceeded", "Business Decline"),
    ("ERR_BD_05", "Business Decline", "Account Inactive / Frozen", "Business Decline"),
    ("ERR_NET_01", "Timeout/Network", "Network Connectivity Interrupted / Gateway Timeout", "Technical Decline"),
    ("ERR_NET_02", "Timeout/Network", "Client Payment App Request Timeout", "Technical Decline")
]

with open(os.path.join(RAW_DATA_DIR, "error_codes.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["error_code", "error_category", "error_description", "technical_or_business_decline"])
    writer.writerows(error_codes_data)

# 3. Devices
device_os_list = [("Android", "11"), ("Android", "12"), ("Android", "13"), ("Android", "14"), ("iOS", "16.5"), ("iOS", "17.2")]
device_categories = ["Budget", "Mid-range", "Premium"]

devices_rows = []
NUM_DEVICES = 5000
for i in range(1, NUM_DEVICES + 1):
    dev_id = f"DEV{i:06d}"
    os_name, os_ver = random.choices(device_os_list, weights=[25, 30, 20, 10, 10, 5])[0]
    cat = random.choices(device_categories, weights=[40, 45, 15])[0]
    devices_rows.append([dev_id, os_name, os_ver, cat])

with open(os.path.join(RAW_DATA_DIR, "devices.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["device_id", "operating_system", "os_version", "device_category"])
    writer.writerows(devices_rows)

# 4. Users
user_segments = ["New", "Occasional", "Frequent", "Power"]
states = ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu", "Uttar Pradesh", "Gujarat", "Telangana", "West Bengal", "Rajasthan", "Haryana"]
age_groups = ["18-24", "25-34", "35-44", "45-59", "60+"]

users_rows = []
NUM_USERS = 10000
start_signup = datetime(2023, 1, 1)

for i in range(1, NUM_USERS + 1):
    u_id = f"USR{i:06d}"
    signup_dt = start_signup + timedelta(days=random.randint(0, 1200))
    seg = random.choices(user_segments, weights=[15, 30, 35, 20])[0]
    st = random.choice(states)
    age = random.choices(age_groups, weights=[30, 40, 18, 9, 3])[0]
    tenure = (datetime(2026, 8, 28) - signup_dt).days
    users_rows.append([u_id, signup_dt.strftime("%Y-%m-%d"), seg, st, age, tenure])

with open(os.path.join(RAW_DATA_DIR, "users.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["user_id", "signup_date", "user_segment", "state", "age_group", "tenure_days"])
    writer.writerows(users_rows)

# 5. Transactions & Stage Events
NUM_TXNS = 50000
txn_types = ["P2P", "P2M"]
networks = ["4G", "5G", "WiFi", "3G"]
payment_apps = ["PhonePe", "Google Pay", "Paytm", "BHIM", "CRED"]

start_time = datetime(2026, 7, 28, 0, 0, 0)
end_time = datetime(2026, 8, 27, 23, 59, 59)
total_seconds = int((end_time - start_time).total_seconds())

transactions_rows = []
stage_events_rows = []

bank_ids = [b[0] for b in banks_data]
psu_banks = ["BNK001", "BNK005", "BNK006", "BNK009"] # SBI, BoB, PNB, Canara

# Create realistic transaction flow
for i in range(1, NUM_TXNS + 1):
    tx_id = f"TXN{i:08d}"
    user_id = f"USR{random.randint(1, NUM_USERS):06d}"
    payer_bank = random.choices(bank_ids, weights=[25, 18, 15, 12, 8, 7, 5, 4, 3, 3])[0]
    payee_bank = random.choices(bank_ids, weights=[20, 20, 15, 12, 8, 8, 6, 5, 3, 3])[0]
    
    # Amount distribution: heavily skewed towards small amounts (P2P/P2M tea/grocery)
    amt_choice = random.random()
    if amt_choice < 0.50:
        amount = round(random.uniform(10, 250), 2)
    elif amt_choice < 0.85:
        amount = round(random.uniform(250, 2000), 2)
    elif amt_choice < 0.96:
        amount = round(random.uniform(2000, 10000), 2)
    else:
        amount = round(random.uniform(10000, 50000), 2)

    offset = random.randint(0, total_seconds)
    tx_dt = start_time + timedelta(seconds=offset)

    tx_type = random.choices(txn_types, weights=[45, 55])[0]
    dev_id = f"DEV{random.randint(1, NUM_DEVICES):06d}"
    net_type = random.choices(networks, weights=[50, 35, 12, 3])[0]
    app = random.choices(payment_apps, weights=[42, 36, 14, 5, 3])[0]

    # Peak hour effect: 19:00 to 21:00 (7 PM to 9 PM)
    is_peak = (19 <= tx_dt.hour <= 21)

    # Calculate failure probability based on bank, peak hour, and network
    fail_prob = 0.04  # base failure ~4%
    if is_peak:
        fail_prob += 0.05
    if payer_bank in psu_banks and is_peak:
        fail_prob += 0.08  # PSU banks core server congestion
    if net_type in ["3G"]:
        fail_prob += 0.06

    is_failed = random.random() < fail_prob

    if not is_failed:
        final_status = "SUCCESS"
        failure_code = "ERR_SUCCESS"
    else:
        final_status = "FAILED"
        # Determine failure category: Technical vs Business vs Network
        if is_peak and payer_bank in psu_banks and random.random() < 0.65:
            failure_code = random.choices(["ERR_TD_01", "ERR_TD_02", "ERR_TD_03"], weights=[60, 25, 15])[0]
        elif net_type in ["3G"] and random.random() < 0.50:
            failure_code = random.choice(["ERR_NET_01", "ERR_NET_02"])
        else:
            failure_code = random.choices(
                ["ERR_BD_01", "ERR_BD_02", "ERR_BD_03", "ERR_BD_04", "ERR_BD_05", "ERR_TD_01", "ERR_NET_01"],
                weights=[35, 30, 10, 5, 5, 10, 5]
            )[0]

    transactions_rows.append([
        tx_id, user_id, payer_bank, payee_bank, amount,
        tx_dt.strftime("%Y-%m-%d %H:%M:%S"), tx_type, dev_id,
        net_type, app, final_status, failure_code
    ])

    # Stage events for funnel (1: INITIATED, 2: REQUEST_SENT, 3: AUTHENTICATION, 4: BANK_PROCESSING, 5: AUTHORIZATION, 6: CONFIRMATION, 7: COMPLETED)
    stages = [
        (1, "INITIATED"),
        (2, "REQUEST_SENT"),
        (3, "AUTHENTICATION"),
        (4, "BANK_PROCESSING"),
        (5, "AUTHORIZATION"),
        (6, "CONFIRMATION"),
        (7, "COMPLETED")
    ]

    curr_ts = tx_dt
    failed_at_stage = None
    if is_failed:
        if failure_code in ["ERR_BD_02"]: # Wrong PIN
            failed_at_stage = 3 # AUTHENTICATION
        elif failure_code in ["ERR_TD_01", "ERR_TD_02", "ERR_TD_03", "ERR_BD_01", "ERR_BD_03", "ERR_BD_04"]: # Bank processing / balance
            failed_at_stage = 4 # BANK_PROCESSING
        elif failure_code in ["ERR_NET_01", "ERR_NET_02"]:
            failed_at_stage = random.choice([3, 4, 5])
        else:
            failed_at_stage = 4

    for stg_id, stg_name in stages:
        latency_ms = random.randint(50, 300)
        curr_ts = curr_ts + timedelta(milliseconds=latency_ms)

        if is_failed and stg_id == failed_at_stage:
            stage_events_rows.append([
                tx_id, stg_id, curr_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "FAILED", failure_code
            ])
            break # Drop off after failure
        elif is_failed and stg_id > failed_at_stage:
            break
        else:
            stage_events_rows.append([
                tx_id, stg_id, curr_ts.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "SUCCESS", "ERR_SUCCESS"
            ])

# Introduce realistic Data Quality Anomalies into transactions_rows to be audited & cleaned in 01_data_quality.sql
print("Injecting controlled data quality anomalies for audit pipeline...")

# Anomaly 1: ~40 Duplicate transactions
for _ in range(40):
    dup_tx = random.choice(transactions_rows).copy()
    transactions_rows.append(dup_tx)

# Anomaly 2: ~25 Inconsistent Bank Names in place of bank_id
inconsistent_names = ["SBI", "State Bank Of India", "HDFC BANK", "hdfc bank", "ICICI_BANK"]
for _ in range(25):
    idx = random.randint(0, len(transactions_rows) - 1)
    row = list(transactions_rows[idx])
    row[2] = random.choice(inconsistent_names) # payer_bank
    transactions_rows[idx] = row

# Anomaly 3: ~20 Invalid transaction amounts (< 0 or extreme string)
for _ in range(20):
    idx = random.randint(0, len(transactions_rows) - 1)
    row = list(transactions_rows[idx])
    row[4] = -1.0 * float(row[4]) # Negative amount
    transactions_rows[idx] = row

# Anomaly 4: ~20 Missing values (None / empty string)
for _ in range(20):
    idx = random.randint(0, len(transactions_rows) - 1)
    row = list(transactions_rows[idx])
    row[8] = "" # missing network_type
    transactions_rows[idx] = row

# Write Transactions
with open(os.path.join(RAW_DATA_DIR, "transactions.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "transaction_id", "user_id", "payer_bank_id", "payee_bank_id", "amount",
        "timestamp", "transaction_type", "device_id", "network_type",
        "payment_app", "final_status", "failure_code"
    ])
    writer.writerows(transactions_rows)

# Write Stage Events
with open(os.path.join(RAW_DATA_DIR, "stage_events.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["transaction_id", "stage_id", "event_timestamp", "stage_status", "error_code"])
    writer.writerows(stage_events_rows)

print(f"Data generation complete! {len(transactions_rows)} transactions and {len(stage_events_rows)} stage events generated.")
