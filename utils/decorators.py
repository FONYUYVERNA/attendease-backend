from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Admin

def get_current_user():
    """Get the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(user_id)
        return None
    except Exception:
        return None

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
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
            current_user = get_current_user()
            if not current_user or current_user.user_type not in roles:
                return jsonify({'error': f'Access denied. Required roles: {", ".join(roles)}'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
