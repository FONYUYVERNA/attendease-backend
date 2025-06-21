from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.attendance_record import AttendanceRecord
from models.attendance_session import AttendanceSession
from models.student import Student
from models.lecturer import Lecturer
from utils.decorators import student_required, lecturer_required, get_current_user
from utils.validators import validate_required_fields, validate_coordinates, ValidationError
from datetime import datetime

attendance_records_bp = Blueprint('attendance_records', __name__)

@attendance_records_bp.route('', methods=['GET'])
@lecturer_required
def get_all_attendance_records():
    try:
        current_user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        session_id = request.args.get('session_id')
        student_id = request.args.get('student_id')
        status = request.args.get('status')
        
        query = AttendanceRecord.query
        
        # If user is student, only show their records
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile:
                query = query.filter(AttendanceRecord.student_id == student_profile.id)
        
        if session_id:
            query = query.filter(AttendanceRecord.session_id == session_id)
        
        if student_id and current_user.user_type in ['lecturer', 'admin']:
            query = query.filter(AttendanceRecord.student_id == student_id)
        
        if status:
            query = query.filter(AttendanceRecord.attendance_status == status)
        
        records = query.order_by(AttendanceRecord.check_in_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'attendance_records': [record.to_dict() for record in records.items],
            'pagination': {
                'page': records.page,
                'pages': records.pages,
                'per_page': records.per_page,
                'total': records.total,
                'has_next': records.has_next,
                'has_prev': records.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/<record_id>', methods=['GET'])
@student_required
def get_attendance_record(record_id):
    try:
        current_user = get_current_user()
        record = AttendanceRecord.query.get(record_id)
        
        if not record:
            return jsonify({'error': 'Attendance record not found'}), 404
        
        # Check if student can access this record
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile and record.student_id != student_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'attendance_record': record.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('', methods=['POST'])
@student_required
def create_attendance_record():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['session_id', 'location_latitude', 'location_longitude']
        validate_required_fields(data, required_fields)
        
        # Validate coordinates
        validate_coordinates(data['location_latitude'], data['location_longitude'])
        
        # Get student profile
        student_profile = Student.query.filter_by(user_id=current_user.id).first()
        if not student_profile:
            return jsonify({'error': 'Student profile not found'}), 404
        
        # Check if session exists and is active
        session = AttendanceSession.query.get(data['session_id'])
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        if session.session_status != 'active':
            return jsonify({'error': 'Attendance session is not active'}), 400
        
        # Check if student is enrolled in the course
        from models.student_enrollment import StudentEnrollment
        from models.course_assignment import CourseAssignment
        
        course_assignment = CourseAssignment.query.get(session.course_assignment_id)
        enrollment = StudentEnrollment.query.filter_by(
            student_id=student_profile.id,
            course_id=course_assignment.course_id,
            semester_id=course_assignment.semester_id,
            enrollment_status='enrolled'
        ).first()
        
        if not enrollment:
            return jsonify({'error': 'Student is not enrolled in this course'}), 403
        
        # Check if attendance record already exists
        existing_record = AttendanceRecord.query.filter_by(
            session_id=data['session_id'],
            student_id=student_profile.id
        ).first()
        if existing_record:
            return jsonify({'error': 'Attendance already recorded for this session'}), 409
        
        # Check if student is within geofence
        geofence_check = db.session.execute(
            "SELECT is_within_geofence(:lat, :lng, :geofence_id)",
            {
                'lat': data['location_latitude'],
                'lng': data['location_longitude'],
                'geofence_id': session.geofence_area_id
            }
        ).fetchone()
        
        if not geofence_check or not geofence_check[0]:
            return jsonify({'error': 'You are not within the required location for attendance'}), 400
        
        # Determine attendance status based on time
        current_time = datetime.utcnow()
        late_threshold = session.started_at + timedelta(minutes=session.late_threshold_minutes)
        
        if current_time <= late_threshold:
            attendance_status = 'present'
        else:
            attendance_status = 'late'
        
        # Create attendance record
        record = AttendanceRecord(
            session_id=data['session_id'],
            student_id=student_profile.id,
            attendance_status=attendance_status,
            check_in_method=data.get('check_in_method', 'face_recognition'),
            face_match_confidence=data.get('face_match_confidence'),
            location_latitude=data['location_latitude'],
            location_longitude=data['location_longitude'],
            device_info=data.get('device_info'),
            notes=data.get('notes')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance recorded successfully',
            'attendance_record': record.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/<record_id>', methods=['PUT'])
@lecturer_required
def update_attendance_record(record_id):
    try:
        current_user = get_current_user()
        record = AttendanceRecord.query.get(record_id)
        
        if not record:
            return jsonify({'error': 'Attendance record not found'}), 404
        
        # Check if lecturer can update this record
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            session = AttendanceSession.query.get(record.session_id)
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update allowed fields
        if 'attendance_status' in data:
            if data['attendance_status'] not in ['present', 'late', 'absent']:
                return jsonify({'error': 'Invalid attendance status'}), 400
            record.attendance_status = data['attendance_status']
        
        if 'is_verified' in data:
            record.is_verified = data['is_verified']
            if data['is_verified']:
                lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
                if lecturer_profile:
                    record.verified_by = lecturer_profile.id
        
        if 'notes' in data:
            record.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance record updated successfully',
            'attendance_record': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/session/<session_id>', methods=['GET'])
@lecturer_required
def get_session_attendance_records(session_id):
    try:
        current_user = get_current_user()
        
        # Check if session exists
        session = AttendanceSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer can access this session
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and session.started_by != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        records = AttendanceRecord.query.filter_by(
            session_id=session_id
        ).order_by(AttendanceRecord.check_in_time).all()
        
        return jsonify({
            'attendance_records': [record.to_dict() for record in records],
            'session': session.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/student/<student_id>/history', methods=['GET'])
@student_required
def get_student_attendance_history(student_id):
    try:
        current_user = get_current_user()
        
        # Check if student can access this history
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile and str(student_profile.id) != student_id:
                return jsonify({'error': 'Access denied'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        course_id = request.args.get('course_id')
        
        query = AttendanceRecord.query.filter_by(student_id=student_id)
        
        if course_id:
            # Filter by course through session and course assignment
            query = query.join(AttendanceSession).join(CourseAssignment).filter(
                CourseAssignment.course_id == course_id
            )
        
        records = query.order_by(AttendanceRecord.check_in_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'attendance_history': [record.to_dict() for record in records.items],
            'pagination': {
                'page': records.page,
                'pages': records.pages,
                'per_page': records.per_page,
                'total': records.total,
                'has_next': records.has_next,
                'has_prev': records.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/manual-override', methods=['POST'])
@lecturer_required
def create_manual_attendance():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['session_id', 'student_id', 'attendance_status', 'override_reason']
        validate_required_fields(data, required_fields)
        
        # Get lecturer profile
        lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
        if not lecturer_profile:
            return jsonify({'error': 'Lecturer profile not found'}), 404
        
        # Check if session exists
        session = AttendanceSession.query.get(data['session_id'])
        if not session:
            return jsonify({'error': 'Attendance session not found'}), 404
        
        # Check if lecturer owns this session
        if session.started_by != lecturer_profile.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if student exists
        student = Student.query.get(data['student_id'])
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Validate attendance status
        if data['attendance_status'] not in ['present', 'late', 'absent']:
            return jsonify({'error': 'Invalid attendance status'}), 400
        
        # Check if record already exists
        existing_record = AttendanceRecord.query.filter_by(
            session_id=data['session_id'],
            student_id=data['student_id']
        ).first()
        
        if existing_record:
            # Create override record
            from models.attendance_override import AttendanceOverride
            override = AttendanceOverride(
                attendance_record_id=existing_record.id,
                original_status=existing_record.attendance_status,
                new_status=data['attendance_status'],
                override_reason=data['override_reason'],
                overridden_by=lecturer_profile.id
            )
            
            # Update the original record
            existing_record.attendance_status = data['attendance_status']
            existing_record.check_in_method = 'manual_override'
            existing_record.verified_by = lecturer_profile.id
            existing_record.notes = data.get('notes', existing_record.notes)
            
            db.session.add(override)
        else:
            # Create new manual record
            record = AttendanceRecord(
                session_id=data['session_id'],
                student_id=data['student_id'],
                attendance_status=data['attendance_status'],
                check_in_method='manual_override',
                verified_by=lecturer_profile.id,
                notes=data.get('notes')
            )
            db.session.add(record)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Manual attendance recorded successfully'
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@attendance_records_bp.route('/statistics', methods=['GET'])
@lecturer_required
def get_attendance_statistics():
    try:
        current_user = get_current_user()
        
        base_query = AttendanceRecord.query
        
        # If user is lecturer, filter by their sessions
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                base_query = base_query.join(AttendanceSession).filter(
                    AttendanceSession.started_by == lecturer_profile.id
                )
        
        # Total records
        total_records = base_query.count()
        
        # Records by status
        status_stats = db.session.query(
            AttendanceRecord.attendance_status,
            db.func.count(AttendanceRecord.id).label('count')
        )
        
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                status_stats = status_stats.join(AttendanceSession).filter(
                    AttendanceSession.started_by == lecturer_profile.id
                )
        
        status_stats = status_stats.group_by(AttendanceRecord.attendance_status).all()
        
        # Records by check-in method
        method_stats = db.session.query(
            AttendanceRecord.check_in_method,
            db.func.count(AttendanceRecord.id).label('count')
        )
        
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                method_stats = method_stats.join(AttendanceSession).filter(
                    AttendanceSession.started_by == lecturer_profile.id
                )
        
        method_stats = method_stats.group_by(AttendanceRecord.check_in_method).all()
        
        return jsonify({
            'total_records': total_records,
            'by_status': [
                {'status': stat.attendance_status, 'count': stat.count} 
                for stat in status_stats
            ],
            'by_method': [
                {'method': stat.check_in_method, 'count': stat.count} 
                for stat in method_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500