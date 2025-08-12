#!/usr/bin/env python3
"""
Simple R2 upload script for bootstrap archive
"""
import os
import sys

def upload_to_r2():
    """Simple R2 upload with minimal setup"""
    
    print("🚀 R2 Bootstrap Archive Upload")
    print("=" * 50)
    
    # Check if archive exists
    archive_path = "workouts_bootstrap_v2.tar.gz"
    if not os.path.exists(archive_path):
        print(f"❌ Archive not found: {archive_path}")
        return False
    
    print(f"📦 Archive ready: {archive_path} ({os.path.getsize(archive_path):,} bytes)")
    print(f"🔒 SHA256: 89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
    print()
    
    # Get R2 credentials
    print("Enter your Cloudflare R2 credentials:")
    access_key = input("AWS_ACCESS_KEY_ID: ").strip()
    if not access_key:
        print("❌ Access key required")
        return False
    
    secret_key = input("AWS_SECRET_ACCESS_KEY: ").strip()
    if not secret_key:
        print("❌ Secret key required")
        return False
        
    endpoint_url = input("R2_ENDPOINT_URL (e.g., https://xxxxx.r2.cloudflarestorage.com): ").strip()
    if not endpoint_url:
        print("❌ Endpoint URL required")
        return False
        
    bucket_name = input("R2_BUCKET_NAME: ").strip()
    if not bucket_name:
        print("❌ Bucket name required")
        return False
        
    public_domain = input("R2_PUBLIC_DOMAIN (e.g., https://pub-xxxxx.r2.dev): ").strip()
    if not public_domain:
        print("❌ Public domain required")
        return False
    
    # Try to import and use boto3
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("❌ boto3 not installed. Install with: pip install boto3")
        return False
    
    print("\n🔄 Uploading to R2...")
    
    try:
        # Configure R2 client
        client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(region_name='auto')
        )
        
        key = "bootstrap/workouts_bootstrap_v2.tar.gz"
        
        # Upload file
        client.upload_file(
            archive_path,
            bucket_name, 
            key,
            ExtraArgs={
                'ContentType': 'application/gzip',
                'Metadata': {
                    'version': 'v2-2025-08-08',
                    'purpose': 'workout-bootstrap-data'
                }
            }
        )
        
        public_url = f"{public_domain.rstrip('/')}/{key}"
        
        print("✅ Upload successful!")
        print("\n" + "=" * 60)
        print("📋 RENDER ENVIRONMENT VARIABLES:")
        print("=" * 60)
        print(f"BOOTSTRAP_DATA_URL={public_url}")
        print(f"BOOTSTRAP_DATA_SHA256=89cc0035adb8291a753eb450dc73c222bd96883d184e342c84290d4e8114db38")
        print(f"BOOTSTRAP_DATA_VERSION=v2-2025-08-08")
        print("=" * 60)
        print(f"\n🔗 Public URL: {public_url}")
        print("\n🎯 Next steps:")
        print("1. Copy the environment variables above to Render")
        print("2. Run Manual Deploy in Render")
        print("3. The system will auto-download and import data")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

if __name__ == "__main__":
    success = upload_to_r2()
    sys.exit(0 if success else 1)