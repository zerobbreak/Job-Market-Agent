#!/usr/bin/env python3
"""
CareerBoost AI - Quick Launch Script
====================================

Simple launcher for CareerBoost AI with common configurations.

Usage:
    python run.py                # Interactive mode
    python run.py demo          # Automated demonstration
    python run.py web           # Web server mode
    python run.py --help        # Show help
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if required files exist"""
    required_files = [
        'main.py',
        'requirements.txt',
        '.env'
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print("❌ Missing required files:")
        for file in missing:
            print(f"   • {file}")
        print("\nPlease ensure all required files are present.")
        return False

    return True

def run_command(args):
    """Run main.py with specified arguments"""
    cmd = [sys.executable, 'main.py'] + args
    print(f"🚀 Running: {' '.join(cmd)}")
    print("="*60)

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Operation cancelled by user.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)

def show_help():
    """Show help information"""
    print(__doc__)

def main():
    if len(sys.argv) < 2:
        # Default: Interactive mode
        if not check_requirements():
            sys.exit(1)
        run_command(['--interactive'])
    else:
        command = sys.argv[1].lower()

        if command in ['help', '--help', '-h']:
            show_help()

        elif command == 'interactive':
            if not check_requirements():
                sys.exit(1)
            run_command(['--interactive'])

        elif command == 'demo':
            if not check_requirements():
                sys.exit(1)
            run_command(['--demo'])

        elif command == 'web':
            port = sys.argv[2] if len(sys.argv) > 2 else '8000'
            if not check_requirements():
                sys.exit(1)
            run_command(['--web-server', '--port', port])

        elif command == 'platform':
            # Platform mode with additional args
            args = ['--platform'] + sys.argv[2:]
            if not check_requirements():
                sys.exit(1)
            run_command(args)

        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  (no args)    - Interactive mode")
            print("  interactive  - Interactive mode")
            print("  demo         - Automated demonstration")
            print("  web [port]   - Web server mode (default port 8000)")
            print("  platform     - Platform mode (pass additional args)")
            print("  help         - Show this help")
            sys.exit(1)

if __name__ == '__main__':
    main()
