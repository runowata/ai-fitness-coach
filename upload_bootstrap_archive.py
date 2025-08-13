#!/usr/bin/env python3
"""
Upload bootstrap archive to R2 with public access
"""
import os

import boto3
from botocore.config import Config

# R2 credentials and config
AWS_ACCESS_KEY_ID = input("Enter R2 AWS_ACCESS_KEY_ID: ").strip()
AWS_SECRET_ACCESS_KEY = input("Enter R2 AWS_SECRET_ACCESS_KEY: ").strip()
R2_ENDPOINT_URL = input("Enter R2_ENDPOINT_URL (e.g., https://xxxxx.r2.cloudflarestorage.com): ").strip()
R2_BUCKET_NAME = input("Enter R2_BUCKET_NAME: ").strip()
R2_PUBLIC_BASE = input("Enter R2_PUBLIC_BASE (e.g., https://pub-xxxxx.r2.dev): ").strip()

# Configure R2 client
r2_client = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(
        region_name='auto',
        retries={'max_attempts': 3}
    )
)

def upload_archive():
    """Upload the bootstrap archive to R2"""
    archive_path = "workouts_bootstrap_v2.tar.gz"
    key = "bootstrap/workouts_bootstrap_v2.tar.gz"
    
    if not os.path.exists(archive_path):
        print(f"❌ Archive not found: {archive_path}")
        return
    
    print(f"📤 Uploading {archive_path} to R2...")
    
    try:
        # Upload with public-read ACL
        r2_client.upload_file(
            archive_path,
            R2_BUCKET_NAME,
            key,
            ExtraArgs={
                'ContentType': 'application/gzip',
                'Metadata': {
                    'version': 'v2-2025-08-08',
                    'purpose': 'workout-bootstrap-data'
                }
            }
        )
        
        # Try to set public ACL (might not work on all R2 configurations)
        try:
            r2_client.put_object_acl(
                Bucket=R2_BUCKET_NAME,
                Key=key,
                ACL='public-read'
            )
            print("✅ Set public ACL")
        except Exception as e:
            print(f"⚠️ Could not set public ACL: {e}")
        
        public_url = f"{R2_PUBLIC_BASE.rstrip('/')}/{key}"
        
        print("🎉 Upload completed!")
        print("="*60)
        print(f"📁 Archive: {archive_path}")
        print(f"🔗 Public URL: {public_url}")
        print(f"🔒 SHA256: 89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
        print("="*60)
        print("\n📋 Environment variables for Render:")
        print(f"BOOTSTRAP_DATA_URL={public_url}")
        print(f"BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
        print(f"BOOTSTRAP_DATA_VERSION=v2-2025-08-08")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    upload_archive()