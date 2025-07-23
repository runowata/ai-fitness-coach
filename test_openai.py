#!/usr/bin/env python3
"""
Quick smoke test for OpenAI integration
Usage: python test_openai.py
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from openai import OpenAI, AuthenticationError
from django.conf import settings

def test_openai_connection():
    """Test basic OpenAI connection and API key"""
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        print("🔄 Testing OpenAI connection...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0
        )
        
        print("✅ OpenAI connection successful!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except AuthenticationError:
        print("❌ Authentication failed - check OPENAI_API_KEY")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    print(f"🔑 API Key length: {len(settings.OPENAI_API_KEY)} chars")
    print(f"🤖 Model: {settings.OPENAI_MODEL}")
    
    success = test_openai_connection()
    sys.exit(0 if success else 1)