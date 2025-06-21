from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models.user import User
from models.user_preference import UserPreference
from utils.decorators import admin_required, get_current_user
from utils.validators import ValidationError

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@admin_required
def get_all_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_type = request.args.get('type')
        search = request.args.get('search')
        
        query = User.query
        
        if user_type:
            query = query.filter(User.user_type == user_type)
        
        if search:
            query = query.filter(User.email.ilike(f'%{search}%'))
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        current_user = get_current_user()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Users can only view their own profile unless they're admin
        if current_user.user_type != 'admin' and current_user.id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        current_user = get_current_user()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Users can only update their own profile unless they're admin
        if current_user.user_type != 'admin' and current_user.id != user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Only admins can change user type and active status
        if current_user.user_type == 'admin':
            if 'user_type' in data:
                user.user_type = data['user_type']
            if 'is_active' in data:
                user.is_active = data['is_active']
        
        if 'email_verified' in data and current_user.user_type == 'admin':
            user.email_verified = data['email_verified']
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Soft delete - deactivate instead of deleting
        user.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'User deactivated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<user_id>/preferences', methods=['GET'])
@jwt_required()
def get_user_preferences(user_id):
    try:
        current_user = get_current_user()
        
        # Users can only view their own preferences
        if current_user.id != user_id and current_user.user_type != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            return jsonify({'error': 'Preferences not found'}), 404
        
        return jsonify({'preferences': preferences.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/<user_id>/preferences', methods=['PUT'])
@jwt_required()
def update_user_preferences(user_id):
    try:
        current_user = get_current_user()
        
        # Users can only update their own preferences
        if current_user.id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        preferences = UserPreference.query.filter_by(user_id=user_id).first()
        
        if not preferences:
            preferences = UserPreference(user_id=user_id)
            db.session.add(preferences)
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'theme_mode', 'auto_login', 'notification_enabled',
            'email_notifications', 'push_notifications', 'language',
            'timezone', 'preferences_data'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(preferences, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': preferences.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500