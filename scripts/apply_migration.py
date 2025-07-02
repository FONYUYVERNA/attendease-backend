import psycopg2
import sys
import os
from datetime import datetime

# Production database URL
PRODUCTION_DB_URL = "postgresql://attendease_user:UBjvm30T0XorXNwoai7T14zNGbvOSgKp@dpg-d1bd26odl3ps73eikkmg-a.frankfurt-postgres.render.com/attendease"

def apply_migration(migration_file):
    """Apply a migration SQL file to the production database"""
    print("🚀 Database Migration Applier")
    print("=" * 50)
    
    # Check if migration file exists
    if not os.path.exists(migration_file):
        # Try looking in scripts directory
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        migration_file = os.path.join(scripts_dir, migration_file)
        
        if not os.path.exists(migration_file):
            print(f"❌ Migration file not found: {migration_file}")
            sys.exit(1)
    
    print(f"📄 Migration file: {migration_file}")
    
    try:
        # Read migration file
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        if not migration_sql.strip():
            print("❌ Migration file is empty")
            sys.exit(1)
        
        print("📋 Migration SQL:")
        print("-" * 30)
        print(migration_sql)
        print("-" * 30)
        
        # Confirm before applying
        response = input("\n❓ Apply this migration to production database? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Migration cancelled")
            sys.exit(0)
        
        # Connect to production database
        print("\n🔌 Connecting to production database...")
        conn = psycopg2.connect(PRODUCTION_DB_URL)
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # Apply migration
        print("\n🔧 Applying migration...")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement.startswith('--') or not statement:
                continue
                
            try:
                print(f"  📝 Executing statement {i}/{len(statements)}...")
                cursor.execute(statement)
                print(f"  ✅ Statement {i} executed successfully")
            except Exception as e:
                print(f"  ❌ Error in statement {i}: {e}")
                print(f"  📄 Statement: {statement}")
                conn.rollback()
                raise
        
        # Commit all changes
        conn.commit()
        print("\n💾 Migration applied successfully!")
        
        # Log migration
        timestamp = datetime.now().isoformat()
        print(f"📅 Migration completed at: {timestamp}")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python apply_migration.py <migration_file.sql>")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    apply_migration(migration_file)
