-- Migration script to rename user_id to user_name for consistency
-- This script should be run after the application code has been updated

USE phemcast;

-- Backup existing data (optional but recommended)
-- CREATE TABLE scheduled_tasks_backup AS SELECT * FROM scheduled_tasks;
-- CREATE TABLE task_execution_history_backup AS SELECT * FROM task_execution_history;

-- Modify scheduled_tasks table
ALTER TABLE scheduled_tasks 
CHANGE COLUMN user_id user_name VARCHAR(100) NOT NULL;

-- Modify task_execution_history table
ALTER TABLE task_execution_history 
CHANGE COLUMN user_id user_name VARCHAR(100) NOT NULL;

-- Recreate indexes for the new column name
-- Drop old indexes if they exist
DROP INDEX IF EXISTS idx_scheduled_tasks_user_id ON scheduled_tasks;
DROP INDEX IF EXISTS idx_task_execution_history_user_id ON task_execution_history;

-- Create new indexes
CREATE INDEX idx_scheduled_tasks_user_name ON scheduled_tasks(user_name);
CREATE INDEX idx_task_execution_history_user_name ON task_execution_history(user_name);

-- Verify the changes
DESCRIBE scheduled_tasks;
DESCRIBE task_execution_history;

-- Show indexes
SHOW INDEX FROM scheduled_tasks WHERE Key_name LIKE '%user%';
SHOW INDEX FROM task_execution_history WHERE Key_name LIKE '%user%';
