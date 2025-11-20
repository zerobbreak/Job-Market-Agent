#!/usr/bin/env python3
"""
Test runner for Job Market AI agents

This script provides a convenient way to run all tests for the AI agents.
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests using pytest"""
    print("🚀 Running Job Market AI Agent Tests")
    print("=" * 50)

    # Change to the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest:")
        print("   pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_specific_test(test_file):
    """Run a specific test file"""
    print(f"🎯 Running specific test: {test_file}")
    print("=" * 50)

    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    try:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

def list_available_tests():
    """List all available test files"""
    print("📋 Available Test Files:")
    print("=" * 30)

    tests_dir = "tests"
    if os.path.exists(tests_dir):
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        for test_file in sorted(test_files):
            agent_name = test_file.replace("test_", "").replace("_agent.py", "").replace(".py", "")
            print(f"  • {test_file} ({agent_name})")
    else:
        print("  No tests directory found")

def show_usage():
    """Show usage information"""
    print("Usage:")
    print("  python run_tests.py                    # Run all tests")
    print("  python run_tests.py <test_file>        # Run specific test file")
    print("  python run_tests.py --list             # List available test files")
    print("  python run_tests.py --help             # Show this help")
    print()
    print("Examples:")
    print("  python run_tests.py test_profile_agent.py")
    print("  python run_tests.py test_job_matcher_agent.py")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            show_usage()
        elif sys.argv[1] == "--list":
            list_available_tests()
        else:
            test_file = sys.argv[1]
            if not test_file.startswith("test_"):
                test_file = f"test_{test_file}"
            if not test_file.endswith(".py"):
                test_file = f"{test_file}.py"

            success = run_specific_test(test_file)
            sys.exit(0 if success else 1)
    else:
        success = run_tests()
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
        sys.exit(0 if success else 1)
