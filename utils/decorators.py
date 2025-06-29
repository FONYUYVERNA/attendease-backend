from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Admin
from models.user_session import UserSession
from datetime import datetime
from app import db

def get_current_user():
    """Get the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(user_id)
        return None
    except Exception:
        return None

def validate_session():
    """Validate user session if session token is provided"""
    try:
        user_id = get_jwt_identity()
        session_token = request.headers.get('X-Session-Token')
        
        if session_token and user_id:
            user_session = UserSession.query.filter_by(
                user_id=user_id,
                session_token=session_token,
                is_active=True
            ).first()
            
            if user_session:
                if user_session.expires_at > datetime.utcnow():
                    # Update last activity
                    user_session.last_activity = datetime.utcnow()
                    db.session.commit()
                    return True
                else:
                    # Session expired, deactivate it
                    user_session.is_active = False
                    db.session.commit()
                    return False
            else:
                return False
        
        # If no session token provided, allow JWT validation to handle it
        return True
        
    except Exception:
        return False

def session_required(f):
    """Decorator to validate session along with JWT"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if not validate_session():
            return jsonify({'error': 'Invalid or expired session'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if not validate_session():
            return jsonify({'error': 'Invalid or expired session'}), 401
            
        current_user = get_current_user()
        if not current_user or current_user.user_type != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def lecturer_required(f):
    """Decorator to require lecturer or admin access"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if not validate_session():
            return jsonify({'error': 'Invalid or expired session'}), 401
            
        current_user = get_current_user()
        if not current_user or current_user.user_type not in ['lecturer', 'admin']:
            return jsonify({'error': 'Lecturer or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Decorator to require student, lecturer, or admin access"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if not validate_session():
            return jsonify({'error': 'Invalid or expired session'}), 401
            
        current_user = get_current_user()
        if not current_user or current_user.user_type not in ['student', 'lecturer', 'admin']:
            return jsonify({'error': 'Student, lecturer, or admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            if not validate_session():
                return jsonify({'error': 'Invalid or expired session'}), 401
                
            current_user = get_current_user()
            if not current_user or current_user.user_type not in roles:
                return jsonify({'error': f'Access denied. Required roles: {", ".join(roles)}'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
