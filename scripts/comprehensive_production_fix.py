#!/usr/bin/env python3
"""
Comprehensive Production Database Fix
Fixes ALL database schema mismatches between local and production
"""

import os
import sys
import psycopg2
from datetime import datetime

# Add the parent directory to the path so we can import from the backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use the correct production database URL from your working scripts
PRODUCTION_DB_URL = "postgresql://attendease_user:UBjvm30T0XorXNwoai7T14zNGbvOSgKp@dpg-d1bd26odl3ps73eikkmg-a.frankfurt-postgres.render.com/attendease"

def get_production_connection():
    """Get production database connection using the correct URL"""
    try:
        from urllib.parse import urlparse
        
        # Parse the database URL
        parsed = urlparse(PRODUCTION_DB_URL)
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            port=parsed.port or 5432,
            sslmode="require"
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to production database: {e}")
        return None

def fix_audit_logs_table(cursor):
    """Fix audit_logs table ip_address column"""
    print("🔧 Fixing audit_logs table...")
    
    try:
        # Check if column exists and its type
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'audit_logs' AND column_name = 'ip_address'
        """)
        result = cursor.fetchone()
        
        if result:
            current_type = result[0]
            print(f"  📊 Current ip_address type: {current_type}")
            
            if current_type != 'text':
                print("  🔄 Converting ip_address to TEXT...")
                cursor.execute("ALTER TABLE audit_logs ALTER COLUMN ip_address TYPE TEXT")
                print("  ✅ audit_logs.ip_address converted to TEXT")
            else:
                print("  ✅ audit_logs.ip_address already TEXT")
        else:
            print("  ➕ Adding ip_address column...")
            cursor.execute("ALTER TABLE audit_logs ADD COLUMN ip_address TEXT")
            print("  ✅ audit_logs.ip_address column added")
            
    except Exception as e:
        print(f"  ❌ Error fixing audit_logs: {e}")
        raise

def fix_user_sessions_table(cursor):
    """Fix user_sessions table ip_address column"""
    print("🔧 Fixing user_sessions table...")
    
    try:
        # Check if column exists and its type
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'user_sessions' AND column_name = 'ip_address'
        """)
        result = cursor.fetchone()
        
        if result:
            current_type = result[0]
            print(f"  📊 Current ip_address type: {current_type}")
            
            if current_type != 'text':
                print("  🔄 Converting ip_address to TEXT...")
                cursor.execute("ALTER TABLE user_sessions ALTER COLUMN ip_address TYPE TEXT")
                print("  ✅ user_sessions.ip_address converted to TEXT")
            else:
                print("  ✅ user_sessions.ip_address already TEXT")
        else:
            print("  ➕ Adding ip_address column...")
            cursor.execute("ALTER TABLE user_sessions ADD COLUMN ip_address TEXT")
            print("  ✅ user_sessions.ip_address column added")
            
    except Exception as e:
        print(f"  ❌ Error fixing user_sessions: {e}")
        raise

def fix_verification_codes_table(cursor):
    """Fix verification_codes table completely"""
    print("🔧 Fixing verification_codes table...")
    
    try:
        # Get current columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'verification_codes'
            ORDER BY ordinal_position
        """)
        columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in cursor.fetchall()}
        print(f"  📊 Current columns: {list(columns.keys())}")
        
        # Ensure is_used column exists
        if 'is_used' not in columns:
            print("  ➕ Adding is_used column...")
            cursor.execute("ALTER TABLE verification_codes ADD COLUMN is_used BOOLEAN NOT NULL DEFAULT FALSE")
        else:
            print("  ✅ is_used column exists")
        
        # Ensure used_at column exists
        if 'used_at' not in columns:
            print("  ➕ Adding used_at column...")
            cursor.execute("ALTER TABLE verification_codes ADD COLUMN used_at TIMESTAMP")
        else:
            print("  ✅ used_at column exists")
        
        # Sync data from is_verified to is_used
        print("  🔄 Syncing is_verified → is_used...")
        cursor.execute("""
            UPDATE verification_codes 
            SET is_used = COALESCE(is_verified, FALSE)
            WHERE is_verified IS NOT NULL
        """)
        
        # Sync data from verified_at to used_at
        print("  🔄 Syncing verified_at → used_at...")
        cursor.execute("""
            UPDATE verification_codes 
            SET used_at = verified_at
            WHERE verified_at IS NOT NULL AND used_at IS NULL
        """)
        
        # Make nullable columns actually nullable
        nullable_columns = ['attempts', 'max_attempts', 'created_at', 'purpose']
        for col in nullable_columns:
            if col in columns and columns[col]['nullable'] == 'NO':
                print(f"  🔄 Making {col} nullable...")
                cursor.execute(f"ALTER TABLE verification_codes ALTER COLUMN {col} DROP NOT NULL")
        
        print("  ✅ verification_codes table fixed")
        
    except Exception as e:
        print(f"  ❌ Error fixing verification_codes: {e}")
        raise

def create_performance_indexes(cursor):
    """Create performance indexes"""
    print("📊 Creating performance indexes...")
    
    indexes = [
        ("idx_audit_logs_user_id", "audit_logs", "user_id"),
        ("idx_audit_logs_created_at", "audit_logs", "created_at"),
        ("idx_user_sessions_user_id", "user_sessions", "user_id"),
        ("idx_user_sessions_token", "user_sessions", "session_token"),
        ("idx_user_sessions_expires", "user_sessions", "expires_at"),
        ("idx_verification_codes_email", "verification_codes", "email"),
        ("idx_verification_codes_expires", "verification_codes", "expires_at"),
        ("idx_verification_codes_used", "verification_codes", "is_used"),
    ]
    
    for index_name, table_name, column_name in indexes:
        try:
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name} 
                ON {table_name} ({column_name})
            """)
            print(f"  ✅ Created index: {index_name}")
        except Exception as e:
            print(f"  ⚠️ Index {index_name} might already exist: {e}")

def cleanup_expired_data(cursor):
    """Clean up expired verification codes"""
    print("🧹 Cleaning up expired data...")
    
    try:
        # Remove expired verification codes
        cursor.execute("""
            DELETE FROM verification_codes 
            WHERE expires_at < NOW() - INTERVAL '1 day'
        """)
        deleted_codes = cursor.rowcount
        print(f"  🗑️ Removed {deleted_codes} expired verification codes")
        
        # Remove old user sessions
        cursor.execute("""
            DELETE FROM user_sessions 
            WHERE expires_at < NOW() - INTERVAL '7 days'
        """)
        deleted_sessions = cursor.rowcount
        print(f"  🗑️ Removed {deleted_sessions} old user sessions")
        
    except Exception as e:
        print(f"  ❌ Error during cleanup: {e}")

def main():
    print("🔧 Comprehensive Production Database Fix")
    print("=" * 50)
    
    # Connect to production database
    print("🔌 Connecting to production database...")
    conn = get_production_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # Fix all table issues
        fix_audit_logs_table(cursor)
        fix_user_sessions_table(cursor)
        fix_verification_codes_table(cursor)
        
        # Create performance indexes
        create_performance_indexes(cursor)
        
        # Clean up expired data
        cleanup_expired_data(cursor)
        
        # Commit all changes
        conn.commit()
        print("\n💾 All changes committed successfully!")
        
        # Verify final state
        print("\n🔍 Verifying final database state...")
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name IN ('audit_logs', 'user_sessions', 'verification_codes')
            AND column_name IN ('ip_address', 'is_used', 'used_at')
            ORDER BY table_name, column_name
        """)
        
        results = cursor.fetchall()
        for table, column, dtype, nullable in results:
            print(f"  ✅ {table}.{column}: {dtype} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        print("\n🎉 Database fix completed successfully!")
        print("\n📝 Summary of changes:")
        print("  - Fixed audit_logs.ip_address data type")
        print("  - Fixed user_sessions.ip_address data type")
        print("  - Ensured verification_codes has all required columns")
        print("  - Synced data between old and new columns")
        print("  - Created performance indexes")
        print("  - Cleaned up expired data")
        print("\n✅ Your registration should now work perfectly!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during database fix: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
