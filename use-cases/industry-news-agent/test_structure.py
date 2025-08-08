#!/usr/bin/env python3
"""
Test script to verify the new project structure works correctly.
"""
import sys
from pathlib import Path

def test_project_structure():
    """Test that all files and directories exist in the new structure."""
    print("🧪 Testing new project structure...")
    
    base_dir = Path(__file__).parent
    
    # Test directories
    required_dirs = [
        base_dir / "html",
        base_dir / "html" / "css",
        base_dir / "html" / "js",
        base_dir / "html" / "images",
    ]
    
    # Test files
    required_files = [
        base_dir / "html" / "index.html",
        base_dir / "html" / "css" / "style.css",
        base_dir / "html" / "js" / "app.js",
        base_dir / "src" / "web_interface.py",
    ]
    
    print("📁 Checking directories...")
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"  ✅ {dir_path.relative_to(base_dir)}")
        else:
            print(f"  ❌ {dir_path.relative_to(base_dir)} - MISSING")
    
    print("\n📄 Checking files...")
    for file_path in required_files:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✅ {file_path.relative_to(base_dir)} ({size} bytes)")
        else:
            print(f"  ❌ {file_path.relative_to(base_dir)} - MISSING")
    
    # Test HTML content
    html_file = base_dir / "html" / "index.html"
    if html_file.exists():
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        print(f"\n🔍 Testing HTML content...")
        checks = [
            ('CSS link', '<link rel="stylesheet" href="/static/css/style.css">'),
            ('JS script', '<script src="/static/js/app.js">'),
            ('Form element', '<form id="reportForm"'),
            ('Submit button', '<button type="submit">'),
        ]
        
        for check_name, check_pattern in checks:
            if check_pattern in html_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MISSING")
    
    # Test CSS content
    css_file = base_dir / "html" / "css" / "style.css"
    if css_file.exists():
        with open(css_file, 'r') as f:
            css_content = f.read()
        
        print(f"\n🎨 Testing CSS content...")
        css_checks = [
            ('Container style', '.container {'),
            ('Button style', 'button {'),
            ('Loading spinner', '.loading-spinner {'),
        ]
        
        for check_name, check_pattern in css_checks:
            if check_pattern in css_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MISSING")
    
    # Test JS content
    js_file = base_dir / "html" / "js" / "app.js"
    if js_file.exists():
        with open(js_file, 'r') as f:
            js_content = f.read()
        
        print(f"\n⚡ Testing JavaScript content...")
        js_checks = [
            ('handleSubmit function', 'async function handleSubmit(event)'),
            ('checkStatus function', 'async function checkStatus(taskId)'),
            ('Form submit handler', 'form.addEventListener(\'submit\', handleSubmit)'),
        ]
        
        for check_name, check_pattern in js_checks:
            if check_pattern in js_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MISSING")
    
    print(f"\n🎉 Project structure test completed!")
    
    # Test import (basic syntax check)
    print(f"\n🐍 Testing Python imports...")
    try:
        sys.path.insert(0, str(base_dir / "src"))
        from web_interface import app
        print("  ✅ web_interface.py imports successfully")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        if "/" in routes:
            print("  ✅ Home route (/) exists")
        else:
            print("  ❌ Home route (/) missing")
            
        if any("/api/" in route for route in routes):
            print("  ✅ API routes exist")
        else:
            print("  ❌ API routes missing")
            
    except Exception as e:
        print(f"  ❌ Import failed: {e}")

if __name__ == "__main__":
    test_project_structure()