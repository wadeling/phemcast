-- Migration: Make email field required for users
-- This migration updates the users table to make the email field NOT NULL

-- First, update any existing users with NULL email to have a placeholder email
-- This is necessary because we can't make a column NOT NULL if it contains NULL values
UPDATE users 
SET email = CONCAT('placeholder_', username, '@example.com') 
WHERE email IS NULL;

-- Now make the email column NOT NULL
ALTER TABLE users 
MODIFY COLUMN email VARCHAR(255) NOT NULL;

-- Add a comment to document this change
ALTER TABLE users 
MODIFY COLUMN email VARCHAR(255) NOT NULL COMMENT 'User email address (required)';
