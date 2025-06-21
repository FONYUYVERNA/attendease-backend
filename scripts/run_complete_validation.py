#!/usr/bin/env python3
"""
Complete Validation Suite for AttendEase Backend
Runs all validation checks and generates comprehensive report
"""

import os
import sys
import subprocess
from datetime import datetime

def main():
    """Main validation function"""
    print("🚀 ATTENDEASE BACKEND - COMPLETE VALIDATION SUITE")
    print("="*80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Change to project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up one level from scripts/
    
    print(f"📁 Script directory: {script_dir}")
    print(f"📁 Project root: {project_root}")
    
    # Change to project root
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📂 Contents: {', '.join(os.listdir('.'))}")
    
    try:
        validation_results = []
        
        # 1. Backend Component Validation
        print(f"\n🔄 Running Backend Component Validation...")
        print("="*60)
        try:
            result = subprocess.run([
                sys.executable, 'scripts/comprehensive_validation.py'
            ], capture_output=True, text=True, cwd=project_root)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            validation_results.append({
                'name': 'Backend Component Validation',
                'success': result.returncode == 0,
                'output': result.stdout
            })
            
        except Exception as e:
            print(f"❌ Error running backend validation: {e}")
            validation_results.append({
                'name': 'Backend Component Validation',
                'success': False,
                'error': str(e)
            })
        
        # 2. API Endpoint Validation
        print(f"\n🔄 Running API Endpoint Validation...")
        print("="*60)
        try:
            result = subprocess.run([
                sys.executable, 'scripts/api_endpoint_validator.py'
            ], capture_output=True, text=True, cwd=project_root)
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            validation_results.append({
                'name': 'API Endpoint Validation',
                'success': result.returncode == 0,
                'output': result.stdout
            })
            
        except Exception as e:
            print(f"❌ Error running API validation: {e}")
            validation_results.append({
                'name': 'API Endpoint Validation',
                'success': False,
                'error': str(e)
            })
        
        # Generate summary report
        print("\n" + "="*80)
        print("📋 COMPLETE VALIDATION SUMMARY")
        print("="*80)
        
        successful_validations = sum(1 for r in validation_results if r['success'])
        total_validations = len(validation_results)
        success_rate = (successful_validations / total_validations * 100) if total_validations > 0 else 0
        
        print(f"Total validations: {total_validations}")
        print(f"Successful validations: {successful_validations}")
        print(f"Success rate: {success_rate:.1f}%")
        
        print(f"\n📊 VALIDATION RESULTS:")
        for result in validation_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['name']}")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if successful_validations == total_validations:
            print("🎉 EXCELLENT: All validations passed! Backend is ready for production.")
        elif success_rate >= 50:
            print("✅ GOOD: Most validations passed. Address remaining issues.")
        else:
            print("❌ NEEDS ATTENTION: Critical issues found that must be resolved.")
        
        print(f"\n📝 NEXT STEPS:")
        if successful_validations == total_validations:
            print("  • Deploy to staging environment")
            print("  • Run integration tests")
            print("  • Set up monitoring and logging")
        else:
            print("  • Review and fix all validation failures")
            print("  • Check server configuration")
            print("  • Verify all dependencies are installed")
            print("  • Re-run complete validation")
        
        print(f"\nValidation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        return successful_validations == total_validations
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
