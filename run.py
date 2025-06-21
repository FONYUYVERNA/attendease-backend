#!/usr/bin/env python3
"""
AttendEase Application Runner
Run this script to start the AttendEase backend server locally
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from flask_migrate import upgrade
from sqlalchemy import text

def test_database_connection():
    """Test database connection and schema."""
    app = create_app()
    
    try:
        with app.app_context():
            # Test basic connection
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                print(f"✅ Connected to PostgreSQL: {version}")
                
                # Check if our schema exists
                result = connection.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('users', 'students', 'lecturers', 'admins')
                """))
                table_count = result.fetchone()[0]
                
                if table_count >= 4:
                    print(f"✅ Database schema verified: {table_count} core tables found")
                    return True
                else:
                    print(f"⚠️  Warning: Only {table_count} core tables found. Creating tables...")
                    return True  # We'll create them
                    
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Ensure PostgreSQL is running")
        print("2. Verify database 'attendease' exists")
        print("3. Check your .env file has correct DATABASE_URL")
        print("4. Verify database credentials are correct")
        print("\n📝 Your .env file should look like:")
        print("DATABASE_URL=postgresql://postgres:your_password@localhost:5432/attendease")
        return False

def create_admin_user():
    """Create a default admin user if none exists."""
    from models.user import User
    from models.admin import Admin
    from app import bcrypt
    
    app = create_app()
    with app.app_context():
        try:
            # Check if admin user exists
            admin_user = User.query.filter_by(email='admin@attendease.com').first()
            
            if not admin_user:
                # Create admin user
                admin_user = User(
                    email='admin@attendease.com',
                    password_hash=bcrypt.generate_password_hash('AdminPass123').decode('utf-8'),
                    user_type='admin',
                    email_verified=True
                )
                db.session.add(admin_user)
                db.session.flush()
                
                # Create admin profile
                admin_profile = Admin(
                    user_id=admin_user.id,
                    admin_id='ADMIN001',
                    full_name='System Administrator',
                    institution='AttendEase System',
                    role='Super Administrator'
                )
                db.session.add(admin_profile)
                db.session.commit()
                
                print("✅ Default admin user created:")
                print("   📧 Email: admin@attendease.com")
                print("   🔑 Password: AdminPass123")
                print("   ⚠️  Please change this password after first login!")
            else:
                print("ℹ️  Admin user already exists")
                
        except Exception as e:
            print(f"❌ Failed to create admin user: {e}")

def deploy():
    """Run deployment tasks."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created/verified")
        except Exception as e:
            print(f"ℹ️  Database setup info: {e}")

if __name__ == '__main__':
    print("🚀 Starting AttendEase Backend Server")
    print("=" * 50)
    
    # Print environment info
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 Environment file: {'.env found' if os.path.exists('.env') else '.env NOT FOUND'}")
    
    # Test database connection first
    if not test_database_connection():
        print("\n❌ Cannot start server due to database connection issues")
        sys.exit(1)
    
    # Check if we should run deployment tasks
    if os.environ.get('FLASK_DEPLOY'):
        print("\n📦 Running deployment tasks...")
        deploy()
        create_admin_user()
    else:
        # Normal application startup
        app = create_app()
        
        # Create tables and admin user
        with app.app_context():
            db.create_all()
        create_admin_user()
        
        # Start the server
        host = os.environ.get('FLASK_HOST', '0.0.0.0')
        port = int(os.environ.get('FLASK_PORT', 5000))
        debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"\n🌐 Server starting on http://{host}:{port}")
        print(f"🐛 Debug mode: {'ON' if debug else 'OFF'}")
        print("=" * 50)
        
        app.run(debug=debug, host=host, port=port)
