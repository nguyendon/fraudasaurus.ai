# Fraudasaurus — Investigation & Solution Plan

## Context

Jack Henry DevCon 2026 hackathon challenge: identify fraud in ARFI's data, find the bad actor "CarMeg SanDiego", and propose a detection/prevention solution. Graded on: problem identification, technical approach, creativity, and feasibility.

The prompt hints at these fraud types: **account takeover, dormant account abuse, high-risk digital actions, structuring, and kiting**. CarMeg uses social engineering, knows regulatory limits ($10k CTR threshold), and targets slow-to-notice clients.

## Phase 1: Extract & Profile Data

Run `src/extract.py` to pull all tables to local parquet. Fix the partitioned `user_activity_fct` table (needs date filter). Skip `ip_geo` initially (11M rows, reference only — join in BQ as needed).

**Files:** `src/extract.py` (already written)

## Phase 2: Run Fraud Detection Queries

Run these 5 analyses as SQL against BigQuery. Each targets a specific fraud type from the prompt.

### Analysis 1: Structuring Detection

Transactions just under $10,000 (the CTR reporting threshold). CarMeg has "an acute awareness of regulatory limits."

- Find accounts with multiple cash-like transactions between $3,000-$9,999 within short windows
- Flag accounts where daily/weekly totals exceed $10k but no single transaction does
- Look at BannoType and Memo fields for cash deposit/withdrawal patterns

### Analysis 2: Account Takeover

Login anomalies + profile changes + unusual transactions in sequence.

- Failed login attempts followed by successful ones (login_attempts_fct, result_id patterns)
- Logins from new/unusual IPs (geo-shift detection via ip_geo join)
- Profile changes (user_edits_fct) shortly before or after login anomalies
- New scheduled transfers or external transfers created after suspicious logins

### Analysis 3: Dormant Account Abuse

CarMeg "identifies slow-to-notice clients."

- Find accounts with long inactivity gaps (symitar.account_v1_raw.lastfmdate) followed by sudden transaction bursts
- Cross-reference with login_attempts to see if dormant accounts suddenly get digital access
- Check if new EFTs or external accounts were added to long-dormant members

### Analysis 4: Check Kiting

Moving money between accounts to exploit float.

- Rapid check deposits followed by immediate withdrawals before clearing
- Accounts with high NSF counts (nsfmonthlycount fields in account_v1_raw)
- Round-trip transfers between related accounts (same household via household_raw)
- RDC deposits (rdc_deposits_fct) with subsequent fast withdrawals

### Analysis 5: Find CarMeg SanDiego

Cross-reference all anomalies to find the common thread.

- Which user/account appears across multiple fraud signals?
- Look for accounts touching 2+ fraud categories (structuring AND takeover, etc.)
- Check for any name/memo fields containing hints ("CarMeg", "SanDiego", camelCase references)
- Look at user_demographic_details_fct for unusual patterns
- Check comment_raw for fraud team notes about suspicious members

## Phase 3: Build Detection Script

Write `src/detect.py` — a Python script that runs each analysis and outputs flagged accounts with a risk score.

```
Input:  BigQuery tables (via query) or local parquet files
Output: CSV/JSON of flagged accounts with:
  - account_id / user_id
  - fraud_type (structuring, takeover, dormant, kiting)
  - risk_score (0-100)
  - evidence (list of specific transactions/events)
  - recommended_action
```

## Phase 4: Propose the Solution

Frame it as a practical, implementable system ARFI could actually deploy:

1. **Problem Statement:** "How can ARFI detect and interrupt multi-channel fraud — including structuring, account takeover, and dormant account abuse — before funds leave the institution?"

2. **Solution: Real-time fraud scoring pipeline**
   - Ingest transactions and login events as they happen
   - Score each event against rule-based detectors (structuring thresholds, geo-anomaly, dormancy windows)
   - Generate alerts with priority tiers (investigate immediately / review within 24h / flag for audit)
   - Dashboard showing flagged accounts with evidence trail

3. **Why it's feasible:**
   - Uses data ARFI already has (Banno + Symitar)
   - Rule-based first (no ML black box, auditable, CISO-friendly)
   - Can run as scheduled BigQuery queries or lightweight Python service
   - Low barrier: SQL + Python, tools they already use

## Phase 5: Build Submission

Create a clear writeup with:
- Problem statement
- Data evidence (specific account numbers, transaction IDs, amounts)
- Detection methodology
- Proposed solution architecture
- Demo: run the detector, show flagged results

## Execution Order

1. Extract data (fix partition issue in extract.py, run extract)
2. Run the 5 analysis queries against BigQuery
3. Build `src/detect.py` with the fraud detectors
4. Identify CarMeg and document evidence
5. Write up findings and solution proposal
