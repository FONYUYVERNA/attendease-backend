#!/usr/bin/env python3
"""
Test script for 2FA Registration Flow
Tests the complete registration process with verification codes
"""

import requests
import json
import time
import sys

# Use the correct base URL for your setup
BASE_URL = "http://localhost:5000"  # Since you're using py run.py

def test_health_check():
    """Test if backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"⚠️  Backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running with 'py run.py'")
        return False
    except requests.exceptions.Timeout:
        print("❌ Backend connection timed out")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

def check_departments():
    """Check if FET departments exist"""
    try:
        print("🏫 Checking FET departments...")
        response = requests.get(f"{BASE_URL}/api/departments", timeout=5)
        if response.status_code == 200:
            departments = response.json()
            if len(departments) > 0:
                print(f"✅ Found {len(departments)} FET departments")
                for dept in departments[:3]:  # Show first 3 departments
                    print(f"   • {dept.get('name', 'Unknown')} ({dept.get('code', 'N/A')})")
                if len(departments) > 3:
                    print(f"   ... and {len(departments) - 3} more")
                return True
        
        print("⚠️  No departments found - students will be assigned to first available department")
        return True
    except Exception as e:
        print(f"⚠️  Could not check departments: {str(e)}")
        return True  # Continue anyway

def test_2fa_registration():
    """Test the complete 2FA registration flow"""
    
    print("\n🚀 Starting 2FA Registration Tests for FET")
    print(f"\nMake sure your backend is running on {BASE_URL}")
    print("Start it with: py run.py")
    
    # Check if backend is running
    if not test_health_check():
        print("\n❌ Backend is not accessible. Please start it first.")
        return
    
    # Check FET departments
    check_departments()
    
    print("\n🧪 Testing 2FA Registration Flow")
    print("=" * 50)
    
    # Test data for different user types - using correct enum values and unique emails
    test_users = [
        {
            'email': 'fet.student@gmail.com',  # FET student email
            'user_type': 'student',
            'password': 'StudentPass123',
            'first_name': 'FET',
            'last_name': 'Student',
            'matricle_number': 'FE25A001',  # FET matricle format
            'level': '300',  # Valid enum value: 200, 300, 400, 500
            'gender': 'Male'  # Valid enum value: Male, Female, Other
        },
        {
            'email': 'fet.lecturer@ubuea.cm',  # FET lecturer email
            'user_type': 'lecturer',
            'phone_number': '+237123456789',
            'password': 'LecturerPass123',
            'first_name': 'FET',
            'last_name': 'Lecturer'
        },
        {
            'email': 'fet.admin@gmail.com',  # FET admin email
            'user_type': 'admin',
            'password': 'AdminPass123',
            'first_name': 'FET',
            'last_name': 'Admin'
        }
    ]
    
    successful_registrations = []
    
    for user_data in test_users:
        email = user_data['email']
        user_type = user_data['user_type']
        
        print(f"\n📧 Testing {user_type} registration: {email}")
        print("-" * 50)
        
        try:
            # Step 1: Send verification code
            print("Step 1: Sending verification code...")
            
            verification_data = {
                'email': email,
                'user_type': user_type
            }
            
            if user_type == 'lecturer':
                verification_data['phone_number'] = user_data['phone_number']
            
            response = requests.post(
                f"{BASE_URL}/api/auth/send-verification",
                json=verification_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to send verification code")
                print(f"Response: {json.dumps(response.json(), indent=2)}")
                continue
            
            response_data = response.json()
            verification_id = response_data.get('verification_id')
            delivery_method = response_data.get('delivery_method')
            debug_code = response_data.get('debug_code')  # This contains the actual code
            
            print(f"✅ Verification code sent via {delivery_method}")
            print(f"Verification ID: {verification_id}")
            
            # Display the verification code prominently
            if debug_code:
                print("\n" + "🎯" * 20)
                print(f"🔑 YOUR VERIFICATION CODE IS: {debug_code}")
                print("🎯" * 20)
                print(f"📋 Copy this code: {debug_code}")
                print("🎯" * 20 + "\n")
            
            # Give user time to see the code
            time.sleep(3)
            
            # Step 2: Get verification code from user
            print(f"Enter the 6-digit verification code for {email}")
            print(f"(The code is: {debug_code}): ", end="")
            verification_code = input().strip()
            
            # If user just pressed enter, use the debug code
            if not verification_code:
                verification_code = debug_code
                print(f"Using debug code: {verification_code}")
            
            if not verification_code or len(verification_code) != 6:
                print("❌ Invalid code format. Skipping this user.")
                continue
            
            # Step 3: Verify code and complete registration
            print("Step 2: Verifying code and completing registration...")
            
            verify_data = {
                'verification_id': verification_id,
                'code': verification_code,
                'password': user_data['password'],
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', '')
            }
            
            # Add student-specific data
            if user_type == 'student':
                verify_data['matricle_number'] = user_data.get('matricle_number')
                verify_data['level'] = user_data.get('level', '200')
                verify_data['gender'] = user_data.get('gender', 'Male')
                # Note: department_id will be auto-assigned from existing FET departments
            
            response = requests.post(
                f"{BASE_URL}/api/auth/verify-registration",
                json=verify_data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 201:
                print(f"✅ {user_type.title()} registration successful!")
                successful_registrations.append({
                    'email': email,
                    'password': user_data['password'],
                    'type': user_type
                })
            else:
                print(f"❌ Registration failed: {response.json()}")
                
        except Exception as e:
            print(f"❌ Error during {user_type} registration: {str(e)}")
        
        print("-" * 50)
        time.sleep(1)  # Brief pause between tests
    
    # Test login with successfully registered users
    if successful_registrations:
        print(f"\n🔐 Testing Login with Registered Users")
        print("=" * 50)
        
        for user in successful_registrations:
            try:
                print(f"\nTesting login for {user['type']}: {user['email']}")
                
                login_data = {
                    'email': user['email'],
                    'password': user['password']
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/auth/login",
                    json=login_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    print(f"✅ Login successful for {user['email']}")
                    token_data = response.json()
                    print(f"   Token received: {token_data.get('access_token', 'N/A')[:20]}...")
                    
                    # Show user profile info
                    if token_data.get('profile'):
                        profile = token_data['profile']
                        print(f"   Profile: {profile.get('full_name', 'N/A')}")
                        if user['type'] == 'student':
                            print(f"   Matricle: {profile.get('matricle_number', 'N/A')}")
                            print(f"   Level: {profile.get('level', 'N/A')}")
                            print(f"   Department ID: {profile.get('department_id', 'N/A')}")
                        elif user['type'] == 'lecturer':
                            print(f"   Lecturer ID: {profile.get('lecturer_id', 'N/A')}")
                        elif user['type'] == 'admin':
                            print(f"   Admin ID: {profile.get('admin_id', 'N/A')}")
                else:
                    print(f"❌ Login failed for {user['email']}: {response.json()}")
                    
            except Exception as e:
                print(f"❌ Login test error for {user['email']}: {str(e)}")
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"✅ Successful registrations: {len(successful_registrations)}")
    print(f"📧 Total tests attempted: {len(test_users)}")
    
    if successful_registrations:
        print("\n🎉 Successfully registered FET users:")
        for user in successful_registrations:
            print(f"   • {user['type']}: {user['email']}")
    
    print(f"\n💡 Tips:")
    print("   • The verification codes are displayed clearly above")
    print("   • You can just press Enter to use the displayed code")
    print("   • Codes expire in 15 minutes")
    print("   • Check your backend terminal for detailed logs")
    print(f"\n🔧 FET Backend Info:")
    print("   • Level enum accepts: 200, 300, 400, 500")
    print("   • Gender enum accepts: Male, Female, Other")
    print("   • ID fields are limited to 20 characters")
    print("   • Students auto-assigned to existing FET departments")
    print("   • This is configured for Faculty of Engineering and Technology")

if __name__ == "__main__":
    test_2fa_registration()
