-- Migration 009: Schema Evolution (W-003)
-- Adds captured_at, location, measurement_type; drops currentdate, currenttime.
--
-- EXECUTION ORDER (SCN-008 procedure):
--   1. docker compose down
--   2. Execute this script inside the running mariadb container:
--        docker compose exec mariadb mysql -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" < db/migration-009-schema-evolution.sql
--   3. Verify null-check output (see Step 9 below) — must be 0 before proceeding
--   4. docker compose up -d
--
-- PREREQUISITES: Run IP-001 dry-run tasks (TASK-A-001..A-003) before executing.
-- All DDL (ALTER TABLE ADD/MODIFY/DROP COLUMN) auto-commits in MariaDB/InnoDB
-- and cannot be rolled back. The UPDATE backfill is transactional.

-- Step 1–3: Add new columns as nullable (allows UPDATE backfill before enforcing NOT NULL)
ALTER TABLE sensorreadings ADD COLUMN captured_at DATETIME NULL;
ALTER TABLE sensorreadings ADD COLUMN location TEXT NULL;
ALTER TABLE sensorreadings ADD COLUMN measurement_type TEXT NULL;

-- Steps 4–8: Backfill all existing rows in a single transaction
--   captured_at : TIMESTAMP() combines Date + Time columns into a DATETIME value
--   location    : segments 2+3 of the device topic (e.g. "environment/indoor/attic/temp" → "indoor/attic")
--   measurement_type : final segment of the device topic (e.g. "temperature")
START TRANSACTION;

UPDATE sensorreadings
    SET captured_at = TIMESTAMP(currentdate, currenttime);

UPDATE sensorreadings
    SET location = SUBSTRING_INDEX(SUBSTRING_INDEX(device, '/', 3), '/', -2);

UPDATE sensorreadings
    SET measurement_type = SUBSTRING_INDEX(device, '/', -1);

COMMIT;

-- Step 9: Null-check gate — STOP if result is not 0; investigate before proceeding
-- This query must return 0 before the MODIFY/DROP steps execute.
-- When running manually: inspect this output and abort if nonzero.
SELECT COUNT(*) AS null_rows_remaining
FROM sensorreadings
WHERE captured_at IS NULL
   OR location IS NULL
   OR measurement_type IS NULL;

-- Steps 10–12: Enforce NOT NULL now that all rows are populated (DDL; auto-commits)
ALTER TABLE sensorreadings MODIFY COLUMN captured_at DATETIME NOT NULL;
ALTER TABLE sensorreadings MODIFY COLUMN location TEXT NOT NULL;
ALTER TABLE sensorreadings MODIFY COLUMN measurement_type TEXT NOT NULL;

-- Step 13: Create composite index for filtered time-range queries
--   Column order: (location, measurement_type, captured_at) — equality filters first,
--   then the range column, so the index is usable for queries like:
--   WHERE location = 'indoor/attic' AND measurement_type = 'temperature'
--   ORDER BY captured_at DESC
CREATE INDEX idx_loc_mtype_time
    ON sensorreadings (location(255), measurement_type(255), captured_at);

-- Steps 14–15: Drop legacy timestamp columns (irreversible — null-check gate above must be 0)
ALTER TABLE sensorreadings DROP COLUMN currentdate;
ALTER TABLE sensorreadings DROP COLUMN currenttime;

-- Post-migration verification queries (run manually to confirm):
--   DESCRIBE sensorreadings;
--   SHOW INDEX FROM sensorreadings WHERE Key_name = 'idx_loc_mtype_time';
--   SELECT captured_at, location, measurement_type, device, reading FROM sensorreadings LIMIT 10;
