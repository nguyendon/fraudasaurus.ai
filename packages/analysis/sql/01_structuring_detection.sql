-- STRUCTURING DETECTION
-- Find accounts with multiple sub-$10k transactions where daily totals exceed $10k
-- This is the primary indicator of CTR avoidance (Currency Transaction Report threshold = $10,000)

-- Daily aggregation: accounts with multiple $2k-$9,999 transactions summing over $10k
SELECT
  AccountId,
  CAST(DatePosted AS DATE) as txn_date,
  COUNT(*) as txn_count,
  SUM(ABS(Amount)) as daily_total,
  MAX(ABS(Amount)) as max_single_txn,
  STRING_AGG(CONCAT(BannoType, ':', CAST(Amount AS STRING), ' [', IFNULL(CleanMemo,''), ']'), ' | ' ORDER BY DatePosted) as details
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
WHERE ABS(Amount) BETWEEN 2000 AND 9999
GROUP BY AccountId, CAST(DatePosted AS DATE)
HAVING txn_count >= 2 AND daily_total > 10000
ORDER BY daily_total DESC
LIMIT 50;

-- Deep dive: accounts doing exactly $7,980 transfers (the key structuring amount found)
SELECT
  AccountId,
  COUNT(*) as total_7980_txns,
  COUNT(DISTINCT CAST(DatePosted AS DATE)) as distinct_days,
  MIN(DatePosted) as first_seen,
  MAX(DatePosted) as last_seen,
  SUM(Amount) as total_amount
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
WHERE ABS(Amount) = 7980
GROUP BY AccountId
ORDER BY total_7980_txns DESC;

-- Link structuring accounts to users and member numbers
SELECT DISTINCT
  t.AccountId,
  t.UserId,
  m.member_number,
  COUNT(*) as txn_count
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct` t
LEFT JOIN `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct` m
  ON t.UserId = m.user_id
WHERE ABS(t.Amount) = 7980
GROUP BY t.AccountId, t.UserId, m.member_number
ORDER BY txn_count DESC;
