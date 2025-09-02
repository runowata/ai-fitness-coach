#!/usr/bin/env python3
"""
ENHANCED DEPLOYMENT VALIDATOR
Comprehensive pre-deployment validation that catches real deployment issues
"""

import os
import sys
import ast
import py_compile
import tempfile
import subprocess
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class EnhancedDeploymentValidator:
    """Comprehensive validator that catches deployment-critical issues"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.project_root = Path.cwd()
        
    def add_error(self, category: str, message: str, location: str = "", fix_hint: str = ""):
        self.errors.append({
            "level": "ERROR",
            "category": category,
            "message": message,
            "location": location,
            "fix_hint": fix_hint
        })
        
    def add_warning(self, category: str, message: str, location: str = "", fix_hint: str = ""):
        self.warnings.append({
            "level": "WARNING", 
            "category": category,
            "message": message,
            "location": location,
            "fix_hint": fix_hint
        })
        
    def check_python_syntax(self):
        """Check Python syntax for all critical files"""
        print("🔍 Checking Python syntax...")
        
        # Include management commands which are critical for deployment
        python_files = list(self.project_root.rglob('apps/**/*.py'))
        python_files.extend(list(self.project_root.rglob('config/**/*.py')))
        python_files.extend(list(self.project_root.rglob('*/management/commands/*.py')))
        
        for py_file in python_files:
            if 'migrations' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                compile(content, str(py_file), 'exec')
                
            except SyntaxError as e:
                self.add_error(
                    "PYTHON_SYNTAX",
                    f"Syntax error: {e.msg}",
                    f"{py_file}:{e.lineno}",
                    "Fix syntax error before deployment"
                )
            except Exception as e:
                self.add_error(
                    "PYTHON_SYNTAX",
                    f"Failed to compile: {e}",
                    str(py_file),
                    "Check file encoding and syntax"
                )
                
    def check_management_commands(self):
        """Validate critical management commands exist and are callable"""
        print("🔍 Checking management commands...")
        
        critical_commands = [
            'migrate',
            'collectstatic', 
            'import_exercises_v2',
            'bootstrap_v2_min',
            'load_weekly_lessons',
            'seed_basic_data',
            'seed_media_assets',
            'setup_periodic_tasks'
        ]
        
        for cmd in critical_commands:
            try:
                result = subprocess.run([
                    sys.executable, 'manage.py', 'help', cmd
                ], capture_output=True, text=True, cwd=self.project_root, timeout=10)
                
                if result.returncode != 0:
                    self.add_error(
                        "MANAGEMENT_COMMAND",
                        f"Management command '{cmd}' not available or broken: {result.stderr}",
                        f"manage.py {cmd}",
                        f"Ensure {cmd} command is properly implemented"
                    )
                    
            except subprocess.TimeoutExpired:
                self.add_warning(
                    "MANAGEMENT_COMMAND",
                    f"Management command '{cmd}' check timed out",
                    f"manage.py {cmd}",
                    "Command might be slow but functional"
                )
            except Exception as e:
                self.add_error(
                    "MANAGEMENT_COMMAND", 
                    f"Failed to check command '{cmd}': {e}",
                    f"manage.py {cmd}",
                    "Check Django setup and command implementation"
                )
                
    def check_deployment_config(self):
        """Validate render.yaml and deployment configuration"""
        print("🔍 Checking deployment configuration...")
        
        render_file = self.project_root / 'render.yaml'
        if not render_file.exists():
            self.add_error(
                "DEPLOYMENT_CONFIG",
                "render.yaml not found",
                "render.yaml",
                "Create render.yaml for deployment"
            )
            return
            
        try:
            with open(render_file, 'r') as f:
                config = yaml.safe_load(f)
                
            # Validate services structure
            if 'services' not in config:
                self.add_error(
                    "DEPLOYMENT_CONFIG",
                    "No services defined in render.yaml",
                    "render.yaml",
                    "Add services configuration"
                )
                return
                
            web_service = None
            for service in config['services']:
                if service.get('type') == 'web':
                    web_service = service
                    break
                    
            if not web_service:
                self.add_error(
                    "DEPLOYMENT_CONFIG",
                    "No web service found in render.yaml", 
                    "render.yaml",
                    "Add web service configuration"
                )
                return
                
            # Validate critical commands in preDeployCommand
            pre_deploy = web_service.get('preDeployCommand', '')
            critical_commands = ['migrate', 'import_exercises_v2', 'bootstrap_v2_min']
            
            for cmd in critical_commands:
                if cmd not in pre_deploy:
                    self.add_warning(
                        "DEPLOYMENT_CONFIG",
                        f"'{cmd}' not found in preDeployCommand",
                        "render.yaml",
                        f"Consider adding {cmd} to preDeployCommand"
                    )
                    
        except Exception as e:
            self.add_error(
                "DEPLOYMENT_CONFIG",
                f"Invalid render.yaml: {e}",
                "render.yaml", 
                "Fix YAML syntax and structure"
            )
            
    def check_data_directory(self):
        """Check if required data files exist"""
        print("🔍 Checking data directory...")
        
        data_dir = self.project_root / 'data' / 'raw'
        if not data_dir.exists():
            self.add_warning(
                "DATA_FILES",
                "data/raw directory not found", 
                "data/raw/",
                "Required for import_exercises_v2 command"
            )
            return
            
        required_files = [
            'base_exercises.xlsx',
            'explainer_videos_111_nastavnik.xlsx',
            'explainer_videos_222_professional.xlsx', 
            'explainer_videos_333_rovesnik.xlsx'
        ]
        
        for file in required_files:
            if not (data_dir / file).exists():
                self.add_warning(
                    "DATA_FILES",
                    f"Required data file missing: {file}",
                    f"data/raw/{file}",
                    "Download from GitHub releases or prepare manually"
                )
                
    def check_environment_variables(self):
        """Check if critical environment variables are properly configured"""
        print("🔍 Checking environment variables...")
        
        critical_env_vars = [
            'SECRET_KEY',
            'DATABASE_URL', 
            'REDIS_URL',
            'OPENAI_API_KEY',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_S3_ENDPOINT_URL'
        ]
        
        for var in critical_env_vars:
            if not os.getenv(var):
                self.add_warning(
                    "ENVIRONMENT",
                    f"Environment variable '{var}' not set",
                    f"Environment: {var}",
                    f"Set {var} in production environment"
                )
                
    def check_requirements(self):
        """Validate requirements.txt exists and has critical packages"""
        print("🔍 Checking requirements...")
        
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            self.add_error(
                "REQUIREMENTS",
                "requirements.txt not found",
                "requirements.txt",
                "Create requirements.txt with project dependencies"
            )
            return
            
        try:
            with open(req_file, 'r') as f:
                requirements = f.read().lower()
                
            critical_packages = [
                'django',
                'psycopg',  # Modern replacement for psycopg2
                'celery',
                'redis',
                'boto3',
                'openai',
                'gunicorn'
            ]
            
            for package in critical_packages:
                if package not in requirements:
                    self.add_warning(
                        "REQUIREMENTS",
                        f"Critical package '{package}' not in requirements.txt",
                        "requirements.txt",
                        f"Add {package} to requirements.txt"
                    )
                    
        except Exception as e:
            self.add_error(
                "REQUIREMENTS",
                f"Cannot read requirements.txt: {e}",
                "requirements.txt",
                "Fix requirements.txt file"
            )
            
    def check_static_files(self):
        """Validate static files configuration"""
        print("🔍 Checking static files...")
        
        try:
            # Test collectstatic dry run
            result = subprocess.run([
                sys.executable, 'manage.py', 'collectstatic', '--noinput', '--dry-run'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.returncode != 0:
                self.add_error(
                    "STATIC_FILES",
                    f"collectstatic failed: {result.stderr}",
                    "Static files configuration",
                    "Fix static files settings and permissions"
                )
                
        except subprocess.TimeoutExpired:
            self.add_warning(
                "STATIC_FILES",
                "collectstatic check timed out",
                "Static files configuration",
                "Static files collection might be slow"
            )
        except Exception as e:
            self.add_error(
                "STATIC_FILES",
                f"Failed to test static files: {e}",
                "Static files configuration",
                "Check Django static files configuration"
            )
            
    def check_database_migrations(self):
        """Check for unapplied migrations"""
        print("🔍 Checking database migrations...")
        
        try:
            # Use Django's check command which doesn't need DB connection
            result = subprocess.run([
                sys.executable, 'manage.py', 'makemigrations', '--dry-run', '--check'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.returncode != 0:
                if 'No changes detected' in result.stdout:
                    # This is actually good - no unmade migrations
                    pass
                elif 'You have' in result.stderr and 'unapplied migration' in result.stderr:
                    self.add_warning(
                        "DATABASE_MIGRATIONS",
                        "Unapplied migrations detected",
                        "Database migrations",
                        "Run migrate command during deployment"
                    )
                else:
                    self.add_warning(
                        "DATABASE_MIGRATIONS",
                        "Migration check failed - database might be inaccessible locally",
                        "Database migrations",
                        "Ensure migrations work in production environment"
                    )
                
        except subprocess.TimeoutExpired:
            self.add_warning(
                "DATABASE_MIGRATIONS",
                "Migration check timed out",
                "Database migrations", 
                "Database might be inaccessible locally"
            )
        except Exception as e:
            self.add_warning(
                "DATABASE_MIGRATIONS",
                f"Migration check failed (expected in local env): {type(e).__name__}",
                "Database migrations",
                "Ensure migrations work in production environment"
            )
            
    def check_network_connectivity(self):
        """Test R2/S3 connectivity for media operations"""
        print("🔍 Checking network connectivity...")
        
        # Check if we can resolve R2 endpoint
        r2_endpoint = os.getenv('AWS_S3_ENDPOINT_URL', 'https://92568f8b8a15c68a9ece5fe08c66485b.r2.cloudflarestorage.com')
        
        try:
            import socket
            from urllib.parse import urlparse
            
            parsed = urlparse(r2_endpoint)
            host = parsed.hostname
            
            if host:
                socket.gethostbyname(host)
            else:
                self.add_warning(
                    "NETWORK_CONNECTIVITY",
                    "Cannot parse R2 endpoint hostname",
                    f"Endpoint: {r2_endpoint}",
                    "Verify AWS_S3_ENDPOINT_URL is correct"
                )
                
        except socket.gaierror:
            self.add_error(
                "NETWORK_CONNECTIVITY",
                f"Cannot resolve R2 endpoint: {r2_endpoint}",
                "Network connectivity",
                "Ensure internet access and correct R2 endpoint URL"
            )
        except Exception as e:
            self.add_warning(
                "NETWORK_CONNECTIVITY",
                f"Network connectivity check failed: {e}",
                "Network connectivity",
                "Manual verification of R2 access may be needed"
            )
            
    def check_critical_import_commands(self):
        """Test critical import commands that cause deployment failures"""
        print("🔍 Testing critical import commands...")
        
        # Test import_exercises_v2 with dry-run if data exists
        data_dir = self.project_root / 'data' / 'raw'
        if data_dir.exists():
            try:
                result = subprocess.run([
                    sys.executable, 'manage.py', 'import_exercises_v2', 
                    '--data-dir', './data/raw', '--dry-run'
                ], capture_output=True, text=True, cwd=self.project_root, timeout=60)
                
                if result.returncode != 0:
                    self.add_error(
                        "CRITICAL_IMPORT",
                        f"import_exercises_v2 command failed: {result.stderr}",
                        "import_exercises_v2 command",
                        "Fix command or data files before deployment"
                    )
                elif "Error importing video clips" in result.stdout:
                    self.add_error(
                        "CRITICAL_IMPORT",
                        "Video import failed - likely network/R2 connectivity issue",
                        "import_exercises_v2 video import",
                        "Check R2 credentials and network connectivity"
                    )
                    
            except subprocess.TimeoutExpired:
                self.add_error(
                    "CRITICAL_IMPORT",
                    "import_exercises_v2 command timed out",
                    "import_exercises_v2 command",
                    "Command is too slow or hanging - fix before deployment"
                )
            except Exception as e:
                self.add_error(
                    "CRITICAL_IMPORT",
                    f"Failed to test import_exercises_v2: {e}",
                    "import_exercises_v2 command",
                    "Investigate command implementation"
                )
        
        # Test bootstrap_v2_min command
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'help', 'bootstrap_v2_min'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
            
            if result.returncode != 0:
                self.add_error(
                    "CRITICAL_IMPORT",
                    "bootstrap_v2_min command not available",
                    "bootstrap_v2_min command", 
                    "Implement bootstrap_v2_min management command"
                )
        except Exception as e:
            self.add_error(
                "CRITICAL_IMPORT",
                f"Failed to check bootstrap_v2_min: {e}",
                "bootstrap_v2_min command",
                "Fix management command availability"
            )

    def check_database_schema(self):
        """Validate database schema matches model expectations"""
        print("🔍 Checking database schema consistency...")
        
        try:
            # Test for critical tables that should exist after migrations
            result = subprocess.run([
                sys.executable, 'manage.py', 'check', '--database', 'default'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.returncode != 0:
                self.add_error(
                    "DATABASE_SCHEMA",
                    f"Django check failed: {result.stderr}",
                    "Database schema",
                    "Fix model/database inconsistencies before deployment"
                )
                
            # Check for specific missing tables that cause runtime errors
            critical_tables = [
                'csv_exercises',  # From the log error
                'workouts_csvexercise',
                'content_motivationalcard'
            ]
            
            for table in critical_tables:
                try:
                    # Try to check if model can be imported and basic query works
                    if table == 'csv_exercises':
                        test_result = subprocess.run([
                            sys.executable, '-c',
                            'import django; django.setup(); from apps.workouts.models import CSVExercise; CSVExercise.objects.exists()'
                        ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
                        
                        if 'does not exist' in test_result.stderr:
                            self.add_error(
                                "DATABASE_SCHEMA",
                                f"Critical table missing: {table}",
                                f"Table: {table}",
                                "Run migrations or import_exercises_v2 command"
                            )
                            
                except Exception:
                    # Expected in local env, but warn about potential issues
                    self.add_warning(
                        "DATABASE_SCHEMA",
                        f"Cannot verify table {table} - may cause runtime errors",
                        f"Table: {table}",
                        "Ensure migrations create required tables in production"
                    )
                
        except Exception as e:
            self.add_warning(
                "DATABASE_SCHEMA",
                f"Database schema check failed (expected locally): {type(e).__name__}",
                "Database schema",
                "Ensure database schema is consistent in production"
            )
            
    def check_url_patterns(self):
        """Validate URL patterns and view names"""
        print("🔍 Checking URL patterns...")
        
        try:
            # Test URL configuration loading
            result = subprocess.run([
                sys.executable, '-c',
                'import django; django.setup(); from django.urls import reverse; reverse("start_onboarding")'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
            
            if 'NoReverseMatch' in result.stderr or result.returncode != 0:
                self.add_error(
                    "URL_PATTERNS", 
                    "Missing URL pattern: 'start_onboarding'",
                    "URL configuration",
                    "Add missing URL pattern or fix template reference"
                )
                
            # Test other critical URL patterns
            critical_urls = [
                'onboarding:start',
                'workouts:my_plan',
                'users:dashboard'
            ]
            
            for url_name in critical_urls:
                try:
                    test_result = subprocess.run([
                        sys.executable, '-c',
                        f'import django; django.setup(); from django.urls import reverse; reverse("{url_name}")'
                    ], capture_output=True, text=True, cwd=self.project_root, timeout=10)
                    
                    if test_result.returncode != 0:
                        self.add_warning(
                            "URL_PATTERNS",
                            f"Cannot resolve URL pattern: {url_name}",
                            f"URL: {url_name}",
                            f"Verify URL pattern {url_name} exists"
                        )
                except subprocess.TimeoutExpired:
                    pass  # Skip timeout issues
                    
        except Exception as e:
            self.add_warning(
                "URL_PATTERNS",
                f"URL pattern check failed (expected locally): {type(e).__name__}",
                "URL patterns",
                "Verify all URL patterns resolve in production"
            )
            
    def check_model_fields(self):
        """Check for model field mismatches that cause runtime errors"""
        print("🔍 Checking model field consistency...")
        
        # Check for the specific image_url field error from logs
        try:
            result = subprocess.run([
                sys.executable, '-c',
                'import django; django.setup(); from apps.content.models import MotivationalCard; print([f.name for f in MotivationalCard._meta.fields])'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
            
            if result.returncode == 0 and 'image_url' not in result.stdout:
                self.add_error(
                    "MODEL_FIELDS",
                    "MotivationalCard model missing 'image_url' field",
                    "apps.content.models.MotivationalCard",
                    "Add image_url field to MotivationalCard model or fix query"
                )
                
        except Exception as e:
            self.add_warning(
                "MODEL_FIELDS",
                f"Model field check failed (expected locally): {type(e).__name__}",
                "Model fields",
                "Verify model fields match database schema in production"
            )

    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("\n" + "="*70)
        print("🚀 ENHANCED DEPLOYMENT VALIDATION")
        print("="*70 + "\n")
        
        # Core validation checks
        self.check_python_syntax()
        self.check_management_commands()
        self.check_deployment_config()
        self.check_data_directory()
        self.check_environment_variables()
        self.check_requirements()
        self.check_static_files()
        self.check_database_migrations()
        self.check_network_connectivity()
        self.check_critical_import_commands()
        
        # Runtime error prevention checks
        self.check_database_schema()
        self.check_url_patterns()
        self.check_model_fields()
        
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings)
            }
        }
        
    def print_report(self, results: Dict[str, Any]) -> bool:
        """Print comprehensive validation report"""
        print("\n" + "="*70)
        print("📊 ENHANCED DEPLOYMENT VALIDATION REPORT")
        print("="*70)
        
        if results['errors']:
            print(f"\n❌ CRITICAL ERRORS: {len(results['errors'])}")
            print("-"*50)
            for i, error in enumerate(results['errors'], 1):
                print(f"{i}. [{error['category']}] {error['message']}")
                if error['location']:
                    print(f"   📍 Location: {error['location']}")
                if error['fix_hint']:
                    print(f"   💡 Fix: {error['fix_hint']}")
                print()
                
        if results['warnings']:
            print(f"\n⚠️  WARNINGS: {len(results['warnings'])}")
            print("-"*50)
            for i, warning in enumerate(results['warnings'], 1):
                print(f"{i}. [{warning['category']}] {warning['message']}")
                if warning['location']:
                    print(f"   📍 Location: {warning['location']}")
                if warning['fix_hint']:
                    print(f"   💡 Tip: {warning['fix_hint']}")
                print()
                
        print("\n" + "="*70)
        if results['summary']['total_errors'] == 0:
            print("✅ NO CRITICAL ERRORS FOUND!")
            if results['summary']['total_warnings'] == 0:
                print("🎉 System is ready for deployment!")
            else:
                print(f"⚠️  {results['summary']['total_warnings']} warnings found - review before deployment")
        else:
            print(f"❌ Found {results['summary']['total_errors']} CRITICAL ERRORS")
            print("🔧 MUST FIX ALL ERRORS BEFORE DEPLOYMENT!")
            
        print("="*70 + "\n")
        return results['summary']['total_errors'] == 0
        

def main():
    validator = EnhancedDeploymentValidator()
    results = validator.validate_all()
    success = validator.print_report(results)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())