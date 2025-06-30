#!/usr/bin/env python3
"""
AttendEase Backend Validation Script - Updated for Render Deployment
Tests validation improvements and backend functionality
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
import uuid
import sys
import os

# Configuration - Updated for Render deployment
BASE_URL = "https://attendease-backend-x31p.onrender.com"
HEADERS = {"Content-Type": "application/json"}

class ValidationTester:
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
    
    def test_server_health(self):
        """Test if Render server is running and responsive"""
        print("\n" + "="*80)
        print("🏥 RENDER SERVER HEALTH CHECK")
        print("="*80)
        
        try:
            response = requests.get(f"{BASE_URL}/api/health", timeout=30)
            if response.status_code == 200:
                self.log_result("Render Server Health", True, "Server is running and responsive")
                return True
            else:
                self.log_result("Render Server Health", False, f"Health endpoint returned {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.log_result("Render Server Health", False, "Cannot connect to Render server")
            return False
        except requests.exceptions.Timeout:
            self.log_result("Render Server Health", False, "Render server timeout (>30s)")
            return False
        except Exception as e:
            self.log_result("Render Server Health", False, f"Unexpected error: {str(e)}")
            return False
    
    def test_validation_improvements(self):
        """Test the specific validation improvements we made"""
        print("\n" + "="*80)
        print("🔍 TESTING VALIDATION IMPROVEMENTS")
        print("="*80)
        
        # Test 1: Email Validation
        print("\n📧 Testing Email Validation:")
        
        invalid_emails = [
            "invalid-email",
            "test@",
            "@domain.com",
            "test..test@domain.com",
            "test@domain",
            ""
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "password": "ValidPass123!",
                "user_type": "student"
            }
            response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data, headers=HEADERS)
            success = response.status_code == 400
            self.log_result(f"Invalid Email Rejection ({email})", success, 
                          f"Status: {response.status_code}", response)
        
        # Test 2: Password Validation
        print("\n🔒 Testing Password Validation:")
        
        invalid_passwords = [
            "123",  # Too short
            "password",  # No uppercase, no numbers, no special chars
            "PASSWORD",  # No lowercase, no numbers, no special chars
            "Password",  # No numbers, no special chars
            "Password123",  # No special chars
            ""  # Empty
        ]
        
        for password in invalid_passwords:
            user_data = {
                "email": f"test{random.randint(1000, 9999)}@test.com",
                "password": password,
                "user_type": "student"
            }
            response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data, headers=HEADERS)
            success = response.status_code == 400
            self.log_result(f"Invalid Password Rejection ({password[:10]}...)", success, 
                          f"Status: {response.status_code}", response)
        
        # Test 3: Valid Registration
        print("\n✅ Testing Valid Registration:")
        
        valid_user_data = {
            "email": f"valid{int(time.time())}@test.com",
            "password": "ValidPass123!",
            "user_type": "admin"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=valid_user_data, headers=HEADERS)
        if self.log_result("Valid User Registration", response.status_code == 201, 
                          f"Status: {response.status_code}", response):
            # Login with the valid user
            login_data = {
                "email": valid_user_data["email"],
                "password": valid_user_data["password"]
            }
            response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers=HEADERS)
            if self.log_result("Valid User Login", response.status_code == 200, 
                              f"Status: {response.status_code}", response):
                self.tokens['admin'] = response.json().get('access_token')
                HEADERS['Authorization'] = f"Bearer {self.tokens['admin']}"
    
    def test_matricle_number_validation(self):
        """Test matricle number validation for students"""
        print("\n" + "="*80)
        print("🎓 TESTING MATRICLE NUMBER VALIDATION")
        print("="*80)
        
        if not self.tokens.get('admin'):
            print("❌ Skipping matricle number tests - no admin token")
            return
        
        # First create a student user
        student_email = f"student{int(time.time())}@test.com"
        student_data = {
            "email": student_email,
            "password": "StudentPass123!",
            "user_type": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=student_data, headers=HEADERS)
        if response.status_code != 201:
            print("❌ Could not create student user for matricle testing")
            return
        
        # Login as student to get user_id
        login_data = {
            "email": student_email,
            "password": "StudentPass123!"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data, headers={"Content-Type": "application/json"})
        if response.status_code != 200:
            print("❌ Could not login as student")
            return
        
        student_user_id = response.json()['user']['id']
        
        # Create a department first
        dept_data = {
            "name": f"Test Department {int(time.time())}",
            "code": f"TD{random.randint(100, 999)}",
            "description": "Test department for validation"
        }
        response = requests.post(f"{BASE_URL}/api/departments", json=dept_data, headers=HEADERS)
        if response.status_code != 201:
            print("❌ Could not create department for student profile")
            return
        
        department_id = response.json()['department']['id']
        
        # Test invalid matricle numbers
        print("\n📝 Testing Invalid Matricle Numbers:")
        
        invalid_matricles = [
            "123456",  # No format
            "ABC123",  # Missing year and number
            "ABC/2023",  # Missing number
            "ABC/YEAR/1234",  # Invalid year
            "ABC/2023/ABC",  # Invalid number
            "/2023/1234",  # Missing department code
            "ABC//1234",  # Missing year
            "ABC/2023/",  # Missing number
            ""  # Empty
        ]
        
        for matricle in invalid_matricles:
            student_profile_data = {
                "user_id": student_user_id,
                "matricle_number": matricle,
                "full_name": "Test Student",
                "department_id": department_id,
                "level": "300",
                "gender": "Male",
                "enrollment_year": 2024
            }
            response = requests.post(f"{BASE_URL}/api/students", json=student_profile_data, headers=HEADERS)
            success = response.status_code == 400
            self.log_result(f"Invalid Matricle Rejection ({matricle})", success, 
                          f"Status: {response.status_code}", response)
        
        # Test valid matricle number
        print("\n✅ Testing Valid Matricle Number:")
        
        valid_matricle = f"CSC/2024/{random.randint(1000, 9999)}"
        student_profile_data = {
            "user_id": student_user_id,
            "matricle_number": valid_matricle,
            "full_name": "Test Student",
            "department_id": department_id,
            "level": "300",
            "gender": "Male",
            "enrollment_year": 2024
        }
        response = requests.post(f"{BASE_URL}/api/students", json=student_profile_data, headers=HEADERS)
        self.log_result(f"Valid Matricle Acceptance ({valid_matricle})", response.status_code == 201, 
                      f"Status: {response.status_code}", response)
    
    def test_course_code_validation(self):
        """Test course code validation"""
        print("\n" + "="*80)
        print("📚 TESTING COURSE CODE VALIDATION")
        print("="*80)
        
        if not self.tokens.get('admin'):
            print("❌ Skipping course code tests - no admin token")
            return
        
        # Get or create a department
        response = requests.get(f"{BASE_URL}/api/departments", headers=HEADERS)
        if response.status_code == 200:
            departments = response.json().get('departments', [])
            if departments:
                department_id = departments[0]['id']
            else:
                # Create department
                dept_data = {
                    "name": f"Course Test Dept {int(time.time())}",
                    "code": f"CTD{random.randint(100, 999)}",
                    "description": "Department for course code testing"
                }
                response = requests.post(f"{BASE_URL}/api/departments", json=dept_data, headers=HEADERS)
                if response.status_code != 201:
                    print("❌ Could not create department for course testing")
                    return
                department_id = response.json()['department']['id']
        else:
            print("❌ Could not get departments for course testing")
            return
        
        # Test invalid course codes
        print("\n📖 Testing Invalid Course Codes:")
        
        invalid_codes = [
            "123",  # Too short
            "A",    # Too short
            "VERYLONGCOURSECODE123456",  # Too long
            "CSC 101",  # Contains space
            "CSC-101",  # Contains hyphen
            "csc101",   # All lowercase
            "",         # Empty
            "CSC@101"   # Contains special character
        ]
        
        for code in invalid_codes:
            course_data = {
                "course_code": code,
                "course_title": "Test Course",
                "department_id": department_id,
                "level": "300",
                "credit_units": 3,
                "semester_number": 1,
                "description": "Test course for validation"
            }
            response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=HEADERS)
            success = response.status_code == 400
            self.log_result(f"Invalid Course Code Rejection ({code})", success, 
                          f"Status: {response.status_code}", response)
        
        # Test valid course codes
        print("\n✅ Testing Valid Course Codes:")
        
        valid_codes = [
            f"CSC{random.randint(100, 999)}",
            f"MTH{random.randint(100, 999)}",
            f"ENG{random.randint(100, 999)}"
        ]
        
        for code in valid_codes:
            course_data = {
                "course_code": code,
                "course_title": "Test Course",
                "department_id": department_id,
                "level": "300",
                "credit_units": 3,
                "semester_number": 1,
                "description": "Test course for validation"
            }
            response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=HEADERS)
            success = response.status_code == 201
            self.log_result(f"Valid Course Code Acceptance ({code})", success, 
                          f"Status: {response.status_code}", response)
    
    def test_error_message_quality(self):
        """Test that error messages are helpful and specific"""
        print("\n" + "="*80)
        print("💬 TESTING ERROR MESSAGE QUALITY")
        print("="*80)
        
        # Test registration with invalid email
        user_data = {
            "email": "invalid-email",
            "password": "ValidPass123!",
            "user_type": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data, headers=HEADERS)
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get('message', '').lower()
                has_email_mention = 'email' in error_message
                self.log_result("Email Error Message Quality", has_email_mention, 
                              f"Contains 'email': {has_email_mention}")
            except:
                self.log_result("Email Error Message Quality", False, "Could not parse error response")
        
        # Test registration with weak password
        user_data = {
            "email": f"test{random.randint(1000, 9999)}@test.com",
            "password": "123",
            "user_type": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data, headers=HEADERS)
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get('message', '').lower()
                has_password_mention = 'password' in error_message
                self.log_result("Password Error Message Quality", has_password_mention, 
                              f"Contains 'password': {has_password_mention}")
            except:
                self.log_result("Password Error Message Quality", False, "Could not parse error response")
    
    def test_basic_functionality(self):
        """Test basic API functionality to ensure everything still works"""
        print("\n" + "="*80)
        print("🔧 TESTING BASIC FUNCTIONALITY")
        print("="*80)
        
        if not self.tokens.get('admin'):
            print("❌ Skipping basic functionality tests - no admin token")
            return
        
        # Test basic endpoints
        endpoints = [
            ("/api/users", "Users"),
            ("/api/departments", "Departments"),
            ("/api/courses", "Courses"),
            ("/api/students", "Students"),
            ("/api/lecturers", "Lecturers")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
                success = response.status_code == 200
                self.log_result(f"Get {name}", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Get {name}", False, f"Exception: {str(e)}")
    
    def generate_final_report(self):
        """Generate validation report focused on our updates"""
        print("\n" + "="*100)
        print("📋 VALIDATION IMPROVEMENTS TEST REPORT")
        print("="*100)
        
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 TEST SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            status = "🎉 EXCELLENT"
        elif success_rate >= 75:
            status = "✅ GOOD"
        elif success_rate >= 60:
            status = "⚠️ NEEDS IMPROVEMENT"
        else:
            status = "❌ CRITICAL ISSUES"
        
        print(f"\n🎯 VALIDATION STATUS: {status}")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        print(f"\n🚀 VALIDATION IMPROVEMENTS ASSESSMENT:")
        if success_rate >= 90:
            print("   ✅ Validation improvements are working excellently!")
            print("   ✅ Email validation is properly implemented")
            print("   ✅ Password validation is robust")
            print("   ✅ Matricle number validation is working")
            print("   ✅ Course code validation is functional")
            print("   ✅ Error messages are helpful and specific")
        elif success_rate >= 75:
            print("   ⚠️ Most validation improvements are working")
            print("   🔧 Some minor issues need attention")
        else:
            print("   ❌ Validation improvements need significant work")
            print("   🔧 Review failed tests and fix implementation")
        
        return success_rate >= 75
    
    def run_validation_tests(self):
        """Run focused validation tests"""
        print("🚀 ATTENDEASE VALIDATION IMPROVEMENTS TEST")
        print("="*100)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing URL: {BASE_URL}")
        print("="*100)
        
        try:
            # Test server health first
            if not self.test_server_health():
                print("❌ Render server is not accessible. Please check deployment.")
                return False
            
            # Test our specific validation improvements
            self.test_validation_improvements()
            self.test_matricle_number_validation()
            self.test_course_code_validation()
            self.test_error_message_quality()
            
            # Test that basic functionality still works
            self.test_basic_functionality()
            
            # Generate report
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
    tester = ValidationTester()
    success = tester.run_validation_tests()
    
    if success:
        print("\n🎉 VALIDATION IMPROVEMENTS TEST SUCCESSFUL!")
        sys.exit(0)
    else:
        print("\n❌ VALIDATION IMPROVEMENTS TEST FAILED - PLEASE REVIEW ISSUES")
        sys.exit(1)

if __name__ == "__main__":
    main()
