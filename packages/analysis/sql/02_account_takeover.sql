-- ACCOUNT TAKEOVER DETECTION
-- Look for failed login patterns, multi-IP usage, and brute force attempts

-- Users with failed logins or many distinct IPs
WITH login_stats AS (
  SELECT
    username,
    client_ip,
    result_id,
    attempted_at,
    COUNT(DISTINCT client_ip) OVER (PARTITION BY username) as distinct_ips,
    COUNT(*) OVER (PARTITION BY username) as total_attempts,
    SUM(CASE WHEN result_id != 1 THEN 1 ELSE 0 END) OVER (PARTITION BY username) as failed_attempts
  FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct`
)
SELECT
  username,
  total_attempts,
  failed_attempts,
  distinct_ips,
  STRING_AGG(DISTINCT client_ip) as ips_used,
  MIN(attempted_at) as first_attempt,
  MAX(attempted_at) as last_attempt
FROM login_stats
GROUP BY username, total_attempts, failed_attempts, distinct_ips
HAVING failed_attempts > 0 OR distinct_ips > 2
ORDER BY failed_attempts DESC, distinct_ips DESC
LIMIT 50;

-- Login result code reference
SELECT * FROM `jhdevcon2026.banno_operation_and_transaction_data.login_results_deref`;

-- Dormant account login attempts (result_id = 4)
SELECT
  la.username,
  la.result_id,
  lr.name as result_name,
  la.attempted_at,
  la.client_ip
FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct` la
JOIN `jhdevcon2026.banno_operation_and_transaction_data.login_results_deref` lr
  ON la.result_id = lr.id
WHERE la.result_id = 4
ORDER BY la.attempted_at DESC;
