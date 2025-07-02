#!/usr/bin/env python3
"""
Fix verification_codes table in production - Update column names to match backend code
"""

import psycopg2
import sys
from datetime import datetime
from urllib.parse import urlparse

# Production database URL
PRODUCTION_DB_URL = "postgresql://attendease_user:UBjvm30T0XorXNwoai7T14zNGbvOSgKp@dpg-d1bd26odl3ps73eikkmg-a.frankfurt-postgres.render.com/attendease"

def fix_verification_codes_table():
    """Fix the verification_codes table to match backend expectations"""
    print("🔧 Fixing Verification Codes Table")
    print("=" * 50)
    
    conn = None
    cursor = None
    
    try:
        # Connect to production database
        print("🔌 Connecting to production database...")
        parsed = urlparse(PRODUCTION_DB_URL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # Check current table structure
        print("\n📊 Checking current table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'verification_codes' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        current_columns = cursor.fetchall()
        print(f"📋 Current columns ({len(current_columns)}):")
        for col in current_columns:
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
        
        column_names = [col[0] for col in current_columns]
        
        # The issue: Production has is_verified/verified_at but backend expects is_used/used_at
        changes_made = []
        
        # Step 1: Add is_used column if it doesn't exist
        if 'is_used' not in column_names:
            print("\n🔧 Adding 'is_used' column...")
            cursor.execute("""
                ALTER TABLE verification_codes 
                ADD COLUMN is_used BOOLEAN NOT NULL DEFAULT FALSE;
            """)
            changes_made.append("Added is_used column")
            print("  ✅ Added 'is_used' column")
        else:
            print("\n✅ 'is_used' column already exists")
        
        # Step 2: Add used_at column if it doesn't exist
        if 'used_at' not in column_names:
            print("🔧 Adding 'used_at' column...")
            cursor.execute("""
                ALTER TABLE verification_codes 
                ADD COLUMN used_at TIMESTAMP NULL;
            """)
            changes_made.append("Added used_at column")
            print("  ✅ Added 'used_at' column")
        else:
            print("✅ 'used_at' column already exists")
        
        # Step 3: If we have is_verified, copy its data to is_used
        if 'is_verified' in column_names and 'is_used' in column_names:
            print("🔄 Copying data from 'is_verified' to 'is_used'...")
            cursor.execute("""
                UPDATE verification_codes 
                SET is_used = is_verified 
                WHERE is_verified IS NOT NULL;
            """)
            changes_made.append("Copied is_verified data to is_used")
            print("  ✅ Data copied successfully")
        
        # Step 4: If we have verified_at, copy its data to used_at
        if 'verified_at' in column_names and 'used_at' in column_names:
            print("🔄 Copying data from 'verified_at' to 'used_at'...")
            cursor.execute("""
                UPDATE verification_codes 
                SET used_at = verified_at 
                WHERE verified_at IS NOT NULL;
            """)
            changes_made.append("Copied verified_at data to used_at")
            print("  ✅ Data copied successfully")
        
        # Step 5: Create indexes for performance
        print("\n📊 Creating indexes for performance...")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_codes_email 
                ON verification_codes(email);
            """)
            print("  ✅ Created email index")
        except Exception as e:
            print(f"  ⚠️  Email index: {e}")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_codes_is_used 
                ON verification_codes(is_used);
            """)
            print("  ✅ Created is_used index")
        except Exception as e:
            print(f"  ⚠️  is_used index: {e}")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_verification_codes_expires_at 
                ON verification_codes(expires_at);
            """)
            print("  ✅ Created expires_at index")
        except Exception as e:
            print(f"  ⚠️  expires_at index: {e}")
        
        # Commit all changes
        conn.commit()
        print("\n💾 All changes committed successfully!")
        
        # Verify final structure
        print("\n🔍 Verifying final table structure...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'verification_codes' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        final_columns = cursor.fetchall()
        print(f"📋 Final columns ({len(final_columns)}):")
        for col in final_columns:
            default_val = col[3] if col[3] else 'None'
            print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'} DEFAULT {default_val}")
        
        # Summary
        print(f"\n🎉 Verification codes table fixed successfully!")
        if changes_made:
            print("📝 Changes made:")
            for change in changes_made:
                print(f"  - {change}")
        print("✅ Your registration should now work!")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    success = fix_verification_codes_table()
    sys.exit(0 if success else 1)
