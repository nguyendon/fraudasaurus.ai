# Fraudasaurus

Fraud detection for the Jack Henry DevCon 2026 Hack-A-Thon.

## Setup

### 1. Python & dependencies

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and dependencies.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python, create venv, and install all dependencies
uv sync
```

### 2. BigQuery access

```bash
# Authenticate gcloud (one-time)
gcloud auth application-default login

# Test the connection
python -m src.bq_loader
```

### 3. Run the fraud detection pipeline

```bash
# Run all 4 detectors → outputs to output/fraud_alerts.csv
python -m src.run_detectors
```

This queries BigQuery directly (no local data extract needed), runs structuring / account takeover / dormant abuse / multi-identity detectors, scores all alerts, and writes results to `output/fraud_alerts.csv`.

## BigQuery Project

- **Project:** `jhdevcon2026`
- **Console:** https://console.cloud.google.com/bigquery?project=jhdevcon2026

## Datasets

| Dataset | Tables | Source |
|---|---|---|
| `banno_operation_and_transaction_data` | 44 views | Banno digital banking platform |
| `ip_geo` | 2 tables | MaxMind IP geolocation |
| `symitar` | 48+ views | Symitar core banking system (Episys) |

## Row Counts

### Banno (Digital Banking)

| Table | Rows |
|---|---|
| user_activity_fct | 214,602 |
| transactions_fct | 195,788 |
| trx_accounts_fct | 195,788 |
| accounts_type_fct | 160,737 |
| bud_enrichments_fct | 33,095 |
| loan_payment_breakdowns_fct | 6,026 |
| accounts_fct | 2,594 |
| login_attempts_fct | 2,144 |
| transfer_accounts_fct | 1,854 |
| scheduled_transfers_fct | 1,624 |
| user_edits_fct | 367 |
| login_accounts_fct | 336 |
| users_fct | 336 |
| payments_fct | 335 |
| user_bills_fct | 292 |
| user_member_number_associations_fct | 241 |
| user_demographic_details_fct | 198 |
| rdc_deposits_fct | 181 |
| rdc_accounts_fct | 137 |
| consumer_uis_ids_fct | 97 |
| login_results_deref | 15 |
| moov_transactions_fct | 4 |
| moov_accounts_fct | 4 |
| institution_fct | 1 |
| core_login_details_fct | 0 |

### IP Geo (reference/lookup)

| Table | Rows |
|---|---|
| ip_to_city | 8,144,816 |
| maxmind_ipv4_to_city | 3,532,314 |

### Symitar (Core Banking)

| Table | Rows |
|---|---|
| account_v1_raw | 2,888,232 |
| eft_raw | 570,956 |
| check_raw | 542,511 |
| eft_transfer_raw | 259,740 |
| comment_raw | 165,895 |
| card_raw | 151,601 |
| inventory_raw | 137,250 |
| fmhistory_raw | 106,238 |
| glaccount_raw | 24,990 |
| activity_raw | 21,293 |
| collateral_raw | 18,350 |
| glhistory_raw | 16,140 |
| externalloan_raw | 12,240 |
| agreement_raw | 5,184 |
| batchachorig_raw | 1,771 |
| externalaccount_raw | 1,440 |
| household_raw | 940 |
| agreement_transaction_raw | 39 |
| card_access_raw | 0 |
| check_fmhistory_raw | 0 |

## Key Tables & Schemas

### `banno_operation_and_transaction_data.transactions_fct`

All digital banking transactions (checks, transfers, deposits, etc).

| Column | Type | Notes |
|---|---|---|
| AccountId | STRING | Account UUID |
| DatePosted | TIMESTAMP | Transaction date |
| TransactionId | STRING | Unique transaction hash |
| Sequence | INTEGER | Sequence number |
| BannoType | STRING | Transaction type (CHECK, TRANSFER, etc.) |
| SubType | STRING | |
| PendingStatus | STRING | e.g. NoReconciliation |
| InstitutionId | STRING | Institution UUID |
| UserId | STRING | User UUID |
| AccountType | STRING | e.g. Deposit |
| AccountSubType | STRING | e.g. Demand Deposit |
| Amount | NUMERIC | Negative = debit, positive = credit |
| Currency | STRING | e.g. USD |
| CheckNumber | STRING | |
| Memo | STRING | Raw memo text |
| PayeeName | STRING | |
| CleanMemo | STRING | Cleaned/normalized memo |
| Active | BOOLEAN | |
| LastUpdated | TIMESTAMP | |
| CheckImageIds | STRING | JSON array of check image IDs |
| RunningBalance | NUMERIC | Account balance after transaction |
| CreatedAt | TIMESTAMP | |

### `banno_operation_and_transaction_data.login_attempts_fct`

Every login attempt to Banno digital banking, with IP address.

| Column | Type | Notes |
|---|---|---|
| username | STRING | Login username |
| institution_id | STRING | Institution UUID |
| result_id | INTEGER | Login result code |
| attempted_at | TIMESTAMP | When the attempt occurred |
| request_id | STRING | Request trace ID |
| client_ip | STRING | Source IP address |

### `banno_operation_and_transaction_data.user_activity_fct`

User activity events in the digital banking platform.

| Column | Type | Notes |
|---|---|---|
| institution_id | STRING | Institution UUID |
| user_id | STRING | User UUID |
| activity_date | TIMESTAMP | When the activity occurred |
| type | STRING | Activity type |
| mobile | BOOLEAN | Mobile device or not |

### `banno_operation_and_transaction_data.payments_fct`

Bill payments and transfers.

| Column | Type | Notes |
|---|---|---|
| payment_id | STRING | Payment UUID |
| bill_id | STRING | Bill UUID |
| transaction_id | STRING | Linked transaction |
| payable_from_account_id | STRING | Source account |
| amount | BIGNUMERIC | Payment amount |
| is_active | BOOLEAN | |
| estimated_arrival | TIMESTAMP | |
| process_date | TIMESTAMP | |
| fee | BIGNUMERIC | |
| confirmation_id | STRING | |
| merchant_id | STRING | |
| payment_method | INTEGER | |
| processing_state | INTEGER | |
| partner_status | INTEGER | |
| created_at | TIMESTAMP | |
| memo | STRING | |
| schedule | STRING | |
| institution_id | STRING | |

### `banno_operation_and_transaction_data.rdc_deposits_fct`

Remote deposit capture (mobile check deposits).

| Column | Type | Notes |
|---|---|---|
| deposit_id | STRING | Deposit UUID |
| user_id | STRING | User UUID |
| rdc_account_id | STRING | Target account |
| amount | NUMERIC | Deposit amount |
| error_message | STRING | |
| created_at | TIMESTAMP | |
| last_updated | TIMESTAMP | |
| status | INTEGER | Deposit status code |
| detailed_status | STRING | |
| institution_id | STRING | |

### `banno_operation_and_transaction_data.scheduled_transfers_fct`

Scheduled and recurring transfers.

| Column | Type | Notes |
|---|---|---|
| transfer_id | STRING | Transfer UUID |
| user_id | STRING | User UUID |
| from_account_id | STRING | Source account |
| to_account_id | STRING | Destination account |
| amount | NUMERIC | Transfer amount |
| start_date | DATE | |
| frequency | INTEGER | Frequency code |
| transfer_type | INTEGER | |
| created_at | TIMESTAMP | |
| next_transfer_date | DATE | |
| is_external | BOOLEAN | External transfer flag |
| direction | STRING | |
| institution_id | STRING | |

### `banno_operation_and_transaction_data.user_edits_fct`

User edits to transaction metadata (tags, notes, receipts).

| Column | Type | Notes |
|---|---|---|
| AccountId | STRING | Account UUID |
| DatePosted | TIMESTAMP | |
| TransactionId | STRING | |
| Tags | STRING | User-applied tags |
| ReceiptImages | STRING | |
| CheckImages | STRING | |
| Notes | STRING | User notes |
| CheckNumber | STRING | |
| InstitutionId | STRING | |

### `ip_geo.ip_to_city`

IP-to-city geolocation mapping. Join with `login_attempts_fct.client_ip`.

| Column | Type | Notes |
|---|---|---|
| ip_start | STRING | IP range start |
| ip_end | STRING | IP range end |
| continent | STRING | |
| country | STRING | |
| stateprov | STRING | State/province |
| city | STRING | |
| latitude | FLOAT | |
| longitude | FLOAT | |

### `symitar.account_v1_raw`

Core member account records from Symitar.

| Column | Type | Notes |
|---|---|---|
| number | STRING | Member account number |
| type | INTEGER | Account type code |
| opendate | DATE | Account open date |
| closedate | DATE | Account close date (if closed) |
| lastfmdate | DATE | Last financial modification |
| branch | INTEGER | Branch code |
| restrict | INTEGER | Restriction code |
| memberstatus | INTEGER | Member status code |
| frozenmode | INTEGER | Frozen status |
| warningcode_1..20 | INTEGER | Warning codes (up to 20) |
| warningexpiration_1..20 | DATE | Warning expiration dates |
| nsfmonthlycount_1..24 | INTEGER | NSF counts by month (24 months) |
| nsftoday | INTEGER | NSF count today |
| invalidattemptcount | INTEGER | Invalid access attempts |
| invalidattemptdate | DATE | Last invalid attempt date |
| crtotalamount | NUMERIC | Credit total |
| cdtotalamount | NUMERIC | Debit total |
| wrtotalamount | NUMERIC | Withdrawal total |
| wdtotalamount | NUMERIC | Wire debit total |
| householdaccount | STRING | Linked household account |
| createdbyuser | INTEGER | Creating user ID |
| createdatbranch | INTEGER | Creating branch |

### `symitar.fmhistory_raw`

Core financial modification history (audit trail for all account changes).

| Column | Type | Notes |
|---|---|---|
| accountnumber | STRING | Member account number |
| postdate | DATE | Transaction post date |
| posttime | INTEGER | Post time |
| usernumber | INTEGER | Teller/user who made the change |
| useroverride | INTEGER | Override flag |
| branch | INTEGER | Branch where change was made |
| fmtype | INTEGER | Modification type code |
| recordtype | INTEGER | Record type |
| fieldnumber | INTEGER | Field that was modified |
| oldmoney | NUMERIC | Previous amount |
| newmoney | NUMERIC | New amount |
| oldcharacter | STRING | Previous string value |
| newcharacter | STRING | New string value |
| consolenumber | INTEGER | Console number |
| batchsequence | INTEGER | Batch sequence |

## All Tables

### `banno_operation_and_transaction_data`

accounts_fct, accounts_type_fct, bud_enrichments_fct, consumer_uis_ids_fct, core_login_details_fct, institution_fct, loan_payment_breakdowns_fct, login_accounts_fct, login_attempts_fct, login_results_deref, moov_accounts_fct, moov_transactions_fct, online_aggregations_fct, online_latest_aggregations_fct, org_business_accounts_fct, org_business_addresses_fct, org_business_user_sync_state_fct, org_businesses_fct, org_consumer_name_records_fct, org_consumer_verified_phones_fct, org_consumers_accounts_fct, org_consumers_fct, org_copy_user_status_fct, org_episys_organization_metadata_fct, org_institution_organization_flags_fct, org_netteller_business_metadata_fct, org_netteller_consumer_metadata_fct, org_organization_user_invitations_fct, org_roles_fct, org_user_account_entitlements_fct, org_user_entitlements_fct, org_user_role_xref_fct, payments_fct, rdc_accounts_fct, rdc_deposits_fct, scheduled_transfers_fct, transactions_fct, transfer_accounts_fct, trx_accounts_fct, user_activity_fct, user_bills_fct, user_demographic_details_fct, user_edits_fct, user_member_number_associations_fct, users_fct

### `ip_geo`

ip_to_city, maxmind_ipv4_to_city

### `symitar`

account_v1_raw, activity_raw, agreement_note_raw, agreement_raw, agreement_transaction_raw, batchachorig_raw, card_access_raw, card_name_raw, card_note_raw, card_raw, check_fmhistory_raw, check_raw, collateral_collhold_raw, collateral_document_raw, collateral_document_tracking_raw, collateral_fmhistory_raw, collateral_raw, collateral_tracking_raw, comment_raw, cpworkcard_note_raw, cpworkcard_raw, cpworkcard_tracking_raw, credrep_raw, dealer_comment_raw, dealer_fmhistory_raw, dealer_note_raw, dealer_raw, dealer_tracking_raw, eft_addendainfo_raw, eft_name_raw, eft_raw, eft_transfer_raw, externalaccount_raw, externalloan_name_raw, externalloan_note_raw, externalloan_raw, externalloan_tracking_raw, externalloan_transfer_raw, fmhistory_raw, glaccount_fmhistory_raw, glaccount_raw, glaccount_tracking_raw, glhistory_raw, glsubaccount_raw, household_raw, inventory_raw, invoice_note_raw, invoice_raw, irs_distribution_raw, irs_name_raw

## Quick Query Examples

```sql
-- Count all digital transactions
SELECT COUNT(*)
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`;

-- Recent login attempts with IPs
SELECT username, attempted_at, client_ip, result_id
FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct`
ORDER BY attempted_at DESC LIMIT 20;

-- Large transactions (over $5,000)
SELECT AccountId, DatePosted, Amount, BannoType, Memo
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
WHERE ABS(Amount) > 5000
ORDER BY DatePosted DESC LIMIT 20;

-- Dormant accounts with recent activity
SELECT a.number, a.lastfmdate, a.opendate, a.memberstatus
FROM `jhdevcon2026.symitar.account_v1_raw` a
WHERE a.lastfmdate < DATE_SUB(CURRENT_DATE(), INTERVAL 1 YEAR)
  AND a.closedate IS NULL
LIMIT 20;

-- Potential structuring: multiple transactions just under $10k in a day
SELECT AccountId, DatePosted, COUNT(*) as txn_count, SUM(ABS(Amount)) as daily_total
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
WHERE ABS(Amount) BETWEEN 3000 AND 9999
GROUP BY AccountId, DatePosted
HAVING txn_count > 2 AND daily_total > 10000
ORDER BY daily_total DESC LIMIT 20;
```

***IMPORTANT***: AI agents and run any commands that are read only like python commands or bq commands.
