-- FIND CARMEG SANDIEGO
-- CarMeg = Car + Meg (Meg Bannister, hackathon organizer)
-- She operates under multiple aliases and user accounts

-- All accounts linked to Meg Bannister (by email)
SELECT
  u.user_id,
  u.primary_institution_username,
  u.first_name,
  u.last_name,
  u.email,
  u.user_added_dt,
  u.user_active,
  m.member_number
FROM `jhdevcon2026.banno_operation_and_transaction_data.users_fct` u
LEFT JOIN `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct` m
  ON u.user_id = m.user_id
WHERE LOWER(u.email) LIKE '%bannister%' OR LOWER(u.email) LIKE '%mbannist%'
ORDER BY u.user_added_dt;

-- Search users for "Meg" name variants
SELECT user_id, primary_institution_username, first_name, last_name, email
FROM `jhdevcon2026.banno_operation_and_transaction_data.users_fct`
WHERE LOWER(first_name) LIKE '%meg%'
   OR LOWER(last_name) LIKE '%san%'
   OR LOWER(email) LIKE '%carmeg%'
   OR LOWER(primary_institution_username) LIKE '%meg%';

-- Get user details for the structuring suspects
SELECT
  u.user_id,
  u.primary_institution_username,
  u.first_name,
  u.last_name,
  u.email,
  u.user_added_dt,
  m.member_number
FROM `jhdevcon2026.banno_operation_and_transaction_data.users_fct` u
LEFT JOIN `jhdevcon2026.banno_operation_and_transaction_data.user_member_number_associations_fct` m
  ON u.user_id = m.user_id
WHERE u.user_id IN (
  '045fcb6e-84d0-401c-a590-2030e406c32f',  -- marielong (member 39903)
  'c87c31b0-c7f8-11e9-8330-0242c87f2824',  -- xroguex (member 7000)
  '93986c5d-73eb-4431-b2bd-d42b5d242025',  -- iloveroe (member 33250)
  '4dc8ef0d-c11a-433e-bf15-3989ba556f55',  -- A3ZXNHPWONQ6 (no member)
  'c6c5b4ad-9215-48ab-aa50-acc204ca6143',  -- ilovemlms (no member)
  'fca95013-e365-46d7-b708-f235ed426768'   -- (no username, member 39903)
);

-- Login attempts for CarMeg's known usernames
SELECT username, result_id, attempted_at, client_ip
FROM `jhdevcon2026.banno_operation_and_transaction_data.login_attempts_fct`
WHERE username IN ('ilovemlms', 'iloveroe', 'xroguex', 'lularoe', 'megatoptimus',
                   'studentmeg', 'megatbusybee', 'ghouse', 'marielong', 'bannister')
ORDER BY attempted_at;

-- Transaction memos mentioning San Diego (Symitar HQ location)
SELECT DISTINCT CleanMemo, Memo, COUNT(*) as cnt
FROM `jhdevcon2026.banno_operation_and_transaction_data.transactions_fct`
WHERE LOWER(Memo) LIKE '%sandiego%' OR LOWER(Memo) LIKE '%san diego%'
GROUP BY CleanMemo, Memo;
