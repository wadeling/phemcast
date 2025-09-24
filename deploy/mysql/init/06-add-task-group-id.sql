-- Add task_group_id column to task_execution_history table
-- This migration adds support for task groups where multiple tasks can be grouped together

ALTER TABLE task_execution_history 
ADD COLUMN task_group_id VARCHAR(50) NULL AFTER task_id;

-- Add index for better query performance
CREATE INDEX idx_task_execution_history_task_group_id ON task_execution_history(task_group_id);

-- Add comment to document the purpose
ALTER TABLE task_execution_history 
MODIFY COLUMN task_group_id VARCHAR(50) NULL COMMENT 'Reference to task group for grouping related tasks';
