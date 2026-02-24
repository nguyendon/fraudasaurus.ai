-- KITING / NSF DETECTION
-- Accounts with high NSF (non-sufficient funds) counts indicating possible check kiting

SELECT
  number as account_number,
  type as account_type,
  opendate,
  lastfmdate,
  nsftoday,
  nsfmonthlycount_1 + nsfmonthlycount_2 + nsfmonthlycount_3 +
  nsfmonthlycount_4 + nsfmonthlycount_5 + nsfmonthlycount_6 as nsf_6mo_total,
  nsfmonthlycount_1 + nsfmonthlycount_2 + nsfmonthlycount_3 +
  nsfmonthlycount_4 + nsfmonthlycount_5 + nsfmonthlycount_6 +
  nsfmonthlycount_7 + nsfmonthlycount_8 + nsfmonthlycount_9 +
  nsfmonthlycount_10 + nsfmonthlycount_11 + nsfmonthlycount_12 as nsf_12mo_total,
  frozenmode,
  restrict,
  memberstatus,
  warningcode_1, warningcode_2, warningcode_3
FROM `jhdevcon2026.symitar.account_v1_raw`
WHERE (nsfmonthlycount_1 + nsfmonthlycount_2 + nsfmonthlycount_3 +
       nsfmonthlycount_4 + nsfmonthlycount_5 + nsfmonthlycount_6) > 3
ORDER BY nsf_6mo_total DESC
LIMIT 50;
