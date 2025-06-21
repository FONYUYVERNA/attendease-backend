from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.admin import Admin
from models.user import User
from utils.decorators import admin_required, get_current_user
from utils.validators import validate_required_fields, validate_phone_number, ValidationError

admins_bp = Blueprint('admins', __name__)

@admins_bp.route('', methods=['GET'])
@admin_required
def get_all_admins():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search')
        
        query = Admin.query.join(User).filter(User.is_active == True)
        
        if search:
            query = query.filter(
                db.or_(
                    Admin.full_name.ilike(f'%{search}%'),
                    Admin.admin_id.ilike(f'%{search}%'),
                    Admin.institution.ilike(f'%{search}%')
                )
            )
        
        admins = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'admins': [admin.to_dict() for admin in admins.items],
            'pagination': {
                'page': admins.page,
                'pages': admins.pages,
                'per_page': admins.per_page,
                'total': admins.total,
                'has_next': admins.has_next,
                'has_prev': admins.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admins_bp.route('/<admin_id>', methods=['GET'])
@admin_required
def get_admin(admin_id):
    try:
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        return jsonify({'admin': admin.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admins_bp.route('', methods=['POST'])
@admin_required
def create_admin():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'user_id', 'admin_id', 'full_name'
        ]
        validate_required_fields(data, required_fields)
        
        # Validate phone number if provided
        if data.get('phone_number'):
            validate_phone_number(data['phone_number'])
        
        # Check if user exists and is an admin
        user = User.query.get(data['user_id'])
        if not user or user.user_type != 'admin':
            return jsonify({'error': 'Invalid user or user is not an admin'}), 400
        
        # Check if admin profile already exists for this user
        if Admin.query.filter_by(user_id=data['user_id']).first():
            return jsonify({'error': 'Admin profile already exists for this user'}), 409
        
        # Check if admin ID already exists
        if Admin.query.filter_by(admin_id=data['admin_id']).first():
            return jsonify({'error': 'Admin ID already exists'}), 409
        
        # Create admin
        admin = Admin(
            user_id=data['user_id'],
            admin_id=data['admin_id'],
            full_name=data['full_name'],
            institution=data.get('institution'),
            phone_number=data.get('phone_number'),
            profile_image_url=data.get('profile_image_url'),
            role=data.get('role', 'System Administrator'),
            permissions=data.get('permissions', {})
        )
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'message': 'Admin created successfully',
            'admin': admin.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admins_bp.route('/<admin_id>', methods=['PUT'])
@admin_required
def update_admin(admin_id):
    try:
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        data = request.get_json()
        
        # Fields that can be updated
        updatable_fields = [
            'admin_id', 'full_name', 'institution', 'phone_number',
            'profile_image_url', 'role', 'permissions'
        ]
        
        for field in updatable_fields:
            if field in data:
                if field == 'phone_number' and data[field]:
                    validate_phone_number(data[field])
                if field == 'admin_id':
                    # Check if admin ID already exists for another admin
                    existing = Admin.query.filter(
                        Admin.admin_id == data[field],
                        Admin.id != admin_id
                    ).first()
                    if existing:
                        return jsonify({'error': 'Admin ID already exists'}), 409
                
                setattr(admin, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Admin updated successfully',
            'admin': admin.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admins_bp.route('/<admin_id>', methods=['DELETE'])
@admin_required
def delete_admin(admin_id):
    try:
        current_user = get_current_user()
        admin = Admin.query.get(admin_id)
        
        if not admin:
            return jsonify({'error': 'Admin not found'}), 404
        
        # Prevent admin from deleting themselves
        current_admin = Admin.query.filter_by(user_id=current_user.id).first()
        if current_admin and current_admin.id == admin.id:
            return jsonify({'error': 'Cannot delete your own admin account'}), 400
        
        # Soft delete - deactivate the associated user account
        user = User.query.get(admin.user_id)
        if user:
            user.is_active = False
        
        db.session.commit()
        
        return jsonify({'message': 'Admin deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admins_bp.route('/statistics', methods=['GET'])
@admin_required
def get_admin_statistics():
    try:
        # Total active admins
        total_admins = Admin.query.join(User).filter(User.is_active == True).count()
        
        # Admins by role
        role_stats = db.session.query(
            Admin.role,
            db.func.count(Admin.id).label('count')
        ).join(User).filter(User.is_active == True).group_by(Admin.role).all()
        
        return jsonify({
            'total_admins': total_admins,
            'by_role': [
                {'role': stat.role, 'count': stat.count} 
                for stat in role_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500