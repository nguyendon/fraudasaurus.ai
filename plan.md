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

### Detector 5: Money Mule Detection

**What it catches:** Accounts used to launder money — receiving funds and immediately transferring them out, leaving little balance.

**Rules:**
1. **High velocity funds** — Flag accounts where (total credits / total debits) is between 0.95 and 1.05 over a 30-day period (money comes in and goes right out).
2. **Low retention** — Flag accounts with high transaction volume (> $10k/month) but average daily balance < $100.
3. **Rapid flow-through** — Flag when a large deposit (> $1,000) is followed by a withdrawal of > 90% of that amount within 24 hours.

**Thresholds:**
- Velocity ~1.0 + Volume > $5k → HIGH
- Rapid flow-through (in/out < 24h) → HIGH

### Detector 6: Elderly Exploitation

**What it catches:** Financial abuse of vulnerable older members.

**Rules:**
1. **Age + unusual activity** — Join `user_demographic_details_fct` (if available) or approximate age from core data. Flag users > 65 with a sudden spike in wire transfers or P2P payments.
2. **New beneficiary spike** — Elderly user adds > 2 new transfer recipients in 7 days and sends > $1,000 to them.
3. **Late night activity** — High-value transfers (> $500) initiated between 1 AM and 5 AM local time by an elderly user.

**Thresholds:**
- Age > 65 + New large beneficiary → HIGH
- Age > 75 + Late night high-value transfer → CRITICAL

### Detector 7: Check Kiting (Enhanced)

**What it catches:** Exploiting the "float" time between a check deposit and its clearing.

**Rules:**
1. **Float exploitation** — Flag accounts that deposit a check and withdraw > 50% of the funds before the check clears (using `DatePosted` vs expected clear date).
2. **Cycle detection** — Identify circular flows of checks between two or more accounts (Account A checks deposited to B, B checks to A).
3. **NSF correlation** — High check deposit volume correlated with recent NSF events.

**Thresholds:**
- Withdrawal against uncleared funds > $1,000 → HIGH
- Circular check flow detected → CRITICAL

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

**Option D: Scalable Streaming Architecture (Future State)**

For high-volume, real-time needs (millions of txns/sec), we propose a streaming architecture:
- **Ingest:** Kafka / Google PubSub for real-time transaction and login events.
- **Processing:** Apache Flink or Google Dataflow for stateful stream processing (e.g., calculating rolling windows for velocity checks in real-time).
- **Storage:** BigQuery (for historical patterns) + Redis (for low-latency feature serving).
- **Action:** Real-time API calls to block transactions or step-up authentication (MFA).

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
- [x] BigQuery access configured (project `jhdevcon2026`)
- [x] `src/bq_loader.py` — queries BigQuery directly, returns DataFrames (with tqdm progress bars)
- [x] `pyproject.toml` — all Python dependencies (use `uv sync` to install)
- [x] `README.md` — full data catalog with schemas, row counts, example queries

### Investigation queries
- [x] `sql/00_reference.sql` — reference lookups (transaction types, login codes, user-member mapping)
- [x] `sql/01_structuring_detection.sql` — $7,980 pattern and daily aggregation queries
- [x] `sql/02_account_takeover.sql` — login anomaly and brute force queries
- [x] `sql/03_dormant_account_abuse.sql` — dormant core + active digital queries
- [x] `sql/04_kiting_nsf.sql` — NSF/kiting queries
- [x] `sql/05_find_carmeg.sql` — CarMeg identity and alias queries

### Fraud detection pipeline
- [x] `src/bq_loader.py` — parquet caching in `data/raw/`, column-pruned queries, tqdm progress bars
- [x] `src/detectors/structuring.py` — $7,980 repeat pattern, repeating amounts, daily aggregation
- [x] `src/detectors/account_takeover.py` — brute force, rapid-fire failures, IP velocity, all-fail users
- [x] `src/detectors/dormant.py` — dormant core + active digital cross-reference
- [x] `src/detectors/multi_identity.py` — email clustering, domain variants, creation velocity, shared IPs
- [x] `src/scoring.py` — combines alerts, sums scores per account (capped at 100), assigns tiers
- [x] `src/run_detectors.py` — orchestrator: loads data, runs all 4 detectors, scores, outputs CSV + terminal summary

### Pipeline validated
- [x] Pipeline runs end-to-end: 248 alerts, 204 unique accounts/users flagged
- [x] Tier distribution: 2 CRITICAL, 16 HIGH, 181 MEDIUM, 5 LOW
- [x] All 6 $7,980 structuring accounts detected (score 40 each, MEDIUM tier)
- [x] CarMeg's shared-IP pattern flagged by multi-identity detector
- [x] Brute force / IP velocity flagged for bannowanda1, ilovemlms, brandygalloway06
- [x] Outputs: `output/fraud_alerts.csv` (scored) + `output/fraud_alerts_raw.csv` (raw rule hits)

### Submission document
- [x] `output/submission.md` — problem statement, findings, proposed solution, pipeline results, impact

### Findings documented (in this plan)
- [x] Structuring: $7,980 x 6 accounts = $13.9M
- [x] CarMeg identified: Meg Bannister, 11 accounts, multiple aliases
- [x] Account takeover signals: bannowanda1, ilovemlms, brandygalloway06
- [x] Dormant abuse: Member #6 ($4M), Member #34996 ($145k)
- [x] Detection system design: 4 detectors, risk scoring, alert tiers, implementation options

---

## What's Left

### Known issues
- [ ] **Scoring tier mismatch** — $7,980 structuring accounts score 40 (CRITICAL severity) but land in MEDIUM tier (25-49) because they only trigger one detector. Single-detector CRITICAL alerts should get at least HIGH tier.
- [ ] **Dormant detector** — needs validation; depends on user_member_associations join quality

### Remaining work
- [ ] **Visualizations** — `src/generate_viz.py` (structuring timeline, CarMeg network, login anomalies, risk heatmap) → `output/figures/`
- [ ] **Fix scoring tiers** — CRITICAL severity alerts should never land below HIGH tier
- [ ] **Integration test** — end-to-end run producing `fraud_alerts.csv` + all figures
