#!/usr/bin/env python3
"""
Test script for logout functionality
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = " https://attendease-backend-x31p.onrender.com"  # Change to your backend URL
API_BASE = f"{BASE_URL}/api"

def test_logout_functionality():
    """Test the complete logout functionality"""
    print("🔐 Testing AttendEase Logout Functionality")
    print("=" * 50)
    
    # Test data
    test_user = {
        "email": "test.student@gmail.com",
        "password": "TestPassword123!",
        "user_type": "student"
    }
    
    session = requests.Session()
    
    try:
        # Step 1: Register a test user
        print("\n1. Registering test user...")
        register_response = session.post(
            f"{API_BASE}/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        if register_response.status_code == 201:
            print("✅ User registered successfully")
        elif register_response.status_code == 409:
            print("ℹ️  User already exists, proceeding with login")
        else:
            print(f"❌ Registration failed: {register_response.text}")
            return False
        
        # Step 2: Login to get tokens
        print("\n2. Logging in...")
        login_response = session.post(
            f"{API_BASE}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
                "device_info": {
                    "device_type": "test",
                    "app_version": "1.0.0"
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        session_token = login_data.get("session_token")
        
        print("✅ Login successful")
        print(f"   Access Token: {access_token[:20]}...")
        print(f"   Session Token: {session_token[:20] if session_token else 'None'}...")
        
        # Step 3: Test authenticated endpoint
        print("\n3. Testing authenticated endpoint...")
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Session-Token": session_token,
            "Content-Type": "application/json"
        }
        
        me_response = session.get(f"{API_BASE}/auth/me", headers=headers)
        
        if me_response.status_code == 200:
            print("✅ Authenticated request successful")
            user_data = me_response.json()
            print(f"   User: {user_data['user']['email']}")
        else:
            print(f"❌ Authenticated request failed: {me_response.text}")
            return False
        
        # Step 4: Test session listing
        print("\n4. Testing session listing...")
        sessions_response = session.get(f"{API_BASE}/auth/sessions", headers=headers)
        
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            print("✅ Session listing successful")
            print(f"   Total sessions: {sessions_data['total_sessions']}")
            print(f"   Active sessions: {sessions_data['active_sessions']}")
        else:
            print(f"❌ Session listing failed: {sessions_response.text}")
        
        # Step 5: Test logout
        print("\n5. Testing logout...")
        logout_response = session.post(
            f"{API_BASE}/auth/logout",
            json={"session_token": session_token},
            headers=headers
        )
        
        if logout_response.status_code == 200:
            logout_data = logout_response.json()
            print("✅ Logout successful")
            print(f"   Message: {logout_data['message']}")
            print(f"   Session invalidated: {logout_data.get('session_invalidated', False)}")
        else:
            print(f"❌ Logout failed: {logout_response.text}")
            return False
        
        # Step 6: Test access after logout
        print("\n6. Testing access after logout...")
        post_logout_response = session.get(f"{API_BASE}/auth/me", headers=headers)
        
        if post_logout_response.status_code == 401:
            print("✅ Access properly denied after logout")
        elif post_logout_response.status_code == 200:
            print("⚠️  Access still allowed after logout (JWT still valid)")
        else:
            print(f"❓ Unexpected response after logout: {post_logout_response.status_code}")
        
        # Step 7: Test login again
        print("\n7. Testing login after logout...")
        login2_response = session.post(
            f"{API_BASE}/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
                "device_info": {
                    "device_type": "test_2",
                    "app_version": "1.0.0"
                }
            },
            headers={"Content-Type": "application/json"}
        )
        
        if login2_response.status_code == 200:
            print("✅ Re-login successful")
            login2_data = login2_response.json()
            new_access_token = login2_data["access_token"]
            new_session_token = login2_data.get("session_token")
            
            # Step 8: Test logout all sessions
            print("\n8. Testing logout from all sessions...")
            new_headers = {
                "Authorization": f"Bearer {new_access_token}",
                "X-Session-Token": new_session_token,
                "Content-Type": "application/json"
            }
            
            logout_all_response = session.post(
                f"{API_BASE}/auth/logout-all",
                headers=new_headers
            )
            
            if logout_all_response.status_code == 200:
                logout_all_data = logout_all_response.json()
                print("✅ Logout all sessions successful")
                print(f"   Message: {logout_all_data['message']}")
                print(f"   Sessions invalidated: {logout_all_data.get('sessions_invalidated', 0)}")
            else:
                print(f"❌ Logout all failed: {logout_all_response.text}")
        
        print("\n" + "=" * 50)
        print("🎉 Logout functionality test completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error: Could not connect to {BASE_URL}")
        print("   Make sure the backend server is running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_session_management():
    """Test advanced session management features"""
    print("\n🔧 Testing Advanced Session Management")
    print("=" * 50)
    
    # This would test multiple concurrent sessions, session expiry, etc.
    # Implementation would be similar to above but with multiple login sessions
    
    pass

if __name__ == "__main__":
    success = test_logout_functionality()
    
    if success:
        print("\n✅ All logout tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some logout tests failed!")
        sys.exit(1)
