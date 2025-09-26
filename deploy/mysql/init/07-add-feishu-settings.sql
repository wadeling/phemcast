-- Add Feishu notification settings to user_settings table
-- Migration: 07-add-feishu-settings.sql

USE phemcast;

-- Add Feishu webhook URL and notification enabled fields
ALTER TABLE user_settings 
ADD COLUMN feishu_webhook_url VARCHAR(500) DEFAULT NULL COMMENT 'Feishu webhook URL for notifications',
ADD COLUMN feishu_notifications_enabled BOOLEAN DEFAULT FALSE COMMENT 'Whether Feishu notifications are enabled';

-- Add index for better query performance
CREATE INDEX idx_user_settings_feishu_enabled ON user_settings(feishu_notifications_enabled);

-- Update existing records to have default values
UPDATE user_settings 
SET feishu_notifications_enabled = FALSE 
WHERE feishu_notifications_enabled IS NULL;
