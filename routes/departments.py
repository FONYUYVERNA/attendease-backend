from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.department import Department
from utils.decorators import admin_required
from utils.validators import validate_required_fields, ValidationError

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('', methods=['GET'])
@jwt_required()
def get_all_departments():
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        search = request.args.get('search')
        
        query = Department.query
        
        if active_only:
            query = query.filter(Department.is_active == True)
        
        if search:
            query = query.filter(
                db.or_(
                    Department.name.ilike(f'%{search}%'),
                    Department.code.ilike(f'%{search}%')
                )
            )
        
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
        if Department.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Department name already exists'}), 409
        
        # Check if department code already exists
        if Department.query.filter_by(code=data['code']).first():
            return jsonify({'error': 'Department code already exists'}), 409
        
        # Create department
        department = Department(
            name=data['name'],
            code=data['code'].upper(),
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
        
        # Update fields
        if 'name' in data:
            # Check if department name already exists for another department
            existing = Department.query.filter(
                Department.name == data['name'],
                Department.id != department_id
            ).first()
            if existing:
                return jsonify({'error': 'Department name already exists'}), 409
            department.name = data['name']
        
        if 'code' in data:
            # Check if department code already exists for another department
            existing = Department.query.filter(
                Department.code == data['code'].upper(),
                Department.id != department_id
            ).first()
            if existing:
                return jsonify({'error': 'Department code already exists'}), 409
            department.code = data['code'].upper()
        
        if 'description' in data:
            department.description = data['description']
        
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
        
        # Check if department has associated courses or students
        if department.courses or department.students:
            # Soft delete - deactivate instead of deleting
            department.is_active = False
            db.session.commit()
            return jsonify({'message': 'Department deactivated successfully'}), 200
        
        # Hard delete if no associations
        db.session.delete(department)
        db.session.commit()
        
        return jsonify({'message': 'Department deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@departments_bp.route('/<department_id>/statistics', methods=['GET'])
@jwt_required()
def get_department_statistics(department_id):
    try:
        department = Department.query.get(department_id)
        
        if not department:
            return jsonify({'error': 'Department not found'}), 404
        
        # Get student counts by level
        from models.student import Student
        level_stats = db.session.query(
            Student.level,
            db.func.count(Student.id).label('count')
        ).filter(Student.department_id == department_id).group_by(Student.level).all()
        
        # Get course count
        course_count = len([course for course in department.courses if course.is_active])
        
        # Total students
        total_students = len(department.students)
        
        return jsonify({
            'department': department.to_dict(),
            'total_students': total_students,
            'total_courses': course_count,
            'students_by_level': [
                {'level': stat.level, 'count': stat.count} 
                for stat in level_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500