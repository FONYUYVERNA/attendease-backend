#!/usr/bin/env python3
"""
WSGI entry point for AttendEase Application
This file is used by production servers like Gunicorn on Render
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the create_app function and create the application instance
from app import create_app, db

# Create the Flask application
application = create_app()
app = application  # Gunicorn looks for 'app' variable

def initialize_database():
    """Initialize database tables and create admin user if needed."""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Create default admin user if it doesn't exist
            from models.user import User
            from models.admin import Admin
            from app import bcrypt
            
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
            else:
                print("ℹ️  Admin user already exists")
                
        except Exception as e:
            print(f"⚠️  Database initialization warning: {e}")

# Initialize database when the module is loaded
if __name__ != '__main__':
    # This runs when imported by Gunicorn
    print("🚀 Starting AttendEase via WSGI...")
    initialize_database()

if __name__ == '__main__':
    # This runs when executed directly
    print("🚀 Starting AttendEase directly...")
    initialize_database()
    app.run(debug=True)
