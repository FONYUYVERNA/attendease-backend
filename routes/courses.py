from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.course import Course
from models.department import Department
from utils.decorators import admin_required, lecturer_required
from utils.validators import validate_required_fields, validate_course_code, ValidationError

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('', methods=['GET'])
@jwt_required()
def get_all_courses():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        department_id = request.args.get('department_id')
        level = request.args.get('level')
        semester_number = request.args.get('semester_number', type=int)
        search = request.args.get('search')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Course.query
        
        if active_only:
            query = query.filter(Course.is_active == True)
        
        if department_id:
            query = query.filter(Course.department_id == department_id)
        
        if level:
            query = query.filter(Course.level == level)
        
        if semester_number:
            query = query.filter(Course.semester_number == semester_number)
        
        if search:
            query = query.filter(
                db.or_(
                    Course.course_code.ilike(f'%{search}%'),
                    Course.course_title.ilike(f'%{search}%')
                )
            )
        
        courses = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'courses': [course.to_dict() for course in courses.items],
            'pagination': {
                'page': courses.page,
                'pages': courses.pages,
                'per_page': courses.per_page,
                'total': courses.total,
                'has_next': courses.has_next,
                'has_prev': courses.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<course_id>', methods=['GET'])
@jwt_required()
def get_course(course_id):
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'course': course.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('', methods=['POST'])
@admin_required
def create_course():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['course_code', 'course_title', 'department_id', 'level']
        validate_required_fields(data, required_fields)
        
        # Validate course code format
        validate_course_code(data['course_code'])
        
        # Check if department exists
        if not Department.query.get(data['department_id']):
            return jsonify({'error': 'Department not found'}), 404
        
        # Check if course code already exists
        if Course.query.filter_by(course_code=data['course_code']).first():
            return jsonify({'error': 'Course code already exists'}), 409
        
        # Validate level
        if data['level'] not in ['200', '300', '400', '500']:
            return jsonify({'error': 'Invalid level. Must be one of: 200, 300, 400, 500'}), 400
        
        # Validate semester number if provided
        if 'semester_number' in data and data['semester_number'] not in [1, 2]:
            return jsonify({'error': 'Semester number must be 1 or 2'}), 400
        
        # Create course
        course = Course(
            course_code=data['course_code'].upper(),
            course_title=data['course_title'],
            department_id=data['department_id'],
            level=data['level'],
            credit_units=data.get('credit_units', 3),
            semester_number=data.get('semester_number'),
            description=data.get('description')
        )
        
        db.session.add(course)
        db.session.commit()
        
        return jsonify({
            'message': 'Course created successfully',
            'course': course.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<course_id>', methods=['PUT'])
@admin_required
def update_course(course_id):
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        data = request.get_json()
        
        # Update course code
        if 'course_code' in data:
            validate_course_code(data['course_code'])
            # Check if course code already exists for another course
            existing = Course.query.filter(
                Course.course_code == data['course_code'].upper(),
                Course.id != course_id
            ).first()
            if existing:
                return jsonify({'error': 'Course code already exists'}), 409
            course.course_code = data['course_code'].upper()
        
        # Update other fields
        updatable_fields = [
            'course_title', 'department_id', 'level', 'credit_units',
            'semester_number', 'description', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'department_id':
                    if not Department.query.get(data[field]):
                        return jsonify({'error': 'Department not found'}), 404
                elif field == 'level':
                    if data[field] not in ['200', '300', '400', '500']:
                        return jsonify({'error': 'Invalid level. Must be one of: 200, 300, 400, 500'}), 400
                elif field == 'semester_number':
                    if data[field] and data[field] not in [1, 2]:
                        return jsonify({'error': 'Semester number must be 1 or 2'}), 400
                
                setattr(course, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Course updated successfully',
            'course': course.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/<course_id>', methods=['DELETE'])
@admin_required
def delete_course(course_id):
    try:
        course = Course.query.get(course_id)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Check if course has associated assignments or enrollments
        if course.assignments or course.enrollments:
            # Soft delete - deactivate instead of deleting
            course.is_active = False
            db.session.commit()
            return jsonify({'message': 'Course deactivated successfully'}), 200
        
        # Hard delete if no associations
        db.session.delete(course)
        db.session.commit()
        
        return jsonify({'message': 'Course deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/by-department/<department_id>', methods=['GET'])
@jwt_required()
def get_courses_by_department(department_id):
    try:
        level = request.args.get('level')
        semester_number = request.args.get('semester_number', type=int)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Course.query.filter(Course.department_id == department_id)
        
        if active_only:
            query = query.filter(Course.is_active == True)
        
        if level:
            query = query.filter(Course.level == level)
        
        if semester_number:
            query = query.filter(Course.semester_number == semester_number)
        
        courses = query.order_by(Course.course_code).all()
        
        return jsonify({
            'courses': [course.to_dict() for course in courses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@courses_bp.route('/statistics', methods=['GET'])
@lecturer_required
def get_course_statistics():
    try:
        # Total active courses
        total_courses = Course.query.filter_by(is_active=True).count()
        
        # Courses by level
        level_stats = db.session.query(
            Course.level,
            db.func.count(Course.id).label('count')
        ).filter(Course.is_active == True).group_by(Course.level).all()
        
        # Courses by department
        dept_stats = db.session.query(
            Department.name,
            db.func.count(Course.id).label('count')
        ).join(Course).filter(Course.is_active == True).group_by(Department.name).all()
        
        # Courses by semester
        semester_stats = db.session.query(
            Course.semester_number,
            db.func.count(Course.id).label('count')
        ).filter(
            Course.is_active == True,
            Course.semester_number.isnot(None)
        ).group_by(Course.semester_number).all()
        
        return jsonify({
            'total_courses': total_courses,
            'by_level': [{'level': stat.level, 'count': stat.count} for stat in level_stats],
            'by_department': [{'department': stat.name, 'count': stat.count} for stat in dept_stats],
            'by_semester': [{'semester': stat.semester_number, 'count': stat.count} for stat in semester_stats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500