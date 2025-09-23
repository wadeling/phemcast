-- Update scheduled_tasks table to use companies instead of urls and email_recipients
-- First, add the new companies column
ALTER TABLE scheduled_tasks ADD COLUMN companies TEXT;

-- Update existing records to have empty companies array
UPDATE scheduled_tasks SET companies = '[]' WHERE companies IS NULL;

-- Make companies column NOT NULL
ALTER TABLE scheduled_tasks MODIFY COLUMN companies TEXT NOT NULL;

-- Remove the old columns (optional - comment out if you want to keep them for migration purposes)
-- ALTER TABLE scheduled_tasks DROP COLUMN urls;
-- ALTER TABLE scheduled_tasks DROP COLUMN email_recipients;
