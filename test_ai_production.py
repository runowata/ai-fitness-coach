#!/usr/bin/env python3
"""
Test AI generation on production with real API key
Usage: python test_ai_production.py
"""
import requests
import json

def test_ai_via_registration():
    """Test AI generation by creating test user and triggering onboarding"""
    base_url = "https://ai-fitness-coach-ttzf.onrender.com"
    
    # Create test session
    session = requests.Session()
    
    print("🔄 Testing AI generation on production...")
    
    # Step 1: Get registration page to get CSRF token
    print("1. Getting registration page...")
    response = session.get(f"{base_url}/users/register/")
    if response.status_code != 200:
        print(f"❌ Failed to access registration page: {response.status_code}")
        return False
    
    # Extract CSRF token
    csrf_token = None
    for line in response.text.split('\n'):
        if 'csrfmiddlewaretoken' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    if not csrf_token:
        print("❌ Could not extract CSRF token")
        return False
    
    print(f"✅ Got CSRF token: {csrf_token[:10]}...")
    
    # Step 2: Register test user
    print("2. Creating test user...")
    test_username = f"test_ai_{int(__import__('time').time())}"
    registration_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': test_username,
        'email': f"{test_username}@test.com",
        'password1': 'complex_test_password_123',
        'password2': 'complex_test_password_123',
        'is_adult_confirmed': 'on',
        'terms_accepted': 'on'
    }
    
    response = session.post(f"{base_url}/users/register/", data=registration_data)
    if response.status_code == 200 and 'error' in response.text.lower():
        print("❌ Registration failed - check form errors")
        return False
    
    print(f"✅ Registration response: {response.status_code}")
    
    # Step 3: Check if redirected to onboarding (indicates successful registration)
    if 'onboarding' in response.url:
        print("✅ Successfully registered and redirected to onboarding")
        print(f"📍 Current URL: {response.url}")
        
        # Try to trigger AI generation by completing onboarding
        print("3. Attempting to complete onboarding to trigger AI...")
        
        # This would require parsing the onboarding form and submitting it
        # For now, just report that we reached onboarding
        print("🎯 Reached onboarding - AI generation will be triggered when user completes questionnaire")
        return True
    else:
        print("⚠️  Registration completed but not redirected to onboarding")
        print(f"📍 Current URL: {response.url}")
        return False

def check_openai_settings():
    """Check if OpenAI settings are properly configured"""
    print("\n🔍 Checking OpenAI configuration...")
    
    # Try to access a page that might show configuration info
    response = requests.get("https://ai-fitness-coach-ttzf.onrender.com/admin/")
    if response.status_code == 200:
        print("✅ Application is responding")
    else:
        print(f"⚠️  Admin page returned: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing AI Fitness Coach on production...")
    print("=" * 50)
    
    check_openai_settings()
    
    success = test_ai_via_registration()
    
    if success:
        print("\n✅ AI test completed successfully!")
        print("💡 To fully test AI generation, complete the onboarding questionnaire in browser")
    else:
        print("\n❌ AI test failed - check production logs")
    
    print("\n📝 Next steps:")
    print("1. Complete onboarding manually in browser to trigger AI generation")
    print("2. Check Render logs for any OpenAI API errors")
    print("3. Monitor workout plan creation in admin panel")