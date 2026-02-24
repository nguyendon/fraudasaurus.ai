# Fraudasaurus — Investigation & Solution Plan

## Context

Jack Henry DevCon 2026 hackathon challenge: identify fraud in ARFI's data, find the bad actor "CarMeg SanDiego", and propose a detection/prevention solution. Graded on: problem identification, technical approach, creativity, and feasibility.

The prompt hints at these fraud types: **account takeover, dormant account abuse, high-risk digital actions, structuring, and kiting**. CarMeg uses social engineering, knows regulatory limits ($10k CTR threshold), and targets slow-to-notice clients.

---

## Findings

### Finding 1: Structuring — $7,980 Repeat Transfers

**The clearest fraud signal in the dataset.** Six accounts making identical $7,980 transfers (just under the $10k CTR threshold) repeatedly over 18+ months.

| AccountId | Total $7,980 Txns | Days Active | Total Moved | Member # |
|---|---|---|---|---|
| 8d857485... | 351 | 183 | $2,800,980 | 39903 |
| db903a36... | 315 | 174 | $2,513,700 | 7000 |
| 4d847cfd... | 291 | 161 | $2,322,180 | 33250 |
| cb9e5eca... | 277 | 154 | $2,210,460 | (no member #) |
| bd4f341d... | 260 | 141 | $2,074,800 | (no member #) |
| 6e86aaaa... | 253 | 135 | $2,018,940 | 39903 |

**Pattern:** Exactly $7,980 x 4-5 per day = $31,920-$39,900/day. Always under $10k per transaction. Running since April 2024. Some memos reference "DEPOSIT AT ATM... JLASTNAME TX".

**Users behind these accounts:**

| Username | Name | Email | Member # |
|---|---|---|---|
| marielong | MARIE LONG | kwohlschlegel@jackhenry.com | 39903 |
| xroguex | ANNA MARIE | mbannister@symitar.com | 7000 |
| iloveroe | LULA ROE | mbannister@jackhenry.com | 33250 |
| (no username) | Koral Wohlschlegel | kwohlschlegel@jackhenry.com | 39903 |

### Finding 2: CarMeg SanDiego = Meg Bannister

**CarMeg = Car + Meg. The hackathon organizer IS the villain.**

Meg Bannister has **11 user accounts** registered under various mbannister@ emails, using aliases like LULA ROE, ANNA MARIE, GREGORY HOUSE, and operating under usernames including `ilovemlms`, `iloveroe`, `xroguex`, `lularoe`, `megatoptimus`, `studentmeg`, `megatbusybee`, and `ghouse`.

Key evidence:
- Multiple accounts tied to `mbannister@jackhenry.com`, `mbannister@symitar.com`, `mbannister@gMAL.com`
- The "LULA ROE" accounts are doing the $7,980 structuring
- `ilovemlms` had 25 failed logins (result_id=2) from 5 different IPs — brute force / credential stuffing pattern
- Account `A3ZXNHPWONQ6` created Nov 2025 — random-looking username, likely automated
- "Lula Local" created Jan 2026 — still creating new accounts

### Finding 3: Account Takeover Signals

**Top suspicious login patterns:**

| Username | Total Attempts | Failed | Distinct IPs | Notes |
|---|---|---|---|---|
| bannowanda1 | 151 | 59 | 12 | 39% failure rate, many IPs |
| ilovemlms | 31 | 25 | 5 | 81% failure rate — brute force |
| brandygalloway06@yahoo.com | 14 | 14 | 1 | 100% fail, rapid-fire (2 min window) |
| jessica | 6 | 6 | 6 | Every attempt from different IP |
| mjones1051 | 5 | 5 | 1 | All failures in 3 minutes |

`bannowanda1` is particularly interesting: registered as JAMES B EVANS but email is `mposkey@jackhenry.com` — name doesn't match the email.

`wandaa1` / `Wandaa1` (same person WANDA ADOMYETZ) logs in from **25 distinct IPs** including international-looking addresses.

### Finding 4: Dormant Account Abuse

Two Symitar accounts with `lastfmdate` before 2020 (dormant in core) still show active Banno transactions:

| Member # | Last Core Activity | Banno Txn Count | Banno Total | Banno Date Range |
|---|---|---|---|---|
| 0000000006 | 2012-10-26 | 3,120 | $4,094,081 | 2012-02 to 2024-03 |
| 0000034996 | 2019-10-01 | 1,113 | $145,736 | 2022-12 to 2024-03 |

Member 6 is especially suspicious: dormant since 2012 in Symitar but $4M in digital transactions.

### Finding 5: Login Result Codes

| ID | Name | Description |
|---|---|---|
| 1 | (success) | Successful login |
| 2 | (failure) | Failed login |
| 4 | Dormant Account | User has a dormant account |
| 7 | No Valid Account | No valid accounts found |
| 10 | Service Unavailable | Login during outage |
| 11 | Customer Not Found | Customer not in system |
| 14 | UnknownIp | Login from unknown IP (NetTeller Cash Mgmt) |

### Finding 6: NSF / Kiting Indicators

All high-NSF accounts show `nsf_6mo_total = 183` and `nsf_12mo_total = 365` — this appears to be system default/max values on old accounts rather than actual kiting. Most have `lastfmdate = 1995-01-27`. Real kiting signal would need to come from cross-referencing rapid deposits + withdrawals in `transactions_fct`.

---

## Problem Statement

"How can ARFI automatically detect and interrupt multi-channel fraud — including structuring, account takeover, and dormant account abuse — using the transaction and login data they already collect?"

---

## Proposed Automated Detection System

### Overview

A scheduled detection pipeline that runs against Banno and Symitar data in BigQuery, scoring every account against a set of rule-based detectors. No ML black boxes — every rule is auditable and explainable, which matters for BSA/AML compliance and CISO sign-off.

### Architecture

```
BigQuery (Banno + Symitar data)
        |
        v
  Scheduled SQL Queries (daily or near-real-time)
        |
        v
  Detector Modules (one per fraud type)
        |
        v
  Risk Scoring Engine (combine signals, weight, deduplicate)
        |
        v
  Alert Output (tiered: critical / high / medium / low)
        |
        v
  Fraud Team Dashboard + Case Management
```

### Detector 1: Structuring

**What it catches:** Accounts breaking large sums into sub-$10k transactions to avoid CTR filing.

**Rules:**
1. **Repeating amount detector** — Flag any account that makes 3+ transactions of the exact same dollar amount (within $0.01) in a 7-day window where that amount is between $3,000 and $9,999. This catches the $7,980 pattern directly.
2. **Daily aggregation detector** — For each account, sum all cash-like transactions (deposits, withdrawals, transfers) per calendar day. Flag if the daily total exceeds $10,000 but no single transaction does.
3. **Rolling window detector** — Same as above but across a rolling 3-day and 7-day window. Structurers who spread across days get caught here.
4. **Round number avoidance** — Flag transactions at amounts like $9,900, $9,500, $8,000, $7,980, $7,500 that repeat. Legitimate transactions rarely land on the same amount repeatedly.

**Thresholds (tunable):**
- Single amount repeats: >= 3 times in 7 days at $3k-$9,999 → HIGH
- Daily sub-$10k total > $10k: → HIGH
- Weekly sub-$10k total > $25k: → CRITICAL
- Same dollar amount > 10 times in 30 days: → CRITICAL

**Why it works on this data:** The $7,980 pattern would be flagged on day one. Six accounts doing identical $7,980 transfers 4x/day would immediately trigger both the repeating-amount and daily-aggregation rules at CRITICAL severity. The system would have caught this in April 2024 instead of letting $13.9M flow through.

### Detector 2: Account Takeover

**What it catches:** Unauthorized access to existing member accounts via credential stuffing, brute force, or social engineering.

**Rules:**
1. **Brute force detector** — Flag usernames with a failure rate > 50% over any 24-hour window, or > 5 consecutive failures.
2. **IP velocity detector** — Flag usernames that log in from > 3 distinct IPs in a 7-day window (excluding known VPN/mobile ranges if available).
3. **Geo-impossible travel** — Join `login_attempts_fct.client_ip` with `ip_geo.ip_to_city`. Flag if the same username logs in from two cities > 500 miles apart within 1 hour.
4. **Post-login behavior change** — After a login from a new IP, flag if the user immediately creates a new scheduled transfer, adds an external account, or changes profile details. These are high-risk actions from an unrecognized device.
5. **Name/email mismatch** — Flag accounts where the registered first/last name doesn't match the email prefix (e.g., JAMES EVANS on `mposkey@` email).

**Thresholds:**
- > 5 failures in 5 minutes from one IP → CRITICAL (active brute force)
- > 50% failure rate over 24h → HIGH
- Login from > 5 distinct IPs in 30 days → MEDIUM
- Geo-impossible travel → CRITICAL
- New external transfer within 1 hour of new-IP login → HIGH

**Why it works on this data:** `bannowanda1` (59 failures, 12 IPs) and `ilovemlms` (25 failures, 5 IPs) would both trigger immediately. `brandygalloway06@yahoo.com` (14 failures in 2 minutes) would trigger the brute force rule at CRITICAL. `jessica` (6 IPs, 6 attempts, all failures) would trigger geo-velocity.

### Detector 3: Dormant Account Abuse

**What it catches:** Accounts that have been inactive in core banking but suddenly show digital activity — a sign that someone has gained unauthorized access to an account whose real owner isn't watching.

**Rules:**
1. **Core-digital gap detector** — Compare `symitar.account_v1_raw.lastfmdate` with the latest Banno transaction date for the same member. Flag if core has been dormant > 12 months but digital transactions exist within the last 90 days.
2. **Reactivation spike** — Flag accounts that go from 0 transactions in a 6-month window to > 5 transactions in a 7-day window.
3. **Dormant login detector** — Use `login_results_deref` result_id=4 ("Dormant Account"). Any login attempt against a dormant account is suspicious. Cross-reference with subsequent successful logins on the same or related account.
4. **New digital enrollment on old account** — Flag when a Banno user is linked (via `user_member_number_associations_fct`) to a Symitar account that was opened > 5 years ago but the Banno user was created in the last 90 days.

**Thresholds:**
- Core dormant > 2 years + any digital activity → HIGH
- Core dormant > 5 years + digital activity > $1,000 → CRITICAL
- New Banno user on account opened > 5 years ago → HIGH
- Dormant login attempt (result_id=4) → MEDIUM

**Why it works on this data:** Member #6 (dormant since 2012, $4M in digital transactions) would trigger at CRITICAL severity immediately. Member #34996 (dormant since 2019, $145k digital) would trigger at HIGH.

### Detector 4: Multi-Identity / Synthetic Identity

**What it catches:** One person operating multiple accounts under different names — what CarMeg was doing.

**Rules:**
1. **Email clustering** — Group all users by email domain + prefix. Flag when the same email (or base email with variations like `mbannister@jackhenry.com` vs `mbannister@symitar.com` vs `mbannister@gMAL.com`) is linked to > 2 user accounts with different names.
2. **Shared-device fingerprint** — Flag when multiple usernames log in from the same IP within the same session window (< 30 minutes).
3. **Account creation velocity** — Flag email addresses associated with > 3 new account creations in a 12-month period.
4. **Cross-account money flow** — Flag when money moves between accounts owned by users who share an email or IP. This catches self-dealing and layering.

**Thresholds:**
- Same email base, > 2 user accounts, different names → HIGH
- Same email, > 5 accounts → CRITICAL
- > 3 accounts created in 12 months from same email → HIGH
- Money flowing between accounts sharing an email/IP → CRITICAL

**Why it works on this data:** CarMeg's 11 accounts across 3 email variants with 6+ different names would trigger at CRITICAL on every rule. The cross-account $7,980 transfers between her own accounts would also light up the cross-account money flow rule.

### Risk Scoring

Each detector produces alerts with a severity. The scoring engine combines them:

| Severity | Points |
|---|---|
| CRITICAL | 40 |
| HIGH | 25 |
| MEDIUM | 10 |
| LOW | 5 |

An account's **risk score** = sum of all active alert points, capped at 100. Accounts hitting multiple detectors get compounding scores:

- CarMeg's accounts: structuring (CRITICAL, 40) + multi-identity (CRITICAL, 40) + account takeover signals (HIGH, 25) = **100** (capped)
- Member #6: dormant abuse (CRITICAL, 40) = **40**
- bannowanda1: brute force (CRITICAL, 40) + IP velocity (HIGH, 25) = **65**

### Alert Tiers and Recommended Actions

| Score | Tier | Action |
|---|---|---|
| 80-100 | CRITICAL | Freeze account immediately, notify BSA officer, file SAR |
| 50-79 | HIGH | Restrict digital access, require in-branch verification within 24h |
| 25-49 | MEDIUM | Flag for fraud team review within 48h |
| 1-24 | LOW | Add to monitoring watchlist, review at next audit cycle |

### Implementation

**Option A: Scheduled BigQuery SQL (simplest, recommended for ARFI)**

Run each detector as a scheduled BigQuery query (daily at minimum, hourly if possible). Output to a `fraud_alerts` table. Build a simple dashboard (Looker Studio, free with BigQuery) on top.

- Zero new infrastructure
- Uses data ARFI already has in BigQuery
- SQL is auditable — compliance team can read and approve every rule
- Add/tune rules by editing SQL, no code deployment needed
- Cost: effectively free (BigQuery on-demand pricing, small data volume)

**Option B: Python service (more flexible, needed for real-time)**

Run `src/detect.py` as a scheduled job or event-driven service. Same rules as SQL but with the ability to:
- Send email/Slack alerts in real time
- Maintain state (e.g., rolling windows, IP history per user)
- Integrate with case management or ticketing
- Add ML scoring later as a second layer

**Option C: Hybrid (best of both)**

Use BigQuery scheduled queries for batch detection (daily). Use a lightweight Python Cloud Function triggered on new login events for real-time account takeover detection. Both feed into the same `fraud_alerts` table and dashboard.

### What This Would Have Caught

| Fraud | When Detected | How Long It Ran | Amount Prevented |
|---|---|---|---|
| $7,980 structuring | April 2024 (day 1) | 18+ months undetected | Up to $13.9M |
| CarMeg multi-identity | First duplicate account creation | Years of operation | Full exposure |
| Member #6 dormant abuse | First digital txn post-dormancy | 12+ years gap | Up to $4M |
| bannowanda1 brute force | First 5-failure burst | Months of attempts | Account compromise |

---

## What's Done (on `main`)

### Data access & extraction
- [x] BigQuery access configured (project `jhdevcon2026`, `bq` CLI at `/private/tmp/gcloud/google-cloud-sdk/bin/bq`)
- [x] `src/extract.py` — pulls BigQuery tables to local parquet (optional, not required for pipeline)
- [x] `requirements.txt` — all Python dependencies
- [x] `README.md` — full data catalog with schemas, row counts, example queries

### Investigation queries
- [x] `sql/00_reference.sql` — reference lookups (transaction types, login codes, user-member mapping)
- [x] `sql/01_structuring_detection.sql` — $7,980 pattern and daily aggregation queries
- [x] `sql/02_account_takeover.sql` — login anomaly and brute force queries
- [x] `sql/03_dormant_account_abuse.sql` — dormant core + active digital queries
- [x] `sql/04_kiting_nsf.sql` — NSF/kiting queries
- [x] `sql/05_find_carmeg.sql` — CarMeg identity and alias queries

### Findings documented (in this plan)
- [x] Structuring: $7,980 x 6 accounts = $13.9M
- [x] CarMeg identified: Meg Bannister, 11 accounts, multiple aliases
- [x] Account takeover signals: bannowanda1, ilovemlms, brandygalloway06
- [x] Dormant abuse: Member #6 ($4M), Member #34996 ($145k)
- [x] Detection system design: 4 detectors, risk scoring, alert tiers, implementation options

### NOT on main (was on a different branch, not merged)
The following files were created by another agent on a separate branch but are **not available on main**. They had column mapping issues with the actual BigQuery data anyway, so we're building fresh:
- ~~`src/detectors/*.py`~~ — structuring, account_takeover, dormant, kiting detectors
- ~~`src/scoring.py`, `src/clean.py`, `src/features.py`, `src/visualize.py`, `src/report.py`, `src/ingest.py`~~
- ~~`notebooks/`~~ — 5 Jupyter notebooks

---

## What's Left

Data approach: query BigQuery directly, no local extract needed. All queries return in seconds. Use `google.cloud.bigquery.Client` to get DataFrames.

Prerequisite (manual, one-time): run `gcloud auth application-default login` so the Python BigQuery client can authenticate.

Since the detector pipeline from the other branch is not on main and had compatibility issues with the actual BigQuery column names (e.g., `AccountId` not `account_id`, `DatePosted` not `transaction_date`, ATO detector expected columns that don't exist, dormant detector needed cross-table join), we're writing all pipeline code fresh — designed directly against the real BigQuery schemas documented in README.md.

---

### Task A: Write the BigQuery data loader

**File:** `src/bq_loader.py`

Write a module that queries BigQuery and returns pandas DataFrames. No local files — just query and return.

Functions needed:
- `get_client()` — returns authenticated `bigquery.Client(project="jhdevcon2026")`
- `load_transactions()` — query `banno_operation_and_transaction_data.transactions_fct`
- `load_login_attempts()` — query `banno_operation_and_transaction_data.login_attempts_fct`
- `load_users()` — query `banno_operation_and_transaction_data.users_fct`
- `load_user_member_associations()` — query `banno_operation_and_transaction_data.user_member_number_associations_fct`
- `load_scheduled_transfers()` — query `banno_operation_and_transaction_data.scheduled_transfers_fct`
- `load_rdc_deposits()` — query `banno_operation_and_transaction_data.rdc_deposits_fct`
- `load_user_edits()` — query `banno_operation_and_transaction_data.user_edits_fct`
- `load_symitar_accounts()` — query `symitar.account_v1_raw`
- `load_login_results()` — query `banno_operation_and_transaction_data.login_results_deref`
- `run_query(sql)` — run arbitrary SQL, return DataFrame (for ad-hoc use)

Keep it simple — `client.query(sql).to_dataframe()`. Use the actual BigQuery column names as-is (no renaming).

---

### Task B: Write the fraud detectors (blocks D, E)

**Files:** `src/detectors/__init__.py`, `src/detectors/structuring.py`, `src/detectors/account_takeover.py`, `src/detectors/dormant.py`, `src/detectors/multi_identity.py`

Write 4 detector modules from scratch, designed against the **actual BigQuery column names** from README.md. Each detector takes DataFrames from `bq_loader` and returns a list of alerts.

**Alert format** (consistent across all detectors):
```python
{
    "account_id": str,       # AccountId from transactions or account number
    "user_id": str,          # UserId if available
    "member_number": str,    # member_number if available
    "fraud_type": str,       # "structuring" | "account_takeover" | "dormant_abuse" | "multi_identity"
    "severity": str,         # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    "score": int,            # 0-100
    "evidence": str,         # human-readable description of what was found
}
```

**Structuring detector** — uses `transactions_fct` DataFrame:
- Columns available: `AccountId`, `DatePosted`, `Amount`, `BannoType`, `CleanMemo`, `Memo`, `UserId`, `RunningBalance`
- Rule 1: Flag accounts with 3+ transactions of the same amount ($3k-$9,999) in a 7-day window
- Rule 2: Flag accounts where daily sum > $10k but no single txn > $10k
- Rule 3: Flag the specific $7,980 repeat pattern (our strongest finding)
- Score based on frequency and total amount moved

**Account takeover detector** — uses `login_attempts_fct` + `login_results_deref` + `user_edits_fct` DataFrames:
- Login columns: `username`, `result_id`, `attempted_at`, `client_ip`
- Rule 1: Failure rate > 50% in 24h window
- Rule 2: > 5 consecutive failures
- Rule 3: > 3 distinct IPs in 7 days
- Rule 4: Profile edits (`user_edits_fct`) within 1 hour of login from new IP
- Score based on failure rate, IP diversity, behavioral changes

**Dormant account detector** — uses `symitar.account_v1_raw` + `transactions_fct` DataFrames:
- Symitar columns: `number` (account #), `lastfmdate`, `memberstatus`, `opendate`
- Rule 1: `lastfmdate` > 12 months ago but Banno transactions exist in last 90 days (cross-table join on member_number)
- Rule 2: `lastfmdate` > 5 years ago + digital activity > $1,000 → CRITICAL
- Score based on dormancy duration and digital transaction volume

**Multi-identity detector** — uses `users_fct` + `user_member_number_associations_fct` + `login_attempts_fct` DataFrames:
- User columns: `user_id`, `primary_institution_username`, `first_name`, `last_name`, `email`, `user_added_dt`, `user_active`
- Rule 1: Same email base across > 2 user accounts with different names
- Rule 2: > 3 accounts created from same email in 12 months
- Rule 3: Multiple usernames logging in from same IP within 30 minutes
- Score based on number of identities and cross-account activity

---

### Task C: Write the orchestrator and scoring (blocks E)

**Files:** `src/run_detectors.py`, `src/scoring.py`

**`src/scoring.py`:**
- Takes list of alerts from all detectors
- Combines per-account: sum scores, cap at 100
- Assigns tier: CRITICAL (80-100), HIGH (50-79), MEDIUM (25-49), LOW (1-24)
- Deduplicates (same account flagged by multiple detectors gets one row with combined score)

**`src/run_detectors.py`:**
- Loads data via `src/bq_loader.py`
- Runs all 4 detectors
- Scores and tiers results via `src/scoring.py`
- Outputs combined DataFrame, saves to `output/fraud_alerts.csv`
- Prints summary to stdout (top 10 accounts, score distribution)
- Run with: `python3 -m src.run_detectors`

---

### Task D: Generate visualizations (runs after B/C)

**File:** `src/generate_viz.py`

Write a standalone script that queries BigQuery and produces figures. Save to `output/figures/`.

**D1: Structuring timeline** (`structuring_timeline.png`)
- X: date (April 2024 — present), Y: daily count of $7,980 transactions
- Color by AccountId, show 6 structuring accounts
- Data: `transactions_fct WHERE ABS(Amount) = 7980`

**D2: CarMeg account network** (`carmeg_network.png`)
- NetworkX graph: nodes = CarMeg's user accounts (labeled username + name)
- Edges = shared emails, money flows between accounts
- Color nodes by creation date
- Data: `users_fct WHERE email LIKE '%bannister%'`

**D3: Login anomaly chart** (`login_anomalies.png`)
- Bar chart: top 15 usernames by failure count
- Stacked success vs failure bars
- Annotate distinct IP count
- Data: `login_attempts_fct`

**D4: Risk score heatmap** (`risk_heatmap.png`)
- Rows = flagged accounts, columns = fraud types
- Cell values = risk scores from `output/fraud_alerts.csv`
- Sort by composite score descending

---

### Task E: Write the submission document (can start early, finalize after D)

**File:** `output/submission.md`

Write the final hackathon submission. Structure:

1. **Problem Statement** — "How can ARFI detect and interrupt multi-channel fraud before funds leave?"
2. **The Investigation** — data sources, tools, approach (5 parallel analyses)
3. **Findings** — all 4 findings with specific evidence (account IDs, amounts, dates, usernames from this plan)
4. **Proposed Solution** — architecture, 4 detectors, rules, risk scoring, alert tiers, implementation options
5. **Impact** — "what this would have caught" table, $13.9M structuring + $4M dormant
6. **Why It's Feasible** — uses existing data, rule-based, auditable, zero new infrastructure

Reference all specific data from the Findings section above. Embed figures from Task D.

---

### Task F: Integration test (runs last)

1. `python3 -m src.run_detectors` — produces `output/fraud_alerts.csv`
2. `python3 -m src.generate_viz` — produces all 4 figures
3. Verify CarMeg's accounts appear at CRITICAL tier
4. Verify $7,980 structuring accounts are flagged
5. Fix any issues

---

### Dependency graph

```
Task A (bq_loader) ──> Task B (detectors) ──> Task C (orchestrator + scoring) ──> Task F (integration test)
                                                       │
                                                       └──> Task D (visualizations) ──> Task F

Task E (submission doc) ── can start early, finalize after D ──> Task F
```

Tasks A and E can start immediately in parallel.
Task B starts after A.
Tasks C and D start after B.
Task F runs last to verify everything works.
