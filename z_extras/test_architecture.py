#!/usr/bin/env python3
"""
Test script to validate the OBS-TV-Animator WebSocket architecture
"""

import sys
import os
import json
from pathlib import Path

# Add the project directory to the path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_basic_imports():
    """Test that all required modules can be imported"""
    try:
        from flask import Flask
        from flask_socketio import SocketIO
        import requests
        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'app.py',
        'example_trigger.py', 
        'streamerbot_example.py',
        'requirements.txt',
        'README.md',
        'USAGE.md',
        'animations/anim1.html',
        'animations/anim2.html',
        'animations/anim3.html',
        'animations/smart_tv_websocket_demo.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def test_app_configuration():
    """Test app.py for correct WebSocket configuration"""
    app_file = project_dir / 'app.py'
    
    try:
        with open(app_file, 'r') as f:
            content = f.read()
        
        checks = [
            ('Flask-SocketIO import', 'from flask_socketio import SocketIO'),
            ('SocketIO initialization', 'socketio = SocketIO'),
            ('WebSocket event handlers', '@socketio.on'),
            ('Scene change handler', 'scene_change'),
            ('StreamerBot handler', 'streamerbot_event'),
            ('SocketIO run', 'socketio.run')
        ]
        
        for check_name, check_string in checks:
            if check_string in content:
                print(f"✓ {check_name}")
            else:
                print(f"✗ {check_name} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading app.py: {e}")
        return False

def test_requirements():
    """Test that requirements.txt includes WebSocket dependencies"""
    req_file = project_dir / 'requirements.txt'
    
    try:
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        required_packages = [
            'Flask',
            'Flask-SocketIO', 
            'python-socketio',
            'requests'
        ]
        
        for package in required_packages:
            if package in requirements:
                print(f"✓ {package} dependency")
            else:
                print(f"✗ {package} dependency missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def test_documentation_updates():
    """Test that documentation has been updated for WebSocket architecture"""
    readme_file = project_dir / 'README.md'
    usage_file = project_dir / 'USAGE.md'
    
    try:
        # Check README
        with open(readme_file, 'r') as f:
            readme_content = f.read()
        
        if 'browser source' in readme_content.lower() and 'Method 1: Browser Source' in readme_content:
            print("✗ README still contains browser source references")
            return False
        
        websocket_terms = ['WebSocket', 'StreamerBot', 'socket.io']
        if any(term in readme_content for term in websocket_terms):
            print("✓ README updated with WebSocket architecture")
        else:
            print("✗ README missing WebSocket references")
            return False
            
        # Check USAGE
        with open(usage_file, 'r') as f:
            usage_content = f.read()
            
        if 'WebSocket' in usage_content and 'StreamerBot' in usage_content:
            print("✓ USAGE.md updated with new architecture")
        else:
            print("✗ USAGE.md missing WebSocket documentation")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading documentation: {e}")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("=" * 60)
    print("OBS-TV-Animator Architecture Validation")
    print("=" * 60)
    
    tests = [
        test_basic_imports,
        test_file_structure, 
        test_app_configuration,
        test_requirements,
        test_documentation_updates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        else:
            print("❌ Test failed")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Architecture is ready for WebSocket deployment.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start server: python app.py") 
        print("3. Point TV browser to: http://YOUR_IP:8080")
        print("4. Connect OBS/StreamerBot to: ws://YOUR_IP:8080/socket.io/")
    else:
        print("❌ Some tests failed. Please fix issues before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)