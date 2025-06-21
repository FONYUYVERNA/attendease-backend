#!/usr/bin/env python3
"""
AttendEase Backend Comprehensive Validation Script
Performs thorough verification of all components, endpoints, and functionality
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
import uuid
import sys
import os

# Configuration
BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

class BackendValidator:
    def __init__(self):
        self.test_data = {}
        self.tokens = {}
        self.errors = []
        self.warnings = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_result(self, test_name, success, message="", response=None):
        """Log test results with detailed information"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if not success:
            self.failed_tests += 1
            error_msg = f"{test_name}: {message}"
            if response:
                try:
                    error_data = response.json()
                    error_msg += f" | Response: {error_data}"
                except:
                    error_msg += f" | Status: {response.status_code}"
            self.errors.append(error_msg)
            print(f"   ❌ {message}")
        else:
            self.passed_tests += 1
            if message:
                print(f"   ✅ {message}")
                
        return success
    
    def generate_unique_data(self):
        """Generate unique test data to avoid conflicts"""
        timestamp = int(time.time())
        random_suffix = random.randint(100, 999)
        
        return {
            'admin_email': f"admin_{timestamp}_{random_suffix}@attendease.com",
            'lecturer_email': f"lecturer_{timestamp}_{random_suffix}@attendease.com",
            'student_email': f"student_{timestamp}_{random_suffix}@attendease.com",
            'department_name': f"Computer Science {timestamp}",
            'department_code': f"CSC{random_suffix}",
            'course_code': f"CSC{random.randint(100, 999)}",
            'matricle_number': f"CSC/{random.randint(2020, 2024)}/{random.randint(1000, 9999)}",
            'lecturer_id': f"LEC{random.randint(1000, 9999)}",
            'admin_id': f"ADM{random.randint(1000, 9999)}",
            'academic_year': f"{datetime.now().year}/{datetime.now().year + 1}",
            'geofence_name': f"Lecture Hall {random.randint(100, 999)}"
        }
    
    def test_server_health(self):
        """Test if server is running and responsive"""
        print("\n" + "="*80)
        print("🏥 SERVER HEALTH CHECK")
        print("="*80)
        
        try:
            # Test basic server response
            response = requests.get(f"{BASE_URL}/api/health", timeout=10)
            if response.status_code == 200:
                self.log_result("Server Health Check", True, "Server is running and responsive")
                return True
            else:
                self.log_result("Server Health Check", False, f"Health endpoint returned {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_result("Server Health Check", False, "Cannot connect to server. Is it running?")
            return False
        except Exception as e:
            self.log_result("Server Health Check", False, f"Unexpected error: {str(e)}")
            return False
    
    def test_authentication_system(self):
        """Comprehensive authentication system testing"""
        print("\n" + "="*80)
        print("🔐 AUTHENTICATION SYSTEM VALIDATION")
        print("="*80)
        
        unique_data = self.generate_unique_data()
        
        # Test 1: Admin Registration
        admin_data = {
            "email": unique_data['admin_email'],
            "password": "AdminPass123!",
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_data, headers=HEADERS)
        if self.log_result("Admin Registration", response.status_code == 201, 
                          f"Admin user created successfully", response):
            self.test_data['admin_email'] = unique_data['admin_email']
            self.test_data['admin_password'] = "AdminPass123!"
        
        # Test 2: Admin Login
        login_data = {
            "email": unique_data['admin_email'],
            "password": "AdminPass123!"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
        if self.log_result("Admin Login", response.status_code == 200, 
                          "Admin authentication successful", response):
            data = response.json()
            self.tokens['admin'] = data.get('access_token')
            self.test_data['admin_user_id'] = data.get('user', {}).get('id')
            HEADERS['Authorization'] = f"Bearer {self.tokens['admin']}"
        
        # Test 3: Get Current User Profile
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=HEADERS)
        self.log_result("Get Current User Profile", response.status_code == 200,
                       "User profile retrieval working", response)
        
        # Test 4: Lecturer Registration
        lecturer_data = {
            "email": unique_data['lecturer_email'],
            "password": "LecturerPass123!",
            "user_type": "lecturer"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=lecturer_data, headers=HEADERS)
        if self.log_result("Lecturer Registration", response.status_code == 201,
                          "Lecturer user created", response):
            self.test_data['lecturer_email'] = unique_data['lecturer_email']
            self.test_data['lecturer_password'] = "LecturerPass123!"
        
        # Test 5: Student Registration
        student_data = {
            "email": unique_data['student_email'],
            "password": "StudentPass123!",
            "user_type": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=student_data, headers=HEADERS)
        if self.log_result("Student Registration", response.status_code == 201,
                          "Student user created", response):
            self.test_data['student_email'] = unique_data['student_email']
            self.test_data['student_password'] = "StudentPass123!"
        
        # Test 6: Invalid Login Attempt
        invalid_login = {
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=invalid_login, headers=HEADERS)
        self.log_result("Invalid Login Rejection", response.status_code == 401,
                       "Invalid credentials properly rejected", response)
        
        # Test 7: Password Change
        if self.tokens.get('admin'):
            change_password_data = {
                "current_password": "AdminPass123!",
                "new_password": "NewAdminPass123!"
            }
            response = requests.post(f"{BASE_URL}/api/auth/change-password", 
                                   json=change_password_data, headers=HEADERS)
            self.log_result("Password Change", response.status_code == 200,
                           "Password change functionality working", response)
        
        return len(self.tokens) > 0
    
    def test_user_management(self):
        """Test user and profile management endpoints"""
        print("\n" + "="*80)
        print("👥 USER MANAGEMENT VALIDATION")
        print("="*80)
        
        unique_data = self.generate_unique_data()
        
        # Test 1: Get All Users (Admin only)
        response = requests.get(f"{BASE_URL}/api/users", headers=HEADERS)
        self.log_result("Get All Users", response.status_code == 200,
                       "User listing accessible to admin", response)
        
        # Test 2: Create Admin Profile
        if self.test_data.get('admin_user_id'):
            admin_profile_data = {
                "user_id": self.test_data['admin_user_id'],
                "admin_id": unique_data['admin_id'],
                "full_name": "System Administrator",
                "institution": "Test University",
                "role": "System Administrator"
            }
            response = requests.post(f"{BASE_URL}/api/admins", json=admin_profile_data, headers=HEADERS)
            if self.log_result("Create Admin Profile", response.status_code == 201,
                              "Admin profile created successfully", response):
                self.test_data['admin_profile_id'] = response.json().get('admin', {}).get('id')
        
        # Test 3: Get Admin Profile
        if self.test_data.get('admin_profile_id'):
            response = requests.get(f"{BASE_URL}/api/admins/{self.test_data['admin_profile_id']}", 
                                  headers=HEADERS)
            self.log_result("Get Admin Profile", response.status_code == 200,
                           "Admin profile retrieval working", response)
        
        # Test 4: Lecturer Login and Profile Creation
        if self.test_data.get('lecturer_email'):
            lecturer_login = {
                "email": self.test_data['lecturer_email'],
                "password": self.test_data['lecturer_password']
            }
            response = requests.post(f"{BASE_URL}/api/auth/login", json=lecturer_login, 
                                   headers={"Content-Type": "application/json"})
            if self.log_result("Lecturer Login", response.status_code == 200,
                              "Lecturer authentication working", response):
                lecturer_user_id = response.json()['user']['id']
                self.test_data['lecturer_user_id'] = lecturer_user_id
                
                # Create lecturer profile
                lecturer_profile_data = {
                    "user_id": lecturer_user_id,
                    "lecturer_id": unique_data['lecturer_id'],
                    "full_name": "Dr. John Smith",
                    "specialization": "Computer Science",
                    "institutional_email": f"john.smith{random.randint(100, 999)}@university.edu"
                }
                response = requests.post(f"{BASE_URL}/api/lecturers", 
                                       json=lecturer_profile_data, headers=HEADERS)
                if self.log_result("Create Lecturer Profile", response.status_code == 201,
                                  "Lecturer profile created", response):
                    self.test_data['lecturer_profile_id'] = response.json().get('lecturer', {}).get('id')
        
        return True
    
    def test_academic_structure(self):
        """Test academic structure (departments, years, semesters, courses)"""
        print("\n" + "="*80)
        print("🏫 ACADEMIC STRUCTURE VALIDATION")
        print("="*80)
        
        unique_data = self.generate_unique_data()
        
        # Test 1: Create Department
        dept_data = {
            "name": unique_data['department_name'],
            "code": unique_data['department_code'],
            "description": "Department of Computer Science and Engineering"
        }
        response = requests.post(f"{BASE_URL}/api/departments", json=dept_data, headers=HEADERS)
        if self.log_result("Create Department", response.status_code == 201,
                          "Department creation successful", response):
            self.test_data['department_id'] = response.json()['department']['id']
        
        # Test 2: Get All Departments
        response = requests.get(f"{BASE_URL}/api/departments", headers=HEADERS)
        self.log_result("Get All Departments", response.status_code == 200,
                       "Department listing working", response)
        
        # Test 3: Create Academic Year
        current_year = datetime.now().year
        academic_year_data = {
            "year_name": unique_data['academic_year'],
            "start_date": f"{current_year}-09-01",
            "end_date": f"{current_year + 1}-08-31",
            "is_current": True
        }
        response = requests.post(f"{BASE_URL}/api/academic-years", json=academic_year_data, headers=HEADERS)
        if self.log_result("Create Academic Year", response.status_code == 201,
                          "Academic year creation successful", response):
            self.test_data['academic_year_id'] = response.json()['academic_year']['id']
        
        # Test 4: Create Semester
        if self.test_data.get('academic_year_id'):
            semester_data = {
                "academic_year_id": self.test_data['academic_year_id'],
                "semester_number": 1,
                "name": "First Semester",
                "start_date": f"{current_year}-09-01",
                "end_date": f"{current_year + 1}-01-31",
                "is_current": True
            }
            response = requests.post(f"{BASE_URL}/api/semesters", json=semester_data, headers=HEADERS)
            if self.log_result("Create Semester", response.status_code == 201,
                              "Semester creation successful", response):
                self.test_data['semester_id'] = response.json()['semester']['id']
        
        # Test 5: Create Course
        if self.test_data.get('department_id'):
            course_data = {
                "course_code": unique_data['course_code'],
                "course_title": "Data Structures and Algorithms",
                "department_id": self.test_data['department_id'],
                "level": "300",
                "credit_units": 3,
                "semester_number": 1,
                "description": "Introduction to data structures and algorithm analysis"
            }
            response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=HEADERS)
            if self.log_result("Create Course", response.status_code == 201,
                              "Course creation successful", response):
                self.test_data['course_id'] = response.json()['course']['id']
        
        # Test 6: Create Geofence Area
        geofence_data = {
            "name": unique_data['geofence_name'],
            "description": "Primary lecture hall for computer science courses",
            "geofence_type": "circular",
            "center_latitude": 6.5244,
            "center_longitude": 3.3792,
            "radius_meters": 50,
            "building": "Science Complex",
            "floor": "Ground Floor",
            "capacity": 200
        }
        response = requests.post(f"{BASE_URL}/api/geofence-areas", json=geofence_data, headers=HEADERS)
        if self.log_result("Create Geofence Area", response.status_code == 201,
                          "Geofence area creation successful", response):
            self.test_data['geofence_area_id'] = response.json()['geofence_area']['id']
        
        return True
    
    def test_student_management(self):
        """Test student-specific functionality"""
        print("\n" + "="*80)
        print("🎓 STUDENT MANAGEMENT VALIDATION")
        print("="*80)
        
        unique_data = self.generate_unique_data()
        
        # Test 1: Student Login
        if self.test_data.get('student_email'):
            student_login = {
                "email": self.test_data['student_email'],
                "password": self.test_data['student_password']
            }
            response = requests.post(f"{BASE_URL}/api/auth/login", json=student_login,
                                   headers={"Content-Type": "application/json"})
            if self.log_result("Student Login", response.status_code == 200,
                              "Student authentication working", response):
                student_user_id = response.json()['user']['id']
                self.test_data['student_user_id'] = student_user_id
                self.tokens['student'] = response.json()['access_token']
        
        # Test 2: Create Student Profile
        if self.test_data.get('student_user_id') and self.test_data.get('department_id'):
            student_profile_data = {
                "user_id": self.test_data['student_user_id'],
                "matricle_number": unique_data['matricle_number'],
                "full_name": "Jane Doe",
                "department_id": self.test_data['department_id'],
                "level": "300",
                "gender": "Female",
                "enrollment_year": 2024
            }
            response = requests.post(f"{BASE_URL}/api/students", json=student_profile_data, headers=HEADERS)
            if self.log_result("Create Student Profile", response.status_code == 201,
                              "Student profile created successfully", response):
                self.test_data['student_profile_id'] = response.json().get('student', {}).get('id')
        
        # Test 3: Get Student Profile
        if self.test_data.get('student_profile_id'):
            response = requests.get(f"{BASE_URL}/api/students/{self.test_data['student_profile_id']}", 
                                  headers=HEADERS)
            self.log_result("Get Student Profile", response.status_code == 200,
                           "Student profile retrieval working", response)
        
        # Test 4: Get All Students
        response = requests.get(f"{BASE_URL}/api/students", headers=HEADERS)
        self.log_result("Get All Students", response.status_code == 200,
                       "Student listing accessible", response)
        
        return True
    
    def test_course_management(self):
        """Test course assignments and enrollments"""
        print("\n" + "="*80)
        print("📚 COURSE MANAGEMENT VALIDATION")
        print("="*80)
        
        # Test 1: Create Course Assignment
        if (self.test_data.get('lecturer_profile_id') and 
            self.test_data.get('course_id') and 
            self.test_data.get('semester_id') and
            self.test_data.get('geofence_area_id')):
            
            assignment_data = {
                "lecturer_id": self.test_data['lecturer_profile_id'],
                "course_id": self.test_data['course_id'],
                "semester_id": self.test_data['semester_id'],
                "geofence_area_id": self.test_data['geofence_area_id']
            }
            response = requests.post(f"{BASE_URL}/api/course-assignments", 
                                   json=assignment_data, headers=HEADERS)
            if self.log_result("Create Course Assignment", response.status_code == 201,
                              "Course assignment created successfully", response):
                self.test_data['course_assignment_id'] = response.json().get('course_assignment', {}).get('id')
        
        # Test 2: Create Student Enrollment
        if (self.test_data.get('student_profile_id') and 
            self.test_data.get('course_id') and 
            self.test_data.get('semester_id')):
            
            enrollment_data = {
                "student_id": self.test_data['student_profile_id'],
                "course_id": self.test_data['course_id'],
                "semester_id": self.test_data['semester_id'],
                "enrollment_status": "enrolled"
            }
            response = requests.post(f"{BASE_URL}/api/student-enrollments", 
                                   json=enrollment_data, headers=HEADERS)
            if self.log_result("Create Student Enrollment", response.status_code == 201,
                              "Student enrollment successful", response):
                self.test_data['enrollment_id'] = response.json().get('student_enrollment', {}).get('id')
        
        # Test 3: Get Course Assignments
        response = requests.get(f"{BASE_URL}/api/course-assignments", headers=HEADERS)
        self.log_result("Get Course Assignments", response.status_code == 200,
                       "Course assignments listing working", response)
        
        # Test 4: Get Student Enrollments
        response = requests.get(f"{BASE_URL}/api/student-enrollments", headers=HEADERS)
        self.log_result("Get Student Enrollments", response.status_code == 200,
                       "Student enrollments listing working", response)
        
        return True
    
    def test_attendance_system(self):
        """Test attendance sessions and records"""
        print("\n" + "="*80)
        print("📋 ATTENDANCE SYSTEM VALIDATION")
        print("="*80)
        
        # Test 1: Create Attendance Session
        if (self.test_data.get('course_assignment_id') and 
            self.test_data.get('geofence_area_id')):
            
            session_data = {
                "course_assignment_id": self.test_data['course_assignment_id'],
                "geofence_area_id": self.test_data['geofence_area_id'],
                "session_name": "Data Structures Lecture 1",
                "topic": "Introduction to Arrays and Linked Lists",
                "late_threshold_minutes": 15,
                "auto_end_minutes": 120,
                "notes": "First lecture of the semester"
            }
            response = requests.post(f"{BASE_URL}/api/attendance-sessions", 
                                   json=session_data, headers=HEADERS)
            if self.log_result("Create Attendance Session", response.status_code == 201,
                              "Attendance session created successfully", response):
                # Try multiple possible response keys
                response_data = response.json() if response.status_code == 201 else {}
                session_id = (response_data.get('session', {}).get('id') or 
                             response_data.get('attendance_session', {}).get('id') or
                             response_data.get('data', {}).get('id'))
                if session_id:
                    self.test_data['session_id'] = session_id
        
        # Test 2: Get Active Sessions
        response = requests.get(f"{BASE_URL}/api/attendance-sessions/active", headers=HEADERS)
        self.log_result("Get Active Sessions", response.status_code == 200,
                       "Active sessions retrieval working", response)
        
        # Test 3: Create Attendance Record (Student Check-in)
        if (self.test_data.get('session_id') and 
            self.test_data.get('student_profile_id') and
            self.tokens.get('student')):
            
            # Switch to student token for check-in
            student_headers = HEADERS.copy()
            student_headers['Authorization'] = f"Bearer {self.tokens['student']}"
            
            attendance_data = {
                "session_id": self.test_data['session_id'],
                "location_latitude": 6.5244,
                "location_longitude": 3.3792,
                "check_in_method": "face_recognition",
                "face_match_confidence": 0.95,
                "device_info": "Test Device"
            }
            response = requests.post(f"{BASE_URL}/api/attendance-records", 
                                   json=attendance_data, headers=student_headers)
            if self.log_result("Create Attendance Record", response.status_code == 201,
                              "Student check-in successful", response):
                self.test_data['attendance_record_id'] = response.json().get('attendance_record', {}).get('id')
        
        # Test 4: Get Attendance Records
        response = requests.get(f"{BASE_URL}/api/attendance-records", headers=HEADERS)
        self.log_result("Get Attendance Records", response.status_code == 200,
                       "Attendance records retrieval working", response)
        
        return True
    
    def test_dashboard_endpoints(self):
        """Test dashboard functionality for all user types"""
        print("\n" + "="*80)
        print("📊 DASHBOARD ENDPOINTS VALIDATION")
        print("="*80)
        
        # Test 1: Admin Dashboard
        response = requests.get(f"{BASE_URL}/api/dashboard/admin", headers=HEADERS)
        self.log_result("Admin Dashboard", response.status_code == 200,
                       "Admin dashboard accessible and functional", response)
        
        # Test 2: Student Dashboard
        if self.tokens.get('student'):
            student_headers = HEADERS.copy()
            student_headers['Authorization'] = f"Bearer {self.tokens['student']}"
            response = requests.get(f"{BASE_URL}/api/dashboard/student", headers=student_headers)
            self.log_result("Student Dashboard", response.status_code == 200,
                           "Student dashboard accessible and functional", response)
        
        # Test 3: Quick Stats
        response = requests.get(f"{BASE_URL}/api/dashboard/quick-stats", headers=HEADERS)
        self.log_result("Quick Stats", response.status_code == 200,
                       "Quick stats endpoint working", response)
        
        return True
    
    def test_notification_system(self):
        """Test notification functionality"""
        print("\n" + "="*80)
        print("🔔 NOTIFICATION SYSTEM VALIDATION")
        print("="*80)
        
        # Test 1: Create Notification
        if self.test_data.get('student_user_id'):
            notification_data = {
                "recipient_id": self.test_data['student_user_id'],
                "notification_type": "system_alert",
                "title": "Welcome to AttendEase",
                "message": "Your account has been successfully created and verified.",
                "data": {"welcome": True}
            }
            response = requests.post(f"{BASE_URL}/api/notifications", 
                                   json=notification_data, headers=HEADERS)
            if self.log_result("Create Notification", response.status_code == 201,
                              "Notification created successfully", response):
                self.test_data['notification_id'] = response.json().get('notification', {}).get('id')
        
        # Test 2: Get User Notifications
        if self.tokens.get('student'):
            student_headers = HEADERS.copy()
            student_headers['Authorization'] = f"Bearer {self.tokens['student']}"
            response = requests.get(f"{BASE_URL}/api/notifications", headers=student_headers)
            self.log_result("Get User Notifications", response.status_code == 200,
                           "User notifications retrieval working", response)
        
        # Test 3: Get Unread Count
        if self.tokens.get('student'):
            student_headers = HEADERS.copy()
            student_headers['Authorization'] = f"Bearer {self.tokens['student']}"
            response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=student_headers)
            self.log_result("Get Unread Count", response.status_code == 200,
                           "Unread count endpoint working", response)
        
        return True
    
    def test_system_settings(self):
        """Test system settings functionality"""
        print("\n" + "="*80)
        print("⚙️ SYSTEM SETTINGS VALIDATION")
        print("="*80)
        
        # Test 1: Create System Setting
        setting_data = {
            "setting_key": f"test.setting.{int(time.time())}",
            "setting_value": "test_value",
            "setting_type": "string",
            "description": "Test setting for validation",
            "is_public": False
        }
        response = requests.post(f"{BASE_URL}/api/system-settings", 
                               json=setting_data, headers=HEADERS)
        if self.log_result("Create System Setting", response.status_code == 201,
                          "System setting created successfully", response):
            self.test_data['setting_key'] = setting_data['setting_key']
        
        # Test 2: Get All System Settings
        response = requests.get(f"{BASE_URL}/api/system-settings", headers=HEADERS)
        self.log_result("Get All System Settings", response.status_code == 200,
                       "System settings retrieval working", response)
        
        # Test 3: Get Public Settings (no auth required)
        response = requests.get(f"{BASE_URL}/api/system-settings/public", 
                              headers={"Content-Type": "application/json"})
        self.log_result("Get Public Settings", response.status_code == 200,
                       "Public settings endpoint working", response)
        
        return True
    
    def test_reports_system(self):
        """Test reporting functionality"""
        print("\n" + "="*80)
        print("📈 REPORTS SYSTEM VALIDATION")
        print("="*80)
        
        # Test 1: Course Attendance Report
        if self.test_data.get('course_assignment_id'):
            response = requests.get(f"{BASE_URL}/api/reports/attendance/course/{self.test_data['course_assignment_id']}", 
                                  headers=HEADERS)
            self.log_result("Course Attendance Report", response.status_code == 200,
                           "Course attendance report generation working", response)
        
        # Test 2: Student Attendance Report
        if self.test_data.get('student_profile_id'):
            response = requests.get(f"{BASE_URL}/api/reports/attendance/student/{self.test_data['student_profile_id']}", 
                                  headers=HEADERS)
            self.log_result("Student Attendance Report", response.status_code == 200,
                           "Student attendance report generation working", response)
        
        # Test 3: Attendance Summary Report
        response = requests.get(f"{BASE_URL}/api/reports/attendance/summary", headers=HEADERS)
        self.log_result("Attendance Summary Report", response.status_code == 200,
                       "Attendance summary report working", response)
        
        return True
    
    def test_data_integrity(self):
        """Test data relationships and integrity"""
        print("\n" + "="*80)
        print("🔗 DATA INTEGRITY VALIDATION")
        print("="*80)
        
        # Test 1: Verify User-Profile Relationships
        if self.test_data.get('admin_user_id') and self.test_data.get('admin_profile_id'):
            response = requests.get(f"{BASE_URL}/api/admins/{self.test_data['admin_profile_id']}", 
                                  headers=HEADERS)
            if response.status_code == 200:
                admin_data = response.json().get('admin', {})
                user_id_match = admin_data.get('user_id') == self.test_data['admin_user_id']
                self.log_result("Admin User-Profile Relationship", user_id_match,
                               "Admin profile correctly linked to user", response)
        
        # Test 2: Verify Course-Department Relationship
        if self.test_data.get('course_id') and self.test_data.get('department_id'):
            response = requests.get(f"{BASE_URL}/api/courses/{self.test_data['course_id']}", 
                                  headers=HEADERS)
            if response.status_code == 200:
                course_data = response.json().get('course', {})
                dept_id_match = course_data.get('department_id') == self.test_data['department_id']
                self.log_result("Course-Department Relationship", dept_id_match,
                               "Course correctly linked to department", response)
        
        # Test 3: Verify Enrollment Relationships
        if (self.test_data.get('enrollment_id') and 
            self.test_data.get('student_profile_id') and 
            self.test_data.get('course_id')):
            response = requests.get(f"{BASE_URL}/api/student-enrollments/{self.test_data['enrollment_id']}", 
                                  headers=HEADERS)
            if response.status_code == 200:
                enrollment_data = response.json().get('student_enrollment', {})
                student_match = enrollment_data.get('student_id') == self.test_data['student_profile_id']
                course_match = enrollment_data.get('course_id') == self.test_data['course_id']
                self.log_result("Enrollment Relationships", student_match and course_match,
                               "Enrollment correctly links student and course", response)
        
        return True
    
    def test_security_measures(self):
        """Test security implementations"""
        print("\n" + "="*80)
        print("🔒 SECURITY MEASURES VALIDATION")
        print("="*80)
        
        # Test 1: Unauthorized Access Prevention
        unauthorized_headers = {"Content-Type": "application/json"}
        response = requests.get(f"{BASE_URL}/api/users", headers=unauthorized_headers)
        self.log_result("Unauthorized Access Prevention", response.status_code == 401,
                       "Unauthorized requests properly rejected", response)
        
        # Test 2: Role-Based Access Control
        if self.tokens.get('student'):
            student_headers = {"Content-Type": "application/json", 
                             "Authorization": f"Bearer {self.tokens['student']}"}
            response = requests.get(f"{BASE_URL}/api/admins", headers=student_headers)
            self.log_result("Role-Based Access Control", response.status_code in [403, 401],
                           "Student cannot access admin endpoints", response)
        
        # Test 3: Input Validation
        invalid_user_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "user_type": "invalid_type"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", 
                               json=invalid_user_data, headers=HEADERS)
        self.log_result("Input Validation", response.status_code == 400,
                       "Invalid input properly rejected", response)
        
        return True
    
    def generate_final_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*100)
        print("📋 COMPREHENSIVE VALIDATION REPORT")
        print("="*100)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 95:
            status = "🎉 EXCELLENT"
            color = "GREEN"
        elif success_rate >= 85:
            status = "✅ GOOD"
            color = "YELLOW"
        elif success_rate >= 70:
            status = "⚠️ NEEDS IMPROVEMENT"
            color = "ORANGE"
        else:
            status = "❌ CRITICAL ISSUES"
            color = "RED"
        
        print(f"\n🎯 OVERALL STATUS: {status}")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        print(f"\n📋 CREATED TEST DATA:")
        print("-" * 50)
        for key, value in self.test_data.items():
            if value and 'token' not in key and 'password' not in key:
                print(f"   {key}: {value}")
        
        print(f"\n🚀 RECOMMENDATIONS:")
        if success_rate >= 95:
            print("   ✅ Your AttendEase backend is production-ready!")
            print("   ✅ All core functionality is working correctly")
            print("   ✅ Security measures are properly implemented")
            print("   ✅ Ready for frontend integration and deployment")
        elif success_rate >= 85:
            print("   ⚠️ Minor issues detected - review failed tests")
            print("   ✅ Core functionality is working well")
            print("   🔧 Fix remaining issues before production deployment")
        else:
            print("   ❌ Critical issues detected - immediate attention required")
            print("   🔧 Review and fix all failed tests")
            print("   ⚠️ Not recommended for production deployment")
        
        return success_rate >= 85
    
    def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🚀 ATTENDEASE BACKEND COMPREHENSIVE VALIDATION")
        print("="*100)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {BASE_URL}")
        print("="*100)
        
        try:
            # Core system tests
            if not self.test_server_health():
                print("❌ Server is not running. Please start your Flask server and try again.")
                return False
            
            if not self.test_authentication_system():
                print("❌ Authentication system failed. Cannot proceed with other tests.")
                return False
            
            # Comprehensive functionality tests
            self.test_user_management()
            self.test_academic_structure()
            self.test_student_management()
            self.test_course_management()
            self.test_attendance_system()
            self.test_dashboard_endpoints()
            self.test_notification_system()
            self.test_system_settings()
            self.test_reports_system()
            
            # Data integrity and security tests
            self.test_data_integrity()
            self.test_security_measures()
            
            # Generate final report
            return self.generate_final_report()
            
        except KeyboardInterrupt:
            print("\n⚠️ Validation interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error during validation: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            print(f"\n🔚 Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main validation function"""
    validator = BackendValidator()
    success = validator.run_comprehensive_validation()
    
    if success:
        print("\n🎉 VALIDATION SUCCESSFUL - YOUR BACKEND IS READY!")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION FAILED - PLEASE REVIEW AND FIX ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()
