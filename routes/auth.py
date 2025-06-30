from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import check_password_hash, generate_password_hash
from app import db, bcrypt
from models.user import User
from models.student import Student
from models.lecturer import Lecturer
from models.admin import Admin
from models.department import Department
from models.user_preference import UserPreference
from models.user_session import UserSession
from models.verification_code import VerificationCode
from utils.validators import validate_email_format, validate_password, ValidationError
from utils.ub_validators import validate_email_by_user_type, validate_ub_matricle_number
from utils.notification_service import NotificationService
from datetime import datetime, timedelta
import uuid
import secrets
import random

auth_bp = Blueprint('auth', __name__)

def get_default_department():
    """Get the first available department for students"""
    try:
        # Get the first department from the existing FET departments
        department = Department.query.first()
        if department:
            print(f"🏫 Using existing department: {department.name} (ID: {department.id})")
            return department.id
        else:
            print("⚠️ No departments found in database")
            return None
    except Exception as e:
        print(f"❌ Error getting department: {str(e)}")
        return None

@auth_bp.route('/send-verification', methods=['POST'])
def send_verification_code():
    """
    Step 1: Send verification code for registration
    """
    print("\n🚀 SEND VERIFICATION ENDPOINT CALLED")
    try:
        data = request.get_json()
        print(f"📥 Received data: {data}")
        
        # Validate required fields
        required_fields = ['email', 'user_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        email = data['email'].lower()
        user_type = data['user_type']
        phone_number = data.get('phone_number')
        
        print(f"📧 Email: {email}")
        print(f"👤 User Type: {user_type}")
        print(f"📱 Phone: {phone_number}")
        
        # Validate user type
        if user_type not in ['student', 'lecturer', 'admin']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        # Use UB-specific email validation based on user type
        try:
            validate_email_by_user_type(email, user_type)
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
        
        # For lecturers, phone number is required
        if user_type == 'lecturer' and not phone_number:
            return jsonify({'error': 'Phone number required for lecturer registration'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Clean up any existing verification codes for this email
        VerificationCode.query.filter_by(
            email=email,
            purpose='registration'
        ).delete()
        
        # Create new verification code
        verification_code = VerificationCode(
            email=email,
            user_type=user_type,
            phone_number=phone_number,
            purpose='registration'
        )
        
        print(f"🔑 Generated verification code: {verification_code.code}")
        
        db.session.add(verification_code)
        db.session.commit()
        
        print(f"💾 Saved verification code to database")
        
        # Send verification code
        success, message = NotificationService.send_verification_code(
            email, phone_number, verification_code.code, user_type
        )
        
        print(f"📤 Notification result: success={success}, message={message}")
        
        if success:
            return jsonify({
                'message': 'Verification code sent successfully',
                'verification_id': str(verification_code.id),
                'expires_at': verification_code.expires_at.isoformat(),
                'delivery_method': 'sms' if user_type == 'lecturer' else 'email',
                'masked_contact': phone_number[-4:] if user_type == 'lecturer' else f"{email.split('@')[0][:2]}***@{email.split('@')[1]}",
                'debug_code': verification_code.code  # Remove this in production
            }), 200
        else:
            return jsonify({'error': f'Failed to send verification code: {message}'}), 500
            
    except Exception as e:
        print(f"❌ Error in send_verification_code: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-registration', methods=['POST'])
def verify_registration_code():
    """
    Step 2: Verify code and complete registration
    """
    print("\n✅ VERIFY REGISTRATION ENDPOINT CALLED")
    try:
        data = request.get_json()
        print(f"📥 Received data: {data}")
        
        # Validate required fields
        required_fields = ['verification_id', 'code', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        verification_id = data['verification_id']
        provided_code = data['code']
        password = data['password']
        
        # Additional registration data - combine first_name and last_name into full_name
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        matricle_number = data.get('matricle_number')
        department_id = data.get('department_id')
        level = data.get('level', '200')  # Default to 200 level
        gender = data.get('gender', 'Male')  # Default gender
        
        print(f"🔍 Looking for verification ID: {verification_id}")
        
        # Find verification code
        verification_code = VerificationCode.query.get(verification_id)
        if not verification_code:
            return jsonify({'error': 'Invalid verification ID'}), 400
        
        print(f"✅ Found verification code: {verification_code.code}")
        print(f"📝 Provided code: {provided_code}")
        
        # Verify the code
        is_valid, message = verification_code.verify_code(provided_code)
        if not is_valid:
            db.session.commit()  # Save attempt count
            return jsonify({'error': message}), 400
        
        print(f"🎉 Code verification successful!")
        
        # Validate password
        validate_password(password)
        
        # Additional validation for students - be more flexible with matricle number
        if verification_code.user_type == 'student' and matricle_number:
            if len(matricle_number) < 5:
                return jsonify({'error': 'Matricle number too short', 'field': 'matricle_number'}), 400
        
        # Check if user was created in the meantime
        if User.query.filter_by(email=verification_code.email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            email=verification_code.email,
            password_hash=password_hash,
            user_type=verification_code.user_type,
            email_verified=True  # Email is verified through this process
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID before committing
        
        print(f"👤 Created user: {user.email}")
        
        # Create user preferences
        preferences = UserPreference(user_id=user.id)
        db.session.add(preferences)
        
        # Create role-specific profile using the correct field names and constraints
        if verification_code.user_type == 'student':
            # Generate a short student ID for matricle_number if not provided
            if not matricle_number:
                matricle_number = f"ST{random.randint(10000, 99999)}"
            
            # Ensure level is a valid enum value
            if level not in ['200', '300', '400', '500']:
                level = '200'  # Default to 200 level
            
            # Get existing FET department if not provided
            if not department_id:
                department_id = get_default_department()
                if not department_id:
                    return jsonify({'error': 'No departments available. Please contact administrator.'}), 500
            
            student = Student(
                user_id=user.id,
                full_name=full_name or 'Student User',
                matricle_number=matricle_number,
                department_id=department_id,
                level=level,  # Use string value from enum
                gender=gender,
                enrollment_year=datetime.now().year
            )
            db.session.add(student)
            print(f"🎓 Created student profile with level {level} and department {department_id}")
            
        elif verification_code.user_type == 'lecturer':
            # Generate a short lecturer ID (max 20 characters)
            lecturer_id = f"LEC{random.randint(1000, 9999)}"
            
            lecturer = Lecturer(
                user_id=user.id,
                lecturer_id=lecturer_id,  # Short ID that fits in 20 chars
                full_name=full_name or 'Lecturer User',
                institutional_email=verification_code.email,
                phone_number=verification_code.phone_number
            )
            db.session.add(lecturer)
            print(f"👨‍🏫 Created lecturer profile with ID {lecturer_id}")
            
        elif verification_code.user_type == 'admin':
            # Generate a short admin ID (max 20 characters)
            admin_id = f"ADM{random.randint(1000, 9999)}"
            
            admin = Admin(
                user_id=user.id,
                admin_id=admin_id,  # Short ID that fits in 20 chars
                full_name=full_name or 'Admin User'
            )
            db.session.add(admin)
            print(f"👨‍💼 Created admin profile with ID {admin_id}")
        
        # Mark verification as complete
        verification_code.is_verified = True
        verification_code.verified_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"💾 Registration completed successfully!")
        
        return jsonify({
            'message': 'Registration completed successfully',
            'user': user.to_dict(),
            'verification_method': 'sms' if verification_code.user_type == 'lecturer' else 'email'
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        print(f"❌ Error in verify_registration_code: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification_code():
    """
    Resend verification code
    """
    try:
        data = request.get_json()
        
        if not data.get('verification_id'):
            return jsonify({'error': 'Verification ID required'}), 400
        
        verification_id = data['verification_id']
        
        # Find existing verification code
        verification_code = VerificationCode.query.get(verification_id)
        if not verification_code:
            return jsonify({'error': 'Invalid verification ID'}), 400
        
        if verification_code.is_verified:
            return jsonify({'error': 'Code already verified'}), 400
        
        # Generate new code and reset attempts
        verification_code.code = verification_code.generate_code()
        verification_code.attempts = 0
        verification_code.expires_at = datetime.utcnow() + timedelta(minutes=15)
        
        db.session.commit()
        
        # Send new verification code
        success, message = NotificationService.send_verification_code(
            verification_code.email,
            verification_code.phone_number,
            verification_code.code,
            verification_code.user_type
        )
        
        if success:
            return jsonify({
                'message': 'Verification code resent successfully',
                'expires_at': verification_code.expires_at.isoformat(),
                'delivery_method': 'sms' if verification_code.user_type == 'lecturer' else 'email',
                'debug_code': verification_code.code  # Remove this in production
            }), 200
        else:
            return jsonify({'error': f'Failed to resend verification code: {message}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Keep all your existing auth routes below - these are the original ones
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Original registration endpoint - now redirects to 2FA flow
    """
    try:
        data = request.get_json()
        
        # Check if this is a direct registration attempt
        if not data.get('verification_id'):
            return jsonify({
                'error': 'Registration now requires verification. Please use /send-verification first.',
                'next_step': 'Call /api/auth/send-verification to start registration process',
                'required_fields': ['email', 'user_type', 'phone_number (for lecturers)'],
                'new_flow': {
                    'step_1': '/api/auth/send-verification',
                    'step_2': '/api/auth/verify-registration'
                }
            }), 400
        
        # If verification_id is provided, redirect to verify-registration
        return verify_registration_code()
        
    except Exception as e:
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
        
        if not user.email_verified:
            return jsonify({'error': 'Email not verified. Please complete registration.'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        # Create access token
        access_token = create_access_token(
            identity=str(user.id),
            expires_delta=timedelta(days=7)
        )
        
        # Create user session record
        session_token = secrets.token_urlsafe(32)
        user_session = UserSession(
            user_id=user.id,
            session_token=session_token,
            device_info=data.get('device_info', {}),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True
        )
        
        db.session.add(user_session)
        db.session.commit()
        
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
            'session_token': session_token,
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has an active session
        session_token = request.headers.get('X-Session-Token')
        if session_token:
            user_session = UserSession.query.filter_by(
                user_id=user.id,
                session_token=session_token,
                is_active=True
            ).first()
            
            if user_session and user_session.expires_at > datetime.utcnow():
                # Update last activity
                user_session.last_activity = datetime.utcnow()
                db.session.commit()
            elif user_session:
                # Session expired, deactivate it
                user_session.is_active = False
                db.session.commit()
                return jsonify({'error': 'Session expired'}), 401
        
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

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user_id = get_jwt_identity()
        
        # Get session token from header or request body
        session_token = request.headers.get('X-Session-Token')
        if not session_token:
            data = request.get_json() or {}
            session_token = data.get('session_token')
        
        if session_token:
            # Find and deactivate the specific session
            user_session = UserSession.query.filter_by(
                user_id=user_id,
                session_token=session_token,
                is_active=True
            ).first()
            
            if user_session:
                user_session.is_active = False
                user_session.last_activity = datetime.utcnow()
                db.session.commit()
                
                return jsonify({
                    'message': 'Logged out successfully',
                    'session_invalidated': True
                }), 200
        
        # If no session token provided, deactivate all user sessions
        UserSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).update({
            'is_active': False,
            'last_activity': datetime.utcnow()
        })
        
        db.session.commit()
        
        return jsonify({
            'message': 'All sessions logged out successfully',
            'sessions_invalidated': True
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
