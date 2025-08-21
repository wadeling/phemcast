-- Initialize database
CREATE DATABASE IF NOT EXISTS phemcast CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE phemcast;

-- Create invite_codes table
CREATE TABLE IF NOT EXISTS invite_codes (
    code VARCHAR(50) PRIMARY KEY,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    used_by VARCHAR(100),
    used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at DATETIME
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(100) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login DATETIME,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    invite_code_used VARCHAR(50)
);

-- Insert some initial invite codes
INSERT IGNORE INTO invite_codes (code, is_used, expires_at) VALUES
('WELCOME2024', FALSE, DATE_ADD(NOW(), INTERVAL 1 YEAR)),
('INDUSTRY2024', FALSE, DATE_ADD(NOW(), INTERVAL 1 YEAR)),
('NEWS2024', FALSE, DATE_ADD(NOW(), INTERVAL 1 YEAR)),
('AGENT2024', FALSE, DATE_ADD(NOW(), INTERVAL 1 YEAR)),
('TEST123', FALSE, DATE_ADD(NOW(), INTERVAL 1 YEAR));

-- Create indexes
CREATE INDEX idx_invite_codes_used ON invite_codes(is_used);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
