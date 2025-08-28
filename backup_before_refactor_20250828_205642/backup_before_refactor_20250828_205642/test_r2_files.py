#!/usr/bin/env python
"""Quick test script to check R2 files availability"""

import requests
import sys

R2_BASE = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"

# Test files we're looking for
test_files = [
    # Avatar files
    "images/avatars/peer_avatar_1.jpg",
    "images/avatars/professional_avatar_1.jpg", 
    "images/avatars/mentor_avatar_1.jpg",
    "images/avatars/peer.png",
    "images/avatars/professional.png",
    "images/avatars/mentor.png",
    
    # Card backgrounds
    "images/cards/card_motivation_1.jpg",
    "images/cards/card_motivation_2.jpg",
    "images/cards/card_motivation_3.jpg",
    "images/cards/bg01.jpg",
    "images/cards/bg02.jpg", 
    "images/cards/bg03.jpg",
    
    # Alternative paths
    "avatars/peer_avatar_1.jpg",
    "avatars/professional_avatar_1.jpg", 
    "avatars/mentor_avatar_1.jpg",
]

print(f"Testing R2 bucket: {R2_BASE}")
print("=" * 60)

available = []
missing = []

for file_path in test_files:
    url = f"{R2_BASE}/{file_path}"
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            size = response.headers.get('content-length', 'unknown')
            print(f"✅ {file_path} (size: {size} bytes)")
            available.append(file_path)
        elif response.status_code == 404:
            print(f"❌ {file_path} (404 Not Found)")
            missing.append(file_path)
        else:
            print(f"❓ {file_path} (HTTP {response.status_code})")
            missing.append(file_path)
    except Exception as e:
        print(f"❌ {file_path} (Error: {e})")
        missing.append(file_path)

print("\n" + "=" * 60)
print(f"Summary: {len(available)} available, {len(missing)} missing")

if available:
    print("\n✅ Available files - ready for seeding:")
    for f in available:
        print(f"  - {f}")
        
if len(available) >= 6:  # At least some avatars and cards
    print("\n🚀 Good to go! Run: python manage.py seed_media_assets")
else:
    print("\n⚠️  Need to upload more files to R2 bucket first")