from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    # Configuration - Load from environment variables
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/attendease')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-here')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
    
    # Debug: Print the database URL (without password for security)
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    if '@' in db_url:
        # Hide password in logs
        parts = db_url.split('@')
        user_part = parts[0].split('://')[-1]
        if ':' in user_part:
            user, _ = user_part.split(':', 1)
            safe_url = db_url.replace(user_part, f"{user}:***")
        else:
            safe_url = db_url
    else:
        safe_url = db_url
    print(f"🔗 Using database URL: {safe_url}")
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app)
    
    # Import all models explicitly to ensure they're registered with SQLAlchemy
    # Import after app context is created to avoid circular imports
    with app.app_context():
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
    
    # Register blueprints
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
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'AttendEase API is running',
            'version': '1.0.0'
        }), 200
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
