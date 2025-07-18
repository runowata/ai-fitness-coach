#!/usr/bin/env python3
"""
Script to restore production data via HTTP requests to Django management commands
This script calls a special endpoint that executes the restore_data command
"""

import requests
import json
import time

def restore_data():
    """Restore production data by calling Django management command endpoint"""
    
    base_url = "https://ai-fitness-coach-ttzf.onrender.com"
    
    print("🔄 Starting production data restoration...")
    print(f"📡 Target: {base_url}")
    
    # Check if service is healthy
    print("\n1. Checking service health...")
    try:
        response = requests.get(f"{base_url}/health/", timeout=30)
        if response.status_code == 200:
            print("✅ Service is healthy")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False
    
    # Note: We cannot directly execute management commands via HTTP for security reasons
    # The user needs to run the command via Render Shell
    
    print("\n📋 Commands to run in Render Shell:")
    print("=" * 50)
    print("1. Go to Render Dashboard → AI Fitness Coach → Shell")
    print("2. Run: cd /opt/render/project/src")
    print("3. Run: python manage.py restore_data")
    print("4. Run: du -sh /opt/render/project/src/media/videos")
    print("5. Run: python manage.py collectstatic --noinput")
    print("=" * 50)
    
    print("\n⚠️  Security Note:")
    print("Django management commands cannot be executed via HTTP requests")
    print("for security reasons. Please use Render Shell interface.")
    
    return True

if __name__ == "__main__":
    restore_data()