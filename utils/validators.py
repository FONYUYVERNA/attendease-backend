import re
from email_validator import validate_email, EmailNotValidError

class ValidationError(Exception):
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def validate_email_format(email):
    try:
        valid = validate_email(email)
        return valid.email
    except EmailNotValidError:
        raise ValidationError("Invalid email format", "email")

def validate_password(password):
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long", "password")
    
    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("Password must contain at least one letter", "password")
    
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one number", "password")
    
    return True

def validate_phone_number(phone):
    if phone and not re.match(r"^\+?[\d\s\-$$$$]{10,15}$", phone):
        raise ValidationError("Invalid phone number format", "phone_number")
    return True

def validate_matricle_number(matricle_number):
    if not re.match(r"^[A-Z]{2,4}\/\d{4}\/\d{4}$", matricle_number):
        raise ValidationError("Invalid matricle number format. Expected format: ABC/2023/1234", "matricle_number")
    return True

def validate_course_code(course_code):
    if not re.match(r"^[A-Z]{3,4}\s?\d{3,4}$", course_code):
        raise ValidationError("Invalid course code format. Expected format: CSC301 or MATH 101", "course_code")
    return True

def validate_coordinates(latitude, longitude):
    if not (-90 <= float(latitude) <= 90):
        raise ValidationError("Latitude must be between -90 and 90", "latitude")
    
    if not (-180 <= float(longitude) <= 180):
        raise ValidationError("Longitude must be between -180 and 180", "longitude")
    
    return True

def validate_required_fields(data, required_fields):
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True

def validate_matricle_uniqueness(matricle_number, exclude_student_id=None):
    """Validate that matricle number is unique across all students"""
    from models.student import Student
    
    query = Student.query.filter_by(matricle_number=matricle_number)
    if exclude_student_id:
        query = query.filter(Student.id != exclude_student_id)
    
    if query.first():
        raise ValidationError(f"Matricle number '{matricle_number}' is already registered to another student", "matricle_number")
    
    return True

def validate_lecturer_id_uniqueness(lecturer_id, exclude_lecturer_id=None):
    """Validate that lecturer ID is unique across all lecturers"""
    from models.lecturer import Lecturer
    
    query = Lecturer.query.filter_by(lecturer_id=lecturer_id)
    if exclude_lecturer_id:
        query = query.filter(Lecturer.id != exclude_lecturer_id)
    
    if query.first():
        raise ValidationError(f"Lecturer ID '{lecturer_id}' is already assigned to another lecturer", "lecturer_id")
    
    return True

def validate_admin_only_operation(current_user_type, operation_name):
    """Validate that only administrators can perform certain operations"""
    if current_user_type != 'admin':
        raise ValidationError(f"Only administrators can {operation_name}", "permission")
    
    return True
