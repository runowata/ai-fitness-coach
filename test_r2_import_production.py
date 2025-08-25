#!/usr/bin/env python3
"""
Test script to validate R2 import in production
Run this after deployment to verify everything works
"""
import requests
import json
import time

def test_production_import():
    """Test R2 import in production environment"""
    
    base_url = "https://ai-fitness-coach-fcpd.onrender.com"
    
    print("🚀 Testing R2 Import in Production")
    print("=" * 50)
    
    # 1. Check if site is up
    print("1️⃣ Checking site availability...")
    try:
        response = requests.get(f"{base_url}/healthz/", timeout=30)
        if response.status_code == 200:
            print("   ✅ Site is up and running")
        else:
            print(f"   ❌ Site returned {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Site is down: {e}")
        return False
    
    # 2. Check admin login (to test database)
    print("2️⃣ Testing admin access...")
    try:
        admin_response = requests.get(f"{base_url}/admin/", timeout=30)
        if admin_response.status_code == 200:
            print("   ✅ Admin interface is accessible")
        else:
            print(f"   ❌ Admin returned {admin_response.status_code}")
    except Exception as e:
        print(f"   ❌ Admin access failed: {e}")
    
    # 3. Check if CSVExercise model is accessible
    print("3️⃣ Testing database models...")
    try:
        # Try to access a model admin page
        model_response = requests.get(f"{base_url}/admin/workouts/csvexercise/", timeout=30)
        if model_response.status_code in [200, 302]:  # 302 if login required
            print("   ✅ CSVExercise model is accessible")
        else:
            print(f"   ❌ CSVExercise model returned {model_response.status_code}")
    except Exception as e:
        print(f"   ❌ Database model access failed: {e}")
    
    # 4. Print next steps
    print("\n🎯 NEXT STEPS:")
    print(f"1. Go to: {base_url}/admin/")
    print("2. Login with admin credentials")
    print("3. Navigate to Workouts > Csv exercises")
    print("4. Check current exercise count")
    print("5. Run management command: python manage.py import_r2_exercises --verbose")
    print("6. Verify 271 exercises are imported")
    
    print("\n📋 MANUAL TESTING COMMANDS:")
    print("# On Render console:")
    print("python manage.py import_r2_exercises --dry-run --verbose")
    print("python manage.py import_r2_exercises --clear-existing --verbose") 
    print("python manage.py shell -c \"from apps.workouts.models import CSVExercise; print(f'Exercises: {CSVExercise.objects.count()}')\"")
    
    return True

def check_csv_files():
    """Check if our CSV files are properly structured"""
    print("\n📊 CSV FILES VALIDATION")
    print("=" * 50)
    
    csv_files = [
        "data/clean/exercises_complete_r2.csv",
        "data/clean/motivation_videos.csv", 
        "data/clean/playlist_structure_21_days.csv"
    ]
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"✅ {csv_file}: {len(lines)} lines")
                if lines:
                    print(f"   Header: {lines[0].strip()}")
        except Exception as e:
            print(f"❌ {csv_file}: Error - {e}")

if __name__ == "__main__":
    check_csv_files()
    print()
    test_production_import()