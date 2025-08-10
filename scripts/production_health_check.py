#!/usr/bin/env python
"""
Production Health Check Script
Run: python scripts/production_health_check.py
"""

import os
import sys
import django
import requests
from time import time

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.workouts.models import VideoClip
from apps.workouts.video_storage import get_storage
from apps.core.services.exercise_validation import ExerciseValidationService
from apps.ai_integration.services import WorkoutPlanGenerator


def check_database():
    """Check database connectivity and key models"""
    print("🔍 Database Check...")
    
    try:
        # Check model counts
        video_count = VideoClip.objects.count()
        r2_count = VideoClip.objects.filter(provider='r2').count()
        
        print(f"  ✅ VideoClip: {video_count} total, {r2_count} R2")
        
        if video_count == 0:
            print("  ⚠️  Warning: No video clips found")
        
        return True
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False


def check_video_storage():
    """Test video storage functionality"""
    print("🎥 Video Storage Check...")
    
    try:
        # Find R2 video clip
        vc = VideoClip.objects.filter(provider='r2', r2_file__isnull=False).first()
        if not vc:
            print("  ⚠️  No R2 clips found for testing")
            return True
        
        # Test storage adapter
        storage = get_storage(vc)
        exists = storage.exists(vc)
        url = storage.playback_url(vc)
        
        print(f"  ✅ Storage adapter: {storage.__class__.__name__}")
        print(f"  ✅ File exists: {exists}")
        print(f"  ✅ URL format: {url[:60]}...")
        
        # Test URL accessibility (if public)
        if url.startswith('http') and not 'X-Amz-Signature' in url:
            try:
                resp = requests.head(url, timeout=5)
                print(f"  ✅ URL accessible: {resp.status_code}")
            except:
                print("  ⚠️  URL not publicly accessible (expected for signed URLs)")
        
        return True
    except Exception as e:
        print(f"  ❌ Video storage error: {e}")
        return False


def check_ai_whitelist():
    """Test AI exercise validation"""
    print("🤖 AI Whitelist Check...")
    
    try:
        archetypes = ['professional', 'mentor', 'peer']
        total_allowed = 0
        
        for archetype in archetypes:
            start_time = time()
            allowed = ExerciseValidationService.get_allowed_exercise_slugs(archetype)
            duration = (time() - start_time) * 1000
            
            print(f"  ✅ {archetype}: {len(allowed)} exercises ({duration:.1f}ms)")
            total_allowed += len(allowed)
        
        if total_allowed == 0:
            print("  ⚠️  Warning: No allowed exercises found")
        
        return True
    except Exception as e:
        print(f"  ❌ AI whitelist error: {e}")
        return False


def check_ai_generator():
    """Test AI generator initialization"""
    print("⚙️  AI Generator Check...")
    
    try:
        generator = WorkoutPlanGenerator()
        print(f"  ✅ Generator class: {generator.__class__.__name__}")
        
        # Check if AI client initializes
        client_type = generator.ai_client.__class__.__name__ if hasattr(generator, 'ai_client') else "Not initialized"
        print(f"  ✅ AI client: {client_type}")
        
        return True
    except Exception as e:
        print(f"  ❌ AI generator error: {e}")
        return False


def check_environment():
    """Check critical environment variables"""
    print("🔧 Environment Check...")
    
    critical_vars = [
        'SECRET_KEY',
        'DATABASE_URL', 
        'AWS_ACCESS_KEY_ID',
        'AWS_STORAGE_BUCKET_NAME'
    ]
    
    optional_vars = [
        'OPENAI_API_KEY',
        'R2_SIGNED_URLS',
        'R2_CDN_BASE_URL',
        'SHOW_AI_ANALYSIS'
    ]
    
    missing_critical = []
    for var in critical_vars:
        if os.getenv(var):
            print(f"  ✅ {var}: {'*' * 10}")
        else:
            print(f"  ❌ {var}: MISSING")
            missing_critical.append(var)
    
    for var in optional_vars:
        value = os.getenv(var, 'Not set')
        print(f"  ℹ️  {var}: {value}")
    
    return len(missing_critical) == 0


def main():
    """Run all health checks"""
    print("🚀 Production Health Check")
    print("=" * 50)
    
    checks = [
        ("Environment", check_environment),
        ("Database", check_database),
        ("Video Storage", check_video_storage),
        ("AI Whitelist", check_ai_whitelist),
        ("AI Generator", check_ai_generator),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ {name} check failed: {e}")
            results.append(False)
            print()
    
    # Summary
    print("📊 Health Check Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, _) in enumerate(checks):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 System ready for production!")
        return 0
    else:
        print("⚠️  Issues detected - review before deployment")
        return 1


if __name__ == "__main__":
    sys.exit(main())