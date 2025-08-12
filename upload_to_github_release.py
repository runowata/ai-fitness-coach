#!/usr/bin/env python3
"""
Upload bootstrap archive to GitHub Releases (easier than R2)
"""
import os
import sys
import subprocess
import json

def create_github_release():
    """Create GitHub release with bootstrap archive"""
    
    print("🚀 GitHub Release Upload for Bootstrap Archive")
    print("=" * 60)
    
    # Check if archive exists
    archive_path = "workouts_bootstrap_v2.tar.gz"
    if not os.path.exists(archive_path):
        print(f"❌ Archive not found: {archive_path}")
        return False
    
    print(f"📦 Archive: {archive_path} ({os.path.getsize(archive_path):,} bytes)")
    print(f"🔒 SHA256: 89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
    print()
    
    # Check if gh CLI is available
    try:
        result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
        print(f"✅ GitHub CLI found: {result.stdout.strip().split()[2]}")
    except FileNotFoundError:
        print("❌ GitHub CLI not found. Install from: https://cli.github.com/")
        return False
    
    # Check if logged in
    try:
        result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Not logged in to GitHub CLI. Run: gh auth login")
            return False
        print("✅ GitHub CLI authenticated")
    except:
        print("❌ GitHub auth check failed")
        return False
    
    release_tag = "bootstrap-v2.0.0"
    release_title = "Bootstrap Data v2.0.0"
    release_notes = f"""# Workout Bootstrap Data v2.0.0

**📦 Archive**: `workouts_bootstrap_v2.tar.gz`  
**🔒 SHA256**: `89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38`  
**📅 Date**: 2025-08-08

## Contents
- Exercise database (147 exercises)
- Video metadata for R2 organization  
- Archetype-specific content mapping

## Usage in Production
Set these environment variables in Render:

```bash
BOOTSTRAP_DATA_URL=https://github.com/runowata/ai-fitness-coach/releases/download/{release_tag}/workouts_bootstrap_v2.tar.gz
BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38
BOOTSTRAP_DATA_VERSION=v2-2025-08-08
```

Then run Manual Deploy - the system will auto-download and import data.
"""
    
    print(f"🏷️  Creating release: {release_tag}")
    
    try:
        # Create release
        cmd = [
            'gh', 'release', 'create', release_tag,
            archive_path,
            '--title', release_title,
            '--notes', release_notes,
            '--latest'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print("✅ Release created successfully!")
            
            # Get the download URL
            download_url = f"https://github.com/runowata/ai-fitness-coach/releases/download/{release_tag}/workouts_bootstrap_v2.tar.gz"
            
            print("\n" + "=" * 70)
            print("📋 RENDER ENVIRONMENT VARIABLES:")
            print("=" * 70)
            print(f"BOOTSTRAP_DATA_URL={download_url}")
            print(f"BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
            print(f"BOOTSTRAP_DATA_VERSION=v2-2025-08-08")
            print("=" * 70)
            print(f"\n🔗 Release URL: https://github.com/runowata/ai-fitness-coach/releases/tag/{release_tag}")
            print(f"📥 Download URL: {download_url}")
            print("\n🎯 Next steps:")
            print("1. Copy the environment variables above to Render")
            print("2. Run Manual Deploy in Render") 
            print("3. The system will auto-download and import data")
            
            return True
        else:
            print(f"❌ Failed to create release:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_github_release()
    sys.exit(0 if success else 1)