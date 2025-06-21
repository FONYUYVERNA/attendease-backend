#!/usr/bin/env python3
"""
API Endpoint Validation Script
Tests all API endpoints to ensure they're properly implemented
"""

import requests
import json
import time
from datetime import datetime
import sys

class APIValidator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json"}
        self.auth_token = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, endpoint, method, status_code, expected_status, message=""):
        """Log test result"""
        self.total_tests += 1
        passed = status_code == expected_status
        if passed:
            self.passed_tests += 1
        
        result = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'expected_status': expected_status,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "[PASS]" if passed else "[FAIL]"
        print(f"{status_icon} {method} {endpoint}: {status_code} (expected {expected_status})")
        if message:
            print(f"   {message}")

    def test_health_check(self):
        """Test health check endpoint"""
        print("\n[INFO] Testing Health Check...")
        try:
            response = requests.get(f"{self.base_url}/api/health")
            self.log_test("/api/health", "GET", response.status_code, 200)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    print("   [PASS] Health check response is valid")
                else:
                    print("   [WARN] Health check response format unexpected")
        except Exception as e:
            self.log_test("/api/health", "GET", 0, 200, f"Connection error: {str(e)}")

    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        print("\n[INFO] Testing Authentication Endpoints...")
        
        # Test login endpoint exists
        try:
            login_data = {"email": "test@example.com", "password": "wrongpassword"}
            response = requests.post(f"{self.base_url}/api/auth/login", 
                                   json=login_data, headers=self.headers)
            # Should return 401 for invalid credentials, not 404
            if response.status_code == 404:
                self.log_test("/api/auth/login", "POST", 404, 401, "Endpoint not found")
            else:
                self.log_test("/api/auth/login", "POST", response.status_code, 401, "Endpoint exists")
        except Exception as e:
            self.log_test("/api/auth/login", "POST", 0, 401, f"Connection error: {str(e)}")
        
        # Test register endpoint
        try:
            register_data = {
                "email": "test@example.com",
                "password": "testpass",
                "user_type": "student"
            }
            response = requests.post(f"{self.base_url}/api/auth/register", 
                                   json=register_data, headers=self.headers)
            # Should return 400 for missing data or 201 for success, not 404
            if response.status_code == 404:
                self.log_test("/api/auth/register", "POST", 404, 400, "Endpoint not found")
            else:
                self.log_test("/api/auth/register", "POST", response.status_code, 400, "Endpoint exists")
        except Exception as e:
            self.log_test("/api/auth/register", "POST", 0, 400, f"Connection error: {str(e)}")

    def test_crud_endpoints(self):
        """Test CRUD endpoints for all resources"""
        print("\n[INFO] Testing CRUD Endpoints...")
        
        resources = [
            'users', 'students', 'lecturers', 'admins', 'departments',
            'academic-years', 'semesters', 'courses', 'geofence-areas',
            'course-assignments', 'student-enrollments', 'attendance-sessions',
            'attendance-records', 'notifications', 'system-settings'
        ]
        
        for resource in resources:
            # Test GET (list)
            try:
                response = requests.get(f"{self.base_url}/api/{resource}")
                # Should return 401 (unauthorized) or 200, not 404
                if response.status_code == 404:
                    self.log_test(f"/api/{resource}", "GET", 404, 401, "Endpoint not found")
                else:
                    self.log_test(f"/api/{resource}", "GET", response.status_code, 401, "Endpoint exists")
            except Exception as e:
                self.log_test(f"/api/{resource}", "GET", 0, 401, f"Connection error: {str(e)}")

    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print("\n[INFO] Testing Dashboard Endpoints...")
        
        dashboard_endpoints = [
            'admin', 'lecturer', 'student', 'quick-stats'
        ]
        
        for endpoint in dashboard_endpoints:
            try:
                response = requests.get(f"{self.base_url}/api/dashboard/{endpoint}")
                # Should return 401 (unauthorized) or 200, not 404
                if response.status_code == 404:
                    self.log_test(f"/api/dashboard/{endpoint}", "GET", 404, 401, "Endpoint not found")
                else:
                    self.log_test(f"/api/dashboard/{endpoint}", "GET", response.status_code, 401, "Endpoint exists")
            except Exception as e:
                self.log_test(f"/api/dashboard/{endpoint}", "GET", 0, 401, f"Connection error: {str(e)}")

    def test_reports_endpoints(self):
        """Test reports endpoints"""
        print("\n[INFO] Testing Reports Endpoints...")
        
        report_endpoints = [
            'attendance/summary',
            'attendance/student/1',
            'attendance/course/1',
            'courses/performance',
            'students/performance'
        ]
        
        for endpoint in report_endpoints:
            try:
                response = requests.get(f"{self.base_url}/api/reports/{endpoint}")
                # Should return 401 (unauthorized) or 200, not 404
                if response.status_code == 404:
                    self.log_test(f"/api/reports/{endpoint}", "GET", 404, 401, "Endpoint not found")
                else:
                    self.log_test(f"/api/reports/{endpoint}", "GET", response.status_code, 401, "Endpoint exists")
            except Exception as e:
                self.log_test(f"/api/reports/{endpoint}", "GET", 0, 401, f"Connection error: {str(e)}")

    def generate_report(self):
        """Generate validation report"""
        print("\n" + "="*80)
        print("API ENDPOINT VALIDATION REPORT")
        print("="*80)
        print(f"Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total endpoints tested: {self.total_tests}")
        print(f"Endpoints working correctly: {self.passed_tests}")
        print(f"Success rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        # Group results by status
        passed = [r for r in self.test_results if r['passed']]
        failed = [r for r in self.test_results if not r['passed']]
        
        if failed:
            print(f"\n[FAIL] FAILED ENDPOINTS ({len(failed)}):")
            for result in failed:
                print(f"  * {result['method']} {result['endpoint']}: {result['status_code']} - {result['message']}")
        
        if passed:
            print(f"\n[PASS] WORKING ENDPOINTS ({len(passed)}):")
            for result in passed[:10]:  # Show first 10
                print(f"  * {result['method']} {result['endpoint']}: {result['status_code']}")
            if len(passed) > 10:
                print(f"  ... and {len(passed) - 10} more")
        
        # Overall assessment
        print("\n" + "="*80)
        print("ENDPOINT ASSESSMENT")
        print("="*80)
        
        if self.passed_tests == self.total_tests:
            print("[EXCELLENT] All API endpoints are properly configured!")
        elif self.passed_tests / self.total_tests >= 0.8:
            print("[GOOD] Most API endpoints are working correctly.")
            print("Fix the failing endpoints for complete functionality.")
        else:
            print("[NEEDS ATTENTION] Many endpoints are not working.")
            print("Review route implementations and server configuration.")
        
        # Save report
        report_data = {
            'validation_timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'success_rate': round(self.passed_tests/self.total_tests*100, 1),
            'results': self.test_results
        }
        
        with open('api_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        print("\nDetailed report saved to: api_validation_report.json")
        
        return self.passed_tests == self.total_tests

    def run_validation(self):
        """Run complete API validation"""
        print("STARTING API ENDPOINT VALIDATION")
        print("="*80)
        print(f"Testing API at: {self.base_url}")
        print("="*80)
        
        # Run all tests
        self.test_health_check()
        self.test_authentication_endpoints()
        self.test_crud_endpoints()
        self.test_dashboard_endpoints()
        self.test_reports_endpoints()
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate AttendEase API endpoints')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL for the API (default: http://localhost:5000)')
    
    args = parser.parse_args()
    
    validator = APIValidator(args.url)
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
