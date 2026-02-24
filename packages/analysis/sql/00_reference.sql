-- REFERENCE QUERIES
-- Useful lookups and data profiling

-- Transaction types and counts
SELECT DISTINCT BannoType, COUNT(*) as cnt
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
GROUP BY BannoType ORDER BY cnt DESC;

-- Login result codes
SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.login_results_deref`;

-- How Banno users map to Symitar member numbers
SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct`
LIMIT 10;

-- Sample transactions
SELECT AccountId, DatePosted, Amount, BannoType, CleanMemo, UserId, RunningBalance
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
LIMIT 10;
