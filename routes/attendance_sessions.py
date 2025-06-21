from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.attendance_session import AttendanceSession
from models.course_assignment import CourseAssignment
from models.geofence_area import GeofenceArea
from models.lecturer import Lecturer
from models.student_enrollment import StudentEnrollment
from utils.decorators import lecturer_required, get_current_user
from utils.validators import validate_required_fields, ValidationError
from datetime import datetime, timedelta

attendance_sessions_bp = Blueprint('attendance_sessions', __name__)

@attendance_sessions_bp.route('', methods=['GET'])
@lecturer_required
def get_all_attendance_sessions():
    try:
        current_user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        course_assignment_id = request.args.get('course_assignment_id')
        status = request.args.get('status')
        
        query = AttendanceSession.query
        
        # If user is lecturer, only show their sessions
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                query = query.filter(AttendanceSession.started_by == lecturer_profile.id)
        
        if course_assignment_id:
            query = query.filter(AttendanceSession.course_assignment_id == course_assignment_id)
        
        if status:
            query = query.filter(AttendanceSession.session_status == status)
        
        sessions = query.order_by(AttendanceSession.started_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'attendance_sessions': [session.to_dict() for session in sessions.items],
            'pagination': {
                'page': sessions.page,
                'pages': sessions.pages,
                'per_page': sessions.per_page,
                'total': sessions.total,
                'has_next': sessions.has_next,
                'has_prev': sessions.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/<session_id>', methods=['GET'])
@lecturer_required
def get_attendance_session(session_id):
    try:
        current_user = get_current_user()
        session = AttendanceSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer can access this session
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'attendance_session': session.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('', methods=['POST'])
@lecturer_required
def create_attendance_session():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['course_assignment_id', 'geofence_area_id']
        validate_required_fields(data, required_fields)
        
        # Get lecturer profile
        lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
        if not lecturer_profile:
            return jsonify({'error': 'Lecturer profile not found'}), 404
        
        # Check if course assignment exists and belongs to lecturer
        course_assignment = CourseAssignment.query.get(data['course_assignment_id'])
        if not course_assignment or not course_assignment.is_active:
            return jsonify({'error': 'Course assignment not found or inactive'}), 404
        
        if course_assignment.lecturer_id != lecturer_profile.id:
            return jsonify({'error': 'Access denied. You are not assigned to this course'}), 403
        
        # Check if geofence area exists
        geofence_area = GeofenceArea.query.get(data['geofence_area_id'])
        if not geofence_area or not geofence_area.is_active:
            return jsonify({'error': 'Geofence area not found or inactive'}), 404
        
        # Check if there's already an active session for this course assignment
        existing_session = AttendanceSession.query.filter_by(
            course_assignment_id=data['course_assignment_id'],
            session_status='active'
        ).first()
        if existing_session:
            return jsonify({'error': 'There is already an active session for this course'}), 409
        
        # Count expected students
        expected_students = StudentEnrollment.query.filter_by(
            course_id=course_assignment.course_id,
            semester_id=course_assignment.semester_id,
            enrollment_status='enrolled'
        ).count()
        
        # Create attendance session
        session = AttendanceSession(
            course_assignment_id=data['course_assignment_id'],
            geofence_area_id=data['geofence_area_id'],
            session_name=data.get('session_name'),
            topic=data.get('topic'),
            started_by=lecturer_profile.id,
            expected_students=expected_students,
            late_threshold_minutes=data.get('late_threshold_minutes', 15),
            auto_end_minutes=data.get('auto_end_minutes', 120),
            notes=data.get('notes')
        )
        
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance session created successfully',
            'attendance_session': session.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/<session_id>', methods=['PUT'])
@lecturer_required
def update_attendance_session(session_id):
    try:
        current_user = get_current_user()
        session = AttendanceSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer can update this session
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        updatable_fields = [
            'session_name', 'topic', 'late_threshold_minutes', 
            'auto_end_minutes', 'notes'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(session, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance session updated successfully',
            'attendance_session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/<session_id>/end', methods=['POST'])
@lecturer_required
def end_attendance_session(session_id):
    try:
        current_user = get_current_user()
        session = AttendanceSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer can end this session
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        if session.session_status != 'active':
            return jsonify({'error': 'Session is not active'}), 400
        
        # End the session
        session.ended_at = datetime.utcnow()
        session.session_status = 'ended'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance session ended successfully',
            'attendance_session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/<session_id>/cancel', methods=['POST'])
@lecturer_required
def cancel_attendance_session(session_id):
    try:
        current_user = get_current_user()
        session = AttendanceSession.query.get(session_id)
        
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer can cancel this session
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        if session.session_status != 'active':
            return jsonify({'error': 'Session is not active'}), 400
        
        # Cancel the session
        session.ended_at = datetime.utcnow()
        session.session_status = 'cancelled'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance session cancelled successfully',
            'attendance_session': session.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/active', methods=['GET'])
@lecturer_required
def get_active_sessions():
    try:
        current_user = get_current_user()
        
        query = AttendanceSession.query.filter_by(session_status='active')
        
        # If user is lecturer, only show their sessions
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                query = query.filter(AttendanceSession.started_by == lecturer_profile.id)
        
        sessions = query.order_by(AttendanceSession.started_at.desc()).all()
        
        return jsonify({
            'active_sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/lecturer/<lecturer_id>/recent', methods=['GET'])
@lecturer_required
def get_lecturer_recent_sessions(lecturer_id):
    try:
        current_user = get_current_user()
        
        # Check if lecturer can access these sessions
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and str(lecturer_profile.id) != lecturer_id:
                return jsonify({'error': 'Access denied'}), 403
        
        limit = request.args.get('limit', 10, type=int)
        
        sessions = AttendanceSession.query.filter_by(
            started_by=lecturer_id
        ).order_by(AttendanceSession.started_at.desc()).limit(limit).all()
        
        return jsonify({
            'recent_sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_sessions_bp.route('/statistics', methods=['GET'])
@lecturer_required
def get_session_statistics():
    try:
        current_user = get_current_user()
        
        base_query = AttendanceSession.query
        
        # If user is lecturer, only show their statistics
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                base_query = base_query.filter(AttendanceSession.started_by == lecturer_profile.id)
        
        # Total sessions
        total_sessions = base_query.count()
        
        # Sessions by status
        status_stats = db.session.query(
            AttendanceSession.session_status,
            db.func.count(AttendanceSession.id).label('count')
        )
        
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                status_stats = status_stats.filter(AttendanceSession.started_by == lecturer_profile.id)
        
        status_stats = status_stats.group_by(AttendanceSession.session_status).all()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sessions = base_query.filter(
            AttendanceSession.started_at >= thirty_days_ago
        ).count()
        
        return jsonify({
            'total_sessions': total_sessions,
            'recent_sessions_30_days': recent_sessions,
            'by_status': [
                {'status': stat.session_status, 'count': stat.count} 
                for stat in status_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500