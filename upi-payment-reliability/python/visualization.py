import os
import shutil
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed").replace("\\", "/")
DASH_DIR = os.path.join(BASE_DIR, "dashboard")
ARTIFACT_DIR = r"C:\Users\bhuky\.gemini\antigravity\brain\3a98c5f0-8463-45da-897a-9446403f2cfb"

os.makedirs(DASH_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Set global aesthetic style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']

# Connect to DuckDB & load tables
con = duckdb.connect(database=":memory:")
for table in ["banks", "devices", "error_codes", "stage_events", "transactions", "users"]:
    con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_csv_auto('{PROC_DIR}/{table}.csv');")

# -----------------------------------------------------------------------------
# GRAPH 1: KPI Overview & Transaction Status Breakdown
# -----------------------------------------------------------------------------
df_status = con.execute("""
    SELECT 
        CASE 
            WHEN final_status = 'SUCCESS' THEN 'Success (90.42%)'
            WHEN failure_code LIKE 'ERR_TD%' THEN 'Technical Decline (4.68%)'
            WHEN failure_code LIKE 'ERR_BD%' THEN 'Business Decline (3.82%)'
            ELSE 'Network Timeout (1.08%)'
        END AS status_category,
        COUNT(*) AS count
    FROM transactions
    GROUP BY status_category
""").df()

plt.figure(figsize=(8, 5))
colors = ['#2e7d32', '#c62828', '#f57c00', '#0288d1']
plt.pie(df_status['count'], labels=df_status['status_category'], autopct='%1.2f%%', startangle=140, 
        colors=colors, wedgeprops={'edgecolor': 'white', 'linewidth': 2}, textprops={'fontweight': 'bold'})
plt.title('Overall UPI Payment Status Breakdown (49,980 Attempts)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
g1_path = os.path.join(DASH_DIR, "graph1_kpi_overview.png")
plt.savefig(g1_path, dpi=300)
shutil.copy(g1_path, os.path.join(ARTIFACT_DIR, "graph1_kpi_overview.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 2: Failure Reason Breakdown by Category & Code
# -----------------------------------------------------------------------------
df_reasons = con.execute("""
    SELECT 
        COALESCE(e.error_category, 'Unknown') AS category,
        COALESCE(e.error_description, t.failure_code) AS description,
        COUNT(*) AS count
    FROM transactions t
    LEFT JOIN error_codes e ON t.failure_code = e.error_code
    WHERE t.final_status = 'FAILED'
    GROUP BY category, description
    ORDER BY count DESC
""").df()

plt.figure(figsize=(10, 5.5))
palette = {'Technical Decline': '#c62828', 'Business Decline': '#f57c00', 'Timeout/Network': '#0288d1'}
ax = sns.barplot(data=df_reasons, y='description', x='count', hue='category', dodge=False, palette=palette)
for p in ax.patches:
    width = p.get_width()
    if width > 0:
        ax.annotate(f'{int(width):,}', (width + 20, p.get_y() + p.get_height() / 2.),
                    ha='left', va='center', fontweight='bold', fontsize=10)
plt.xlim(0, max(df_reasons['count']) * 1.15)
plt.title('UPI Payment Failure Causes by Volume & Category', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Number of Failed Transactions', fontsize=11, fontweight='bold')
plt.ylabel('Failure Reason', fontsize=11, fontweight='bold')
plt.tight_layout()
g2_path = os.path.join(DASH_DIR, "graph2_failure_reasons.png")
plt.savefig(g2_path, dpi=300)
shutil.copy(g2_path, os.path.join(ARTIFACT_DIR, "graph2_failure_reasons.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 3: Payer Bank Reliability Comparison (PSR vs TD Rate)
# -----------------------------------------------------------------------------
df_banks = con.execute("""
    SELECT 
        b.bank_name,
        ROUND(100.0 * SUM(CASE WHEN t.final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS psr,
        ROUND(100.0 * SUM(CASE WHEN e.technical_or_business_decline = 'Technical Decline' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 2) AS td_rate
    FROM transactions t
    JOIN banks b ON t.payer_bank_id = b.bank_id
    LEFT JOIN error_codes e ON t.failure_code = e.error_code
    GROUP BY b.bank_name
    ORDER BY psr ASC
""").df()

fig, ax = plt.subplots(figsize=(10, 5.5))
y_pos = range(len(df_banks))
ax.barh(y_pos, df_banks['psr'], color='#43a047', alpha=0.85, label='PSR %')
ax.barh(y_pos, df_banks['td_rate'], color='#e53935', alpha=0.9, label='Technical Decline Rate %')
for i, (p, td) in enumerate(zip(df_banks['psr'], df_banks['td_rate'])):
    ax.text(p + 1, i, f'PSR: {p}% (TD: {td}%)', va='center', fontweight='bold', fontsize=9.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(df_banks['bank_name'], fontweight='bold')
ax.set_xlim(0, 115)
ax.set_xlabel('Percentage (%)', fontsize=11, fontweight='bold')
plt.title('Payer Bank Reliability Benchmark (PSR vs Technical Decline Rate)', fontsize=13, fontweight='bold', pad=15)
plt.legend(loc='lower right')
plt.tight_layout()
g3_path = os.path.join(DASH_DIR, "graph3_bank_reliability.png")
plt.savefig(g3_path, dpi=300)
shutil.copy(g3_path, os.path.join(ARTIFACT_DIR, "graph3_bank_reliability.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 4: Bank Pair Failure Rate Heatmap (Payer -> Payee)
# -----------------------------------------------------------------------------
df_matrix = con.execute("""
    SELECT 
        b1.bank_name AS payer_bank,
        b2.bank_name AS payee_bank,
        ROUND(100.0 * SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(t.transaction_id), 1) AS failure_rate
    FROM transactions t
    JOIN banks b1 ON t.payer_bank_id = b1.bank_id
    JOIN banks b2 ON t.payee_bank_id = b2.bank_id
    GROUP BY b1.bank_name, b2.bank_name
""").df()

heatmap_data = df_matrix.pivot(index='payer_bank', columns='payee_bank', values='failure_rate')
plt.figure(figsize=(10, 7))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="YlOrRd", cbar_kws={'label': 'Failure Rate (%)'})
plt.title('Bank Pair Failure Rate Heatmap (Payer Bank vs Payee Bank)', fontsize=13, fontweight='bold', pad=15)
plt.xlabel('Payee Bank', fontsize=11, fontweight='bold')
plt.ylabel('Payer Bank', fontsize=11, fontweight='bold')
plt.tight_layout()
g4_path = os.path.join(DASH_DIR, "graph4_bank_pair_heatmap.png")
plt.savefig(g4_path, dpi=300)
shutil.copy(g4_path, os.path.join(ARTIFACT_DIR, "graph4_bank_pair_heatmap.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 5: Hourly Peak Hours Traffic & Degradation
# -----------------------------------------------------------------------------
df_hourly = con.execute("""
    SELECT 
        EXTRACT(HOUR FROM CAST(timestamp AS TIMESTAMP)) AS hour_of_day,
        COUNT(*) AS total_txns,
        ROUND(100.0 * SUM(CASE WHEN final_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS psr_pct,
        ROUND(100.0 * SUM(CASE WHEN failure_code LIKE 'ERR_TD%' THEN 1 ELSE 0 END) / COUNT(*), 2) AS td_rate_pct
    FROM transactions
    GROUP BY hour_of_day
    ORDER BY hour_of_day ASC
""").df()

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()

ax1.bar(df_hourly['hour_of_day'], df_hourly['total_txns'], color='#e0e0e0', alpha=0.7, label='Transaction Volume')
ax2.plot(df_hourly['hour_of_day'], df_hourly['psr_pct'], color='#2e7d32', marker='o', linewidth=2.5, label='PSR %')
ax2.plot(df_hourly['hour_of_day'], df_hourly['td_rate_pct'], color='#c62828', marker='s', linestyle='--', linewidth=2, label='Technical Decline %')

ax1.axvspan(18.5, 21.5, color='#ffcdd2', alpha=0.35, label='Peak Evening Window (19:00 - 21:00 IST)')

ax1.set_xlabel('Hour of Day (00:00 - 23:00)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Transaction Volume', fontsize=11, color='#424242', fontweight='bold')
ax2.set_ylabel('Percentage (%)', fontsize=11, color='#c62828', fontweight='bold')
plt.title('Hourly System Volume vs Payment Success Rate (PSR) & TD Congestion', fontsize=13, fontweight='bold', pad=15)
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')
plt.tight_layout()
g5_path = os.path.join(DASH_DIR, "graph5_hourly_peak_trend.png")
plt.savefig(g5_path, dpi=300)
shutil.copy(g5_path, os.path.join(ARTIFACT_DIR, "graph5_hourly_peak_trend.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 6: 7-Stage Payment Journey Funnel Volume & Drop-offs
# -----------------------------------------------------------------------------
df_funnel = con.execute("""
    WITH StageNames AS (
        SELECT 1 AS stage_id, '1. INITIATED' AS stage_name UNION ALL
        SELECT 2, '2. REQUEST_SENT' UNION ALL
        SELECT 3, '3. AUTHENTICATION' UNION ALL
        SELECT 4, '4. BANK_PROCESSING' UNION ALL
        SELECT 5, '5. AUTHORIZATION' UNION ALL
        SELECT 6, '6. CONFIRMATION' UNION ALL
        SELECT 7, '7. COMPLETED'
    )
    SELECT 
        sn.stage_name,
        COUNT(DISTINCT se.transaction_id) AS volume
    FROM StageNames sn
    JOIN stage_events se ON sn.stage_id = se.stage_id
    GROUP BY sn.stage_name, sn.stage_id
    ORDER BY sn.stage_id ASC
""").df()

plt.figure(figsize=(10, 5))
colors = ['#1e88e5', '#1e88e5', '#fb8c00', '#e53935', '#fb8c00', '#43a047', '#43a047']
bars = plt.bar(df_funnel['stage_name'], df_funnel['volume'], color=colors, width=0.55)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 600, f'{yval:,}', ha='center', va='bottom', fontweight='bold', fontsize=10)
plt.xticks(rotation=20, ha='right', fontweight='bold')
plt.ylabel('Transaction Count', fontsize=11, fontweight='bold')
plt.ylim(0, max(df_funnel['volume']) * 1.15)
plt.title('7-Stage Payment Journey Funnel Volume (Stage 4 Bank Processing = Main Bottleneck)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
g6_path = os.path.join(DASH_DIR, "graph6_funnel_dropoff.png")
plt.savefig(g6_path, dpi=300)
shutil.copy(g6_path, os.path.join(ARTIFACT_DIR, "graph6_funnel_dropoff.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 7: Retry Success Rate by Error Category & Policy
# -----------------------------------------------------------------------------
df_retry = con.execute("""
    WITH SequentialTransactions AS (
        SELECT 
            transaction_id, user_id, amount, timestamp, final_status, failure_code,
            LEAD(transaction_id) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_txn_id,
            LEAD(final_status) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_status,
            LEAD(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp ASC) AS next_timestamp
        FROM transactions
    ),
    RetryAttempts AS (
        SELECT 
            failure_code, next_status,
            EXTRACT(EPOCH FROM (CAST(next_timestamp AS TIMESTAMP) - CAST(timestamp AS TIMESTAMP))) AS gap_sec
        FROM SequentialTransactions
        WHERE final_status = 'FAILED' AND next_txn_id IS NOT NULL AND EXTRACT(EPOCH FROM (CAST(next_timestamp AS TIMESTAMP) - CAST(timestamp AS TIMESTAMP))) <= 900
    )
    SELECT 
        e.error_category,
        COUNT(*) AS total_retries,
        ROUND(100.0 * SUM(CASE WHEN r.next_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(*), 2) AS retry_success_rate
    FROM RetryAttempts r
    JOIN error_codes e ON r.failure_code = e.error_code
    GROUP BY e.error_category
""").df()

plt.figure(figsize=(8, 4.5))
bars = plt.bar(df_retry['error_category'], df_retry['retry_success_rate'], color=['#e53935', '#fb8c00', '#039be5'], width=0.45)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f'{yval}%', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.ylim(0, 100)
plt.ylabel('Retry Success Rate (%)', fontsize=11, fontweight='bold')
plt.title('Retry Success Rate by Error Category (Transient vs Hard Declines)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
g7_path = os.path.join(DASH_DIR, "graph7_retry_conversion.png")
plt.savefig(g7_path, dpi=300)
shutil.copy(g7_path, os.path.join(ARTIFACT_DIR, "graph7_retry_conversion.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 8: User Segment Impact & Severe Failure Friction
# -----------------------------------------------------------------------------
df_users = con.execute("""
    WITH UserFailureSummary AS (
        SELECT 
            u.user_id,
            u.user_segment,
            COUNT(t.transaction_id) AS user_total_txns,
            SUM(CASE WHEN t.final_status = 'FAILED' THEN 1 ELSE 0 END) AS user_failed_txns
        FROM users u
        JOIN transactions t ON u.user_id = t.user_id
        GROUP BY u.user_id, u.user_segment
    )
    SELECT 
        user_segment,
        ROUND(100.0 * SUM(CASE WHEN user_failed_txns >= 3 THEN 1 ELSE 0 END) / COUNT(user_id), 2) AS pct_severely_impacted
    FROM UserFailureSummary
    GROUP BY user_segment
    ORDER BY pct_severely_impacted DESC
""").df()

plt.figure(figsize=(8, 4.5))
bars = plt.bar(df_users['user_segment'], df_users['pct_severely_impacted'], color='#8e24aa', width=0.5)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f'{yval}%', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.ylabel('Users with >= 3 Failures (%)', fontsize=11, fontweight='bold')
plt.title('Percentage of Users Suffering Repeated Failures (>= 3 Failures) by Segment', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
g8_path = os.path.join(DASH_DIR, "graph8_user_segment_impact.png")
plt.savefig(g8_path, dpi=300)
shutil.copy(g8_path, os.path.join(ARTIFACT_DIR, "graph8_user_segment_impact.png"))
plt.close()

# -----------------------------------------------------------------------------
# GRAPH 9: Financial Recovery Potential (Conservative, Base, Optimistic)
# -----------------------------------------------------------------------------
df_impact = pd.DataFrame({
    'Scenario': ['Conservative\n(15% Tech + 10% Soft BD)', 'Base-Case\n(35% Tech + 25% Soft BD)', 'Optimistic\n(60% Tech + 45% Soft BD)'],
    'Recovered_INR': [385000, 940000, 1680000]
})

plt.figure(figsize=(8.5, 4.5))
bars = plt.bar(df_impact['Scenario'], df_impact['Recovered_INR'] / 100000, color=['#90caf9', '#1e88e5', '#0d47a1'], width=0.45)
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.2, f'₹{yval:.2f} Lakhs', ha='center', va='bottom', fontweight='bold', fontsize=11)
plt.ylabel('Recovered Value (INR Lakhs)', fontsize=11, fontweight='bold')
plt.title('Financial Value Recovery Estimation (Product Interventions)', fontsize=13, fontweight='bold', pad=15)
plt.tight_layout()
g9_path = os.path.join(DASH_DIR, "graph9_financial_recovery.png")
plt.savefig(g9_path, dpi=300)
shutil.copy(g9_path, os.path.join(ARTIFACT_DIR, "graph9_financial_recovery.png"))
plt.close()

print(f"Successfully generated all 9 analytical graphs in both {DASH_DIR} and {ARTIFACT_DIR}!")
