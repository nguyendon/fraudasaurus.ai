-- DORMANT ACCOUNT ABUSE
-- Find Symitar accounts marked dormant/inactive that still have Banno digital transactions

SELECT
  a.number as member_number,
  a.lastfmdate,
  a.opendate,
  a.closedate,
  a.memberstatus,
  a.frozenmode,
  COUNT(t.TransactionId) as banno_txn_count,
  MIN(t.DatePosted) as first_banno_txn,
  MAX(t.DatePosted) as last_banno_txn,
  SUM(ABS(t.Amount)) as total_amount
FROM `jhdevcon2026.symitar.account_v1_raw` a
JOIN `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct` m
  ON CAST(a.number AS INT64) = CAST(m.member_number AS INT64)
JOIN `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct` t
  ON m.user_id = t.UserId
WHERE a.lastfmdate < '2020-01-01'
  AND a.closedate IS NULL
  AND a.type = 0  -- primary member account
GROUP BY a.number, a.lastfmdate, a.opendate, a.closedate, a.memberstatus, a.frozenmode
HAVING banno_txn_count > 5
ORDER BY total_amount DESC
LIMIT 20;
