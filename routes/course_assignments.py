from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.course_assignment import CourseAssignment
from models.course import Course
from models.lecturer import Lecturer
from models.semester import Semester
from models.geofence_area import GeofenceArea
from utils.decorators import admin_required, lecturer_required, get_current_user
from utils.validators import validate_required_fields, ValidationError

course_assignments_bp = Blueprint('course_assignments', __name__)

@course_assignments_bp.route('', methods=['GET'])
@lecturer_required
def get_all_course_assignments():
    try:
        current_user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        lecturer_id = request.args.get('lecturer_id')
        semester_id = request.args.get('semester_id')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = CourseAssignment.query
        
        # If user is lecturer, only show their assignments unless they're admin
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile:
                query = query.filter(CourseAssignment.lecturer_id == lecturer_profile.id)
        
        if lecturer_id and current_user.user_type == 'admin':
            query = query.filter(CourseAssignment.lecturer_id == lecturer_id)
        
        if semester_id:
            query = query.filter(CourseAssignment.semester_id == semester_id)
        
        if active_only:
            query = query.filter(CourseAssignment.is_active == True)
        
        assignments = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'course_assignments': [assignment.to_dict() for assignment in assignments.items],
            'pagination': {
                'page': assignments.page,
                'pages': assignments.pages,
                'per_page': assignments.per_page,
                'total': assignments.total,
                'has_next': assignments.has_next,
                'has_prev': assignments.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('/<assignment_id>', methods=['GET'])
@lecturer_required
def get_course_assignment(assignment_id):
    try:
        current_user = get_current_user()
        assignment = CourseAssignment.query.get(assignment_id)
        
        if not assignment:
            return jsonify({'error': 'Course assignment not found'}), 404
        
        # Check if lecturer can access this assignment
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and assignment.lecturer_id != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'course_assignment': assignment.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('', methods=['POST'])
@admin_required
def create_course_assignment():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['lecturer_id', 'course_id', 'semester_id']
        validate_required_fields(data, required_fields)
        
        # Check if lecturer exists
        lecturer = Lecturer.query.get(data['lecturer_id'])
        if not lecturer or not lecturer.is_active:
            return jsonify({'error': 'Lecturer not found or inactive'}), 404
        
        # Check if course exists
        course = Course.query.get(data['course_id'])
        if not course or not course.is_active:
            return jsonify({'error': 'Course not found or inactive'}), 404
        
        # Check if semester exists
        semester = Semester.query.get(data['semester_id'])
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        # Check if geofence area exists (if provided)
        if data.get('geofence_area_id'):
            geofence_area = GeofenceArea.query.get(data['geofence_area_id'])
            if not geofence_area or not geofence_area.is_active:
                return jsonify({'error': 'Geofence area not found or inactive'}), 404
        
        # Check if assignment already exists
        existing = CourseAssignment.query.filter_by(
            lecturer_id=data['lecturer_id'],
            course_id=data['course_id'],
            semester_id=data['semester_id']
        ).first()
        if existing:
            return jsonify({'error': 'Course assignment already exists'}), 409
        
        # Get admin profile for assigned_by field
        from models.admin import Admin
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        if not admin_profile:
            return jsonify({'error': 'Admin profile not found'}), 404
        
        # Create course assignment
        assignment = CourseAssignment(
            lecturer_id=data['lecturer_id'],
            course_id=data['course_id'],
            semester_id=data['semester_id'],
            geofence_area_id=data.get('geofence_area_id'),
            assigned_by=admin_profile.id
        )
        
        db.session.add(assignment)
        db.session.commit()
        
        return jsonify({
            'message': 'Course assignment created successfully',
            'course_assignment': assignment.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('/<assignment_id>', methods=['PUT'])
@admin_required
def update_course_assignment(assignment_id):
    try:
        assignment = CourseAssignment.query.get(assignment_id)
        
        if not assignment:
            return jsonify({'error': 'Course assignment not found'}), 404
        
        data = request.get_json()
        
        # Update lecturer
        if 'lecturer_id' in data:
            lecturer = Lecturer.query.get(data['lecturer_id'])
            if not lecturer or not lecturer.is_active:
                return jsonify({'error': 'Lecturer not found or inactive'}), 404
            
            # Check if new assignment would create a duplicate
            existing = CourseAssignment.query.filter(
                CourseAssignment.lecturer_id == data['lecturer_id'],
                CourseAssignment.course_id == assignment.course_id,
                CourseAssignment.semester_id == assignment.semester_id,
                CourseAssignment.id != assignment_id
            ).first()
            if existing:
                return jsonify({'error': 'Course assignment already exists for this lecturer'}), 409
            
            assignment.lecturer_id = data['lecturer_id']
        
        # Update course
        if 'course_id' in data:
            course = Course.query.get(data['course_id'])
            if not course or not course.is_active:
                return jsonify({'error': 'Course not found or inactive'}), 404
            
            # Check if new assignment would create a duplicate
            existing = CourseAssignment.query.filter(
                CourseAssignment.lecturer_id == assignment.lecturer_id,
                CourseAssignment.course_id == data['course_id'],
                CourseAssignment.semester_id == assignment.semester_id,
                CourseAssignment.id != assignment_id
            ).first()
            if existing:
                return jsonify({'error': 'Course assignment already exists for this course'}), 409
            
            assignment.course_id = data['course_id']
        
        # Update semester
        if 'semester_id' in data:
            semester = Semester.query.get(data['semester_id'])
            if not semester:
                return jsonify({'error': 'Semester not found'}), 404
            
            # Check if new assignment would create a duplicate
            existing = CourseAssignment.query.filter(
                CourseAssignment.lecturer_id == assignment.lecturer_id,
                CourseAssignment.course_id == assignment.course_id,
                CourseAssignment.semester_id == data['semester_id'],
                CourseAssignment.id != assignment_id
            ).first()
            if existing:
                return jsonify({'error': 'Course assignment already exists for this semester'}), 409
            
            assignment.semester_id = data['semester_id']
        
        # Update geofence area
        if 'geofence_area_id' in data:
            if data['geofence_area_id']:
                geofence_area = GeofenceArea.query.get(data['geofence_area_id'])
                if not geofence_area or not geofence_area.is_active:
                    return jsonify({'error': 'Geofence area not found or inactive'}), 404
            assignment.geofence_area_id = data['geofence_area_id']
        
        # Update active status
        if 'is_active' in data:
            assignment.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course assignment updated successfully',
            'course_assignment': assignment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('/<assignment_id>', methods=['DELETE'])
@admin_required
def delete_course_assignment(assignment_id):
    try:
        assignment = CourseAssignment.query.get(assignment_id)
        
        if not assignment:
            return jsonify({'error': 'Course assignment not found'}), 404
        
        # Check if assignment has associated attendance sessions
        if assignment.attendance_sessions:
            # Soft delete - deactivate instead of deleting
            assignment.is_active = False
            db.session.commit()
            return jsonify({'message': 'Course assignment deactivated successfully'}), 200
        
        # Hard delete if no associations
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({'message': 'Course assignment deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('/lecturer/<lecturer_id>/current', methods=['GET'])
@lecturer_required
def get_lecturer_current_assignments(lecturer_id):
    try:
        current_user = get_current_user()
        
        # Check if lecturer can access these assignments
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and str(lecturer_profile.id) != lecturer_id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get current semester
        current_semester = Semester.query.filter_by(is_current=True).first()
        if not current_semester:
            return jsonify({'error': 'No current semester set'}), 404
        
        assignments = CourseAssignment.query.filter_by(
            lecturer_id=lecturer_id,
            semester_id=current_semester.id,
            is_active=True
        ).all()
        
        return jsonify({
            'course_assignments': [assignment.to_dict() for assignment in assignments],
            'semester': current_semester.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@course_assignments_bp.route('/statistics', methods=['GET'])
@admin_required
def get_assignment_statistics():
    try:
        # Get current semester
        current_semester = Semester.query.filter_by(is_current=True).first()
        
        # Total active assignments
        total_assignments = CourseAssignment.query.filter_by(is_active=True).count()
        
        # Assignments for current semester
        current_semester_assignments = 0
        if current_semester:
            current_semester_assignments = CourseAssignment.query.filter_by(
                semester_id=current_semester.id,
                is_active=True
            ).count()
        
        # Assignments by lecturer
        lecturer_stats = db.session.query(
            Lecturer.full_name,
            db.func.count(CourseAssignment.id).label('count')
        ).join(CourseAssignment).filter(
            CourseAssignment.is_active == True
        ).group_by(Lecturer.full_name).all()
        
        return jsonify({
            'total_assignments': total_assignments,
            'current_semester_assignments': current_semester_assignments,
            'by_lecturer': [
                {'lecturer': stat.full_name, 'count': stat.count} 
                for stat in lecturer_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500