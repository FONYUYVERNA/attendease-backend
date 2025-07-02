-- Database Migration Script
-- Generated on: 2025-07-02 03:00:13.734070
-- This script syncs production database with local changes

BEGIN;

ALTER TABLE verification_codes ADD COLUMN IF NOT EXISTS used_at timestamp without time zone NULL;
ALTER TABLE verification_codes ADD COLUMN IF NOT EXISTS is_used boolean NOT NULL DEFAULT false;
CREATE INDEX idx_attendance_overrides_lecturer ON public.attendance_overrides USING btree (overridden_by);
CREATE INDEX idx_attendance_overrides_record ON public.attendance_overrides USING btree (attendance_record_id);
CREATE INDEX idx_audit_logs_user ON public.audit_logs USING btree (user_id);
CREATE INDEX idx_audit_logs_action ON public.audit_logs USING btree (action);
CREATE INDEX idx_audit_logs_table ON public.audit_logs USING btree (table_name);
CREATE INDEX idx_audit_logs_date ON public.audit_logs USING btree (created_at);
CREATE INDEX idx_lecturers_active ON public.lecturers USING btree (is_active);
CREATE INDEX idx_lecturers_institutional_email ON public.lecturers USING btree (institutional_email);
CREATE INDEX idx_lecturers_lecturer_id ON public.lecturers USING btree (lecturer_id);
CREATE INDEX idx_notifications_recipient_unread ON public.notifications USING btree (recipient_id, is_read);
CREATE INDEX idx_notifications_expiry ON public.notifications USING btree (expires_at);
CREATE INDEX idx_notifications_type ON public.notifications USING btree (notification_type);
CREATE INDEX idx_academic_years_current ON public.academic_years USING btree (is_current);
CREATE INDEX idx_academic_years_dates ON public.academic_years USING btree (start_date, end_date);
CREATE INDEX idx_system_settings_key ON public.system_settings USING btree (setting_key);
CREATE INDEX idx_system_settings_public ON public.system_settings USING btree (is_public);
CREATE INDEX idx_admins_admin_id ON public.admins USING btree (admin_id);
CREATE INDEX idx_users_active ON public.users USING btree (is_active);
CREATE INDEX idx_users_email ON public.users USING btree (email);
CREATE INDEX idx_users_user_type ON public.users USING btree (user_type);
CREATE INDEX idx_user_sessions_token ON public.user_sessions USING btree (session_token);
CREATE INDEX idx_user_sessions_user_active ON public.user_sessions USING btree (user_id, is_active);
CREATE INDEX idx_user_sessions_expiry ON public.user_sessions USING btree (expires_at);
CREATE INDEX idx_verification_codes_is_used ON public.verification_codes USING btree (is_used);
CREATE INDEX idx_verification_codes_email ON public.verification_codes USING btree (email);
CREATE INDEX idx_verification_codes_code ON public.verification_codes USING btree (code);
CREATE INDEX idx_verification_codes_expires_at ON public.verification_codes USING btree (expires_at);
CREATE INDEX idx_students_enrollment_year ON public.students USING btree (enrollment_year);
CREATE INDEX idx_students_department_level ON public.students USING btree (department_id, level);
CREATE INDEX idx_students_matricle ON public.students USING btree (matricle_number);
CREATE INDEX idx_students_face_registered ON public.students USING btree (is_face_registered);
CREATE INDEX idx_departments_code ON public.departments USING btree (code);
CREATE INDEX idx_departments_active ON public.departments USING btree (is_active);
CREATE INDEX idx_geofence_location ON public.geofence_areas USING btree (center_latitude, center_longitude);
CREATE INDEX idx_geofence_active ON public.geofence_areas USING btree (is_active);
CREATE INDEX idx_geofence_type ON public.geofence_areas USING btree (geofence_type);
CREATE INDEX idx_attendance_sessions_dates ON public.attendance_sessions USING btree (started_at, ended_at);
CREATE INDEX idx_attendance_sessions_course_assignment ON public.attendance_sessions USING btree (course_assignment_id);
CREATE INDEX idx_attendance_sessions_status ON public.attendance_sessions USING btree (session_status);
CREATE INDEX idx_attendance_records_status ON public.attendance_records USING btree (attendance_status);
CREATE INDEX idx_attendance_records_session_status ON public.attendance_records USING btree (session_id, attendance_status);
CREATE INDEX idx_attendance_records_student_time ON public.attendance_records USING btree (student_id, check_in_time);
CREATE INDEX idx_courses_semester ON public.courses USING btree (semester_number);
CREATE INDEX idx_courses_dept_level ON public.courses USING btree (department_id, level);
CREATE INDEX idx_courses_active ON public.courses USING btree (is_active);
CREATE INDEX idx_semesters_current ON public.semesters USING btree (is_current);
CREATE INDEX idx_semesters_dates ON public.semesters USING btree (start_date, end_date);
CREATE INDEX idx_course_assignments_lecturer_semester ON public.course_assignments USING btree (lecturer_id, semester_id);
CREATE INDEX idx_course_assignments_course_semester ON public.course_assignments USING btree (course_id, semester_id);
CREATE INDEX idx_student_enrollments_course_semester ON public.student_enrollments USING btree (course_id, semester_id);
CREATE INDEX idx_student_enrollments_student_semester ON public.student_enrollments USING btree (student_id, semester_id);
CREATE INDEX idx_student_enrollments_status ON public.student_enrollments USING btree (enrollment_status);

COMMIT;

-- Verify changes
SELECT 'Migration completed successfully' as result;
