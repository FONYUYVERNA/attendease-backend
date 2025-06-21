from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.student import Student
from models.user import User
from models.department import Department
from utils.decorators import admin_required, lecturer_required, get_current_user
from utils.validators import validate_required_fields, validate_matricle_number, validate_phone_number, ValidationError

students_bp = Blueprint('students', __name__)

@students_bp.route('', methods=['GET'])
@lecturer_required
def get_all_students():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        department_id = request.args.get('department_id')
        level = request.args.get('level')
        search = request.args.get('search')
        
        query = Student.query.join(User).filter(User.is_active == True)
        
        if department_id:
            query = query.filter(Student.department_id == department_id)
        
        if level:
            query = query.filter(Student.level == level)
        
        if search:
            query = query.filter(
                db.or_(
                    Student.full_name.ilike(f'%{search}%'),
                    Student.matricle_number.ilike(f'%{search}%')
                )
            )
        
        students = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'students': [student.to_dict() for student in students.items],
            'pagination': {
                'page': students.page,
                'pages': students.pages,
                'per_page': students.per_page,
                'total': students.total,
                'has_next': students.has_next,
                'has_prev': students.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@students_bp.route('/<student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    try:
        current_user = get_current_user()
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Students can only view their own profile unless user is lecturer/admin
        if (current_user.user_type == 'student' and 
            current_user.id != student.user_id and 
            current_user.user_type not in ['lecturer', 'admin']):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'student': student.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@students_bp.route('', methods=['POST'])
@admin_required
def create_student():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'user_id', 'matricle_number', 'full_name', 
            'department_id', 'level', 'gender', 'enrollment_year'
        ]
        validate_required_fields(data, required_fields)
        
        # Validate matricle number format
        validate_matricle_number(data['matricle_number'])
        
        # Validate phone number if provided
        if data.get('phone_number'):
            validate_phone_number(data['phone_number'])
        
        # Check if user exists and is a student
        user = User.query.get(data['user_id'])
        if not user or user.user_type != 'student':
            return jsonify({'error': 'Invalid user or user is not a student'}), 400
        
        # Check if student profile already exists for this user
        if Student.query.filter_by(user_id=data['user_id']).first():
            return jsonify({'error': 'Student profile already exists for this user'}), 409
        
        # Check if matricle number already exists
        if Student.query.filter_by(matricle_number=data['matricle_number']).first():
            return jsonify({'error': 'Matricle number already exists'}), 409
        
        # Check if department exists
        if not Department.query.get(data['department_id']):
            return jsonify({'error': 'Department not found'}), 404
        
        # Create student
        student = Student(
            user_id=data['user_id'],
            matricle_number=data['matricle_number'],
            full_name=data['full_name'],
            department_id=data['department_id'],
            level=data['level'],
            gender=data['gender'],
            enrollment_year=data['enrollment_year'],
            phone_number=data.get('phone_number'),
            date_of_birth=data.get('date_of_birth'),
            profile_image_url=data.get('profile_image_url')
        )
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'message': 'Student created successfully',
            'student': student.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@students_bp.route('/<student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    try:
        current_user = get_current_user()
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Students can update their own profile, admins can update any
        if (current_user.user_type == 'student' and current_user.id != student.user_id and
            current_user.user_type != 'admin'):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Fields students can update themselves
        student_updatable_fields = [
            'phone_number', 'profile_image_url', 'face_encoding_data'
        ]
        
        # Fields only admins can update
        admin_only_fields = [
            'matricle_number', 'full_name', 'department_id', 
            'level', 'gender', 'enrollment_year', 'date_of_birth'
        ]
        
        # Update fields based on user permissions
        if current_user.user_type == 'admin':
            # Admins can update all fields
            updatable_fields = student_updatable_fields + admin_only_fields
        else:
            # Students can only update certain fields
            updatable_fields = student_updatable_fields
        
        for field in updatable_fields:
            if field in data:
                if field == 'phone_number' and data[field]:
                    validate_phone_number(data[field])
                if field == 'matricle_number':
                    validate_matricle_number(data[field])
                    # Check if matricle number already exists for another student
                    existing = Student.query.filter(
                        Student.matricle_number == data[field],
                        Student.id != student_id
                    ).first()
                    if existing:
                        return jsonify({'error': 'Matricle number already exists'}), 409
                
                setattr(student, field, data[field])
        
        # Update face registration status if face encoding is provided
        if 'face_encoding_data' in data:
            student.is_face_registered = bool(data['face_encoding_data'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Student updated successfully',
            'student': student.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@students_bp.route('/<student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Soft delete - deactivate the associated user account
        user = User.query.get(student.user_id)
        if user:
            user.is_active = False
        
        db.session.commit()
        
        return jsonify({'message': 'Student deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@students_bp.route('/by-department/<department_id>', methods=['GET'])
@lecturer_required
def get_students_by_department(department_id):
    try:
        level = request.args.get('level')
        
        query = Student.query.join(User).filter(
            Student.department_id == department_id,
            User.is_active == True
        )
        
        if level:
            query = query.filter(Student.level == level)
        
        students = query.all()
        
        return jsonify({
            'students': [student.to_dict() for student in students]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@students_bp.route('/statistics', methods=['GET'])
@admin_required
def get_student_statistics():
    try:
        # Get student counts by level
        level_stats = db.session.query(
            Student.level,
            db.func.count(Student.id).label('count')
        ).join(User).filter(User.is_active == True).group_by(Student.level).all()
        
        # Get student counts by department
        dept_stats = db.session.query(
            Department.name,
            db.func.count(Student.id).label('count')
        ).join(Student).join(User).filter(User.is_active == True).group_by(Department.name).all()
        
        # Total active students
        total_students = Student.query.join(User).filter(User.is_active == True).count()
        
        # Students with face registration
        face_registered = Student.query.join(User).filter(
            User.is_active == True,
            Student.is_face_registered == True
        ).count()
        
        return jsonify({
            'total_students': total_students,
            'face_registered': face_registered,
            'by_level': [{'level': stat.level, 'count': stat.count} for stat in level_stats],
            'by_department': [{'department': stat.name, 'count': stat.count} for stat in dept_stats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500