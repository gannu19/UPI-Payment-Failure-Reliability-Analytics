# Experiment Design Framework: A/B Testing Smart Failure Experience

## 1. Experiment Overview

* **Experiment Name**: `EXP_UPI_SMART_FAILURE_RECOVERY_V1`
* **Feature Under Test**: Smart Failure UX + Intent-Aware Auto-Retry Engine vs Control
* **Owner**: Payment Reliability Product Team

---

## 2. Hypothesis

Providing contextual failure explanations based on exact error categories and automatically executing background retries for transient technical declines will increase overall **Payment Success Rate (PSR)** by **+2.5 percentage points** and improve **Retry Success Rate** by **+15 percentage points** without increasing duplicate debits or payment initiation drop-offs.

---

## 3. Experiment Variants

* **Control Group (50% traffic)**:
  * Current payment failure modal ("Payment Failed. Please try again.").
  * Manual user retry button for all failure types.
* **Treatment Group (50% traffic)**:
  * **Smart Failure UX**: Context-aware modal tailored to specific error codes (`ERR_TD`, `ERR_BD_01`, `ERR_BD_02`, `ERR_NET`).
  * **Auto-Retry Engine**: Automatic single background retry for transient `ERR_TD` and `ERR_NET` errors within 3-5 seconds.
  * **Pre-Decline Bank Nudge**: Switch bank recommendation if selected bank rolling PSR < 88%.

---

## 4. Metric Definitions

### Primary Metric
* **Payment Success Rate (PSR)**: `Successful Transactions / Total Initiated Transactions`
  * *Target*: Statistical significance at $p < 0.05$ with minimum detectible effect (MDE) of +1.5%.

### Secondary Metrics
* **Retry Success Rate**: `Successful Retries / Total Retried Failed Transactions` (Target: +15%).
* **Payment Completion Time**: Average duration from initiation to final success state (Target: < 3.5 seconds).
* **Payment Funnel Drop-off Rate**: Percentage of users abandoning app after experiencing a failure (Target: -20% reduction).

### Guardrail Metrics (Zero Tolerance Thresholds)
* **Duplicate Payment Rate**: `Duplicate Debits for Same Intent / Total Completed` — **Must equal 0.00%**.
* **Refund Request Rate**: Customer support refund disputes per 10,000 transactions — **Must not increase by > 0.05%**.
* **Customer Support Contact Rate**: Payment failure ticket tickets per 1,000 txns — **Must drop by >= 10%**.

---

## 5. Experiment Setup & Sample Size

* **Randomization Unit**: `user_id` (Salted hash of user_id to ensure consistent experience across sessions).
* **Target Sample Size**: Minimum **100,000 users per variant** over a 14-day duration to achieve 80% statistical power at $\alpha = 0.05$.
* **Exclusion Criteria**: Transactions with test merchant credentials or non-standard UPI app versions (< v12.0).

---

## 6. Success & Failure Criteria

### Launch / Rollout Criteria
1. Statistically significant increase in primary metric (PSR $p < 0.05$).
2. Guardrail metrics strictly satisfied (Zero increase in duplicate payment rate).
3. Customer support volume for payment failures drops by at least 10%.

### Rollback / Kill Switch Triggers
1. Duplicate payment rate > 0.01%.
2. Payment initiation drop-off rate increases by > 0.5%.
3. Server API latency increases by > 200ms due to retry loops.
