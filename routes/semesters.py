from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.semester import Semester
from models.academic_year import AcademicYear
from utils.decorators import admin_required
from utils.validators import validate_required_fields, ValidationError
from datetime import datetime

semesters_bp = Blueprint('semesters', __name__)

@semesters_bp.route('', methods=['GET'])
@jwt_required()
def get_all_semesters():
    try:
        academic_year_id = request.args.get('academic_year_id')
        current_only = request.args.get('current_only', 'false').lower() == 'true'
        
        query = Semester.query
        
        if academic_year_id:
            query = query.filter(Semester.academic_year_id == academic_year_id)
        
        if current_only:
            query = query.filter(Semester.is_current == True)
        
        semesters = query.order_by(Semester.start_date.desc()).all()
        
        return jsonify({
            'semesters': [semester.to_dict() for semester in semesters]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_semester():
    try:
        current_semester = Semester.query.filter_by(is_current=True).first()
        
        if not current_semester:
            return jsonify({'error': 'No current semester set'}), 404
        
        return jsonify({'semester': current_semester.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('/<semester_id>', methods=['GET'])
@jwt_required()
def get_semester(semester_id):
    try:
        semester = Semester.query.get(semester_id)
        
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        return jsonify({'semester': semester.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('', methods=['POST'])
@admin_required
def create_semester():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['academic_year_id', 'semester_number', 'name', 'start_date', 'end_date']
        validate_required_fields(data, required_fields)
        
        # Validate semester number
        if data['semester_number'] not in [1, 2]:
            return jsonify({'error': 'Semester number must be 1 or 2'}), 400
        
        # Check if academic year exists
        academic_year = AcademicYear.query.get(data['academic_year_id'])
        if not academic_year:
            return jsonify({'error': 'Academic year not found'}), 404
        
        # Parse and validate dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate date logic
        if start_date >= end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400

        # Check if academic year exists and is valid
        academic_year = AcademicYear.query.get(data['academic_year_id'])
        if not academic_year:
            return jsonify({'error': 'Academic year not found'}), 404

        # Validate dates are within academic year (with some tolerance)
        if (start_date < academic_year.start_date or 
            end_date > academic_year.end_date):
            return jsonify({
                'error': 'Semester dates must be within academic year dates',
                'academic_year_start': academic_year.start_date.isoformat(),
                'academic_year_end': academic_year.end_date.isoformat()
            }), 400
        
        # Check if semester already exists for this academic year and number
        existing = Semester.query.filter_by(
            academic_year_id=data['academic_year_id'],
            semester_number=data['semester_number']
        ).first()
        if existing:
            return jsonify({'error': 'Semester already exists for this academic year'}), 409
        
        # Create semester
        semester = Semester(
            academic_year_id=data['academic_year_id'],
            semester_number=data['semester_number'],
            name=data['name'],
            start_date=start_date,
            end_date=end_date,
            is_current=data.get('is_current', False)
        )
        
        # If this is set as current, unset others
        if semester.is_current:
            Semester.query.update({'is_current': False})
        
        db.session.add(semester)
        db.session.commit()
        
        return jsonify({
            'message': 'Semester created successfully',
            'semester': semester.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('/<semester_id>', methods=['PUT'])
@admin_required
def update_semester(semester_id):
    try:
        semester = Semester.query.get(semester_id)
        
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        data = request.get_json()
        
        # Update semester number
        if 'semester_number' in data:
            if data['semester_number'] not in [1, 2]:
                return jsonify({'error': 'Semester number must be 1 or 2'}), 400
            # Check if another semester exists with this number in the same academic year
            existing = Semester.query.filter(
                Semester.academic_year_id == semester.academic_year_id,
                Semester.semester_number == data['semester_number'],
                Semester.id != semester_id
            ).first()
            if existing:
                return jsonify({'error': 'Semester number already exists for this academic year'}), 409
            semester.semester_number = data['semester_number']
        
        # Update name
        if 'name' in data:
            semester.name = data['name']
        
        # Update dates
        if 'start_date' in data:
            semester.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        if 'end_date' in data:
            semester.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Validate date logic
        if semester.start_date >= semester.end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
        
        # Validate dates are within academic year
        academic_year = AcademicYear.query.get(semester.academic_year_id)
        if (semester.start_date < academic_year.start_date or 
            semester.end_date > academic_year.end_date):
            return jsonify({'error': 'Semester dates must be within academic year dates'}), 400
        
        # Update current status
        if 'is_current' in data:
            if data['is_current']:
                # Unset current status for all other semesters
                Semester.query.update({'is_current': False})
            semester.is_current = data['is_current']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Semester updated successfully',
            'semester': semester.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('/<semester_id>', methods=['DELETE'])
@admin_required
def delete_semester(semester_id):
    try:
        semester = Semester.query.get(semester_id)
        
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        # Check if semester has associated course assignments or enrollments
        if semester.course_assignments or semester.student_enrollments:
            return jsonify({
                'error': 'Cannot delete semester with associated course assignments or enrollments'
            }), 400
        
        db.session.delete(semester)
        db.session.commit()
        
        return jsonify({'message': 'Semester deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@semesters_bp.route('/<semester_id>/set-current', methods=['POST'])
@admin_required
def set_current_semester(semester_id):
    try:
        semester = Semester.query.get(semester_id)
        
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        # Unset current status for all semesters
        Semester.query.update({'is_current': False})
        
        # Set this semester as current
        semester.is_current = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Semester set as current successfully',
            'semester': semester.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
