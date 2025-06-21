#!/usr/bin/env python3
"""
Comprehensive Backend Validation Script for AttendEase
This script performs thorough verification of all backend components
"""

import os
import sys
import importlib
import inspect
from datetime import datetime
import json

class BackendValidator:
    def __init__(self):
        self.results = {
            'models': {'status': 'pending', 'details': []},
            'routes': {'status': 'pending', 'details': []},
            'database': {'status': 'pending', 'details': []},
            'authentication': {'status': 'pending', 'details': []},
            'api_endpoints': {'status': 'pending', 'details': []},
            'configuration': {'status': 'pending', 'details': []},
            'dependencies': {'status': 'pending', 'details': []},
            'security': {'status': 'pending', 'details': []},
            'documentation': {'status': 'pending', 'details': []},
            'testing': {'status': 'pending', 'details': []}
        }
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def log_result(self, category, check_name, status, message, severity='info'):
        """Log validation result"""
        self.total_checks += 1
        result = {
            'check': check_name,
            'status': status,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results[category]['details'].append(result)
        
        if status == 'pass':
            self.success_count += 1
        elif severity == 'error':
            self.errors.append(f"{category}.{check_name}: {message}")
        elif severity == 'warning':
            self.warnings.append(f"{category}.{check_name}: {message}")

    def validate_models(self):
        """Validate all database models"""
        print("[INFO] Validating Database Models...")
        
        required_models = [
            'User', 'Student', 'Lecturer', 'Admin', 'Department',
            'AcademicYear', 'Semester', 'Course', 'GeofenceArea',
            'CourseAssignment', 'StudentEnrollment', 'AttendanceSession',
            'AttendanceRecord', 'AttendanceOverride', 'Notification',
            'SystemSetting', 'UserSession', 'UserPreference',
            'TwoFactorAuth', 'AuditLog'
        ]
        
        try:
            # Check if models directory exists
            if not os.path.exists('models'):
                self.log_result('models', 'directory_exists', 'fail', 
                              'Models directory not found', 'error')
                return
            
            # Check __init__.py exists
            if not os.path.exists('models/__init__.py'):
                self.log_result('models', 'init_file', 'fail', 
                              'models/__init__.py not found', 'error')
                return
            
            # Import models module
            sys.path.insert(0, '.')
            import models
            
            # Check each required model
            missing_models = []
            for model_name in required_models:
                if hasattr(models, model_name):
                    model_class = getattr(models, model_name)
                    
                    # Check if it's a proper SQLAlchemy model
                    if hasattr(model_class, '__tablename__'):
                        self.log_result('models', f'{model_name}_exists', 'pass',
                                      f'{model_name} model properly defined')
                        
                        # Check for required methods
                        if hasattr(model_class, 'to_dict'):
                            self.log_result('models', f'{model_name}_to_dict', 'pass',
                                          f'{model_name} has to_dict method')
                        else:
                            self.log_result('models', f'{model_name}_to_dict', 'fail',
                                          f'{model_name} missing to_dict method', 'warning')
                    else:
                        self.log_result('models', f'{model_name}_sqlalchemy', 'fail',
                                      f'{model_name} is not a proper SQLAlchemy model', 'error')
                else:
                    missing_models.append(model_name)
            
            if missing_models:
                self.log_result('models', 'all_models_present', 'fail',
                              f'Missing models: {", ".join(missing_models)}', 'error')
            else:
                self.log_result('models', 'all_models_present', 'pass',
                              'All required models are present')
            
            # Check enums
            required_enums = [
                'user_type_enum', 'level_enum', 'gender_enum', 'enrollment_status_enum',
                'session_status_enum', 'attendance_status_enum', 'check_in_method_enum',
                'notification_type_enum', 'setting_type_enum', 'geofence_type_enum'
            ]
            
            missing_enums = []
            for enum_name in required_enums:
                if hasattr(models, enum_name):
                    self.log_result('models', f'{enum_name}_exists', 'pass',
                                  f'{enum_name} enum defined')
                else:
                    missing_enums.append(enum_name)
            
            if missing_enums:
                self.log_result('models', 'all_enums_present', 'fail',
                              f'Missing enums: {", ".join(missing_enums)}', 'warning')
            else:
                self.log_result('models', 'all_enums_present', 'pass',
                              'All required enums are present')
            
            self.results['models']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('models', 'import_error', 'fail',
                          f'Error importing models: {str(e)}', 'error')
            self.results['models']['status'] = 'failed'

    def validate_routes(self):
        """Validate all route blueprints"""
        print("[INFO] Validating API Routes...")
        
        required_routes = [
            'auth', 'users', 'students', 'lecturers', 'admins',
            'departments', 'academic_years', 'semesters', 'courses',
            'geofence_areas', 'course_assignments', 'student_enrollments',
            'attendance_sessions', 'attendance_records', 'notifications',
            'system_settings', 'dashboard', 'reports'
        ]
        
        try:
            # Check if routes directory exists
            if not os.path.exists('routes'):
                self.log_result('routes', 'directory_exists', 'fail',
                              'Routes directory not found', 'error')
                return
            
            missing_routes = []
            for route_name in required_routes:
                route_file = f'routes/{route_name}.py'
                if os.path.exists(route_file):
                    self.log_result('routes', f'{route_name}_file_exists', 'pass',
                                  f'{route_name}.py exists')
                    
                    # Try to import the route module
                    try:
                        module = importlib.import_module(f'routes.{route_name}')
                        
                        # Check for blueprint
                        blueprint_name = f'{route_name}_bp'
                        if hasattr(module, blueprint_name):
                            self.log_result('routes', f'{route_name}_blueprint', 'pass',
                                          f'{route_name} blueprint defined')
                        else:
                            self.log_result('routes', f'{route_name}_blueprint', 'fail',
                                          f'{route_name} blueprint not found', 'error')
                    except Exception as e:
                        self.log_result('routes', f'{route_name}_import', 'fail',
                                      f'Error importing {route_name}: {str(e)}', 'error')
                else:
                    missing_routes.append(route_name)
            
            if missing_routes:
                self.log_result('routes', 'all_routes_present', 'fail',
                              f'Missing route files: {", ".join(missing_routes)}', 'error')
            else:
                self.log_result('routes', 'all_routes_present', 'pass',
                              'All required route files are present')
            
            self.results['routes']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('routes', 'validation_error', 'fail',
                          f'Error validating routes: {str(e)}', 'error')
            self.results['routes']['status'] = 'failed'

    def validate_database_config(self):
        """Validate database configuration and scripts"""
        print("[INFO] Validating Database Configuration...")
        
        try:
            # Check for database scripts
            scripts_dir = 'scripts'
            if os.path.exists(scripts_dir):
                self.log_result('database', 'scripts_directory', 'pass',
                              'Scripts directory exists')
                
                # Check for required scripts
                required_scripts = [
                    'create_database.sql',
                    'attendease_schema.sql'
                ]
                
                for script in required_scripts:
                    script_path = os.path.join(scripts_dir, script)
                    if os.path.exists(script_path):
                        self.log_result('database', f'{script}_exists', 'pass',
                                      f'{script} exists')
                    else:
                        self.log_result('database', f'{script}_exists', 'fail',
                                      f'{script} not found', 'warning')
            else:
                self.log_result('database', 'scripts_directory', 'fail',
                              'Scripts directory not found', 'warning')
            
            # Check for migrations
            if os.path.exists('migrations'):
                self.log_result('database', 'migrations_directory', 'pass',
                              'Migrations directory exists')
            else:
                self.log_result('database', 'migrations_directory', 'fail',
                              'Migrations directory not found', 'warning')
            
            self.results['database']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('database', 'validation_error', 'fail',
                          f'Error validating database config: {str(e)}', 'error')
            self.results['database']['status'] = 'failed'

    def validate_app_configuration(self):
        """Validate main application configuration"""
        print("[INFO] Validating Application Configuration...")
        
        try:
            # Check if app.py exists
            if os.path.exists('app.py'):
                self.log_result('configuration', 'app_file_exists', 'pass',
                              'app.py exists')
                
                # Read app.py content
                with open('app.py', 'r', encoding='utf-8') as f:
                    app_content = f.read()
                
                # Check for required imports
                required_imports = [
                    'Flask', 'SQLAlchemy', 'JWTManager', 'Bcrypt', 'CORS'
                ]
                
                for import_name in required_imports:
                    if import_name in app_content:
                        self.log_result('configuration', f'{import_name}_import', 'pass',
                                      f'{import_name} imported')
                    else:
                        self.log_result('configuration', f'{import_name}_import', 'fail',
                                      f'{import_name} not imported', 'error')
                
                # Check for blueprint registrations
                if 'register_blueprint' in app_content:
                    self.log_result('configuration', 'blueprints_registered', 'pass',
                                  'Blueprints are registered')
                else:
                    self.log_result('configuration', 'blueprints_registered', 'fail',
                                  'No blueprint registrations found', 'error')
                
                # Check for error handlers
                if '@app.errorhandler' in app_content:
                    self.log_result('configuration', 'error_handlers', 'pass',
                                  'Error handlers defined')
                else:
                    self.log_result('configuration', 'error_handlers', 'fail',
                                  'No error handlers found', 'warning')
            else:
                self.log_result('configuration', 'app_file_exists', 'fail',
                              'app.py not found', 'error')
            
            # Check for requirements.txt
            if os.path.exists('requirements.txt'):
                self.log_result('configuration', 'requirements_file', 'pass',
                              'requirements.txt exists')
            else:
                self.log_result('configuration', 'requirements_file', 'fail',
                              'requirements.txt not found', 'warning')
            
            # Check for .env file
            if os.path.exists('.env'):
                self.log_result('configuration', 'env_file', 'pass',
                              '.env file exists')
            else:
                self.log_result('configuration', 'env_file', 'fail',
                              '.env file not found', 'warning')
            
            self.results['configuration']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('configuration', 'validation_error', 'fail',
                          f'Error validating configuration: {str(e)}', 'error')
            self.results['configuration']['status'] = 'failed'

    def validate_dependencies(self):
        """Validate project dependencies"""
        print("[INFO] Validating Dependencies...")
        
        try:
            if os.path.exists('requirements.txt'):
                with open('requirements.txt', 'r', encoding='utf-8') as f:
                    requirements = f.read()
                
                required_packages = [
                    'Flask', 'Flask-SQLAlchemy', 'Flask-JWT-Extended',
                    'Flask-Bcrypt', 'Flask-CORS', 'psycopg2-binary',
                    'python-dotenv', 'Pillow', 'face-recognition'
                ]
                
                missing_packages = []
                for package in required_packages:
                    if package.lower() in requirements.lower():
                        self.log_result('dependencies', f'{package}_listed', 'pass',
                                      f'{package} listed in requirements')
                    else:
                        missing_packages.append(package)
                
                if missing_packages:
                    self.log_result('dependencies', 'all_packages_listed', 'fail',
                                  f'Missing packages: {", ".join(missing_packages)}', 'warning')
                else:
                    self.log_result('dependencies', 'all_packages_listed', 'pass',
                                  'All required packages listed')
            else:
                self.log_result('dependencies', 'requirements_file', 'fail',
                              'requirements.txt not found', 'error')
            
            self.results['dependencies']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('dependencies', 'validation_error', 'fail',
                          f'Error validating dependencies: {str(e)}', 'error')
            self.results['dependencies']['status'] = 'failed'

    def validate_security(self):
        """Validate security implementations"""
        print("[INFO] Validating Security Features...")
        
        try:
            # Check for authentication decorators
            utils_dir = 'utils'
            if os.path.exists(utils_dir):
                decorators_file = os.path.join(utils_dir, 'decorators.py')
                if os.path.exists(decorators_file):
                    self.log_result('security', 'decorators_file', 'pass',
                                  'Security decorators file exists')
                    
                    with open(decorators_file, 'r', encoding='utf-8') as f:
                        decorators_content = f.read()
                    
                    if 'jwt_required' in decorators_content:
                        self.log_result('security', 'jwt_decorators', 'pass',
                                      'JWT decorators implemented')
                    else:
                        self.log_result('security', 'jwt_decorators', 'fail',
                                      'JWT decorators not found', 'warning')
                else:
                    self.log_result('security', 'decorators_file', 'fail',
                                  'decorators.py not found', 'warning')
            
            # Check for password hashing
            if os.path.exists('app.py'):
                with open('app.py', 'r', encoding='utf-8') as f:
                    app_content = f.read()
                
                if 'Bcrypt' in app_content:
                    self.log_result('security', 'password_hashing', 'pass',
                                  'Password hashing configured')
                else:
                    self.log_result('security', 'password_hashing', 'fail',
                                  'Password hashing not configured', 'error')
                
                # Check for CORS configuration
                if 'CORS' in app_content:
                    self.log_result('security', 'cors_configured', 'pass',
                                  'CORS configured')
                else:
                    self.log_result('security', 'cors_configured', 'fail',
                                  'CORS not configured', 'warning')
            
            self.results['security']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('security', 'validation_error', 'fail',
                          f'Error validating security: {str(e)}', 'error')
            self.results['security']['status'] = 'failed'

    def validate_testing(self):
        """Validate testing infrastructure"""
        print("[INFO] Validating Testing Infrastructure...")
        
        try:
            test_files = [
                'test_api.py',
                'test_api_comprehensive.py',
                'test_complete_verification.py'
            ]
            
            existing_tests = []
            for test_file in test_files:
                if os.path.exists(test_file):
                    existing_tests.append(test_file)
                    self.log_result('testing', f'{test_file}_exists', 'pass',
                                  f'{test_file} exists')
            
            if existing_tests:
                self.log_result('testing', 'test_files_present', 'pass',
                              f'{len(existing_tests)} test files found')
            else:
                self.log_result('testing', 'test_files_present', 'fail',
                              'No test files found', 'warning')
            
            # Check for Postman collection
            postman_files = [
                'AttendEase_API_Tests.postman_collection.json',
                'complete_postman_collection.json'
            ]
            
            for postman_file in postman_files:
                if os.path.exists(postman_file):
                    self.log_result('testing', f'{postman_file}_exists', 'pass',
                                  f'{postman_file} exists')
            
            self.results['testing']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('testing', 'validation_error', 'fail',
                          f'Error validating testing: {str(e)}', 'error')
            self.results['testing']['status'] = 'failed'

    def validate_documentation(self):
        """Validate documentation"""
        print("[INFO] Validating Documentation...")
        
        try:
            doc_files = [
                'README.md',
                'verification_report.md'
            ]
            
            for doc_file in doc_files:
                if os.path.exists(doc_file):
                    self.log_result('documentation', f'{doc_file}_exists', 'pass',
                                  f'{doc_file} exists')
                else:
                    self.log_result('documentation', f'{doc_file}_exists', 'fail',
                                  f'{doc_file} not found', 'warning')
            
            self.results['documentation']['status'] = 'complete'
            
        except Exception as e:
            self.log_result('documentation', 'validation_error', 'fail',
                          f'Error validating documentation: {str(e)}', 'error')
            self.results['documentation']['status'] = 'failed'

    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BACKEND VALIDATION REPORT")
        print("="*80)
        print(f"Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total checks performed: {self.total_checks}")
        print(f"Successful checks: {self.success_count}")
        print(f"Success rate: {(self.success_count/self.total_checks*100):.1f}%")
        print()
        
        # Summary by category
        for category, data in self.results.items():
            status_icon = "[PASS]" if data['status'] == 'complete' else "[FAIL]"
            passed = len([d for d in data['details'] if d['status'] == 'pass'])
            total = len(data['details'])
            print(f"{status_icon} {category.upper()}: {passed}/{total} checks passed")
        
        print("\n" + "="*80)
        print("DETAILED RESULTS")
        print("="*80)
        
        for category, data in self.results.items():
            print(f"\n{category.upper()}")
            print("-" * 40)
            
            for detail in data['details']:
                status_icon = "[PASS]" if detail['status'] == 'pass' else "[FAIL]"
                severity_icon = "[ERROR]" if detail['severity'] == 'error' else "[WARN]" if detail['severity'] == 'warning' else "[INFO]"
                
                if detail['status'] != 'pass':
                    print(f"  {status_icon} {severity_icon} {detail['check']}: {detail['message']}")
                else:
                    print(f"  {status_icon} {detail['check']}: {detail['message']}")
        
        # Errors and warnings summary
        if self.errors:
            print(f"\nCRITICAL ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  * {error}")
        
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  * {warning}")
        
        # Overall assessment
        print("\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)
        
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                print("[EXCELLENT] Backend implementation is complete and production-ready!")
                print("All critical components are properly implemented.")
            else:
                print("[GOOD] Backend implementation is functional with minor issues.")
                print(f"{len(self.warnings)} warnings should be addressed for optimal performance.")
        else:
            print("[NEEDS ATTENTION] Critical errors found that must be fixed.")
            print(f"{len(self.errors)} errors and {len(self.warnings)} warnings need resolution.")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        if len(self.errors) == 0 and len(self.warnings) == 0:
            print("  * Run comprehensive API tests")
            print("  * Set up monitoring and logging")
            print("  * Configure production environment")
            print("  * Deploy to staging for final testing")
        else:
            print("  * Address all critical errors first")
            print("  * Review and fix warnings")
            print("  * Re-run validation after fixes")
            print("  * Test all functionality thoroughly")
        
        print("\n" + "="*80)
        
        # Save detailed report to file
        report_data = {
            'validation_timestamp': datetime.now().isoformat(),
            'total_checks': self.total_checks,
            'successful_checks': self.success_count,
            'success_rate': round(self.success_count/self.total_checks*100, 1),
            'errors': self.errors,
            'warnings': self.warnings,
            'results': self.results
        }
        
        with open('validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        print("Detailed report saved to: validation_report.json")
        
        return len(self.errors) == 0

    def run_validation(self):
        """Run complete validation suite"""
        print("STARTING COMPREHENSIVE BACKEND VALIDATION")
        print("="*80)
        
        # Run all validation checks
        self.validate_models()
        self.validate_routes()
        self.validate_database_config()
        self.validate_app_configuration()
        self.validate_dependencies()
        self.validate_security()
        self.validate_testing()
        self.validate_documentation()
        
        # Generate and return report
        return self.generate_report()

def main():
    """Main validation function"""
    validator = BackendValidator()
    success = validator.run_validation()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
