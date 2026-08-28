# Product Requirements Document (PRD): Payment Reliability & Failure Experience

## 1. Product Interventions Overview

To address the key root causes identified in our analytical deep-dive, we propose three core product interventions:

1. **Intervention 1: Dynamic Real-time Bank Reliability Indicator & Pre-decline Nudge**
2. **Intervention 2: Contextual Smart Failure Experience & Intent-Aware Auto-Retry Engine**
3. **Intervention 3: Asynchronous Status Ledger with De-duplication Lock**

---

## 2. Detailed Intervention Specifications

### Intervention 1: Dynamic Real-Time Bank Reliability & Pre-Decline Nudge

* **Problem**: Users attempt payments using PSU bank accounts during peak server congestion (7-9 PM), resulting in predictable 11.4% technical declines.
* **Evidence**: SBI and BoB experience severe CBS latency spikes between 19:00 - 21:00 IST; users have alternative linked accounts (e.g. HDFC, ICICI) with 98%+ uptime.
* **Proposed Solution**:
  * Real-time monitoring of bank health metrics (5-minute rolling PSR).
  * If selected bank PSR drops below 88%, display a subtle nudge on payment screen: *"SBI servers are responding slowly right now. Use your HDFC Bank account for faster completion."*
* **Expected Impact**: **+2.5% PSR uplift** across peak traffic windows.
* **Risks**: Potential user hesitation or bank partner sensitivity.
* **Guardrail Metrics**: Payment Initiation Drop-off Rate must not increase by >0.2%.

---

### Intervention 2: Contextual Smart Failure Experience & Intent-Aware Auto-Retry

* **Problem**: Generic failure messages ("Payment Failed. Try again.") trigger blind retries on permanent failures and user drop-off on recoverable network blips.
* **Evidence**: Retries on `ERR_TD` (Technical Decline) succeed 64.8% of the time, while retries on `ERR_BD_01` (Balance) fail 88.8% of the time.
* **Proposed Solution**:
  * **Transient Technical Decline**: Show progress modal — *"Bank connection timed out. We are safely retrying your payment automatically (Attempt 1/2)..."*
  * **Insufficient Balance**: Show clear context — *"Payment could not be processed due to low account balance. Pay using linked wallet or alternative bank account."*
  * **Incorrect MPIN**: Show dedicated PIN reset entry — *"Incorrect MPIN entered. Re-enter MPIN or tap Forgot MPIN."*
* **Expected Impact**: **+3.2% Overall PSR uplift**, +18% Retry Success Rate on recoverable failures.
* **Risks**: Accidental duplicate debits if retry timing collides with delayed CBS execution.
* **Guardrail Metrics**: **Duplicate Payment Rate MUST remain at 0.00%**.

---

### Intervention 3: Asynchronous Status Ledger & Duplicate Lock

* **Problem**: Network timeouts (`ERR_NET_01`) cause pending payment status anxiety, prompting duplicate user attempts while original payment is processing.
* **Evidence**: 540 network timeout events per month; 14% lead to duplicate user payment attempts within 3 minutes.
* **Proposed Solution**:
  * Implement an idempotent transaction lock key (`user_id + payee_id + amount + 180s_window`).
  * If status is pending/ambiguous, lock immediate duplicate attempts and initiate background polling with bank switch.
* **Expected Impact**: 45% reduction in payment support tickets, zero duplicate debits.
* **Guardrail Metrics**: Average time to resolution for pending payments < 15 seconds.

---

## 3. Smart Failure Experience Wireframe & User Flow

```
[ Generic Failure Experience - OLD ]
+------------------------------------------+
|            Payment Failed               |
|                                          |
|      An error occurred. Try again.       |
|                                          |
|            [ RETRY BUTTON ]              |
+------------------------------------------+

[ Smart Contextual Experience - NEW ]
+-----------------------------------------------------------------+
|                      Payment Status Update                       |
|                                                                 |
|  (i) Bank Server Latency Detected                               |
|  State Bank of India is taking longer than usual.               |
|  We are checking status to ensure your account is not debited.  |
|                                                                 |
|  Status: Verifying with NPCI Switch (5s)...                     |
|                                                                 |
|  [ Switch Payment Bank ]        [ Check Account Balance ]       |
+-----------------------------------------------------------------+
```
