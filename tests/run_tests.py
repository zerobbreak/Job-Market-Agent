#!/usr/bin/env python3
"""
Simple test runner for the main application tests.
"""
import sys
import os
import subprocess

def run_tests():
    """Run all tests in the tests directory."""
    # Change to the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("🚀 Running Agno Application Tests")
    print("=" * 50)

    # Run pytest on the tests directory
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], capture_output=False)

        return result.returncode == 0

    except FileNotFoundError:
        print("❌ pytest not found. Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"])

        # Try again
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v",
            "--tb=short",
            "--color=yes"
        ], capture_output=False)

        return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
