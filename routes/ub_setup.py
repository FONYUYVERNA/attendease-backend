"""
University of Buea FET Setup Routes
Special endpoints for UB FET-specific operations
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.department import Department
from models.course import Course
from models.geofence_area import GeofenceArea
from models.system_setting import SystemSetting
from utils.decorators import admin_required
from utils.ub_validators import (
    validate_ub_matricle_number, 
    validate_ub_course_code,
    validate_ub_lecturer_email,
    get_department_from_course_code,
    validate_ub_classroom_name
)

ub_setup_bp = Blueprint('ub_setup', __name__)

@ub_setup_bp.route('/departments/ub-fet', methods=['GET'])
@jwt_required()
def get_ub_fet_departments():
    """Get all UB FET departments"""
    try:
        ub_departments = Department.query.filter(
            Department.code.in_(['CEF', 'EEF', 'CIV', 'MEF'])
        ).all()
        
        return jsonify({
            'departments': [dept.to_dict() for dept in ub_departments],
            'total': len(ub_departments)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ub_setup_bp.route('/classrooms/ub-fet', methods=['GET'])
@jwt_required()
def get_ub_fet_classrooms():
    """Get all UB FET classroom geofence areas"""
    try:
        ub_classrooms = GeofenceArea.query.filter(
            GeofenceArea.building.in_(['FET Building', 'Technology Building'])
        ).all()
        
        # Group by building
        fet_building = []
        tech_building = []
        
        for classroom in ub_classrooms:
            classroom_data = classroom.to_dict()
            if classroom.building == 'FET Building':
                fet_building.append(classroom_data)
            else:
                tech_building.append(classroom_data)
        
        return jsonify({
            'classrooms': {
                'fet_building': fet_building,
                'technology_building': tech_building
            },
            'total': len(ub_classrooms)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ub_setup_bp.route('/courses/validate-code', methods=['POST'])
@admin_required
def validate_course_code():
    """Validate UB FET course code format"""
    try:
        data = request.get_json()
        course_code = data.get('course_code')
        department_code = data.get('department_code')
        
        if not course_code:
            return jsonify({'error': 'Course code is required'}), 400
        
        # Validate course code
        validation_result = validate_ub_course_code(course_code, department_code)
        
        # Get department info
        dept_info = get_department_from_course_code(course_code)
        
        return jsonify({
            'valid': True,
            'course_code': course_code.upper(),
            'validation_result': validation_result,
            'department_info': dept_info,
            'message': f'Valid UB FET course code for {validation_result["semester"]}{"st" if validation_result["semester"] == 1 else "nd"} semester'
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400

@ub_setup_bp.route('/matricle/validate', methods=['POST'])
@admin_required
def validate_matricle():
    """Validate UB FET matricle number format"""
    try:
        data = request.get_json()
        matricle_number = data.get('matricle_number')
        
        if not matricle_number:
            return jsonify({'error': 'Matricle number is required'}), 400
        
        # Validate matricle number
        validate_ub_matricle_number(matricle_number)
        
        # Extract information
        year_part = matricle_number[2:4]
        number_part = matricle_number[5:8]
        
        return jsonify({
            'valid': True,
            'matricle_number': matricle_number.upper(),
            'year': f"20{year_part}",
            'sequence_number': number_part,
            'message': 'Valid UB FET matricle number format'
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400

@ub_setup_bp.route('/lecturer/validate-email', methods=['POST'])
@admin_required
def validate_lecturer_email():
    """Validate lecturer email (UB institutional or general)"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Validate email
        is_ub_institutional = validate_ub_lecturer_email(email)
        
        return jsonify({
            'valid': True,
            'email': email.lower(),
            'is_ub_institutional': is_ub_institutional,
            'message': 'Valid UB institutional email' if is_ub_institutional else 'Valid email (external)'
        }), 200
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400

@ub_setup_bp.route('/setup-status', methods=['GET'])
@jwt_required()
def get_ub_setup_status():
    """Get UB FET setup status"""
    try:
        # Check departments
        dept_count = Department.query.filter(
            Department.code.in_(['CEF', 'EEF', 'CIV', 'MEF'])
        ).count()
        
        # Check classrooms
        classroom_count = GeofenceArea.query.filter(
            GeofenceArea.building.in_(['FET Building', 'Technology Building'])
        ).count()
        
        # Check courses
        course_count = Course.query.join(Department).filter(
            Department.code.in_(['CEF', 'EEF', 'CIV', 'MEF'])
        ).count()
        
        # Check system settings
        settings_count = SystemSetting.query.filter(
            SystemSetting.setting_key.in_([
                'institution_name', 'matricle_format', 
                'course_code_patterns', 'semester_numbering_rule'
            ])
        ).count()
        
        setup_complete = (
            dept_count >= 4 and 
            classroom_count >= 7 and 
            course_count >= 8 and 
            settings_count >= 4
        )
        
        return jsonify({
            'setup_complete': setup_complete,
            'status': {
                'departments': f"{dept_count}/4 UB FET departments",
                'classrooms': f"{classroom_count}/7 UB FET classrooms", 
                'courses': f"{course_count}+ UB FET courses",
                'settings': f"{settings_count}/4 UB FET settings"
            },
            'next_steps': [] if setup_complete else [
                'Run the UB FET setup script',
                'Verify all departments are created',
                'Check classroom geofence areas',
                'Validate course codes and formats'
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
