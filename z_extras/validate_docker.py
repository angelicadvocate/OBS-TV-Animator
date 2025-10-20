#!/usr/bin/env python3
"""
Docker Configuration Validator for OBS-TV-Animator
Validates Docker setup without requiring Docker to be running.
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a required file exists"""
    if Path(file_path).exists():
        print(f"✓ {description}: {file_path}")
        return True
    else:
        print(f"✗ {description} missing: {file_path}")
        return False

def validate_dockerfile():
    """Validate Dockerfile configuration"""
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("✗ Dockerfile not found")
        return False
    
    with open(dockerfile_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("Python base image", "FROM python:3.11-slim"),
        ("Port exposure", "EXPOSE 8080"),
        ("Working directory", "WORKDIR /app"),
        ("Requirements copy", "COPY requirements.txt"),
        ("Dependencies install", "pip install"),
        ("Application copy", "COPY . ."),
        ("Non-root user", "useradd -r"),
        ("Health check", "HEALTHCHECK"),
        ("Entrypoint script", "ENTRYPOINT"),
        ("CMD directive", "CMD")
    ]
    
    passed = 0
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✓ {check_name}")
            passed += 1
        else:
            print(f"✗ {check_name} missing")
    
    return passed == len(checks)

def validate_docker_compose():
    """Validate docker-compose.yml configuration"""
    compose_path = Path("docker-compose.yml")
    if not compose_path.exists():
        print("✗ docker-compose.yml not found")
        return False
    
    with open(compose_path, 'r') as f:
        content = f.read()
    
    checks = [
        ("Version specified", "version:"),
        ("Services defined", "services:"),
        ("Port mapping", "8080:8080"),
        ("Volume mounts", "volumes:"),
        ("Animations volume", "./animations:/app/animations"),
        ("Videos volume", "./videos:/app/videos"),
        ("Data volume", "./data:/app/data"),
        ("Health check", "healthcheck:"),
        ("Network config", "networks:")
    ]
    
    passed = 0
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✓ {check_name}")
            passed += 1
        else:
            print(f"✗ {check_name} missing")
    
    return passed == len(checks)

def validate_directory_structure():
    """Validate required directory structure"""
    required_files = [
        ("Application", "app.py"),
        ("Requirements", "requirements.txt"),
        ("Docker entrypoint", "docker-entrypoint.sh"),
        ("Docker ignore", ".dockerignore"),
        ("Environment example", ".env.example"),
        ("Video player template", "templates/video_player_template.html"),
        ("Example trigger", "example_trigger.py"),
        ("StreamerBot example", "streamerbot_example.py")
    ]
    
    required_dirs = [
        ("Animations directory", "animations"),
        ("Videos directory", "videos"),
        ("Data directory", "data")
    ]
    
    all_good = True
    
    for description, file_path in required_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    for description, dir_path in required_dirs:
        dir_obj = Path(dir_path)
        if dir_obj.exists() and dir_obj.is_dir():
            print(f"✓ {description}: {dir_path}")
        else:
            print(f"✗ {description} missing: {dir_path}")
            all_good = False
    
    return all_good

def validate_entrypoint_script():
    """Validate entrypoint script"""
    script_path = Path("docker-entrypoint.sh")
    if not script_path.exists():
        print("✗ docker-entrypoint.sh not found")
        return False
    
    # Check if script is executable (Unix-like systems)
    if hasattr(os, 'access') and os.access(script_path, os.X_OK):
        print("✓ Entrypoint script is executable")
    else:
        print("⚠ Entrypoint script may not be executable (check on Unix systems)")
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    if '#!/bin/bash' in content and 'exec "$@"' in content:
        print("✓ Entrypoint script format valid")
        return True
    else:
        print("✗ Entrypoint script format invalid")
        return False

def check_requirements():
    """Check if requirements.txt includes all necessary dependencies"""
    req_path = Path("requirements.txt")
    if not req_path.exists():
        print("✗ requirements.txt not found")
        return False
    
    with open(req_path, 'r') as f:
        requirements = f.read()
    
    required_packages = [
        'Flask',
        'Flask-SocketIO',
        'python-socketio',
        'requests'
    ]
    
    passed = 0
    for package in required_packages:
        if package in requirements:
            print(f"✓ {package} dependency")
            passed += 1
        else:
            print(f"✗ {package} dependency missing")
    
    return passed == len(required_packages)

def main():
    """Main validation function"""
    print("=" * 70)
    print("OBS-TV-Animator Docker Configuration Validator")
    print("=" * 70)
    
    tests = [
        ("Directory Structure", validate_directory_structure),
        ("Dockerfile Configuration", validate_dockerfile),
        ("Docker Compose Configuration", validate_docker_compose),
        ("Requirements Dependencies", check_requirements),
        ("Entrypoint Script", validate_entrypoint_script)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        if test_func():
            passed += 1
            print(f"✓ {test_name} validation passed")
        else:
            print(f"✗ {test_name} validation failed")
    
    print("\n" + "=" * 70)
    print(f"Docker Configuration Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Docker configurations are valid!")
        print("\nReady for deployment:")
        print("1. Start Docker Desktop")
        print("2. Run: docker-compose up -d")
        print("3. Access: http://localhost:8080")
        print("4. Connect TV: http://[YOUR_IP]:8080")
        print("5. WebSocket: ws://[YOUR_IP]:8080/socket.io/")
    else:
        print("❌ Some configurations need fixing before Docker deployment.")
        print("Please resolve the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)