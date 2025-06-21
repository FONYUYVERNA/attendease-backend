-- AttendEase Database Schema for PostgreSQL 17
-- Comprehensive schema for attendance management system

-- =============================================
-- 1. ENABLE REQUIRED EXTENSIONS
-- =============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================
-- 2. CREATE CUSTOM TYPES (ENUMS)
-- =============================================

-- User types
CREATE TYPE user_type_enum AS ENUM ('student', 'lecturer', 'admin');

-- Student/Course levels
CREATE TYPE level_enum AS ENUM ('200', '300', '400', '500');

-- Gender types
CREATE TYPE gender_enum AS ENUM ('Male', 'Female');

-- Enrollment status
CREATE TYPE enrollment_status_enum AS ENUM ('enrolled', 'dropped', 'completed');

-- Session status
CREATE TYPE session_status_enum AS ENUM ('active', 'ended', 'cancelled');

-- Attendance status
CREATE TYPE attendance_status_enum AS ENUM ('present', 'late', 'absent');

-- Check-in methods
CREATE TYPE check_in_method_enum AS ENUM ('face_recognition', 'manual_override');

-- Theme modes
CREATE TYPE theme_mode_enum AS ENUM ('light', 'dark', 'system');

-- Notification types
CREATE TYPE notification_type_enum AS ENUM ('session_started', 'session_ending', 'attendance_reminder', 'system_alert', 'course_update');

-- Setting types
CREATE TYPE setting_type_enum AS ENUM ('string', 'number', 'boolean', 'json');

-- Geofence types
CREATE TYPE geofence_type_enum AS ENUM ('circular', 'rectangular');

-- =============================================
-- 3. CORE USER MANAGEMENT TABLES
-- =============================================

-- Base users table for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type user_type_enum NOT NULL,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Create indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_type ON users(user_type);
CREATE INDEX idx_users_active ON users(is_active);

-- Departments table
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for departments
CREATE INDEX idx_departments_code ON departments(code);
CREATE INDEX idx_departments_active ON departments(is_active);

-- Academic years table
CREATE TABLE academic_years (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year_name VARCHAR(20) NOT NULL UNIQUE, -- e.g., "2023/2024"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for academic years
CREATE INDEX idx_academic_years_current ON academic_years(is_current);
CREATE INDEX idx_academic_years_dates ON academic_years(start_date, end_date);

-- Semesters table
CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    academic_year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
    semester_number SMALLINT NOT NULL CHECK (semester_number IN (1, 2)),
    name VARCHAR(20) NOT NULL, -- "First Semester", "Second Semester"
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_semester_year UNIQUE (academic_year_id, semester_number)
);

-- Create indexes for semesters
CREATE INDEX idx_semesters_current ON semesters(is_current);
CREATE INDEX idx_semesters_dates ON semesters(start_date, end_date);

-- Students table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    matricle_number VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id),
    level level_enum NOT NULL,
    gender gender_enum NOT NULL,
    phone_number VARCHAR(20),
    date_of_birth DATE,
    profile_image_url VARCHAR(500),
    face_encoding_data TEXT, -- Stored face recognition data
    is_face_registered BOOLEAN DEFAULT false,
    enrollment_year INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for students
CREATE INDEX idx_students_matricle ON students(matricle_number);
CREATE INDEX idx_students_department_level ON students(department_id, level);
CREATE INDEX idx_students_face_registered ON students(is_face_registered);
CREATE INDEX idx_students_enrollment_year ON students(enrollment_year);

-- Lecturers table
CREATE TABLE lecturers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    lecturer_id VARCHAR(20) NOT NULL UNIQUE, -- Assigned by admin
    full_name VARCHAR(255) NOT NULL,
    institutional_email VARCHAR(255), -- Added institutional email
    phone_number VARCHAR(20),
    profile_image_url VARCHAR(500),
    specialization VARCHAR(255),
    hire_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for lecturers
CREATE INDEX idx_lecturers_lecturer_id ON lecturers(lecturer_id);
CREATE INDEX idx_lecturers_institutional_email ON lecturers(institutional_email);
CREATE INDEX idx_lecturers_active ON lecturers(is_active);

-- Admins table
CREATE TABLE admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    admin_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    institution VARCHAR(255),
    phone_number VARCHAR(20),
    profile_image_url VARCHAR(500),
    role VARCHAR(50) DEFAULT 'System Administrator',
    permissions JSONB, -- Store admin permissions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for admins
CREATE INDEX idx_admins_admin_id ON admins(admin_id);

-- User preferences table
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    theme_mode theme_mode_enum DEFAULT 'system',
    auto_login BOOLEAN DEFAULT false,
    notification_enabled BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences_data JSONB, -- Additional user preferences
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 4. ACADEMIC STRUCTURE TABLES
-- =============================================

-- Courses table
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_code VARCHAR(20) NOT NULL UNIQUE,
    course_title VARCHAR(255) NOT NULL,
    department_id UUID NOT NULL REFERENCES departments(id),
    level level_enum NOT NULL,
    credit_units SMALLINT DEFAULT 3,
    semester_number SMALLINT CHECK (semester_number IN (1, 2)),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for courses
CREATE INDEX idx_courses_dept_level ON courses(department_id, level);
CREATE INDEX idx_courses_semester ON courses(semester_number);
CREATE INDEX idx_courses_active ON courses(is_active);

-- Geofence areas (classrooms/lecture halls)
CREATE TABLE geofence_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    geofence_type geofence_type_enum NOT NULL DEFAULT 'circular',
    
    -- Center point (used for both types)
    center_latitude DECIMAL(10, 8) NOT NULL,
    center_longitude DECIMAL(11, 8) NOT NULL,
    
    -- Circular geofence properties
    radius_meters INTEGER NULL, -- Only for circular geofences
    
    -- Rectangular geofence properties
    north_latitude DECIMAL(10, 8) NULL, -- Northern boundary
    south_latitude DECIMAL(10, 8) NULL, -- Southern boundary
    east_longitude DECIMAL(11, 8) NULL, -- Eastern boundary
    west_longitude DECIMAL(11, 8) NULL, -- Western boundary
    
    building VARCHAR(100),
    floor VARCHAR(20),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints to ensure proper geofence data
    CONSTRAINT chk_circular_geofence CHECK (
        (geofence_type = 'circular' AND radius_meters IS NOT NULL AND radius_meters > 0) OR
        (geofence_type = 'rectangular')
    ),
    CONSTRAINT chk_rectangular_geofence CHECK (
        (geofence_type = 'rectangular' AND 
         north_latitude IS NOT NULL AND south_latitude IS NOT NULL AND
         east_longitude IS NOT NULL AND west_longitude IS NOT NULL AND
         north_latitude > south_latitude AND east_longitude > west_longitude) OR
        (geofence_type = 'circular')
    )
);

-- Create indexes for geofence areas
CREATE INDEX idx_geofence_location ON geofence_areas(center_latitude, center_longitude);
CREATE INDEX idx_geofence_type ON geofence_areas(geofence_type);
CREATE INDEX idx_geofence_active ON geofence_areas(is_active);

-- =============================================
-- 5. COURSE ASSIGNMENT & ENROLLMENT TABLES
-- =============================================

-- Course assignments (lecturer to courses)
CREATE TABLE course_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lecturer_id UUID NOT NULL REFERENCES lecturers(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    geofence_area_id UUID REFERENCES geofence_areas(id),
    assigned_by UUID NOT NULL REFERENCES admins(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    
    CONSTRAINT unique_assignment UNIQUE (lecturer_id, course_id, semester_id)
);

-- Create indexes for course assignments
CREATE INDEX idx_course_assignments_lecturer_semester ON course_assignments(lecturer_id, semester_id);
CREATE INDEX idx_course_assignments_course_semester ON course_assignments(course_id, semester_id);

-- Student enrollments (students to courses)
CREATE TABLE student_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    semester_id UUID NOT NULL REFERENCES semesters(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enrollment_status enrollment_status_enum DEFAULT 'enrolled',
    grade VARCHAR(5), -- Final grade
    enrolled_by UUID REFERENCES users(id),
    
    CONSTRAINT unique_enrollment UNIQUE (student_id, course_id, semester_id)
);

-- Create indexes for student enrollments
CREATE INDEX idx_student_enrollments_student_semester ON student_enrollments(student_id, semester_id);
CREATE INDEX idx_student_enrollments_course_semester ON student_enrollments(course_id, semester_id);
CREATE INDEX idx_student_enrollments_status ON student_enrollments(enrollment_status);

-- =============================================
-- 6. ATTENDANCE SYSTEM TABLES
-- =============================================

-- Attendance sessions
CREATE TABLE attendance_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_assignment_id UUID NOT NULL REFERENCES course_assignments(id) ON DELETE CASCADE,
    geofence_area_id UUID NOT NULL REFERENCES geofence_areas(id),
    session_name VARCHAR(255), -- e.g., "Week 5 Lecture"
    topic VARCHAR(255),
    started_by UUID NOT NULL REFERENCES lecturers(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    session_status session_status_enum DEFAULT 'active',
    expected_students INTEGER DEFAULT 0,
    checked_in_students INTEGER DEFAULT 0,
    late_threshold_minutes INTEGER DEFAULT 15, -- Minutes after start considered late
    auto_end_minutes INTEGER DEFAULT 120, -- Auto-end session after X minutes
    notes TEXT
);

-- Create indexes for attendance sessions
CREATE INDEX idx_attendance_sessions_status ON attendance_sessions(session_status);
CREATE INDEX idx_attendance_sessions_dates ON attendance_sessions(started_at, ended_at);
CREATE INDEX idx_attendance_sessions_course_assignment ON attendance_sessions(course_assignment_id);

-- Attendance records
CREATE TABLE attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    attendance_status attendance_status_enum NOT NULL,
    check_in_method check_in_method_enum DEFAULT 'face_recognition',
    face_match_confidence DECIMAL(5,2), -- Face recognition confidence percentage
    location_latitude DECIMAL(10, 8),
    location_longitude DECIMAL(11, 8),
    device_info JSONB, -- Store device information
    is_verified BOOLEAN DEFAULT true,
    verified_by UUID REFERENCES lecturers(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_session_student UNIQUE (session_id, student_id)
);

-- Create indexes for attendance records
CREATE INDEX idx_attendance_records_session_status ON attendance_records(session_id, attendance_status);
CREATE INDEX idx_attendance_records_student_time ON attendance_records(student_id, check_in_time);
CREATE INDEX idx_attendance_records_status ON attendance_records(attendance_status);

-- Attendance overrides (manual corrections)
CREATE TABLE attendance_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attendance_record_id UUID NOT NULL REFERENCES attendance_records(id) ON DELETE CASCADE,
    original_status attendance_status_enum NOT NULL,
    new_status attendance_status_enum NOT NULL,
    override_reason TEXT NOT NULL,
    overridden_by UUID NOT NULL REFERENCES lecturers(id),
    overridden_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by UUID REFERENCES admins(id),
    approved_at TIMESTAMP NULL
);

-- Create indexes for attendance overrides
CREATE INDEX idx_attendance_overrides_record ON attendance_overrides(attendance_record_id);
CREATE INDEX idx_attendance_overrides_lecturer ON attendance_overrides(overridden_by);

-- =============================================
-- 7. AUTHENTICATION & SECURITY TABLES
-- =============================================

-- Two-factor authentication
CREATE TABLE two_factor_auth (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    secret_key VARCHAR(255) NOT NULL,
    backup_codes JSONB, -- Array of backup codes
    is_enabled BOOLEAN DEFAULT false,
    last_used TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user sessions
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX idx_user_sessions_expiry ON user_sessions(expires_at);

-- =============================================
-- 8. NOTIFICATION & COMMUNICATION TABLES
-- =============================================

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
    notification_type notification_type_enum NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    data JSONB, -- Additional notification data
    is_read BOOLEAN DEFAULT false,
    is_sent BOOLEAN DEFAULT false,
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for notifications
CREATE INDEX idx_notifications_recipient_unread ON notifications(recipient_id, is_read);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_expiry ON notifications(expires_at);

-- =============================================
-- 9. SYSTEM CONFIGURATION & LOGS
-- =============================================

-- System settings
CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type setting_type_enum DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT false, -- Can be accessed by non-admin users
    updated_by UUID REFERENCES admins(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for system settings
CREATE INDEX idx_system_settings_key ON system_settings(setting_key);
CREATE INDEX idx_system_settings_public ON system_settings(is_public);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit logs
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX idx_audit_logs_date ON audit_logs(created_at);

-- =============================================
-- 10. VIEWS FOR COMMON QUERIES
-- =============================================

-- Student dashboard view
CREATE VIEW student_dashboard AS
SELECT 
    s.id as student_id,
    s.matricle_number,
    s.full_name as student_name,
    c.course_code,
    c.course_title,
    c.credit_units,
    d.name as department_name,
    l.full_name as lecturer_name,
    ca.id as course_assignment_id,
    sem.name as semester_name,
    ay.year_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM attendance_sessions ats 
            WHERE ats.course_assignment_id = ca.id 
            AND ats.session_status = 'active'
        ) THEN true 
        ELSE false 
    END as has_active_session,
    (
        SELECT COUNT(*) 
        FROM attendance_records ar 
        JOIN attendance_sessions ats ON ar.session_id = ats.id
        WHERE ar.student_id = s.id 
        AND ats.course_assignment_id = ca.id
        AND ar.attendance_status IN ('present', 'late')
    ) as classes_attended,
    (
        SELECT COUNT(*) 
        FROM attendance_sessions ats 
        WHERE ats.course_assignment_id = ca.id 
        AND ats.session_status = 'ended'
    ) as total_classes
FROM students s
JOIN student_enrollments se ON s.id = se.student_id
JOIN courses c ON se.course_id = c.id
JOIN course_assignments ca ON c.id = ca.course_id
JOIN lecturers l ON ca.lecturer_id = l.id
JOIN departments d ON c.department_id = d.id
JOIN semesters sem ON se.semester_id = sem.id
JOIN academic_years ay ON sem.academic_year_id = ay.id
WHERE se.enrollment_status = 'enrolled'
AND sem.is_current = true;

-- Lecturer dashboard view
CREATE VIEW lecturer_dashboard AS
SELECT 
    l.id as lecturer_id,
    l.lecturer_id as lecturer_staff_id, -- Changed to avoid duplicate column name
    l.full_name as lecturer_name,
    c.course_code,
    c.course_title,
    d.name as department_name,
    ca.id as course_assignment_id,
    ga.name as classroom_name,
    sem.name as semester_name,
    ay.year_name,
    (
        SELECT COUNT(*) 
        FROM student_enrollments se 
        WHERE se.course_id = c.id 
        AND se.semester_id = sem.id
        AND se.enrollment_status = 'enrolled'
    ) as enrolled_students,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM attendance_sessions ats 
            WHERE ats.course_assignment_id = ca.id 
            AND ats.session_status = 'active'
        ) THEN true 
        ELSE false 
    END as has_active_session,
    (
        SELECT COUNT(*) 
        FROM attendance_sessions ats 
        WHERE ats.course_assignment_id = ca.id 
        AND ats.session_status = 'ended'
    ) as total_sessions
FROM lecturers l
JOIN course_assignments ca ON l.id = ca.lecturer_id
JOIN courses c ON ca.course_id = c.id
JOIN departments d ON c.department_id = d.id
JOIN semesters sem ON ca.semester_id = sem.id
JOIN academic_years ay ON sem.academic_year_id = ay.id
LEFT JOIN geofence_areas ga ON ca.geofence_area_id = ga.id
WHERE ca.is_active = true
AND sem.is_current = true;

-- =============================================
-- 11. FUNCTIONS FOR BUSINESS LOGIC
-- =============================================

-- Function to check if a point is within a geofence area
CREATE OR REPLACE FUNCTION is_within_geofence(
    check_lat DECIMAL(10, 8),
    check_lng DECIMAL(11, 8),
    geofence_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    geofence_record RECORD;
    distance_meters DECIMAL(10, 2);
BEGIN
    -- Get geofence details
    SELECT 
        geofence_type, center_latitude, center_longitude, radius_meters,
        north_latitude, south_latitude, east_longitude, west_longitude
    INTO geofence_record
    FROM geofence_areas 
    WHERE id = geofence_id AND is_active = true;
    
    -- If geofence not found, return false
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check circular geofence
    IF geofence_record.geofence_type = 'circular' THEN
        -- Calculate distance using Haversine formula (simplified)
        distance_meters := (
            6371000 * ACOS(
                COS(RADIANS(geofence_record.center_latitude)) * COS(RADIANS(check_lat)) * 
                COS(RADIANS(check_lng) - RADIANS(geofence_record.center_longitude)) + 
                SIN(RADIANS(geofence_record.center_latitude)) * SIN(RADIANS(check_lat))
            )
        );
        
        RETURN distance_meters <= geofence_record.radius_meters;
    END IF;
    
    -- Check rectangular geofence
    IF geofence_record.geofence_type = 'rectangular' THEN
        RETURN (
            check_lat >= geofence_record.south_latitude AND 
            check_lat <= geofence_record.north_latitude AND
            check_lng >= geofence_record.west_longitude AND 
            check_lng <= geofence_record.east_longitude
        );
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 12. TRIGGERS FOR DATA INTEGRITY
-- =============================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lecturers_updated_at BEFORE UPDATE ON lecturers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_admins_updated_at BEFORE UPDATE ON admins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_courses_updated_at BEFORE UPDATE ON courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_geofence_areas_updated_at BEFORE UPDATE ON geofence_areas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update session counters
CREATE OR REPLACE FUNCTION update_session_counters()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE attendance_sessions 
    SET checked_in_students = (
        SELECT COUNT(*) 
        FROM attendance_records 
        WHERE session_id = NEW.session_id 
        AND attendance_status IN ('present', 'late')
    )
    WHERE id = NEW.session_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for attendance session counters
CREATE TRIGGER update_attendance_session_counters 
    AFTER INSERT ON attendance_records
    FOR EACH ROW EXECUTE FUNCTION update_session_counters();

-- Function to update last activity in user sessions
CREATE OR REPLACE FUNCTION update_session_activity()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_activity = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for session activity
CREATE TRIGGER update_user_sessions_activity BEFORE UPDATE ON user_sessions
    FOR EACH ROW EXECUTE FUNCTION update_session_activity();
