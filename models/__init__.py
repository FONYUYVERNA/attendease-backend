from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
import uuid

# Define all enum types that can be imported by model files
user_type_enum = ENUM('student', 'lecturer', 'admin', name='user_type_enum')
level_enum = ENUM('200', '300', '400', '500', name='level_enum')
gender_enum = ENUM('Male', 'Female', name='gender_enum')
enrollment_status_enum = ENUM('enrolled', 'dropped', 'completed', name='enrollment_status_enum')
session_status_enum = ENUM('active', 'ended', 'cancelled', name='session_status_enum')
attendance_status_enum = ENUM('present', 'late', 'absent', name='attendance_status_enum')
check_in_method_enum = ENUM('face_recognition', 'manual_override', name='check_in_method_enum')
theme_mode_enum = ENUM('light', 'dark', 'system', name='theme_mode_enum')
notification_type_enum = ENUM('session_started', 'session_ending', 'attendance_reminder', 'system_alert', 'course_update', name='notification_type_enum')
setting_type_enum = ENUM('string', 'number', 'boolean', 'json', name='setting_type_enum')
geofence_type_enum = ENUM('circular', 'rectangular', name='geofence_type_enum')

# Export enum types for use in model files
__all__ = [
    'user_type_enum', 'level_enum', 'gender_enum', 'enrollment_status_enum',
    'session_status_enum', 'attendance_status_enum', 'check_in_method_enum',
    'theme_mode_enum', 'notification_type_enum', 'setting_type_enum', 'geofence_type_enum'
]
