-- University of Buea Faculty of Engineering and Technology Data Setup
-- This script safely adds UB FET-specific data without breaking existing records

-- =============================================
-- 1. ADD UB FET DEPARTMENTS (IF NOT EXISTS)
-- =============================================

-- Computer Engineering Department
INSERT INTO departments (id, name, code, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'Computer Engineering',
    'CEF',
    'Department of Computer Engineering - Faculty of Engineering and Technology, University of Buea',
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE code = 'CEF'
);

-- Electrical Engineering Department  
INSERT INTO departments (id, name, code, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'Electrical Engineering', 
    'EEF',
    'Department of Electrical Engineering - Faculty of Engineering and Technology, University of Buea',
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE code = 'EEF'
);

-- Civil Engineering Department
INSERT INTO departments (id, name, code, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'Civil Engineering',
    'CIV', 
    'Department of Civil Engineering - Faculty of Engineering and Technology, University of Buea',
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE code = 'CIV'
);

-- Mechanical and Petroleum Engineering Department
INSERT INTO departments (id, name, code, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'Mechanical and Petroleum Engineering',
    'MEF',
    'Department of Mechanical and Petroleum Engineering - Faculty of Engineering and Technology, University of Buea',
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM departments WHERE code = 'MEF'
);

-- =============================================
-- 2. ADD UB FET GEOFENCE AREAS (CLASSROOMS)
-- =============================================

-- FET Building - Ground Floor
INSERT INTO geofence_areas (
    id, name, description, geofence_type, 
    center_latitude, center_longitude, 
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'FET-BGFK',
    'FET Building Ground Floor Classroom - University of Buea',
    'rectangular',
    4.1558, 9.2865, -- Center coordinates for UB campus
    4.1560, 4.1556, 9.2867, 9.2863, -- Rectangular boundaries
    'FET Building',
    'Ground Floor',
    80,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'FET-BGFK'
);

-- FET Building - Hall 1 (1st Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'FET-Hall 1',
    'FET Building Hall 1 - 1st Floor - University of Buea',
    'rectangular',
    4.1559, 9.2866,
    4.1561, 4.1557, 9.2868, 9.2864,
    'FET Building',
    '1st Floor',
    120,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'FET-Hall 1'
);

-- FET Building - Hall 2 (1st Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'FET-Hall 2',
    'FET Building Hall 2 - 1st Floor - University of Buea',
    'rectangular',
    4.1560, 9.2867,
    4.1562, 4.1558, 9.2869, 9.2865,
    'FET Building',
    '1st Floor',
    120,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'FET-Hall 2'
);

-- Technology Building - Tech 1 (Ground Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'Tech 1',
    'Technology Building Tech 1 - Ground Floor - University of Buea',
    'rectangular',
    4.1556, 9.2863,
    4.1558, 4.1554, 9.2865, 9.2861,
    'Technology Building',
    'Ground Floor',
    60,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'Tech 1'
);

-- Technology Building - Tech 2 (Ground Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'Tech 2',
    'Technology Building Tech 2 - Ground Floor - University of Buea',
    'rectangular',
    4.1557, 9.2864,
    4.1559, 4.1555, 9.2866, 9.2862,
    'Technology Building',
    'Ground Floor',
    60,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'Tech 2'
);

-- Technology Building - Tech 3 (1st Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'Tech 3',
    'Technology Building Tech 3 - 1st Floor - University of Buea',
    'rectangular',
    4.1558, 9.2865,
    4.1560, 4.1556, 9.2867, 9.2863,
    'Technology Building',
    '1st Floor',
    60,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'Tech 3'
);

-- Technology Building - Tech 4 (1st Floor)
INSERT INTO geofence_areas (
    id, name, description, geofence_type,
    center_latitude, center_longitude,
    north_latitude, south_latitude, east_longitude, west_longitude,
    building, floor, capacity, is_active, created_at
)
SELECT 
    uuid_generate_v4(),
    'Tech 4',
    'Technology Building Tech 4 - 1st Floor - University of Buea',
    'rectangular',
    4.1559, 9.2866,
    4.1561, 4.1557, 9.2868, 9.2864,
    'Technology Building',
    '1st Floor',
    60,
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM geofence_areas WHERE name = 'Tech 4'
);

-- =============================================
-- 3. ADD SAMPLE UB FET COURSES
-- =============================================

-- Computer Engineering Courses (CEF)
INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'CEF301',
    'Data Structures and Algorithms',
    d.id,
    '300',
    3,
    1, -- First semester (odd number)
    'Introduction to data structures, algorithms, and their applications in computer engineering',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'CEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'CEF301'
);

INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'CEF302',
    'Computer Networks',
    d.id,
    '300',
    3,
    2, -- Second semester (even number)
    'Fundamentals of computer networks, protocols, and network security',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'CEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'CEF302'
);

-- Electrical Engineering Courses (EEF)
INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'EEF301',
    'Circuit Analysis',
    d.id,
    '300',
    3,
    1,
    'Analysis of electrical circuits using various techniques and theorems',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'EEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'EEF301'
);

INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'EEF302',
    'Power Systems',
    d.id,
    '300',
    3,
    2,
    'Introduction to power generation, transmission, and distribution systems',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'EEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'EEF302'
);

-- Civil Engineering Courses (CIV)
INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'CIV301',
    'Structural Analysis',
    d.id,
    '300',
    3,
    1,
    'Analysis of structures under various loading conditions',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'CIV'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'CIV301'
);

INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'CIV302',
    'Concrete Technology',
    d.id,
    '300',
    3,
    2,
    'Properties, design, and construction with concrete materials',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'CIV'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'CIV302'
);

-- Mechanical and Petroleum Engineering Courses (MEF)
INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'MEF301',
    'Thermodynamics',
    d.id,
    '300',
    3,
    1,
    'Principles of thermodynamics and their applications in engineering',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'MEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'MEF301'
);

INSERT INTO courses (id, course_code, course_title, department_id, level, credit_units, semester_number, description, is_active, created_at)
SELECT 
    uuid_generate_v4(),
    'MEF302',
    'Petroleum Engineering Fundamentals',
    d.id,
    '300',
    3,
    2,
    'Introduction to petroleum exploration, drilling, and production',
    true,
    CURRENT_TIMESTAMP
FROM departments d 
WHERE d.code = 'MEF'
AND NOT EXISTS (
    SELECT 1 FROM courses WHERE course_code = 'MEF302'
);

-- =============================================
-- 4. UPDATE SYSTEM SETTINGS FOR UB FET
-- =============================================

-- Institution name
INSERT INTO system_settings (id, setting_key, setting_value, setting_type, description, is_public, updated_at)
SELECT 
    uuid_generate_v4(),
    'institution_name',
    'University of Buea - Faculty of Engineering and Technology',
    'string',
    'Official institution name',
    true,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM system_settings WHERE setting_key = 'institution_name'
);

-- Matricle number format
INSERT INTO system_settings (id, setting_key, setting_value, setting_type, description, is_public, updated_at)
SELECT 
    uuid_generate_v4(),
    'matricle_format',
    'FE{YY}A{NNN}',
    'string',
    'Matricle number format: FE + 2-digit year + A + 3-digit number (e.g., FE22A220)',
    false,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM system_settings WHERE setting_key = 'matricle_format'
);

-- Course code patterns
INSERT INTO system_settings (id, setting_key, setting_value, setting_type, description, is_public, updated_at)
SELECT 
    uuid_generate_v4(),
    'course_code_patterns',
    '{"CEF": "Computer Engineering", "EEF": "Electrical Engineering", "CIV": "Civil Engineering", "MEF": "Mechanical and Petroleum Engineering"}',
    'json',
    'Course code prefixes for each department',
    false,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM system_settings WHERE setting_key = 'course_code_patterns'
);

-- Semester course numbering rule
INSERT INTO system_settings (id, setting_key, setting_value, setting_type, description, is_public, updated_at)
SELECT 
    uuid_generate_v4(),
    'semester_numbering_rule',
    'Odd numbers (XXX1, XXX3, XXX5, etc.) = First Semester, Even numbers (XXX2, XXX4, XXX6, etc.) = Second Semester',
    'string',
    'Rule for determining semester from course code ending',
    false,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM system_settings WHERE setting_key = 'semester_numbering_rule'
);

-- Display success message
DO $$
BEGIN
    RAISE NOTICE '✅ University of Buea FET data setup completed successfully!';
    RAISE NOTICE '📚 Added 4 departments: CEF, EEF, CIV, MEF';
    RAISE NOTICE '🏢 Added 7 classroom geofence areas';
    RAISE NOTICE '📖 Added sample courses for each department';
    RAISE NOTICE '⚙️ Updated system settings for UB FET';
END $$;
