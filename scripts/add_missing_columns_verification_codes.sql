-- Add missing columns to verification_codes table
-- This script safely adds the missing columns without dropping the table

-- Check if the table exists first
DO $$
BEGIN
    -- Add is_used column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_codes' 
        AND column_name = 'is_used'
    ) THEN
        ALTER TABLE verification_codes ADD COLUMN is_used BOOLEAN NOT NULL DEFAULT FALSE;
        RAISE NOTICE 'Added is_used column to verification_codes table';
    ELSE
        RAISE NOTICE 'is_used column already exists in verification_codes table';
    END IF;

    -- Add attempts column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_codes' 
        AND column_name = 'attempts'
    ) THEN
        ALTER TABLE verification_codes ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added attempts column to verification_codes table';
    ELSE
        RAISE NOTICE 'attempts column already exists in verification_codes table';
    END IF;

    -- Add max_attempts column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_codes' 
        AND column_name = 'max_attempts'
    ) THEN
        ALTER TABLE verification_codes ADD COLUMN max_attempts INTEGER NOT NULL DEFAULT 5;
        RAISE NOTICE 'Added max_attempts column to verification_codes table';
    ELSE
        RAISE NOTICE 'max_attempts column already exists in verification_codes table';
    END IF;

    -- Add purpose column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_codes' 
        AND column_name = 'purpose'
    ) THEN
        ALTER TABLE verification_codes ADD COLUMN purpose VARCHAR(50) NOT NULL DEFAULT 'registration';
        RAISE NOTICE 'Added purpose column to verification_codes table';
    ELSE
        RAISE NOTICE 'purpose column already exists in verification_codes table';
    END IF;

    -- Add used_at column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'verification_codes' 
        AND column_name = 'used_at'
    ) THEN
        ALTER TABLE verification_codes ADD COLUMN used_at TIMESTAMP NULL;
        RAISE NOTICE 'Added used_at column to verification_codes table';
    ELSE
        RAISE NOTICE 'used_at column already exists in verification_codes table';
    END IF;

END $$;

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_verification_codes_is_used ON verification_codes(is_used);
CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON verification_codes(email);
CREATE INDEX IF NOT EXISTS idx_verification_codes_code ON verification_codes(code);
CREATE INDEX IF NOT EXISTS idx_verification_codes_expires_at ON verification_codes(expires_at);

-- Verify the table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'verification_codes' 
ORDER BY ordinal_position;

SELECT 'verification_codes table updated successfully with all required columns' AS result;
