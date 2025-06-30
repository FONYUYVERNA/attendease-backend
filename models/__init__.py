from sqlalchemy import Enum

# Define enums that EXACTLY match your database schema
user_type_enum = Enum('student', 'lecturer', 'admin', name='user_type_enum')
level_enum = Enum('200', '300', '400', '500', name='level_enum')  # Fixed: removed '100'
gender_enum = Enum('Male', 'Female', 'Other', name='gender_enum')  # Updated: added 'Other'
enrollment_status_enum = Enum('enrolled', 'dropped', 'completed', name='enrollment_status_enum')
session_status_enum = Enum('active', 'ended', 'cancelled', name='session_status_enum')
attendance_status_enum = Enum('present', 'absent', 'late', 'excused', name='attendance_status_enum')  # Updated: added 'excused'
check_in_method_enum = Enum('face_recognition', 'manual_override', name='check_in_method_enum')
theme_mode_enum = Enum('light', 'dark', 'system', name='theme_mode_enum')
notification_type_enum = Enum('info', 'warning', 'success', 'error', name='notification_type_enum')  # Updated: changed types
notification_status_enum = Enum('unread', 'read', 'archived', name='notification_status_enum')  # New enum added
setting_type_enum = Enum('string', 'number', 'boolean', 'json', name='setting_type_enum')
geofence_type_enum = Enum('circular', 'rectangular', name='geofence_type_enum')
