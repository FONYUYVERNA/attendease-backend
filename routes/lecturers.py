from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.lecturer import Lecturer
from models.user import User
from utils.decorators import admin_required, lecturer_required, get_current_user
from utils.validators import validate_required_fields, validate_phone_number, validate_email_format, ValidationError

lecturers_bp = Blueprint('lecturers', __name__)

@lecturers_bp.route('', methods=['GET'])
@lecturer_required
def get_all_lecturers():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Lecturer.query.join(User).filter(User.is_active == True)
        
        if active_only:
            query = query.filter(Lecturer.is_active == True)
        
        if search:
            query = query.filter(
                db.or_(
                    Lecturer.full_name.ilike(f'%{search}%'),
                    Lecturer.lecturer_id.ilike(f'%{search}%'),
                    Lecturer.institutional_email.ilike(f'%{search}%')
                )
            )
        
        lecturers = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'lecturers': [lecturer.to_dict() for lecturer in lecturers.items],
            'pagination': {
                'page': lecturers.page,
                'pages': lecturers.pages,
                'per_page': lecturers.per_page,
                'total': lecturers.total,
                'has_next': lecturers.has_next,
                'has_prev': lecturers.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lecturers_bp.route('/<lecturer_id>', methods=['GET'])
@lecturer_required
def get_lecturer(lecturer_id):
    try:
        current_user = get_current_user()
        lecturer = Lecturer.query.get(lecturer_id)
        
        if not lecturer:
            return jsonify({'error': 'Lecturer not found'}), 404
        
        # Lecturers can only view their own profile unless user is admin
        if (current_user.user_type == 'lecturer' and 
            current_user.id != lecturer.user_id and 
            current_user.user_type != 'admin'):
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'lecturer': lecturer.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lecturers_bp.route('', methods=['POST'])
@admin_required
def create_lecturer():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'user_id', 'lecturer_id', 'full_name'
        ]
        validate_required_fields(data, required_fields)
        
        # Validate phone number if provided
        if data.get('phone_number'):
            validate_phone_number(data['phone_number'])
        
        # Validate institutional email if provided
        if data.get('institutional_email'):
            validate_email_format(data['institutional_email'])
        
        # Check if user exists and is a lecturer
        user = User.query.get(data['user_id'])
        if not user or user.user_type != 'lecturer':
            return jsonify({'error': 'Invalid user or user is not a lecturer'}), 400
        
        # Check if lecturer profile already exists for this user
        if Lecturer.query.filter_by(user_id=data['user_id']).first():
            return jsonify({'error': 'Lecturer profile already exists for this user'}), 409
        
        # Check if lecturer ID already exists
        if Lecturer.query.filter_by(lecturer_id=data['lecturer_id']).first():
            return jsonify({'error': 'Lecturer ID already exists'}), 409
        
        # Check if institutional email already exists
        if (data.get('institutional_email') and 
            Lecturer.query.filter_by(institutional_email=data['institutional_email']).first()):
            return jsonify({'error': 'Institutional email already exists'}), 409
        
        # Create lecturer
        lecturer = Lecturer(
            user_id=data['user_id'],
            lecturer_id=data['lecturer_id'],
            full_name=data['full_name'],
            institutional_email=data.get('institutional_email'),
            phone_number=data.get('phone_number'),
            profile_image_url=data.get('profile_image_url'),
            specialization=data.get('specialization'),
            hire_date=data.get('hire_date')
        )
        
        db.session.add(lecturer)
        db.session.commit()
        
        return jsonify({
            'message': 'Lecturer created successfully',
            'lecturer': lecturer.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lecturers_bp.route('/<lecturer_id>', methods=['PUT'])
@jwt_required()
def update_lecturer(lecturer_id):
    try:
        current_user = get_current_user()
        lecturer = Lecturer.query.get(lecturer_id)
        
        if not lecturer:
            return jsonify({'error': 'Lecturer not found'}), 404
        
        # Lecturers can update their own profile, admins can update any
        if (current_user.user_type == 'lecturer' and current_user.id != lecturer.user_id and
            current_user.user_type != 'admin'):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Fields lecturers can update themselves
        lecturer_updatable_fields = [
            'phone_number', 'profile_image_url', 'specialization'
        ]
        
        # Fields only admins can update
        admin_only_fields = [
            'lecturer_id', 'full_name', 'institutional_email', 
            'hire_date', 'is_active'
        ]
        
        # Update fields based on user permissions
        if current_user.user_type == 'admin':
            # Admins can update all fields
            updatable_fields = lecturer_updatable_fields + admin_only_fields
        else:
            # Lecturers can only update certain fields
            updatable_fields = lecturer_updatable_fields
        
        for field in updatable_fields:
            if field in data:
                if field == 'phone_number' and data[field]:
                    validate_phone_number(data[field])
                if field == 'institutional_email' and data[field]:
                    validate_email_format(data[field])
                    # Check if institutional email already exists for another lecturer
                    existing = Lecturer.query.filter(
                        Lecturer.institutional_email == data[field],
                        Lecturer.id != lecturer_id
                    ).first()
                    if existing:
                        return jsonify({'error': 'Institutional email already exists'}), 409
                if field == 'lecturer_id':
                    # Check if lecturer ID already exists for another lecturer
                    existing = Lecturer.query.filter(
                        Lecturer.lecturer_id == data[field],
                        Lecturer.id != lecturer_id
                    ).first()
                    if existing:
                        return jsonify({'error': 'Lecturer ID already exists'}), 409
                
                setattr(lecturer, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Lecturer updated successfully',
            'lecturer': lecturer.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lecturers_bp.route('/<lecturer_id>', methods=['DELETE'])
@admin_required
def delete_lecturer(lecturer_id):
    try:
        lecturer = Lecturer.query.get(lecturer_id)
        
        if not lecturer:
            return jsonify({'error': 'Lecturer not found'}), 404
        
        # Soft delete - deactivate the lecturer
        lecturer.is_active = False
        
        # Also deactivate the associated user account
        user = User.query.get(lecturer.user_id)
        if user:
            user.is_active = False
        
        db.session.commit()
        
        return jsonify({'message': 'Lecturer deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lecturers_bp.route('/statistics', methods=['GET'])
@admin_required
def get_lecturer_statistics():
    try:
        # Total active lecturers
        total_lecturers = Lecturer.query.join(User).filter(
            User.is_active == True,
            Lecturer.is_active == True
        ).count()
        
        # Lecturers by specialization
        specialization_stats = db.session.query(
            Lecturer.specialization,
            db.func.count(Lecturer.id).label('count')
        ).join(User).filter(
            User.is_active == True,
            Lecturer.is_active == True,
            Lecturer.specialization.isnot(None)
        ).group_by(Lecturer.specialization).all()
        
        return jsonify({
            'total_lecturers': total_lecturers,
            'by_specialization': [
                {'specialization': stat.specialization, 'count': stat.count} 
                for stat in specialization_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500