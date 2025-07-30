"""
Test runner script for ScannerProxy unit tests.
Provides easy execution of tests with coverage reporting.
"""
import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Run all unit tests with coverage reporting"""
    print("🧪 Running ScannerProxy Unit Tests")
    print("=" * 50)
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Command to run tests with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit/",
        "--cov=src",
        "--cov-report=html:coverage_html",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=90",
        "-v",
        "--tb=short"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed with 90%+ coverage!")
            print("📊 Coverage report generated in: coverage_html/index.html")
        else:
            print("\n❌ Some tests failed or coverage is below 90%")
            
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def run_specific_test(test_path):
    """Run a specific test file or test function"""
    print(f"🧪 Running specific test: {test_path}")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1


def check_coverage():
    """Check current test coverage without running tests"""
    print("📊 Checking current test coverage")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "coverage",
        "report",
        "--show-missing"
    ]
    
    try:
        result = subprocess.run(cmd, check=False, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Error checking coverage: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "coverage":
            exit_code = check_coverage()
        else:
            # Run specific test
            exit_code = run_specific_test(sys.argv[1])
    else:
        # Run all tests
        exit_code = run_tests()
    
    sys.exit(exit_code)
