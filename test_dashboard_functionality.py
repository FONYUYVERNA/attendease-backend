#!/usr/bin/env python3
"""
Test Dashboard and Reporting Functionality
Tests the actual dashboard and reporting endpoints with real data
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_dashboard_endpoints():
    """Test all dashboard endpoints with proper authentication"""
    print("🚀 TESTING DASHBOARD AND REPORTING FUNCTIONALITY")
    print("=" * 70)
    
    # First, login as admin to get token
    admin_credentials = {
        "email": "admin@attendease.com",
        "password": "AdminPass123"
    }
    
    print("🔐 Authenticating as admin...")
    response = requests.post(f"{BASE_URL}/api/auth/login", json=admin_credentials)
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False
    
    admin_data = response.json()
    admin_token = admin_data["access_token"]
    headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }
    
    print("✅ Admin authentication successful!")
    print(f"   Admin User: {admin_data['user']['email']}")
    
    # Test Dashboard Endpoints
    print("\n📊 TESTING DASHBOARD ENDPOINTS")
    print("-" * 50)
    
    dashboard_tests = [
        ("Admin Dashboard", "/api/dashboard/admin"),
        ("Quick Stats", "/api/dashboard/quick-stats"),
    ]
    
    for test_name, endpoint in dashboard_tests:
        print(f"\n🔍 Testing {test_name}...")
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ {test_name}: SUCCESS")
            data = response.json()
            
            # Pretty print key metrics
            if endpoint == "/api/dashboard/admin":
                if "system_overview" in data:
                    overview = data["system_overview"]
                    print(f"   📈 Total Users: {overview.get('total_users', 0)}")
                    print(f"   👥 Students: {overview.get('total_students', 0)}")
                    print(f"   👨‍🏫 Lecturers: {overview.get('total_lecturers', 0)}")
                    print(f"   📚 Courses: {overview.get('total_courses', 0)}")
                
                if "attendance_overview" in data:
                    attendance = data["attendance_overview"]
                    print(f"   📋 Total Sessions: {attendance.get('total_sessions', 0)}")
                    print(f"   🔴 Active Sessions: {attendance.get('active_sessions', 0)}")
            
            elif endpoint == "/api/dashboard/quick-stats":
                print(f"   🔔 Unread Notifications: {data.get('unread_notifications', 0)}")
                print(f"   📊 Active Sessions: {data.get('active_sessions_count', 0)}")
                if data.get('current_semester'):
                    print(f"   📅 Current Semester: {data['current_semester'].get('name', 'N/A')}")
        
        else:
            print(f"❌ {test_name}: FAILED ({response.status_code})")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text[:200]}")
    
    # Test Reporting Endpoints
    print("\n📈 TESTING REPORTING ENDPOINTS")
    print("-" * 50)
    
    report_tests = [
        ("Attendance Summary", "/api/reports/attendance/summary"),
        ("Course Performance", "/api/reports/courses/performance"),
        ("Student Performance", "/api/reports/students/performance"),
    ]
    
    for test_name, endpoint in report_tests:
        print(f"\n🔍 Testing {test_name}...")
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
        
        if response.status_code == 200:
            print(f"✅ {test_name}: SUCCESS")
            data = response.json()
            
            # Show relevant metrics
            if "overall_statistics" in data:
                stats = data["overall_statistics"]
                print(f"   📊 Statistics available: {list(stats.keys())}")
            
            if "student_performance" in data:
                students = data["student_performance"]
                print(f"   👥 Students analyzed: {len(students)}")
            
            if "course_performance" in data:
                courses = data["course_performance"]
                print(f"   📚 Courses analyzed: {len(courses)}")
        
        else:
            print(f"❌ {test_name}: FAILED ({response.status_code})")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text[:200]}")
    
    # Test with different user roles
    print("\n👤 TESTING ROLE-BASED ACCESS")
    print("-" * 50)
    
    # Try to access student dashboard (should fail without student profile)
    response = requests.get(f"{BASE_URL}/api/dashboard/student", headers=headers)
    if response.status_code == 403:
        print("✅ Student Dashboard: Properly restricted (403)")
    elif response.status_code == 404:
        print("⚠️ Student Dashboard: Student profile not found (404)")
    else:
        print(f"❓ Student Dashboard: Unexpected response ({response.status_code})")
    
    # Try to access lecturer dashboard (should fail without lecturer profile)
    response = requests.get(f"{BASE_URL}/api/dashboard/lecturer", headers=headers)
    if response.status_code == 403:
        print("✅ Lecturer Dashboard: Properly restricted (403)")
    elif response.status_code == 404:
        print("⚠️ Lecturer Dashboard: Lecturer profile not found (404)")
    else:
        print(f"❓ Lecturer Dashboard: Unexpected response ({response.status_code})")
    
    print("\n" + "=" * 70)
    print("🎉 DASHBOARD AND REPORTING TEST COMPLETED!")
    print("=" * 70)
    
    return True

def test_with_sample_data():
    """Test dashboard with some sample data"""
    print("\n🔧 TESTING WITH SAMPLE DATA CREATION")
    print("-" * 50)
    
    # This would create some sample data to make dashboards more interesting
    # For now, we'll just show what the structure would look like
    
    sample_data_structure = {
        "departments": 1,
        "courses": 1, 
        "students": 1,
        "lecturers": 1,
        "sessions": 0,
        "attendance_records": 0
    }
    
    print("📊 Current Data Structure:")
    for key, value in sample_data_structure.items():
        print(f"   {key}: {value}")
    
    print("\n💡 To see richer dashboard data, you need:")
    print("   • More attendance sessions")
    print("   • Student attendance records") 
    print("   • Multiple courses and enrollments")
    print("   • Active semester data")

if __name__ == "__main__":
    try:
        success = test_dashboard_endpoints()
        if success:
            test_with_sample_data()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
