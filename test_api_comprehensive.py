# AttendEase API Complete Test Suite
# Comprehensive testing of all endpoints with proper data flow

import requests
import json
from datetime import datetime, timedelta
import uuid
import time
import random

BASE_URL = "http://localhost:5000"
headers = {"Content-Type": "application/json"}

# Global variables to store created data
created_data = {
    'admin_token': None,
    'lecturer_token': None,
    'student_token': None,
    'admin_user_id': None,
    'lecturer_user_id': None,
    'student_user_id': None,
    'department_id': None,
    'academic_year_id': None,
    'semester_id': None,
    'student_id': None,
    'lecturer_id': None,
    'admin_id': None,
    'course_id': None,
    'course_assignment_id': None,
    'geofence_area_id': None,
    'attendance_session_id': None,
    'student_enrollment_id': None,
    'attendance_record_id': None,
    'notification_id': None
}

def print_test_result(test_name, response, expected_status=200):
    """Print formatted test results"""
    status = "✅ PASS" if response.status_code == expected_status else "❌ FAIL"
    print(f"{status} {test_name}: {response.status_code}")
    if response.status_code != expected_status:
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Error: {response.text[:200]}...")
    return response.status_code == expected_status

def generate_unique_email(base_email):
    """Generate unique email for testing"""
    timestamp = int(time.time())
    random_num = random.randint(100, 999)
    name, domain = base_email.split('@')
    return f"{name}_{timestamp}_{random_num}@{domain}"

def generate_matricle_number():
    """Generate valid matricle number format: ABC/2023/1234"""
    dept_codes = ['CSC', 'ENG', 'MTH', 'PHY', 'CHM']
    dept_code = random.choice(dept_codes)
    year = random.randint(2020, 2024)
    number = random.randint(1000, 9999)
    return f"{dept_code}/{year}/{number}"

def test_authentication():
    """Test authentication endpoints"""
    print("\n" + "="*60)
    print("🔐 TESTING AUTHENTICATION ENDPOINTS")
    print("="*60)
    
    # Try multiple admin login attempts with different possible credentials
    admin_credentials = [
        {"email": "admin@attendease.com", "password": "AdminPass123"},
        {"email": "admin@attendease.com", "password": "NewAdminPass123!"},
        {"email": "admin@test.com", "password": "AdminPass123"},
    ]
    
    admin_logged_in = False
    
    for creds in admin_credentials:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=creds, headers=headers)
        if response.status_code == 200:
            try:
                response_data = response.json()
                print_test_result(f"Login Admin ({creds['email']})", response, 200)
                created_data['admin_token'] = response_data["access_token"]
                created_data['admin_user_id'] = response_data["user"]["id"]
                headers["Authorization"] = f"Bearer {created_data['admin_token']}"
                admin_logged_in = True
                break
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
                continue
    
    # If no existing admin works, create a new one
    if not admin_logged_in:
        admin_email = generate_unique_email("admin@attendease.com")
        admin_password = "AdminPass123!"
        admin_data = {
            "email": admin_email,
            "password": admin_password,
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_data, headers=headers)
        if print_test_result("Register New Admin", response, 201):
            # Login with new admin
            login_data = {
                "email": admin_email,
                "password": admin_password
            }
            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
            if print_test_result("Login New Admin", response, 200):
                try:
                    response_data = response.json()
                    created_data['admin_token'] = response_data["access_token"]
                    created_data['admin_user_id'] = response_data["user"]["id"]
                    headers["Authorization"] = f"Bearer {created_data['admin_token']}"
                    admin_logged_in = True
                except (KeyError, json.JSONDecodeError) as e:
                    print(f"   Error parsing response: {e}")
    
    if not admin_logged_in:
        print("❌ Could not establish admin authentication")
        return False
    
    # Create new users for testing
    lecturer_email = generate_unique_email("lecturer@attendease.com")
    lecturer_password = "LecturerPass123!"
    lecturer_data = {
        "email": lecturer_email,
        "password": lecturer_password,
        "user_type": "lecturer"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=lecturer_data, headers=headers)
    if print_test_result("Register Lecturer", response, 201):
        created_data['lecturer_email'] = lecturer_email
        created_data['lecturer_password'] = lecturer_password
    
    student_email = generate_unique_email("student@attendease.com")
    student_password = "StudentPass123!"
    student_data = {
        "email": student_email,
        "password": student_password,
        "user_type": "student"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=student_data, headers=headers)
    if print_test_result("Register Student", response, 201):
        created_data['student_email'] = student_email
        created_data['student_password'] = student_password
    
    # Test profile endpoint
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print_test_result("Get Current User Profile", response, 200)
    
    return True

def test_departments():
    """Test department endpoints"""
    print("\n" + "="*60)
    print("🏢 TESTING DEPARTMENT ENDPOINTS")
    print("="*60)
    
    # Create department
    dept_name = f"Computer Science {int(time.time())}"
    dept_code = f"CSC{random.randint(100, 999)}"
    dept_data = {
        "name": dept_name,
        "code": dept_code,
        "description": "Department of Computer Science and Engineering"
    }
    response = requests.post(f"{BASE_URL}/api/departments", json=dept_data, headers=headers)
    if print_test_result("Create Department", response, 201):
        try:
            created_data['department_id'] = response.json()["department"]["id"]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Get all departments
    response = requests.get(f"{BASE_URL}/api/departments", headers=headers)
    print_test_result("Get All Departments", response, 200)
    
    # Get department by ID
    if created_data['department_id']:
        response = requests.get(f"{BASE_URL}/api/departments/{created_data['department_id']}", headers=headers)
        print_test_result("Get Department by ID", response, 200)
        
        # Update department
        update_data = {"description": "Updated Department Description"}
        response = requests.put(f"{BASE_URL}/api/departments/{created_data['department_id']}", json=update_data, headers=headers)
        print_test_result("Update Department", response, 200)

def test_academic_structure():
    """Test academic years and semesters"""
    print("\n" + "="*60)
    print("📅 TESTING ACADEMIC STRUCTURE")
    print("="*60)
    
    # Create academic year with unique name
    current_year = datetime.now().year
    year_suffix = random.randint(100, 999)  # Use larger range for uniqueness
    academic_year_data = {
        "year_name": f"{current_year + year_suffix}/{current_year + year_suffix + 1}",
        "start_date": f"{current_year + year_suffix}-09-01",
        "end_date": f"{current_year + year_suffix + 1}-08-31",
        "is_current": False
    }
    response = requests.post(f"{BASE_URL}/api/academic-years", json=academic_year_data, headers=headers)
    if print_test_result("Create Academic Year", response, 201):
        try:
            created_data['academic_year_id'] = response.json()["academic_year"]["id"]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Create semester - try to get existing academic year if creation failed
    if not created_data['academic_year_id']:
        # Get any existing academic year
        response = requests.get(f"{BASE_URL}/api/academic-years", headers=headers)
        if response.status_code == 200:
            years = response.json().get('academic_years', [])
            if years:
                created_data['academic_year_id'] = years[0]['id']
                print(f"   Using existing academic year: {years[0]['year_name']}")

    if created_data['academic_year_id']:
        semester_data = {
            "academic_year_id": created_data['academic_year_id'],
            "semester_number": 1,
            "name": f"Test Semester {random.randint(100, 999)}",
            "start_date": f"{current_year + year_suffix}-09-01",
            "end_date": f"{current_year + year_suffix + 1}-01-31",
            "is_current": False
        }
        response = requests.post(f"{BASE_URL}/api/semesters", json=semester_data, headers=headers)
        if print_test_result("Create Semester", response, 201):
            try:
                created_data['semester_id'] = response.json()["semester"]["id"]
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
        else:
            # Try to get existing semester if creation failed
            response = requests.get(f"{BASE_URL}/api/semesters", headers=headers)
            if response.status_code == 200:
                semesters = response.json().get('semesters', [])
                if semesters:
                    created_data['semester_id'] = semesters[0]['id']
                    print(f"   Using existing semester: {semesters[0]['name']}")
    
    # Get all academic years
    response = requests.get(f"{BASE_URL}/api/academic-years", headers=headers)
    print_test_result("Get All Academic Years", response, 200)
    
    # Get all semesters
    response = requests.get(f"{BASE_URL}/api/semesters", headers=headers)
    print_test_result("Get All Semesters", response, 200)

def test_user_profiles():
    """Test user profile creation and management"""
    print("\n" + "="*60)
    print("👥 TESTING USER PROFILE MANAGEMENT")
    print("="*60)
    
    # Login as lecturer and get user ID
    if 'lecturer_email' in created_data:
        lecturer_login = {
            "email": created_data['lecturer_email'],
            "password": created_data['lecturer_password']
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=lecturer_login, headers={"Content-Type": "application/json"})
        if print_test_result("Lecturer Login", response, 200):
            try:
                response_data = response.json()
                created_data['lecturer_user_id'] = response_data["user"]["id"]
                created_data['lecturer_token'] = response_data["access_token"]
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
    
    # Login as student and get user ID
    if 'student_email' in created_data:
        student_login = {
            "email": created_data['student_email'],
            "password": created_data['student_password']
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=student_login, headers={"Content-Type": "application/json"})
        if print_test_result("Student Login", response, 200):
            try:
                response_data = response.json()
                created_data['student_user_id'] = response_data["user"]["id"]
                created_data['student_token'] = response_data["access_token"]
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
    
    # Switch back to admin token for profile creation
    headers["Authorization"] = f"Bearer {created_data['admin_token']}"
    
    # Create lecturer profile
    if created_data['lecturer_user_id']:
        lecturer_profile_data = {
            "user_id": created_data['lecturer_user_id'],
            "lecturer_id": f"LEC{random.randint(1000, 9999)}",
            "full_name": "Dr. John Smith",
            "specialization": "Computer Science",
            "institutional_email": f"john.smith{random.randint(100, 999)}@university.edu"
        }
        response = requests.post(f"{BASE_URL}/api/lecturers", json=lecturer_profile_data, headers=headers)
        if print_test_result("Create Lecturer Profile", response, 201):
            try:
                response_data = response.json()
                created_data['lecturer_id'] = response_data.get("lecturer", {}).get("id")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
    
    # Create student profile with correct matricle number format
    if created_data['student_user_id'] and created_data['department_id']:
        student_profile_data = {
            "user_id": created_data['student_user_id'],
            "matricle_number": generate_matricle_number(),  # Fixed format
            "full_name": "Jane Doe",
            "department_id": created_data['department_id'],
            "level": "300",
            "gender": "Female",
            "enrollment_year": 2024
        }
        response = requests.post(f"{BASE_URL}/api/students", json=student_profile_data, headers=headers)
        if print_test_result("Create Student Profile", response, 201):
            try:
                response_data = response.json()
                created_data['student_id'] = response_data.get("student", {}).get("id")
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")

def test_courses_and_geofence():
    """Test courses and geofence areas"""
    print("\n" + "="*60)
    print("📖 TESTING COURSES AND GEOFENCE")
    print("="*60)
    
    # Create geofence area
    geofence_name = f"Lecture Hall {random.randint(100, 999)}"
    geofence_data = {
        "name": geofence_name,
        "description": "Primary lecture hall for computer science courses",
        "geofence_type": "circular",
        "center_latitude": 6.5244,
        "center_longitude": 3.3792,
        "radius_meters": 50,
        "building": "Science Complex",
        "floor": "Ground Floor",
        "capacity": 200
    }
    response = requests.post(f"{BASE_URL}/api/geofence-areas", json=geofence_data, headers=headers)
    if print_test_result("Create Geofence Area", response, 201):
        try:
            response_data = response.json()
            created_data['geofence_area_id'] = response_data["geofence_area"]["id"]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Get all geofence areas
    response = requests.get(f"{BASE_URL}/api/geofence-areas", headers=headers)
    print_test_result("Get All Geofence Areas", response, 200)
    
    # Create course
    if created_data['department_id']:
        course_code = f"CSC{random.randint(100, 999)}"
        course_data = {
            "course_code": course_code,
            "course_title": "Data Structures and Algorithms",
            "department_id": created_data['department_id'],
            "level": "300",
            "credit_units": 3,
            "semester_number": 1,
            "description": "Introduction to data structures and algorithm analysis"
        }
        response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=headers)
        if print_test_result("Create Course", response, 201):
            try:
                response_data = response.json()
                created_data['course_id'] = response_data["course"]["id"]
            except (KeyError, json.JSONDecodeError) as e:
                print(f"   Error parsing response: {e}")
    
    # Get all courses
    response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
    print_test_result("Get All Courses", response, 200)

def test_course_assignments():
    """Test course assignments"""
    print("\n" + "="*60)
    print("👨‍🏫 TESTING COURSE ASSIGNMENTS")
    print("="*60)
    
    if not all([created_data['lecturer_id'], created_data['course_id'], created_data['semester_id']]):
        print("❌ Skipping course assignment tests - missing dependencies")
        print(f"   Lecturer ID: {created_data['lecturer_id']}")
        print(f"   Course ID: {created_data['course_id']}")
        print(f"   Semester ID: {created_data['semester_id']}")
        return
    
    # Create course assignment
    assignment_data = {
        "lecturer_id": created_data['lecturer_id'],
        "course_id": created_data['course_id'],
        "semester_id": created_data['semester_id'],
        "geofence_area_id": created_data['geofence_area_id']
    }
    response = requests.post(f"{BASE_URL}/api/course-assignments", json=assignment_data, headers=headers)
    if print_test_result("Create Course Assignment", response, 201):
        try:
            response_data = response.json()
            created_data['course_assignment_id'] = response_data["course_assignment"]["id"]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Get all course assignments
    response = requests.get(f"{BASE_URL}/api/course-assignments", headers=headers)
    print_test_result("Get All Course Assignments", response, 200)

def test_student_enrollments():
    """Test student enrollments"""
    print("\n" + "="*60)
    print("🎓 TESTING STUDENT ENROLLMENTS")
    print("="*60)
    
    if not all([created_data['student_id'], created_data['course_id'], created_data['semester_id']]):
        print("❌ Skipping enrollment tests - missing dependencies")
        print(f"   Student ID: {created_data['student_id']}")
        print(f"   Course ID: {created_data['course_id']}")
        print(f"   Semester ID: {created_data['semester_id']}")
        return
    
    # Create student enrollment
    enrollment_data = {
        "student_id": created_data['student_id'],
        "course_id": created_data['course_id'],
        "semester_id": created_data['semester_id']
    }
    response = requests.post(f"{BASE_URL}/api/student-enrollments", json=enrollment_data, headers=headers)
    if print_test_result("Create Student Enrollment", response, 201):
        response_data = response.json()
        # Handle different possible response keys
        if "student_enrollment" in response_data:
            created_data['student_enrollment_id'] = response_data["student_enrollment"]["id"]
        elif "enrollment" in response_data:
            created_data['student_enrollment_id'] = response_data["enrollment"]["id"]
        else:
            print(f"   Response keys: {list(response_data.keys())}")
    
    # Get all enrollments
    response = requests.get(f"{BASE_URL}/api/student-enrollments", headers=headers)
    print_test_result("Get All Enrollments", response, 200)

def test_attendance_system():
    """Test attendance sessions and records"""
    print("\n" + "="*60)
    print("📋 TESTING ATTENDANCE SYSTEM")
    print("="*60)
    
    if not all([created_data['course_assignment_id'], created_data['geofence_area_id']]):
        print("❌ Skipping attendance tests - missing dependencies")
        print(f"   Course Assignment ID: {created_data['course_assignment_id']}")
        print(f"   Geofence Area ID: {created_data['geofence_area_id']}")
        return
    
    # Create attendance session
    session_data = {
        "course_assignment_id": created_data['course_assignment_id'],
        "geofence_area_id": created_data['geofence_area_id'],
        "session_name": "Week 1 Lecture",
        "topic": "Introduction to Data Structures",
        "late_threshold_minutes": 15,
        "auto_end_minutes": 120
    }
    response = requests.post(f"{BASE_URL}/api/attendance-sessions", json=session_data, headers=headers)
    if print_test_result("Create Attendance Session", response, 201):
        try:
            response_data = response.json()
            created_data['attendance_session_id'] = response_data["session"]["id"]
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Get all sessions
    response = requests.get(f"{BASE_URL}/api/attendance-sessions", headers=headers)
    print_test_result("Get All Attendance Sessions", response, 200)
    
    # Create attendance record
    if created_data['attendance_session_id'] and created_data['student_id']:
        record_data = {
            "session_id": created_data['attendance_session_id'],
            "student_id": created_data['student_id'],
            "attendance_status": "present",
            "check_in_method": "face_recognition",
            "face_match_confidence": 95.5,
            "location_latitude": 6.5244,
            "location_longitude": 3.3792
        }
        response = requests.post(f"{BASE_URL}/api/attendance-records", json=record_data, headers=headers)
        if print_test_result("Create Attendance Record", response, 201):
            response_data = response.json()
            if "attendance_record" in response_data:
                created_data['attendance_record_id'] = response_data["attendance_record"]["id"]
            elif "record" in response_data:
                created_data['attendance_record_id'] = response_data["record"]["id"]
        
        # Get attendance records
        response = requests.get(f"{BASE_URL}/api/attendance-records", headers=headers)
        print_test_result("Get All Attendance Records", response, 200)

def test_notifications():
    """Test notification system"""
    print("\n" + "="*60)
    print("🔔 TESTING NOTIFICATION SYSTEM")
    print("="*60)
    
    if not created_data['student_user_id']:
        print("❌ Skipping notification tests - no student user")
        return
    
    # Create notification
    notification_data = {
        "recipient_id": created_data['student_user_id'],
        "notification_type": "session_started",
        "title": "New Attendance Session Started",
        "message": "Data Structures and Algorithms class has started. Please check in.",
        "data": {"session_id": created_data['attendance_session_id']}
    }
    response = requests.post(f"{BASE_URL}/api/notifications", json=notification_data, headers=headers)
    if print_test_result("Create Notification", response, 201):
        response_data = response.json()
        if "notification" in response_data:
            created_data['notification_id'] = response_data["notification"]["id"]
        elif "id" in response_data:
            created_data['notification_id'] = response_data["id"]
    
    # Get all notifications
    response = requests.get(f"{BASE_URL}/api/notifications", headers=headers)
    print_test_result("Get All Notifications", response, 200)

def test_dashboard_and_reports():
    """Test dashboard and reporting endpoints"""
    print("\n" + "="*60)
    print("📊 TESTING DASHBOARD AND REPORTS")
    print("="*60)
    
    # Test dashboard endpoints with correct paths
    response = requests.get(f"{BASE_URL}/api/dashboard/admin", headers=headers)
    print_test_result("Get Admin Dashboard", response, 200)
    
    response = requests.get(f"{BASE_URL}/api/dashboard/quick-stats", headers=headers)
    print_test_result("Get Quick Stats", response, 200)
    
    # Test reports endpoints
    response = requests.get(f"{BASE_URL}/api/reports/attendance/summary", headers=headers)
    print_test_result("Get Attendance Summary Report", response, 200)
    
    response = requests.get(f"{BASE_URL}/api/reports/courses/performance", headers=headers)
    print_test_result("Get Course Performance Report", response, 200)

def test_system_settings():
    """Test system settings"""
    print("\n" + "="*60)
    print("⚙️ TESTING SYSTEM SETTINGS")
    print("="*60)
    
    # Create system setting
    setting_data = {
        "setting_key": f"test_setting_{int(time.time())}",
        "setting_value": "test_value",
        "setting_type": "string",
        "description": "Test setting for API testing",
        "is_public": True
    }
    response = requests.post(f"{BASE_URL}/api/system-settings", json=setting_data, headers=headers)
    if print_test_result("Create System Setting", response, 201):
        try:
            response_data = response.json()
        except (KeyError, json.JSONDecodeError) as e:
            print(f"   Error parsing response: {e}")
    
    # Get all settings
    response = requests.get(f"{BASE_URL}/api/system-settings", headers=headers)
    print_test_result("Get All System Settings", response, 200)

def main():
    """Main test function"""
    print("🚀 STARTING ATTENDEASE API COMPREHENSIVE TESTS")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # Test in logical order
        if not test_authentication():
            print("❌ Authentication failed. Stopping tests.")
            return
        
        test_departments()
        test_academic_structure()
        test_user_profiles()
        test_courses_and_geofence()
        test_course_assignments()
        test_student_enrollments()
        test_attendance_system()
        test_notifications()
        test_dashboard_and_reports()
        test_system_settings()
        
        print("\n" + "=" * 80)
        print("🎉 COMPREHENSIVE API TESTS COMPLETED!")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print summary
        print("\n📋 CREATED TEST DATA SUMMARY:")
        print("-" * 50)
        for key, value in created_data.items():
            if value and 'token' not in key and 'email' not in key and 'password' not in key:
                print(f"{key}: {value}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔚 Test session ended")

if __name__ == "__main__":
    main()
