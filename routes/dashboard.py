from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Admin
from models.department import Department
from models.course import Course
from models.attendance_session import AttendanceSession
from models.attendance_record import AttendanceRecord

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/admin', methods=['GET'])
@jwt_required()
def admin_dashboard():
    try:
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
            
        if current_user.user_type != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get system statistics
        total_users = User.query.count()
        total_students = Student.query.count()
        total_lecturers = Lecturer.query.count()
        total_admins = Admin.query.count()
        total_departments = Department.query.count()
        total_courses = Course.query.count()
        total_sessions = AttendanceSession.query.count()
        active_sessions = AttendanceSession.query.filter_by(session_status='active').count()
        
        dashboard_data = {
            'user_info': {
                'id': current_user.id,
                'email': current_user.email,
                'user_type': current_user.user_type
            },
            'system_overview': {
                'total_users': total_users,
                'total_students': total_students,
                'total_lecturers': total_lecturers,
                'total_admins': total_admins,
                'total_departments': total_departments,
                'total_courses': total_courses,
                'total_sessions': total_sessions,
                'active_sessions': active_sessions
            },
            'status': 'operational'
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/student', methods=['GET'])
@jwt_required()
def student_dashboard():
    try:
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
            
        if current_user.user_type != 'student':
            return jsonify({'error': 'Student access required'}), 403
        
        # Try to get student profile
        student = Student.query.filter_by(user_id=current_user.id).first()
        
        if not student:
            return jsonify({'error': 'Student profile not found. Please create your profile first.'}), 404
        
        # Get student statistics
        total_attendance_records = AttendanceRecord.query.filter_by(student_id=student.id).count()
        present_records = AttendanceRecord.query.filter_by(
            student_id=student.id, 
            attendance_status='present'
        ).count()
        
        attendance_rate = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
        
        dashboard_data = {
            'user_info': {
                'id': current_user.id,
                'email': current_user.email,
                'user_type': current_user.user_type
            },
            'student_info': {
                'id': student.id,
                'matricle_number': student.matricle_number,
                'full_name': student.full_name,
                'level': student.level,
                'gender': student.gender if hasattr(student, 'gender') else None
            },
            'attendance_summary': {
                'total_sessions': total_attendance_records,
                'attended': present_records,
                'attendance_rate': f"{attendance_rate:.1f}%"
            },
            'status': 'active'
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/lecturer', methods=['GET'])
@jwt_required()
def lecturer_dashboard():
    try:
        # Get current user ID from JWT
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
            
        if current_user.user_type != 'lecturer':
            return jsonify({'error': 'Lecturer access required'}), 403
        
        # Try to get lecturer profile
        lecturer = Lecturer.query.filter_by(user_id=current_user.id).first()
        
        if not lecturer:
            return jsonify({'error': 'Lecturer profile not found. Please create your profile first.'}), 404
        
        # Get lecturer statistics
        total_sessions = AttendanceSession.query.filter_by(started_by=lecturer.id).count()
        active_sessions = AttendanceSession.query.filter_by(
            started_by=lecturer.id, 
            session_status='active'
        ).count()
        
        dashboard_data = {
            'user_info': {
                'id': current_user.id,
                'email': current_user.email,
                'user_type': current_user.user_type
            },
            'lecturer_info': {
                'id': lecturer.id,
                'lecturer_id': lecturer.lecturer_id,
                'full_name': lecturer.full_name,
                'specialization': lecturer.specialization if hasattr(lecturer, 'specialization') else None
            },
            'session_summary': {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions
            },
            'status': 'active'
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/quick-stats', methods=['GET'])
@jwt_required()
def quick_stats():
    """Get quick statistics for any user type"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = {
            'user_type': current_user.user_type,
            'system_status': 'operational',
            'active_sessions': AttendanceSession.query.filter_by(session_status='active').count()
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
