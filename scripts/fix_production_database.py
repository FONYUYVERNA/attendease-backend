#!/usr/bin/env python3
"""
Fix Production Database - Add Missing Columns to verification_codes Table
This script connects to your production database and adds missing columns safely.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables"""
    # Try different environment variable names
    db_url = (
        os.getenv('DATABASE_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DB_URL') or
        os.getenv('RENDER_DATABASE_URL')
    )
    
    if not db_url:
        logger.error("❌ No database URL found in environment variables")
        logger.info("Please set one of: DATABASE_URL, POSTGRES_URL, DB_URL, or RENDER_DATABASE_URL")
        return None
    
    return db_url

def connect_to_database():
    """Connect to the production database"""
    db_url = get_database_url()
    if not db_url:
        return None
    
    try:
        # Parse the database URL
        parsed = urlparse(db_url)
        
        # Handle SSL requirement for production databases
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'  # Required for most cloud databases
        )
        
        logger.info("✅ Connected to production database successfully")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        return None

def check_table_exists(cursor, table_name):
    """Check if table exists"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = %s
        );
    """, (table_name,))
    return cursor.fetchone()[0]

def get_existing_columns(cursor, table_name):
    """Get list of existing columns in the table"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s;
    """, (table_name,))
    return [row[0] for row in cursor.fetchall()]

def add_missing_columns(cursor):
    """Add missing columns to verification_codes table"""
    table_name = 'verification_codes'
    
    # Check if table exists
    if not check_table_exists(cursor, table_name):
        logger.error(f"❌ Table '{table_name}' does not exist!")
        return False
    
    # Get existing columns
    existing_columns = get_existing_columns(cursor, table_name)
    logger.info(f"📋 Existing columns: {existing_columns}")
    
    # Define required columns with their definitions
    required_columns = {
        'is_used': 'BOOLEAN NOT NULL DEFAULT FALSE',
        'attempts': 'INTEGER NOT NULL DEFAULT 0',
        'max_attempts': 'INTEGER NOT NULL DEFAULT 5',
        'purpose': 'VARCHAR(50) NOT NULL DEFAULT \'registration\'',
        'used_at': 'TIMESTAMP NULL'
    }
    
    # Add missing columns
    columns_added = []
    for column_name, column_def in required_columns.items():
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def};")
                columns_added.append(column_name)
                logger.info(f"✅ Added column: {column_name}")
            except Exception as e:
                logger.error(f"❌ Failed to add column {column_name}: {e}")
                return False
    
    if columns_added:
        logger.info(f"🎉 Successfully added {len(columns_added)} columns: {columns_added}")
    else:
        logger.info("ℹ️ All required columns already exist")
    
    return True

def create_indexes(cursor):
    """Create performance indexes"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON verification_codes(email);",
        "CREATE INDEX IF NOT EXISTS idx_verification_codes_code ON verification_codes(code);",
        "CREATE INDEX IF NOT EXISTS idx_verification_codes_expires_at ON verification_codes(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_verification_codes_is_used ON verification_codes(is_used);"
    ]
    
    for index_sql in indexes:
        try:
            cursor.execute(index_sql)
            logger.info(f"✅ Created index: {index_sql.split()[5]}")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")

def show_final_structure(cursor):
    """Show the final table structure"""
    cursor.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'verification_codes'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    logger.info("📊 Final table structure:")
    logger.info("=" * 80)
    logger.info(f"{'Column Name':<20} {'Data Type':<15} {'Nullable':<10} {'Default':<20}")
    logger.info("-" * 80)
    
    for column in columns:
        name, data_type, nullable, default = column
        default_str = str(default)[:18] + "..." if default and len(str(default)) > 20 else str(default)
        logger.info(f"{name:<20} {data_type:<15} {nullable:<10} {default_str:<20}")
    
    logger.info("=" * 80)

def main():
    """Main function to fix the production database"""
    logger.info("🚀 Starting production database fix...")
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        sys.exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Add missing columns
        if not add_missing_columns(cursor):
            logger.error("❌ Failed to add missing columns")
            sys.exit(1)
        
        # Create indexes for performance
        create_indexes(cursor)
        
        # Commit changes
        conn.commit()
        logger.info("✅ All changes committed successfully")
        
        # Show final structure
        show_final_structure(cursor)
        
        logger.info("🎉 Production database fix completed successfully!")
        logger.info("🚀 Your registration should now work!")
        
    except Exception as e:
        logger.error(f"❌ Error during database fix: {e}")
        conn.rollback()
        sys.exit(1)
        
    finally:
        cursor.close()
        conn.close()
        logger.info("🔐 Database connection closed")

if __name__ == "__main__":
    main()
