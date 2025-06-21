#!/usr/bin/env python3
"""
Test database connection and verify schema
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables
load_dotenv()

def test_connection():
    """Test PostgreSQL connection and verify schema."""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    try:
        # Parse the database URL
        # Format: postgresql://username:password@host:port/database
        if database_url.startswith('postgresql://'):
            url_parts = database_url.replace('postgresql://', '').split('/')
            db_name = url_parts[1] if len(url_parts) > 1 else 'attendease'
            auth_host = url_parts[0].split('@')
            host_port = auth_host[1].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            
            if '@' in auth_host[0]:
                username, password = auth_host[0].split(':')
            else:
                username = auth_host[0].split(':')[0]
                password = auth_host[0].split(':')[1]
        else:
            print("❌ Invalid DATABASE_URL format")
            return False
        
        print(f"🔗 Attempting to connect to:")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Database: {db_name}")
        print(f"   Username: {username}")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=db_name,
            user=username,
            password=password
        )
        
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"   PostgreSQL version: {version}")
        
        # Check schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        print(f"\n📋 Found {len(table_names)} tables:")
        for table in table_names:
            print(f"   • {table}")
        
        # Check for core tables
        core_tables = ['users', 'students', 'lecturers', 'admins', 'courses', 'departments']
        missing_tables = [table for table in core_tables if table not in table_names]
        
        if missing_tables:
            print(f"\n⚠️  Missing core tables: {', '.join(missing_tables)}")
            print("   You may need to run your schema script first.")
        else:
            print("\n✅ All core tables found!")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Common solutions:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify your username and password")
        print("3. Ensure the database 'attendease' exists")
        print("4. Check if PostgreSQL is accepting connections on port 5432")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    print("🧪 AttendEase Database Connection Test")
    print("=" * 40)
    
    if test_connection():
        print("\n🎉 Database connection test passed!")
        sys.exit(0)
    else:
        print("\n💥 Database connection test failed!")
        sys.exit(1)
