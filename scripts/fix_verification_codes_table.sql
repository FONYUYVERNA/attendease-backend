-- Fix verification_codes table structure
-- This script adds the missing columns to the verification_codes table

-- First, check if the table exists and drop it if it has wrong structure
DROP TABLE IF EXISTS verification_codes CASCADE;

-- Create the verification_codes table with correct structure
CREATE TABLE verification_codes (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    user_type user_type_enum NOT NULL,
    phone_number VARCHAR(20),
    code VARCHAR(10) NOT NULL,
    purpose VARCHAR(50) NOT NULL DEFAULT 'registration',
    is_used BOOLEAN NOT NULL DEFAULT false,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 5,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL
);

-- Create indexes for better performance
CREATE INDEX idx_verification_codes_email ON verification_codes(email);
CREATE INDEX idx_verification_codes_code ON verification_codes(code);
CREATE INDEX idx_verification_codes_expires_at ON verification_codes(expires_at);
CREATE INDEX idx_verification_codes_is_used ON verification_codes(is_used);

-- Success message
SELECT 'verification_codes table created successfully with all required columns' as result;
