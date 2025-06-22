from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, bcrypt
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Admin
from models.user_preference import UserPreference
from utils.validators import validate_email_format, validate_password, ValidationError
from utils.ub_validators import validate_email_by_user_type  # Import UB validator
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'user_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate user type
        if data['user_type'] not in ['student', 'lecturer', 'admin']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        # Use UB-specific email validation based on user type
        try:
            validate_email_by_user_type(data['email'], data['user_type'])
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
        
        # Validate password
        validate_password(data['password'])
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        user = User(
            email=data['email'].lower(),  # Store emails in lowercase
            password_hash=password_hash,
            user_type=data['user_type']
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        # Create user preferences
        preferences = UserPreference(user_id=user.id)
        db.session.add(preferences)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'email_type': 'institutional' if data['user_type'] == 'lecturer' else 'personal'
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        # Find user (case-insensitive email search)
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        
        # Get user profile based on type
        profile = None
        if user.user_type == 'student':
            profile = Student.query.filter_by(user_id=user.id).first()
        elif user.user_type == 'lecturer':
            profile = Lecturer.query.filter_by(user_id=user.id).first()
        elif user.user_type == 'admin':
            profile = Admin.query.filter_by(user_id=user.id).first()
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user profile based on type
        profile = None
        if user.user_type == 'student':
            profile = Student.query.filter_by(user_id=user.id).first()
        elif user.user_type == 'lecturer':
            profile = Lecturer.query.filter_by(user_id=user.id).first()
        elif user.user_type == 'admin':
            profile = Admin.query.filter_by(user_id=user.id).first()
        
        return jsonify({
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password required'}), 400
        
        # Check current password
        if not bcrypt.check_password_hash(user.password_hash, data['current_password']):
            return jsonify({'error': 'Invalid current password'}), 401
        
        # Validate new password
        validate_password(data['new_password'])
        
        # Update password
        user.password_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        user.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a more sophisticated setup, you would blacklist the token
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/validate-email', methods=['POST'])
def validate_email_for_user_type():
    """
    Validate email format based on user type (UB FET specific)
    """
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('user_type'):
            return jsonify({'error': 'Email and user_type required'}), 400
        
        validate_email_by_user_type(data['email'], data['user_type'])
        
        return jsonify({
            'message': 'Email format is valid',
            'email': data['email'],
            'user_type': data['user_type'],
            'email_type': 'institutional' if data['user_type'] == 'lecturer' else 'personal'
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
