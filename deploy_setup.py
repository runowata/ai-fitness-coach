#!/usr/bin/env python
"""
Post-deployment setup script for Render.com
This script should be run after deployment to setup periodic tasks
"""
import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

def main():
    """Run post-deployment setup tasks"""
    print("🚀 Starting post-deployment setup...")
    
    # Run migrations
    print("📊 Running migrations...")
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Setup periodic tasks
    print("⏰ Setting up periodic tasks...")
    execute_from_command_line(['manage.py', 'setup_periodic_tasks'])
    
    print("✅ Post-deployment setup complete!")

if __name__ == '__main__':
    main()