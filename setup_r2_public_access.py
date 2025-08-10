#!/usr/bin/env python3
"""
Script to configure Cloudflare R2 bucket for public access to motivational card images.

This script sets up bucket policy to allow public read access to the photos/progress/ folder
while keeping other files private.
"""

import json
import boto3
import os
from botocore.exceptions import ClientError


def create_bucket_policy():
    """Create bucket policy allowing public read access to photos/progress/ folder"""
    
    bucket_name = input("Enter R2 bucket name: ").strip()
    account_id = input("Enter Cloudflare Account ID: ").strip()
    
    # Public read policy for photos/progress folder only
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadMotivationalImages",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/photos/progress/*"
            }
        ]
    }
    
    return json.dumps(policy, indent=2), bucket_name, account_id


def setup_r2_client(account_id):
    """Setup R2 client with credentials"""
    
    access_key = input("Enter R2 Access Key ID: ").strip()
    secret_key = input("Enter R2 Secret Access Key: ").strip()
    
    # Create R2 client
    client = boto3.client(
        's3',
        endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto'  # R2 uses 'auto' as region
    )
    
    return client


def apply_bucket_policy(client, bucket_name, policy):
    """Apply bucket policy to allow public access"""
    
    try:
        print(f"Applying bucket policy to {bucket_name}...")
        print("Policy content:")
        print(policy)
        print()
        
        confirm = input("Apply this policy? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return False
        
        client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy
        )
        
        print(f"✅ Successfully applied bucket policy to {bucket_name}")
        return True
        
    except ClientError as e:
        print(f"❌ Error applying bucket policy: {e}")
        return False


def verify_public_access(bucket_name, account_id):
    """Verify that public access is working"""
    
    # Test URL format: https://pub-{hash}.r2.dev/photos/progress/card_progress_0066.jpg
    public_domain = input(f"Enter R2 public domain (e.g., https://pub-xxxxx.r2.dev): ").strip()
    
    test_url = f"{public_domain}/photos/progress/card_progress_0066.jpg"
    
    print(f"Test this URL in your browser: {test_url}")
    print("It should return the image without 401 Unauthorized error.")
    print()
    print("If it works, add this to your production environment variables:")
    print(f"R2_PUBLIC_BASE={public_domain}")


def main():
    """Main function"""
    
    print("=== Cloudflare R2 Public Access Setup ===")
    print()
    print("This script will configure your R2 bucket to allow public read access")
    print("to the 'photos/progress/' folder for motivational card images.")
    print()
    print("⚠️  IMPORTANT: This only affects photos/progress/ folder.")
    print("   Other files remain private and require authentication.")
    print()
    
    try:
        # Create policy
        policy, bucket_name, account_id = create_bucket_policy()
        
        # Setup client
        client = setup_r2_client(account_id)
        
        # Test connection
        print("Testing connection...")
        client.head_bucket(Bucket=bucket_name)
        print("✅ Successfully connected to R2 bucket")
        print()
        
        # Apply policy
        if apply_bucket_policy(client, bucket_name, policy):
            print()
            verify_public_access(bucket_name, account_id)
        
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()