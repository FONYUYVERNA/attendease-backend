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
        
        db.session.add(verification_code)
        db.session.commit()
        
        print(f"✅ Verification code created: {verification_code.id}")
        print(f"🔢 Code: {verification_code.code}")
        
        # Send notification with the code
        delivery_method = 'SMS' if user_type == 'lecturer' and phone_number else 'Email'
        contact = phone_number if user_type == 'lecturer' and phone_number else email
        
        # Send the notification
        NotificationService.send_verification_code(
            code=verification_code.code,
            contact=contact,
            delivery_method=delivery_method
        )
        
        # Mask contact for response
        if delivery_method == 'SMS':
            masked_contact = f"{phone_number[:4]}***{phone_number[-3:]}" if phone_number else None
        else:
            email_parts = email.split('@')
            masked_contact = f"{email_parts[0][:2]}***@{email_parts[1]}"
        
        return jsonify({
            'success': True,
            'message': f'Verification code sent via {delivery_method}',
            'verification_id': verification_code.id,
            'delivery_method': delivery_method,
            'masked_contact': masked_contact,
            'debug_code': verification_code.code  # For testing - remove in production
        }), 200
        
    except Exception as e:
        print(f"❌ Send verification error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/verify-registration', methods=['POST'])
def verify_registration():
    """
    Step 2: Verify code and complete registration
    """
    print("\n🔐 VERIFY REGISTRATION ENDPOINT CALLED")
    try:
        data = request.get_json()
        print(f"📥 Received data: {data}")
        
        # Validate required fields
        required_fields = ['verification_id', 'code', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        verification_id = data['verification_id']
        entered_code = data['code']
        password = data['password']
        first_name = data['first_name']
        last_name = data['last_name']
        
        print(f"🆔 Verification ID: {verification_id}")
        print(f"🔢 Entered Code: {entered_code}")
        
        # Find verification code
        verification = VerificationCode.query.filter_by(
            id=verification_id,
            purpose='registration'
        ).first()
        
        if not verification:
            return jsonify({'error': 'Invalid verification session'}), 400
        
        # Check if code is expired
        if verification.is_expired():
            return jsonify({'error': 'Verification code has expired'}), 400
        
        # Verify the code
        if not verification.verify_code(entered_code):
            return jsonify({'error': 'Invalid verification code'}), 400
        
        print(f"✅ Code verified successfully!")
        
        # Validate password
        try:
            validate_password(password)
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
        
        # Check if user already exists (double check)
        if User.query.filter_by(email=verification.email).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user account
        user = User(
            email=verification.email,
            password_hash=bcrypt.generate_password_hash(password).decode('utf-8'),
            first_name=first_name,
            last_name=last_name,
            user_type=verification.user_type,
            is_verified=True,
            phone_number=verification.phone_number
        )
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        print(f"👤 User created: {user.id}")
        
        # Create role-specific profile
        if verification.user_type == 'student':
            matricle_number = data.get('matricle_number')
            department_id = data.get('department_id')
            
            # Validate matricle number if provided
            if matricle_number:
                try:
                    validate_ub_matricle_number(matricle_number)
                except ValidationError as e:
                    db.session.rollback()
                    return jsonify({'error': e.message, 'field': e.field}), 400
                
                # Check if matricle number already exists
                if Student.query.filter_by(matricle_number=matricle_number).first():
                    db.session.rollback()
                    return jsonify({'error': 'Matricle number already registered'}), 409
            
            # Use default department if not provided
            if not department_id:
                department_id = get_default_department()
                if not department_id:
                    db.session.rollback()
                    return jsonify({'error': 'No departments available'}), 500
            
            student = Student(
                user_id=user.id,
                matricle_number=matricle_number,
                department_id=department_id,
                level='200',  # Default level
                gender='Male'  # Default gender - should be provided in form
            )
            db.session.add(student)
            print(f"🎓 Student profile created")
            
        elif verification.user_type == 'lecturer':
            lecturer = Lecturer(
                user_id=user.id,
                staff_id=f"LEC{user.id:06d}",  # Generate staff ID
                title='Mr.',  # Default title
                department_id=get_default_department() or 1
            )
            db.session.add(lecturer)
            print(f"👨‍🏫 Lecturer profile created")
            
        elif verification.user_type == 'admin':
            admin = Admin(
                user_id=user.id,
                admin_id=f"ADM{user.id:06d}",  # Generate admin ID
                role='system_admin',
                permissions=['user_management', 'system_settings']
            )
            db.session.add(admin)
            print(f"👨‍💼 Admin profile created")
        
        # Create user preferences
        preferences = UserPreference(
            user_id=user.id,
            theme='system',
            language='en',
            notifications_enabled=True,
            email_notifications=True,
            push_notifications=True
        )
        db.session.add(preferences)
        
        # Mark verification as used
        verification.is_used = True
        verification.used_at = datetime.utcnow()
        
        # Commit all changes
        db.session.commit()
        
        print(f"🎉 Registration completed successfully!")
        
        # Clean up old verification codes
        VerificationCode.query.filter(
            VerificationCode.email == verification.email,
            VerificationCode.id != verification.id
        ).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration completed successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Verify registration error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification_code():
    """
    Resend verification code
    """
    print("\n🔄 RESEND VERIFICATION ENDPOINT CALLED")
    try:
        data = request.get_json()
        verification_id = data.get('verification_id')
        
        if not verification_id:
            return jsonify({'error': 'Missing verification_id'}), 400
        
        # Find verification code
        verification = VerificationCode.query.filter_by(
            id=verification_id,
            purpose='registration'
        ).first()
        
        if not verification:
            return jsonify({'error': 'Invalid verification session'}), 400
        
        if verification.is_used:
            return jsonify({'error': 'Verification already completed'}), 400
        
        # Generate new code
        verification.regenerate_code()
        db.session.commit()
        
        print(f"🔄 New code generated: {verification.code}")
        
        # Send notification
        delivery_method = 'SMS' if verification.user_type == 'lecturer' and verification.phone_number else 'Email'
        contact = verification.phone_number if verification.user_type == 'lecturer' and verification.phone_number else verification.email
        
        NotificationService.send_verification_code(
            code=verification.code,
            contact=contact,
            delivery_method=delivery_method
        )
        
        # Mask contact for response
        if delivery_method == 'SMS':
            masked_contact = f"{verification.phone_number[:4]}***{verification.phone_number[-3:]}" if verification.phone_number else None
        else:
            email_parts = verification.email.split('@')
            masked_contact = f"{email_parts[0][:2]}***@{email_parts[1]}"
        
        return jsonify({
            'success': True,
            'message': f'Verification code resent via {delivery_method}',
            'delivery_method': delivery_method,
            'masked_contact': masked_contact,
            'debug_code': verification.code  # For testing - remove in production
        }), 200
        
    except Exception as e:
        print(f"❌ Resend verification error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    """
    print("\n🔐 LOGIN ENDPOINT CALLED")
    try:
        data = request.get_json()
        print(f"📥 Login data: {data}")
        
        # Validate required fields
        required_fields = ['email', 'password', 'user_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        email = data['email'].lower()
        password = data['password']
        user_type = data['user_type']
        
        print(f"📧 Email: {email}")
        print(f"👤 User Type: {user_type}")
        
        # Find user
        user = User.query.filter_by(email=email, user_type=user_type).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check password
        if not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is verified
        if not user.is_verified:
            return jsonify({'error': 'Account not verified'}), 401
        
        print(f"✅ User authenticated: {user.id}")
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(days=7)
        )
        
        # Create user session
        session = UserSession(
            user_id=user.id,
            session_token=str(uuid.uuid4()),
            device_info=request.headers.get('User-Agent', 'Unknown'),
            ip_address=request.remote_addr,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(session)
        
        # Update last login
        user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Get role-specific profile
        profile = None
        if user.user_type == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                profile = {
                    'matricle_number': student.matricle_number,
                    'department_id': student.department_id,
                    'level': student.level,
                    'gender': student.gender
                }
        elif user.user_type == 'lecturer':
            lecturer = Lecturer.query.filter_by(user_id=user.id).first()
            if lecturer:
                profile = {
                    'staff_id': lecturer.staff_id,
                    'title': lecturer.title,
                    'department_id': lecturer.department_id
                }
        elif user.user_type == 'admin':
            admin = Admin.query.filter_by(user_id=user.id).first()
            if admin:
                profile = {
                    'admin_id': admin.admin_id,
                    'role': admin.role,
                    'permissions': admin.permissions
                }
        
        print(f"🎉 Login successful!")
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'profile': profile
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint
    """
    print("\n🚪 LOGOUT ENDPOINT CALLED")
    try:
        user_id = get_jwt_identity()
        jti = get_jwt()['jti']
        
        # Find and deactivate user session
        session = UserSession.query.filter_by(user_id=user_id, is_active=True).first()
        if session:
            session.is_active = False
            session.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        print(f"✅ User {user_id} logged out successfully")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Logout error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get role-specific profile
        profile = None
        if user.user_type == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                profile = {
                    'matricle_number': student.matricle_number,
                    'department_id': student.department_id,
                    'level': student.level,
                    'gender': student.gender
                }
        elif user.user_type == 'lecturer':
            lecturer = Lecturer.query.filter_by(user_id=user.id).first()
            if lecturer:
                profile = {
                    'staff_id': lecturer.staff_id,
                    'title': lecturer.title,
                    'department_id': lecturer.department_id
                }
        elif user.user_type == 'admin':
            admin = Admin.query.filter_by(user_id=user.id).first()
            if admin:
                profile = {
                    'admin_id': admin.admin_id,
                    'role': admin.role,
                    'permissions': admin.permissions
                }
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'is_verified': user.is_verified,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'profile': profile
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Get current user error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/validate-email', methods=['POST'])
def validate_email():
    """
    Validate email format for specific user type
    """
    try:
        data = request.get_json()
        email = data.get('email', '').lower()
        user_type = data.get('user_type')
        
        if not email or not user_type:
            return jsonify({'error': 'Email and user_type required'}), 400
        
        try:
            validate_email_by_user_type(email, user_type)
            return jsonify({
                'success': True,
                'message': f'Email format valid for {user_type}'
            }), 200
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@auth_bp.route('/validate-matricle', methods=['POST'])
def validate_matricle():
    """
    Validate UB matricle number format
    """
    try:
        data = request.get_json()
        matricle_number = data.get('matricle_number', '').upper()
        
        if not matricle_number:
            return jsonify({'error': 'Matricle number required'}), 400
        
        try:
            validate_ub_matricle_number(matricle_number)
            return jsonify({
                'success': True,
                'message': 'Matricle number format is valid'
            }), 200
        except ValidationError as e:
            return jsonify({'error': e.message, 'field': e.field}), 400
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500
