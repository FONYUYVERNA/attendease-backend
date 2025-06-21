"""
Render Setup Script for AttendEase Backend
Run this after deployment to set up the database and create admin user
"""

import os
import sys
from sqlalchemy import create_engine, text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def setup_render_database():
    """Set up the database on Render after deployment."""
    
    print("🚀 Setting up AttendEase Database on Render")
    print("=" * 50)
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found!")
        return False
    
    print(f"📊 Connecting to database...")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Import and create app to run migrations
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app import create_app, db
        from flask_migrate import upgrade
        
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create admin user
            from models.user import User
            from models.admin import Admin
            from app import bcrypt
            
            admin_user = User.query.filter_by(email='admin@attendease.com').first()
            if not admin_user:
                admin_user = User(
                    email='admin@attendease.com',
                    password_hash=bcrypt.generate_password_hash('AdminPass123').decode('utf-8'),
                    user_type='admin',
                    email_verified=True
                )
                db.session.add(admin_user)
                db.session.flush()
                
                admin_profile = Admin(
                    user_id=admin_user.id,
                    admin_id='ADMIN001',
                    full_name='System Administrator',
                    institution='AttendEase System',
                    role='Super Administrator'
                )
                db.session.add(admin_profile)
                db.session.commit()
                
                print("✅ Admin user created successfully")
                print("   📧 Email: admin@attendease.com")
                print("   🔑 Password: AdminPass123")
            else:
                print("ℹ️  Admin user already exists")
        
        print("🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_render_database()
