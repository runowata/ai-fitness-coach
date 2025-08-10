#!/usr/bin/env python3
"""
Script to check and fix Content-Type metadata for R2 objects
"""
import os
import sys
import boto3
from pathlib import Path

# Add Django project to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings


def get_content_type(key: str) -> str:
    """Determine correct Content-Type based on file extension"""
    ext = Path(key).suffix.lower()
    content_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.avi': 'video/avi',
        '.mov': 'video/quicktime',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.pdf': 'application/pdf',
    }
    return content_types.get(ext, 'application/octet-stream')


def check_r2_content_types(bucket_name: str, dry_run: bool = True) -> dict:
    """
    Check Content-Type metadata for all objects in R2 bucket
    
    Args:
        bucket_name: R2 bucket name
        dry_run: If True, only report issues without fixing
        
    Returns:
        Dict with statistics
    """
    # Initialize R2 client
    s3 = boto3.client(
        's3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    stats = {
        'total_objects': 0,
        'correct_content_type': 0,
        'incorrect_content_type': 0,
        'fixed_objects': 0,
        'errors': 0,
        'issues': []
    }
    
    try:
        # List all objects
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                stats['total_objects'] += 1
                
                try:
                    # Get object metadata
                    response = s3.head_object(Bucket=bucket_name, Key=key)
                    current_content_type = response.get('ContentType', '')
                    expected_content_type = get_content_type(key)
                    
                    if current_content_type == expected_content_type:
                        stats['correct_content_type'] += 1
                    else:
                        stats['incorrect_content_type'] += 1
                        issue = {
                            'key': key,
                            'current': current_content_type,
                            'expected': expected_content_type
                        }
                        stats['issues'].append(issue)
                        
                        print(f"❌ {key}")
                        print(f"   Current: {current_content_type}")
                        print(f"   Expected: {expected_content_type}")
                        
                        # Fix if not dry run
                        if not dry_run:
                            try:
                                s3.copy_object(
                                    Bucket=bucket_name,
                                    Key=key,
                                    CopySource={'Bucket': bucket_name, 'Key': key},
                                    MetadataDirective='REPLACE',
                                    ContentType=expected_content_type
                                )
                                stats['fixed_objects'] += 1
                                print(f"   ✅ FIXED")
                            except Exception as e:
                                print(f"   ❌ FIX FAILED: {e}")
                                stats['errors'] += 1
                        
                except Exception as e:
                    print(f"❌ Error processing {key}: {e}")
                    stats['errors'] += 1
                    
    except Exception as e:
        print(f"❌ Error accessing bucket {bucket_name}: {e}")
        stats['errors'] += 1
        
    return stats


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check and fix R2 Content-Type metadata')
    parser.add_argument('--bucket', default='ai-fitness-media', help='R2 bucket name')
    parser.add_argument('--fix', action='store_true', help='Actually fix issues (default: dry-run)')
    parser.add_argument('--filter', help='Filter objects by prefix')
    
    args = parser.parse_args()
    
    print(f"🔍 Checking Content-Type for bucket: {args.bucket}")
    print(f"Mode: {'FIX' if args.fix else 'DRY-RUN'}")
    print("-" * 50)
    
    stats = check_r2_content_types(args.bucket, dry_run=not args.fix)
    
    print("\n" + "="*50)
    print("📊 SUMMARY")
    print("="*50)
    print(f"Total objects: {stats['total_objects']}")
    print(f"Correct Content-Type: {stats['correct_content_type']}")
    print(f"Incorrect Content-Type: {stats['incorrect_content_type']}")
    if args.fix:
        print(f"Fixed objects: {stats['fixed_objects']}")
    print(f"Errors: {stats['errors']}")
    
    if stats['incorrect_content_type'] > 0 and not args.fix:
        print(f"\n💡 Run with --fix to correct {stats['incorrect_content_type']} objects")


if __name__ == '__main__':
    main()