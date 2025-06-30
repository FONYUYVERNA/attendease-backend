from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from datetime import timedelta, datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    # Configuration - Load from environment variables with better defaults
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-for-development-only')
    
    # Handle DATABASE_URL for both local and production
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found in environment variables!")
        # Use a fallback that won't crash the app
        database_url = 'sqlite:///fallback.db'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    # Debug: Print configuration info
    print(f"🔧 SECRET_KEY: {'✅ Set' if os.getenv('SECRET_KEY') else '❌ Using fallback'}")
    print(f"🔧 JWT_SECRET_KEY: {'✅ Set' if os.getenv('JWT_SECRET_KEY') else '❌ Using fallback'}")
    print(f"🔧 DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Using fallback'}")
    
    # Initialize extensions with app
    try:
        db.init_app(app)
        jwt.init_app(app)
        bcrypt.init_app(app)
        CORS(app)
        print("✅ Flask extensions initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Flask extensions: {e}")
    
    # Import models with error handling
    with app.app_context():
        try:
            from models.user import User
            from models.student import Student
            from models.lecturer import Lecturer
            from models.admin import Admin
            from models.department import Department
            from models.academic_year import AcademicYear
            from models.semester import Semester
            from models.course import Course
            from models.geofence_area import GeofenceArea
            from models.course_assignment import CourseAssignment
            from models.student_enrollment import StudentEnrollment
            from models.attendance_session import AttendanceSession
            from models.attendance_record import AttendanceRecord
            from models.attendance_override import AttendanceOverride
            from models.notification import Notification
            from models.system_setting import SystemSetting
            from models.user_session import UserSession
            from models.user_preference import UserPreference
            from models.two_factor_auth import TwoFactorAuth
            from models.audit_log import AuditLog
            from models.verification_code import VerificationCode  # New model
            print("✅ Models imported successfully")
            
            # Try to create tables
            db.create_all()
            print("✅ Database tables created/verified")
            
        except Exception as e:
            print(f"⚠️  Database/Models warning: {e}")
            print("   App will continue without database functionality")
    
    # Register blueprints with error handling
    try:
        from routes.auth import auth_bp
        from routes.users import users_bp
        from routes.students import students_bp
        from routes.lecturers import lecturers_bp
        from routes.admins import admins_bp
        from routes.departments import departments_bp
        from routes.academic_years import academic_years_bp
        from routes.semesters import semesters_bp
        from routes.courses import courses_bp
        from routes.geofence_areas import geofence_areas_bp
        from routes.course_assignments import course_assignments_bp
        from routes.student_enrollments import student_enrollments_bp
        from routes.attendance_sessions import attendance_sessions_bp
        from routes.attendance_records import attendance_records_bp
        from routes.notifications import notifications_bp
        from routes.system_settings import system_settings_bp
        from routes.dashboard import dashboard_bp
        from routes.reports import reports_bp
        from routes.ub_setup import ub_setup_bp
        
        # Register all blueprints with /api prefix
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(students_bp, url_prefix='/api/students')
        app.register_blueprint(lecturers_bp, url_prefix='/api/lecturers')
        app.register_blueprint(admins_bp, url_prefix='/api/admins')
        app.register_blueprint(departments_bp, url_prefix='/api/departments')
        app.register_blueprint(academic_years_bp, url_prefix='/api/academic-years')
        app.register_blueprint(semesters_bp, url_prefix='/api/semesters')
        app.register_blueprint(courses_bp, url_prefix='/api/courses')
        app.register_blueprint(geofence_areas_bp, url_prefix='/api/geofence-areas')
        app.register_blueprint(course_assignments_bp, url_prefix='/api/course-assignments')
        app.register_blueprint(student_enrollments_bp, url_prefix='/api/student-enrollments')
        app.register_blueprint(attendance_sessions_bp, url_prefix='/api/attendance-sessions')
        app.register_blueprint(attendance_records_bp, url_prefix='/api/attendance-records')
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
        app.register_blueprint(system_settings_bp, url_prefix='/api/system-settings')
        app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
        app.register_blueprint(reports_bp, url_prefix='/api/reports')
        app.register_blueprint(ub_setup_bp, url_prefix='/api/ub-setup')
        print("✅ All routes registered successfully")
        
    except Exception as e:
        print(f"❌ Error registering routes: {e}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'details': str(error)}), 500
    
    # Health check endpoint with detailed diagnostics
    @app.route('/api/health')
    def health_check():
        health_info = {
            'status': 'healthy',
            'message': 'AttendEase API is running',
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'diagnostics': {
                'secret_key': 'configured' if os.getenv('SECRET_KEY') else 'using_fallback',
                'jwt_secret': 'configured' if os.getenv('JWT_SECRET_KEY') else 'using_fallback',
                'database_url': 'configured' if os.getenv('DATABASE_URL') else 'missing',
                'smtp_configured': 'configured' if os.getenv('SMTP_USERNAME') else 'using_mock',
                'sms_configured': 'configured' if os.getenv('TWILIO_ACCOUNT_SID') else 'using_mock'
            }
        }
        
        # Test database connection
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            health_info['database'] = 'connected'
        except Exception as e:
            health_info['database'] = f'error: {str(e)}'
        
        return jsonify(health_info), 200

    # Root endpoint with diagnostics
    @app.route('/')
    def root():
        return jsonify({
            'message': 'Welcome to AttendEase API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': str(datetime.now()),
            'environment': {
                'DATABASE_URL': 'configured' if os.getenv('DATABASE_URL') else 'missing',
                'SECRET_KEY': 'configured' if os.getenv('SECRET_KEY') else 'missing',
                'JWT_SECRET_KEY': 'configured' if os.getenv('JWT_SECRET_KEY') else 'missing',
                'SMTP_USERNAME': 'configured' if os.getenv('SMTP_USERNAME') else 'missing',
                'TWILIO_ACCOUNT_SID': 'configured' if os.getenv('TWILIO_ACCOUNT_SID') else 'missing'
            },
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'registration_flow': {
                    'step_1': '/api/auth/send-verification',
                    'step_2': '/api/auth/verify-registration',
                    'resend': '/api/auth/resend-verification'
                },
                'users': '/api/users',
                'students': '/api/students',
                'lecturers': '/api/lecturers',
                'courses': '/api/courses',
                'departments': '/api/departments',
                'attendance': '/api/attendance-sessions'
            },
            'features': {
                '2fa_registration': 'enabled',
                'email_verification': 'enabled (students/admins)',
                'sms_verification': 'enabled (lecturers)',
                'session_management': 'enabled',
                'mock_notifications': 'enabled (development)'
            },
            'next_steps': [
                'Visit /api/health for detailed diagnostics',
                'Use /api/auth/send-verification to start registration',
                'Configure SMTP_USERNAME and SMTP_PASSWORD for email',
                'Configure TWILIO credentials for SMS'
            ]
        }), 200
    
    print("🚀 Flask app created successfully!")
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
