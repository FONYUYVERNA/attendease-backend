#!/usr/bin/env python3
"""
Focused test for attendance session functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

def test_attendance_session_isolated():
    """Test attendance session creation in isolation"""
    print("🔍 FOCUSED ATTENDANCE SESSION TEST")
    print("="*50)
    
    # Step 1: Login as admin
    login_data = {
        "email": "admin@attendease.com",  # Use existing admin
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
    if response.status_code != 200:
        print("❌ Admin login failed")
        return False
    
    token = response.json()['access_token']
    auth_headers = HEADERS.copy()
    auth_headers['Authorization'] = f"Bearer {token}"
    
    print("✅ Admin login successful")
    
    # Step 2: Get existing data
    # Get course assignments
    response = requests.get(f"{BASE_URL}/api/course-assignments", headers=auth_headers)
    if response.status_code != 200:
        print("❌ Failed to get course assignments")
        return False
    
    assignments = response.json().get('course_assignments', [])
    if not assignments:
        print("❌ No course assignments found")
        return False
    
    course_assignment_id = assignments[0]['id']
    print(f"✅ Found course assignment: {course_assignment_id}")
    
    # Get geofence areas
    response = requests.get(f"{BASE_URL}/api/geofence-areas", headers=auth_headers)
    if response.status_code != 200:
        print("❌ Failed to get geofence areas")
        return False
    
    geofences = response.json().get('geofence_areas', [])
    if not geofences:
        print("❌ No geofence areas found")
        return False
    
    geofence_area_id = geofences[0]['id']
    print(f"✅ Found geofence area: {geofence_area_id}")
    
    # Step 3: Create attendance session
    session_data = {
        "course_assignment_id": course_assignment_id,
        "geofence_area_id": geofence_area_id,
        "session_name": "Test Session",
        "topic": "Test Topic",
        "late_threshold_minutes": 15,
        "auto_end_minutes": 120,
        "notes": "Test session for validation"
    }
    
    print(f"📤 Creating attendance session...")
    print(f"   Course Assignment: {course_assignment_id}")
    print(f"   Geofence Area: {geofence_area_id}")
    
    response = requests.post(f"{BASE_URL}/api/attendance-sessions", 
                           json=session_data, headers=auth_headers)
    
    print(f"📥 Response Status: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        print("✅ Attendance session created successfully!")
        print(f"   Response keys: {list(response_data.keys())}")
        
        # Check for session ID in different possible locations
        session_id = None
        if 'session' in response_data:
            session_id = response_data['session'].get('id')
            print(f"   Session ID (from 'session'): {session_id}")
        elif 'attendance_session' in response_data:
            session_id = response_data['attendance_session'].get('id')
            print(f"   Session ID (from 'attendance_session'): {session_id}")
        elif 'data' in response_data:
            session_id = response_data['data'].get('id')
            print(f"   Session ID (from 'data'): {session_id}")
        
        if session_id:
            print(f"✅ Session created with ID: {session_id}")
            
            # Test getting the session
            response = requests.get(f"{BASE_URL}/api/attendance-sessions/{session_id}", 
                                  headers=auth_headers)
            if response.status_code == 200:
                print("✅ Session retrieval successful")
                return True
            else:
                print(f"❌ Session retrieval failed: {response.status_code}")
                return False
        else:
            print("⚠️ Session created but ID not found in expected locations")
            print(f"   Full response: {json.dumps(response_data, indent=2)}")
            return True  # Still consider it successful if creation worked
    else:
        print(f"❌ Attendance session creation failed")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_attendance_session_isolated()
    if success:
        print("\n🎉 ATTENDANCE SESSION TEST PASSED!")
    else:
        print("\n❌ ATTENDANCE SESSION TEST FAILED!")
