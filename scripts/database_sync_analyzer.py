#!/usr/bin/env python3
"""
Database Sync Analyzer - Compare local and production database schemas
This script helps identify differences between your local and production databases
"""

import os
import sys
import psycopg2
import json
from datetime import datetime
from urllib.parse import urlparse

# Database configurations
PRODUCTION_DB_URL = "postgresql://attendease_user:UBjvm30T0XorXNwoai7T14zNGbvOSgKp@dpg-d1bd26odl3ps73eikkmg-a.frankfurt-postgres.render.com/attendease"

def connect_to_local_database():
    """Try to connect to local database with common configurations"""
    local_configs = [
        "postgresql://postgres:kilve123@localhost/attendease",
        "postgresql://postgres@localhost/attendease",
        "postgresql://localhost/attendease",
        "postgresql://postgres:kilve123@localhost/attendease_dev",
        "postgresql://postgres@localhost/attendease_dev",
        "postgresql://localhost/attendease_dev"
    ]
    
    for config in local_configs:
        try:
            conn = psycopg2.connect(config)
            print(f"✅ Connected to local database: {config}")
            return conn
        except Exception as e:
            continue
    
    print("❌ Could not connect to local database")
    print("💡 Make sure PostgreSQL is running locally and you have a database named 'attendease' or 'attendease_dev'")
    return None

def connect_to_production_database():
    """Connect to production database"""
    try:
        parsed = urlparse(PRODUCTION_DB_URL)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        print("✅ Connected to production database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to production database: {e}")
        return None

def get_table_columns(conn, table_name):
    """Get column information for a specific table"""
    cursor = conn.cursor()
    
    try:
        # Simple query that should work on all PostgreSQL versions
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = {}
        rows = cursor.fetchall()
        
        for row in rows:
            if len(row) >= 4:  # Make sure we have at least 4 columns
                col_name, data_type, is_nullable, column_default = row[0], row[1], row[2], row[3]
                columns[col_name] = {
                    'type': data_type,
                    'nullable': is_nullable == 'YES',
                    'default': column_default
                }
            else:
                print(f"⚠️ Unexpected row format for table {table_name}: {row}")
        
        cursor.close()
        return columns
        
    except Exception as e:
        print(f"❌ Error getting columns for table {table_name}: {e}")
        cursor.close()
        return {}

def get_all_tables(conn):
    """Get list of all tables in the database"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
        
    except Exception as e:
        print(f"❌ Error getting table list: {e}")
        cursor.close()
        return []

def compare_table_columns(local_conn, prod_conn, table_name):
    """Compare columns between local and production for a specific table"""
    print(f"🔍 Comparing table: {table_name}")
    
    local_columns = get_table_columns(local_conn, table_name)
    prod_columns = get_table_columns(prod_conn, table_name)
    
    differences = {
        'missing_in_prod': [],
        'missing_in_local': [],
        'different_types': []
    }
    
    # Find missing columns
    local_col_names = set(local_columns.keys())
    prod_col_names = set(prod_columns.keys())
    
    missing_in_prod = local_col_names - prod_col_names
    missing_in_local = prod_col_names - local_col_names
    
    if missing_in_prod:
        differences['missing_in_prod'] = list(missing_in_prod)
        print(f"  ❌ Missing in production: {missing_in_prod}")
    
    if missing_in_local:
        differences['missing_in_local'] = list(missing_in_local)
        print(f"  ❌ Missing in local: {missing_in_local}")
    
    # Compare common columns
    common_columns = local_col_names & prod_col_names
    for col_name in common_columns:
        local_col = local_columns[col_name]
        prod_col = prod_columns[col_name]
        
        if local_col['type'] != prod_col['type'] or local_col['nullable'] != prod_col['nullable']:
            differences['different_types'].append({
                'column': col_name,
                'local': local_col,
                'production': prod_col
            })
            print(f"  ⚠️ Different: {col_name} - Local: {local_col['type']} vs Prod: {prod_col['type']}")
    
    return differences

def generate_fix_sql(table_name, differences, local_columns):
    """Generate SQL to fix the differences"""
    sql_statements = []
    
    # Add missing columns
    for col_name in differences.get('missing_in_prod', []):
        if col_name in local_columns:
            col_info = local_columns[col_name]
            
            # Build column definition
            col_def = f"{col_name} {col_info['type']}"
            
            if not col_info['nullable']:
                if col_info['default']:
                    col_def += f" NOT NULL DEFAULT {col_info['default']}"
                else:
                    # Add safe defaults for NOT NULL columns
                    if 'boolean' in col_info['type'].lower():
                        col_def += " NOT NULL DEFAULT FALSE"
                    elif 'integer' in col_info['type'].lower() or 'bigint' in col_info['type'].lower():
                        col_def += " NOT NULL DEFAULT 0"
                    elif 'varchar' in col_info['type'].lower() or 'text' in col_info['type'].lower():
                        col_def += " NOT NULL DEFAULT ''"
                    elif 'timestamp' in col_info['type'].lower():
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    else:
                        col_def += " NULL"  # Fallback to NULL if we can't determine a safe default
            
            sql_statements.append(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_def};")
    
    return sql_statements

def main():
    """Main function to compare databases"""
    print("🔍 Database Sync Analyzer")
    print("=" * 50)
    
    # Connect to databases
    print("🔌 Connecting to databases...")
    
    local_conn = connect_to_local_database()
    if not local_conn:
        return
    
    prod_conn = connect_to_production_database()
    if not prod_conn:
        local_conn.close()
        return
    
    print("\n🔍 Analyzing database differences...")
    
    # Get all tables
    local_tables = get_all_tables(local_conn)
    prod_tables = get_all_tables(prod_conn)
    
    print(f"📊 Local database has {len(local_tables)} tables")
    print(f"📊 Production database has {len(prod_tables)} tables")
    
    # Find missing tables
    local_table_set = set(local_tables)
    prod_table_set = set(prod_tables)
    
    missing_in_prod = local_table_set - prod_table_set
    missing_in_local = prod_table_set - local_table_set
    
    if missing_in_prod:
        print(f"❌ Tables missing in production: {missing_in_prod}")
    
    if missing_in_local:
        print(f"❌ Tables missing in local: {missing_in_local}")
    
    # Compare common tables
    common_tables = local_table_set & prod_table_set
    print(f"\n🔄 Comparing {len(common_tables)} common tables...")
    
    all_differences = {}
    all_sql_statements = []
    
    for table_name in sorted(common_tables):
        differences = compare_table_columns(local_conn, prod_conn, table_name)
        
        if any(differences.values()):  # If there are any differences
            all_differences[table_name] = differences
            
            # Get local columns for SQL generation
            local_columns = get_table_columns(local_conn, table_name)
            sql_statements = generate_fix_sql(table_name, differences, local_columns)
            all_sql_statements.extend(sql_statements)
    
    # Generate migration script
    if all_sql_statements:
        print(f"\n🔧 Generating migration script with {len(all_sql_statements)} statements...")
        
        # Create scripts directory if it doesn't exist
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(scripts_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_file = os.path.join(scripts_dir, f"migration_{timestamp}.sql")
        
        with open(migration_file, 'w') as f:
            f.write("-- Database Migration Script\n")
            f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
            f.write("-- This script will sync production database with local database\n\n")
            f.write("BEGIN;\n\n")
            
            for sql in all_sql_statements:
                f.write(sql + "\n")
            
            f.write("\nCOMMIT;\n")
            f.write("\n-- Migration completed\n")
        
        print(f"✅ Migration script saved to: {migration_file}")
        print(f"\n🚀 To apply the migration, run:")
        print(f"python scripts/apply_migration.py {os.path.basename(migration_file)}")
    else:
        print("\n✅ No differences found - databases are in sync!")
    
    # Save detailed report
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(scripts_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(scripts_dir, f"database_comparison_{timestamp}.json")
    
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'local_tables': local_tables,
        'production_tables': prod_tables,
        'missing_tables_in_prod': list(missing_in_prod),
        'missing_tables_in_local': list(missing_in_local),
        'table_differences': all_differences,
        'sql_statements': all_sql_statements
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"📋 Detailed report saved to: {report_file}")
    
    # Close connections
    local_conn.close()
    prod_conn.close()

if __name__ == "__main__":
    main()
