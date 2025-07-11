"""
University of Buea Faculty of Engineering and Technology
Custom validators for UB FET-specific data formats
"""
import re
from datetime import datetime
from utils.validators import ValidationError

def validate_ub_matricle_number(matricle_number):
    """
    Validate UB FET matricle number format: FE22A220
    Format: FE + 2-digit year + A + 3-digit number
    """
    if not matricle_number:
        raise ValidationError("Matricle number is required", "matricle_number")
    
    # UB FET matricle pattern: FE + 2 digits + A + 3 digits
    pattern = r'^FE\d{2}A\d{3}$'
    
    if not re.match(pattern, matricle_number.upper()):
        raise ValidationError(
            "Invalid matricle number format. Expected format: FE22A220 (FE + 2-digit year + A + 3-digit number)",
            "matricle_number"
        )
    
    # Extract year from matricle number
    year_part = matricle_number[2:4]
    try:
        year = int(year_part)
        current_year = datetime.now().year % 100  # Get last 2 digits of current year
        
        # Validate year is reasonable (not more than 10 years in future or 20 years in past)
        if year > current_year + 10 or year < current_year - 20:
            raise ValidationError(
                f"Invalid year in matricle number. Year '{year_part}' seems unrealistic",
                "matricle_number"
            )
    except ValueError:
        raise ValidationError("Invalid year format in matricle number", "matricle_number")

def validate_ub_course_code(course_code, department_code=None):
    """
    Validate UB FET course code format
    Format: Department prefix (CEF/EEF/CIV/MEF) + 3-digit number
    Odd numbers = First semester, Even numbers = Second semester
    """
    if not course_code:
        raise ValidationError("Course code is required", "course_code")
    
    # Valid department prefixes
    valid_prefixes = ['CEF', 'EEF', 'CIV', 'MEF']
    
    # Course code pattern: 3-letter prefix + 3-digit number
    pattern = r'^(CEF|EEF|CIV|MEF)(\d{3})$'
    match = re.match(pattern, course_code.upper())
    
    if not match:
        raise ValidationError(
            f"Invalid course code format. Expected format: {'/'.join(valid_prefixes)} + 3-digit number (e.g., CEF301)",
            "course_code"
        )
    
    prefix, number = match.groups()
    
    # Validate department code matches if provided
    if department_code and prefix != department_code:
        raise ValidationError(
            f"Course code prefix '{prefix}' doesn't match department code '{department_code}'",
            "course_code"
        )
    
    # Validate number range (typically 200-599 for undergraduate courses)
    number_int = int(number)
    if number_int < 200 or number_int > 599:
        raise ValidationError(
            "Course number should be between 200-599 for undergraduate courses",
            "course_code"
        )
    
    return {
        'prefix': prefix,
        'number': number,
        'semester': 1 if number_int % 2 == 1 else 2,  # Odd = 1st semester, Even = 2nd semester
        'level': str((number_int // 100) * 100)  # 200, 300, 400, 500
    }

def validate_ub_lecturer_email(email):
    """
    Validate University of Buea lecturer institutional email
    LECTURERS ONLY: Must use firstname.lastname@ubuea.cm format
    """
    if not email:
        raise ValidationError("Email is required", "email")
    
    # UB institutional email pattern for LECTURERS
    ub_pattern = r'^[a-zA-Z]+\.[a-zA-Z]+@ubuea\.cm$'
    
    if not re.match(ub_pattern, email.lower()):
        raise ValidationError(
            "Invalid UB lecturer email format. Expected: firstname.lastname@ubuea.cm",
            "email"
        )
    
    return True

def validate_ub_student_email(email):
    """
    Validate student email - can be any valid email format
    STUDENTS: Use personal emails since institutional emails are not active
    """
    if not email:
        raise ValidationError("Email is required", "email")
    
    # General email validation for students
    general_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(general_pattern, email.lower()):
        raise ValidationError("Invalid email format", "email")
    
    # Optional: Warn if student tries to use institutional email
    if '@ubuea.cm' in email.lower():
        raise ValidationError(
            "Students should use personal emails. UB institutional emails are not active for students.",
            "email"
        )
    
    return True

def validate_email_by_user_type(email, user_type):
    """
    Validate email based on user type
    - Lecturers: Must use @ubuea.cm institutional email
    - Students: Must use personal email (not @ubuea.cm)
    - Admins: Any valid email format
    """
    if user_type == 'lecturer':
        return validate_ub_lecturer_email(email)
    elif user_type == 'student':
        return validate_ub_student_email(email)
    else:  # admin or other
        # General email validation
        general_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(general_pattern, email.lower()):
            raise ValidationError("Invalid email format", "email")
        return True

def get_department_from_course_code(course_code):
    """
    Extract department information from UB FET course code
    """
    department_mapping = {
        'CEF': {
            'name': 'Computer Engineering',
            'full_name': 'Department of Computer Engineering'
        },
        'EEF': {
            'name': 'Electrical Engineering', 
            'full_name': 'Department of Electrical Engineering'
        },
        'CIV': {
            'name': 'Civil Engineering',
            'full_name': 'Department of Civil Engineering'
        },
        'MEF': {
            'name': 'Mechanical and Petroleum Engineering',
            'full_name': 'Department of Mechanical and Petroleum Engineering'
        }
    }
    
    if len(course_code) >= 3:
        prefix = course_code[:3].upper()
        return department_mapping.get(prefix)
    
    return None

def generate_ub_matricle_number(year=None):
    """
    Generate a UB FET matricle number
    Format: FE + 2-digit year + A + 3-digit sequential number
    """
    if year is None:
        year = datetime.now().year % 100
    
    # This would typically query the database for the next sequential number
    # For now, return a template that can be filled in
    return f"FE{year:02d}A{{sequential_number:03d}}"

def validate_ub_classroom_name(classroom_name):
    """
    Validate UB FET classroom naming convention
    Valid formats: FET-BGFL, FET-Hall 1, FET-Hall 2, Tech 1, Tech 2, Tech 3, Tech 4
    """
    if not classroom_name:
        raise ValidationError("Classroom name is required", "classroom_name")
    
    valid_classrooms = [
        'FET-BGFK',
        'FET-Hall 1', 'FET-Hall 2',
        'Tech 1', 'Tech 2', 'Tech 3', 'Tech 4'
    ]
    
    if classroom_name not in valid_classrooms:
        raise ValidationError(
            f"Invalid classroom name. Valid options: {', '.join(valid_classrooms)}",
            "classroom_name"
        )
    
    # Return building and floor information
    if classroom_name.startswith('FET'):
        building = 'FET Building'
        floor = 'Ground Floor' if 'BGFL' in classroom_name else '1st Floor'
    else:  # Tech classrooms
        building = 'Technology Building'
        floor = 'Ground Floor' if classroom_name in ['Tech 1', 'Tech 2'] else '1st Floor'
    
    return {
        'building': building,
        'floor': floor,
        'name': classroom_name
    }

def validate_ub_matricle_uniqueness(matricle_number, exclude_student_id=None):
    """
    Validate UB FET matricle number uniqueness
    Combines format validation with uniqueness check
    """
    # First validate format
    validate_ub_matricle_number(matricle_number)
    
    # Then validate uniqueness
    from models.student import Student
    query = Student.query.filter_by(matricle_number=matricle_number.upper())
    if exclude_student_id:
        query = query.filter(Student.id != exclude_student_id)
    
    existing_student = query.first()
    if existing_student:
        raise ValidationError(
            f"Matricle number '{matricle_number}' is already registered to another student",
            "matricle_number"
        )
    
    return True

def validate_ub_lecturer_id_assignment(lecturer_id, current_user_type, exclude_lecturer_id=None):
    """
    Validate UB FET lecturer ID assignment
    Only admins can assign lecturer IDs and they must be unique
    """
    # Validate admin permission
    if current_user_type != 'admin':
        raise ValidationError(
            "Only administrators can assign lecturer IDs. Please contact your system administrator.",
            "lecturer_id"
        )
    
    # Validate uniqueness
    from models.lecturer import Lecturer
    query = Lecturer.query.filter_by(lecturer_id=lecturer_id)
    if exclude_lecturer_id:
        query = query.filter(Lecturer.id != exclude_lecturer_id)
    
    existing_lecturer = query.first()
    if existing_lecturer:
        raise ValidationError(
            f"Lecturer ID '{lecturer_id}' is already assigned to another lecturer",
            "lecturer_id"
        )
    
    return True

def get_available_lecturer_ids():
    """
    Get list of available lecturer IDs that haven't been assigned
    This would typically be managed by admins
    """
    # This is a placeholder - in a real system, you might have a table
    # of pre-approved lecturer IDs that admins can assign
    from models.lecturer import Lecturer
    
    # Get all assigned lecturer IDs
    assigned_ids = [l.lecturer_id for l in Lecturer.query.all()]
    
    # Return info about assigned IDs (for admin reference)
    return {
        'assigned_lecturer_ids': assigned_ids,
        'total_assigned': len(assigned_ids),
        'note': 'Lecturer IDs must be assigned by administrators only'
    }
