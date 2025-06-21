# AttendEase API Comprehensive Test Script
# Based on actual backend implementation analysis

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
    'student_enrollment_id': None
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
    """Test authentication endpoints based on actual implementation"""
    print("\n" + "="*60)
    print("🔐 TESTING AUTHENTICATION ENDPOINTS")
    print("="*60)
    
    # Try to login with existing admin first
    existing_admin_login = {
        "email": "admin@attendease.com",
        "password": "AdminPass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=existing_admin_login, headers=headers)
    
    admin_password = "AdminPass123"  # Default password for existing admin
    
    if response.status_code == 200:
        print_test_result("Login Existing Admin", response, 200)
        created_data['admin_token'] = response.json()["access_token"]
        created_data['admin_user_id'] = response.json()["user"]["id"]
        headers["Authorization"] = f"Bearer {created_data['admin_token']}"
    else:
        # Create new admin if existing login fails
        admin_email = generate_unique_email("admin@attendease.com")
        admin_password = "AdminPass123!"
        admin_data = {
            "email": admin_email,
            "password": admin_password,
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_data, headers=headers)
        print_test_result("Register New Admin", response, 201)
        
        # Login with new admin
        login_data = {
            "email": admin_email,
            "password": admin_password
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=headers)
        if print_test_result("Login New Admin", response, 200):
            created_data['admin_token'] = response.json()["access_token"]
            created_data['admin_user_id'] = response.json()["user"]["id"]
            headers["Authorization"] = f"Bearer {created_data['admin_token']}"
    
    # Test lecturer registration (only creates User record initially)
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
    
    # Test student registration (only creates User record initially)
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
    
    # Test getting current user profile
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print_test_result("Get Current User Profile", response, 200)
    
    # Test change password (with correct current password)
    change_password_data = {
        "current_password": admin_password,
        "new_password": "NewAdminPass123!"
    }
    response = requests.post(f"{BASE_URL}/api/auth/change-password", json=change_password_data, headers=headers)
    print_test_result("Change Password", response, 200)
    
    # Test logout
    response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
    print_test_result("Logout", response, 200)
    
    return created_data['admin_token'] is not None

def test_departments():
    """Test department endpoints"""
    print("\n" + "="*60)
    print("🏢 TESTING DEPARTMENT ENDPOINTS")
    print("="*60)
    
    # Create department with unique name
    dept_name = f"Computer Science {int(time.time())}"
    dept_code = f"CSC{random.randint(100, 999)}"
    dept_data = {
        "name": dept_name,
        "code": dept_code,
        "description": "Department of Computer Science and Engineering"
    }
    response = requests.post(f"{BASE_URL}/api/departments", json=dept_data, headers=headers)
    if print_test_result("Create Department", response, 201):
        created_data['department_id'] = response.json()["department"]["id"]
    
    # Get all departments
    response = requests.get(f"{BASE_URL}/api/departments", headers=headers)
    print_test_result("Get All Departments", response, 200)
    
    # Get department by ID
    if created_data['department_id']:
        response = requests.get(f"{BASE_URL}/api/departments/{created_data['department_id']}", headers=headers)
        print_test_result("Get Department by ID", response, 200)

def test_users_and_profiles():
    """Test user and profile management"""
    print("\n" + "="*60)
    print("👥 TESTING USER AND PROFILE MANAGEMENT")
    print("="*60)
    
    # Get all users
    response = requests.get(f"{BASE_URL}/api/users", headers=headers)
    print_test_result("Get All Users", response, 200)
    
    # Create admin profile (since registration only creates User record)
    if created_data['admin_user_id']:
        admin_profile_data = {
            "user_id": created_data['admin_user_id'],
            "admin_id": f"ADM{random.randint(1000, 9999)}",
            "full_name": "System Administrator",
            "institution": "Test University",
            "role": "System Administrator"
        }
        response = requests.post(f"{BASE_URL}/api/admins", json=admin_profile_data, headers=headers)
        if print_test_result("Create Admin Profile", response, 201):
            created_data['admin_id'] = response.json().get("admin", {}).get("id")
    
    # Test lecturer login and create profile
    if 'lecturer_email' in created_data:
        lecturer_login = {
            "email": created_data['lecturer_email'],
            "password": created_data['lecturer_password']
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=lecturer_login, headers={"Content-Type": "application/json"})
        if print_test_result("Lecturer Login", response, 200):
            lecturer_user_id = response.json()["user"]["id"]
            created_data['lecturer_user_id'] = lecturer_user_id
            
            # Create lecturer profile
            lecturer_profile_data = {
                "user_id": lecturer_user_id,
                "lecturer_id": f"LEC{random.randint(1000, 9999)}",
                "full_name": "Dr. John Smith",
                "specialization": "Computer Science",
                "institutional_email": f"john.smith{random.randint(100, 999)}@university.edu"
            }
            # Switch to admin token for creating profiles
            temp_headers = headers.copy()
            response = requests.post(f"{BASE_URL}/api/lecturers", json=lecturer_profile_data, headers=temp_headers)
            if print_test_result("Create Lecturer Profile", response, 201):
                created_data['lecturer_id'] = response.json().get("lecturer", {}).get("id")
    
    # Test student login and create profile
    if 'student_email' in created_data and created_data['department_id']:
        student_login = {
            "email": created_data['student_email'],
            "password": created_data['student_password']
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=student_login, headers={"Content-Type": "application/json"})
        if print_test_result("Student Login", response, 200):
            student_user_id = response.json()["user"]["id"]
            created_data['student_user_id'] = student_user_id
            
            # Create student profile
            student_profile_data = {
                "user_id": student_user_id,
                "matricle_number": generate_matricle_number(),  # Use the new function
                "full_name": "Jane Doe",
                "department_id": created_data['department_id'],
                "level": "300",
                "gender": "Female",
                "enrollment_year": 2024
            }
            # Switch to admin token for creating profiles
            temp_headers = headers.copy()
            response = requests.post(f"{BASE_URL}/api/students", json=student_profile_data, headers=temp_headers)
            if print_test_result("Create Student Profile", response, 201):
                created_data['student_id'] = response.json().get("student", {}).get("id")

def test_academic_structure():
    """Test academic year and semester endpoints"""
    print("\n" + "="*60)
    print("📅 TESTING ACADEMIC STRUCTURE")
    print("="*60)
    
    # Create academic year
    current_year = datetime.now().year
    year_suffix = random.randint(10, 99)
    academic_year_data = {
        "year_name": f"{current_year + year_suffix}/{current_year + year_suffix + 1}",
        "start_date": f"{current_year + year_suffix}-09-01",
        "end_date": f"{current_year + year_suffix + 1}-08-31",
        "is_current": False
    }
    response = requests.post(f"{BASE_URL}/api/academic-years", json=academic_year_data, headers=headers)
    if print_test_result("Create Academic Year", response, 201):
        created_data['academic_year_id'] = response.json()["academic_year"]["id"]
    
    # Create semester
    if created_data['academic_year_id']:
        semester_data = {
            "academic_year_id": created_data['academic_year_id'],
            "semester_number": 1,
            "name": "First Semester",
            "start_date": f"{current_year + year_suffix}-09-01",
            "end_date": f"{current_year + year_suffix + 1}-01-31",
            "is_current": False
        }
        response = requests.post(f"{BASE_URL}/api/semesters", json=semester_data, headers=headers)
        if print_test_result("Create Semester", response, 201):
            created_data['semester_id'] = response.json()["semester"]["id"]

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
        created_data['geofence_area_id'] = response.json()["geofence_area"]["id"]
    
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
            created_data['course_id'] = response.json()["course"]["id"]

def test_basic_endpoints():
    """Test basic endpoints that should exist"""
    print("\n" + "="*60)
    print("🔧 TESTING BASIC ENDPOINTS")
    print("="*60)
    
    # Test endpoints that should exist based on your routes
    basic_endpoints = [
        ("/api/users", "Users"),
        ("/api/students", "Students"),
        ("/api/lecturers", "Lecturers"),
        ("/api/admins", "Admins"),
        ("/api/departments", "Departments"),
        ("/api/academic-years", "Academic Years"),
        ("/api/semesters", "Semesters"),
        ("/api/courses", "Courses"),
        ("/api/geofence-areas", "Geofence Areas")
    ]
    
    for endpoint, name in basic_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print_test_result(f"Get {name}", response, 200)
        except Exception as e:
            print(f"❌ FAIL Get {name}: Exception - {str(e)}")

def main():
    """Main test function"""
    print("🚀 STARTING ATTENDEASE API COMPREHENSIVE TESTS")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # Test authentication first
        if not test_authentication():
            print("❌ Authentication failed. Stopping tests.")
            return
        
        # Test core functionality in logical order
        test_departments()
        test_academic_structure()
        test_users_and_profiles()
        test_courses_and_geofence()
        test_basic_endpoints()
        
        print("\n" + "=" * 80)
        print("🎉 API TESTS COMPLETED!")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Print summary of created data
        print("\n📋 CREATED TEST DATA SUMMARY:")
        print("-" * 40)
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
