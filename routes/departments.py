from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.department import Department
from models.student import Student
from models.course import Course
from models.user import User
from utils.decorators import admin_required
from utils.validators import validate_required_fields, ValidationError

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('', methods=['GET'])
@jwt_required()
def get_all_departments():
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Department.query
        if active_only:
            query = query.filter(Department.is_active == True)
        
        departments = query.order_by(Department.name).all()
        
        return jsonify({
            'departments': [dept.to_dict() for dept in departments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@departments_bp.route('/<department_id>', methods=['GET'])
@jwt_required()
def get_department(department_id):
    try:
        department = Department.query.get(department_id)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        return jsonify({'department': department.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@departments_bp.route('', methods=['POST'])
@admin_required
def create_department():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'code']
        validate_required_fields(data, required_fields)
        
        # Check if department name already exists
        existing_name = Department.query.filter_by(name=data['name']).first()
        if existing_name:
            return jsonify({'error': 'Department name already exists'}), 409
        
        # Check if department code already exists
        existing_code = Department.query.filter_by(code=data['code']).first()
        if existing_code:
            return jsonify({'error': 'Department code already exists'}), 409
        
        # Create department
        department = Department(
            name=data['name'],
            code=data['code'],
            description=data.get('description')
        )
        
        db.session.add(department)
        db.session.commit()
        
        return jsonify({
            'message': 'Department created successfully',
            'department': department.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@departments_bp.route('/<department_id>', methods=['PUT'])
@admin_required
def update_department(department_id):
    try:
        department = Department.query.get(department_id)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        data = request.get_json()
        
        # Update name if provided
        if 'name' in data:
            # Check if new name already exists for another department
            existing = Department.query.filter(
                Department.name == data['name'],
                Department.id != department_id
            ).first()
            if existing:
                return jsonify({'error': 'Department name already exists'}), 409
            department.name = data['name']
        
        # Update code if provided
        if 'code' in data:
            # Check if new code already exists for another department
            existing = Department.query.filter(
                Department.code == data['code'],
                Department.id != department_id
            ).first()
            if existing:
                return jsonify({'error': 'Department code already exists'}), 409
            department.code = data['code']
        
        # Update description
        if 'description' in data:
            department.description = data['description']
        
        # Update active status
        if 'is_active' in data:
            department.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Department updated successfully',
            'department': department.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@departments_bp.route('/<department_id>', methods=['DELETE'])
@admin_required
def delete_department(department_id):
    try:
        department = Department.query.get(department_id)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        # Check if department has associated students or courses
        student_count = Student.query.filter_by(department_id=department_id).count()
        course_count = Course.query.filter_by(department_id=department_id).count()
        
        if student_count > 0 or course_count > 0:
            # Soft delete - deactivate instead of deleting
            department.is_active = False
            db.session.commit()
            return jsonify({
                'message': 'Department deactivated successfully (has associated records)',
                'students_count': student_count,
                'courses_count': course_count
            }), 200
        
        # Hard delete if no associations
        db.session.delete(department)
        db.session.commit()
        
        return jsonify({'message': 'Department deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@departments_bp.route('/<department_id>/statistics', methods=['GET'])
@admin_required
def get_department_statistics(department_id):
    try:
        department = Department.query.get(department_id)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        # Get student statistics for this department
        total_students = Student.query.join(User).filter(
            Student.department_id == department_id,
            User.is_active == True
        ).count()
        
        # Students by level
        level_stats = db.session.query(
            Student.level,
            db.func.count(Student.id).label('count')
        ).join(User).filter(
            Student.department_id == department_id,
            User.is_active == True
        ).group_by(Student.level).all()
        
        # Total courses
        total_courses = Course.query.filter(
            Course.department_id == department_id,
            Course.is_active == True
        ).count()
        
        # Courses by level
        course_level_stats = db.session.query(
            Course.level,
            db.func.count(Course.id).label('count')
        ).filter(
            Course.department_id == department_id,
            Course.is_active == True
        ).group_by(Course.level).all()
        
        return jsonify({
            'department': department.to_dict(),
            'statistics': {
                'total_students': total_students,
                'total_courses': total_courses,
                'students_by_level': [
                    {'level': stat.level, 'count': stat.count} 
                    for stat in level_stats
                ],
                'courses_by_level': [
                    {'level': stat.level, 'count': stat.count} 
                    for stat in course_level_stats
                ]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
