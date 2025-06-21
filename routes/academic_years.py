from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.academic_year import AcademicYear
from utils.decorators import admin_required
from utils.validators import validate_required_fields, ValidationError
from datetime import datetime

academic_years_bp = Blueprint('academic_years', __name__)

@academic_years_bp.route('', methods=['GET'])
@jwt_required()
def get_all_academic_years():
    try:
        years = AcademicYear.query.order_by(AcademicYear.start_date.desc()).all()
        
        return jsonify({
            'academic_years': [year.to_dict() for year in years]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_academic_year():
    try:
        current_year = AcademicYear.query.filter_by(is_current=True).first()
        
        if not current_year:
            return jsonify({'error': 'No current academic year set'}), 404
        
        return jsonify({'academic_year': current_year.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('/<year_id>', methods=['GET'])
@jwt_required()
def get_academic_year(year_id):
    try:
        year = AcademicYear.query.get(year_id)
        
        if not year:
            return jsonify({'error': 'Academic year not found'}), 404
        
        return jsonify({'academic_year': year.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('', methods=['POST'])
@admin_required
def create_academic_year():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['year_name', 'start_date', 'end_date']
        validate_required_fields(data, required_fields)
        
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Validate date logic
        if start_date >= end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
        
        # Check if academic year name already exists
        if AcademicYear.query.filter_by(year_name=data['year_name']).first():
            return jsonify({'error': 'Academic year name already exists'}), 409
        
        # Create academic year
        academic_year = AcademicYear(
            year_name=data['year_name'],
            start_date=start_date,
            end_date=end_date,
            is_current=data.get('is_current', False)
        )
        
        # If this is set as current, unset others
        if academic_year.is_current:
            AcademicYear.query.update({'is_current': False})
        
        db.session.add(academic_year)
        db.session.commit()
        
        return jsonify({
            'message': 'Academic year created successfully',
            'academic_year': academic_year.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('/<year_id>', methods=['PUT'])
@admin_required
def update_academic_year(year_id):
    try:
        academic_year = AcademicYear.query.get(year_id)
        
        if not academic_year:
            return jsonify({'error': 'Academic year not found'}), 404
        
        data = request.get_json()
        
        # Update year name
        if 'year_name' in data:
            # Check if academic year name already exists for another year
            existing = AcademicYear.query.filter(
                AcademicYear.year_name == data['year_name'],
                AcademicYear.id != year_id
            ).first()
            if existing:
                return jsonify({'error': 'Academic year name already exists'}), 409
            academic_year.year_name = data['year_name']
        
        # Update dates
        if 'start_date' in data:
            academic_year.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        
        if 'end_date' in data:
            academic_year.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Validate date logic
        if academic_year.start_date >= academic_year.end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
        
        # Update current status
        if 'is_current' in data:
            if data['is_current']:
                # Unset current status for all other years
                AcademicYear.query.update({'is_current': False})
            academic_year.is_current = data['is_current']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Academic year updated successfully',
            'academic_year': academic_year.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('/<year_id>', methods=['DELETE'])
@admin_required
def delete_academic_year(year_id):
    try:
        academic_year = AcademicYear.query.get(year_id)
        
        if not academic_year:
            return jsonify({'error': 'Academic year not found'}), 404
        
        # Check if academic year has associated semesters
        if academic_year.semesters:
            return jsonify({
                'error': 'Cannot delete academic year with associated semesters'
            }), 400
        
        db.session.delete(academic_year)
        db.session.commit()
        
        return jsonify({'message': 'Academic year deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@academic_years_bp.route('/<year_id>/set-current', methods=['POST'])
@admin_required
def set_current_academic_year(year_id):
    try:
        academic_year = AcademicYear.query.get(year_id)
        
        if not academic_year:
            return jsonify({'error': 'Academic year not found'}), 404
        
        # Unset current status for all years
        AcademicYear.query.update({'is_current': False})
        
        # Set this year as current
        academic_year.is_current = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Academic year set as current successfully',
            'academic_year': academic_year.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500