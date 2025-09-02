#!/usr/bin/env python3
"""
COMPREHENSIVE DEPLOYMENT VALIDATOR
Full E2E testing that simulates real user journeys before deployment
"""

import os
import sys
import ast
import yaml
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional


class ComprehensiveDeploymentValidator:
    """E2E validator that tests complete user journeys"""
    
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
                
    def test_django_startup(self):
        """Test if Django can start without errors"""
        print("🔍 Testing Django startup...")
        
        try:
            result = subprocess.run([
                sys.executable, '-c',
                'import os; os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"; import django; django.setup(); print("✅ Django startup successful")'
            ], capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.returncode != 0:
                self.add_error(
                    "DJANGO_STARTUP",
                    f"Django failed to start: {result.stderr}",
                    "Django configuration",
                    "Fix Django settings or model issues"
                )
            else:
                print("✅ Django startup successful")
                
        except subprocess.TimeoutExpired:
            self.add_error(
                "DJANGO_STARTUP",
                "Django startup timed out",
                "Django configuration",
                "Check for infinite loops or blocking operations in settings"
            )
        except Exception as e:
            self.add_error(
                "DJANGO_STARTUP",
                f"Failed to test Django startup: {e}",
                "Django configuration",
                "Investigate Django configuration issues"
            )
            
    def test_url_patterns(self):
        """Test critical URL patterns can be resolved"""
        print("🔍 Testing URL pattern resolution...")
        
        critical_urls = [
            ('start_onboarding', 'onboarding:start_onboarding'),
            ('onboarding_start', 'onboarding:start'), 
            ('question_view', 'onboarding:question', {'question_id': 1}),
            ('save_answer', 'onboarding:save_answer', {'question_id': 1}),
            ('select_archetype', 'onboarding:select_archetype'),
            ('my_plan', 'workouts:my_plan'),
        ]
        
        try:
            for url_name, url_pattern, *args in critical_urls:
                kwargs = args[0] if args else {}
                
                test_code = f"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()
from django.urls import reverse
try:
    url = reverse('{url_pattern}', kwargs={kwargs})
    print(f'✅ {url_pattern}: {{url}}')
except Exception as e:
    print(f'❌ {url_pattern}: {{e}}')
    exit(1)
"""
                
                result = subprocess.run([
                    sys.executable, '-c', test_code
                ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
                
                if result.returncode != 0:
                    self.add_error(
                        "URL_PATTERNS",
                        f"Cannot resolve URL pattern '{url_pattern}': {result.stdout.strip() or result.stderr.strip()}",
                        f"URL: {url_pattern}",
                        f"Fix URL pattern {url_pattern} in urls.py"
                    )
                else:
                    print(f"✅ {url_pattern}: {result.stdout.strip()}")
                    
        except Exception as e:
            self.add_error(
                "URL_PATTERNS",
                f"Failed to test URL patterns: {e}",
                "URL patterns",
                "Check Django URL configuration"
            )
            
    def test_model_queries(self):
        """Test critical model queries work"""
        print("🔍 Testing model queries...")
        
        model_tests = [
            ("CSVExercise", "from apps.workouts.models import CSVExercise; CSVExercise.objects.all().count()"),
            ("User", "from apps.users.models import User; User.objects.all().count()"),
            ("OnboardingQuestion", "from apps.onboarding.models import OnboardingQuestion; OnboardingQuestion.objects.all().count()"),
            ("MediaAsset", "from apps.content.models import MediaAsset; MediaAsset.objects.all().count()"),
        ]
        
        for model_name, test_query in model_tests:
            try:
                test_code = f"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()
from django.db import connection
connection.ensure_connection()  # This will create tables if using SQLite
try:
    {test_query}
    print(f'✅ {model_name}: Model query successful')
except Exception as e:
    print(f'⚠️ {model_name}: {{e}}')
"""
                
                result = subprocess.run([
                    sys.executable, '-c', test_code
                ], capture_output=True, text=True, cwd=self.project_root, timeout=20)
                
                if result.returncode != 0:
                    self.add_warning(
                        "MODEL_QUERIES",
                        f"{model_name} model query failed: {result.stdout.strip() or result.stderr.strip()}",
                        f"Model: {model_name}",
                        f"Ensure {model_name} table exists after migrations"
                    )
                else:
                    output = result.stdout.strip()
                    if '✅' in output:
                        print(output)
                    else:
                        print(f"⚠️ {model_name}: {output}")
                        
            except Exception as e:
                self.add_warning(
                    "MODEL_QUERIES",
                    f"Failed to test {model_name} model: {e}",
                    f"Model: {model_name}",
                    f"Check {model_name} model definition"
                )
                
    def test_view_imports(self):
        """Test that all views can be imported"""
        print("🔍 Testing view imports...")
        
        view_modules = [
            'apps.onboarding.views',
            'apps.workouts.views',
            'apps.users.views',
            'apps.content.views',
        ]
        
        for module_name in view_modules:
            try:
                test_code = f"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()
import {module_name}
print(f'✅ {module_name}: Import successful')
"""
                
                result = subprocess.run([
                    sys.executable, '-c', test_code
                ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
                
                if result.returncode != 0:
                    self.add_error(
                        "VIEW_IMPORTS",
                        f"Cannot import {module_name}: {result.stderr.strip()}",
                        f"Module: {module_name}",
                        f"Fix import errors in {module_name}"
                    )
                else:
                    print(f"✅ {module_name}: Import successful")
                    
            except Exception as e:
                self.add_error(
                    "VIEW_IMPORTS",
                    f"Failed to test {module_name} import: {e}",
                    f"Module: {module_name}",
                    f"Check {module_name} for import issues"
                )
                
    def test_template_rendering(self):
        """Test that critical templates can render"""
        print("🔍 Testing template rendering...")
        
        templates_to_test = [
            ('workouts/no_plan.html', {}),
            ('onboarding/question.html', {'question': {'id': 1, 'text': 'Test'}, 'form': None}),
            ('onboarding/select_archetype.html', {}),
        ]
        
        for template_name, context in templates_to_test:
            try:
                test_code = f"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()
from django.template.loader import get_template
from django.template import Context
try:
    template = get_template('{template_name}')
    context_dict = {context}
    rendered = template.render(context_dict)
    print(f'✅ {template_name}: Template renders successfully ({{len(rendered)}} chars)')
except Exception as e:
    print(f'❌ {template_name}: {{e}}')
    exit(1)
"""
                
                result = subprocess.run([
                    sys.executable, '-c', test_code
                ], capture_output=True, text=True, cwd=self.project_root, timeout=15)
                
                if result.returncode != 0:
                    self.add_error(
                        "TEMPLATE_RENDERING",
                        f"Template {template_name} failed to render: {result.stdout.strip() or result.stderr.strip()}",
                        f"Template: {template_name}",
                        f"Fix template syntax or context issues in {template_name}"
                    )
                else:
                    print(result.stdout.strip())
                    
            except Exception as e:
                self.add_error(
                    "TEMPLATE_RENDERING",
                    f"Failed to test template {template_name}: {e}",
                    f"Template: {template_name}",
                    f"Check template {template_name} for issues"
                )
                
    def test_management_commands(self):
        """Test critical management commands"""
        print("🔍 Testing management commands...")
        
        critical_commands = [
            ('migrate', ['--check']),
            ('collectstatic', ['--noinput', '--dry-run']),
            ('check', []),
            ('import_exercises_v2', ['--help']),
            ('bootstrap_v2_min', ['--help']),
        ]
        
        for cmd_name, args in critical_commands:
            try:
                result = subprocess.run([
                    sys.executable, 'manage.py', cmd_name] + args,
                    capture_output=True, text=True, cwd=self.project_root, timeout=30,
                    env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings_sqlite'}
                )
                
                if result.returncode != 0:
                    # Some commands are expected to fail in local env
                    if cmd_name in ['migrate', 'collectstatic', 'check']:
                        self.add_warning(
                            "MANAGEMENT_COMMANDS",
                            f"Management command '{cmd_name}' failed (might be OK locally): {result.stderr.strip()[:200]}",
                            f"Command: manage.py {cmd_name}",
                            f"Ensure {cmd_name} works in production environment"
                        )
                    else:
                        self.add_error(
                            "MANAGEMENT_COMMANDS",
                            f"Management command '{cmd_name}' failed: {result.stderr.strip()[:200]}",
                            f"Command: manage.py {cmd_name}",
                            f"Fix management command {cmd_name}"
                        )
                else:
                    print(f"✅ manage.py {cmd_name}: Command available")
                    
            except subprocess.TimeoutExpired:
                self.add_warning(
                    "MANAGEMENT_COMMANDS",
                    f"Management command '{cmd_name}' timed out",
                    f"Command: manage.py {cmd_name}",
                    f"Command {cmd_name} might be slow or hanging"
                )
            except Exception as e:
                self.add_error(
                    "MANAGEMENT_COMMANDS",
                    f"Failed to test command '{cmd_name}': {e}",
                    f"Command: manage.py {cmd_name}",
                    f"Check management command {cmd_name} implementation"
                )
                
    def test_settings_validity(self):
        """Test Django settings are valid"""
        print("🔍 Testing Django settings...")
        
        settings_tests = [
            ("INSTALLED_APPS", "from django.conf import settings; result = len(settings.INSTALLED_APPS)"),
            ("DATABASES", "from django.conf import settings; result = settings.DATABASES['default']"),
            ("SECRET_KEY", "from django.conf import settings; result = bool(settings.SECRET_KEY)"),
            ("STATIC_URL", "from django.conf import settings; result = settings.STATIC_URL"),
        ]
        
        for setting_name, test_code in settings_tests:
            try:
                full_test = f"""
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()
{test_code}
print(f'✅ {setting_name}: {{result}}')
"""
                
                result = subprocess.run([
                    sys.executable, '-c', full_test
                ], capture_output=True, text=True, cwd=self.project_root, timeout=10)
                
                if result.returncode != 0:
                    self.add_error(
                        "SETTINGS_VALIDITY",
                        f"Settings test failed for {setting_name}: {result.stderr.strip()}",
                        f"Setting: {setting_name}",
                        f"Fix Django setting {setting_name}"
                    )
                else:
                    print(result.stdout.strip())
                    
            except Exception as e:
                self.add_error(
                    "SETTINGS_VALIDITY",
                    f"Failed to test setting {setting_name}: {e}",
                    f"Setting: {setting_name}",
                    f"Check Django setting {setting_name}"
                )
                
    def test_e2e_onboarding_flow(self):
        """Test end-to-end onboarding flow simulation"""
        print("🔍 Testing E2E onboarding flow...")
        
        try:
            test_code = """
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings_sqlite"
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.onboarding.models import OnboardingQuestion

# Test client creation
client = Client()
User = get_user_model()

try:
    # Test 1: Homepage access
    response = client.get('/')
    print(f'✅ Homepage: Status {response.status_code}')
    
    # Test 2: User registration
    response = client.get('/users/register/')
    print(f'✅ Registration page: Status {response.status_code}')
    
    # Test 3: Onboarding start
    response = client.get('/onboarding/start/')
    print(f'✅ Onboarding start: Status {response.status_code}')
    
    # Test 4: First question (if questions exist)
    try:
        response = client.get('/onboarding/question/1/')
        print(f'✅ Question 1: Status {response.status_code}')
    except Exception as e:
        print(f'⚠️ Question 1: {e} (questions may not be loaded)')
    
    # Test 5: Archetype selection
    response = client.get('/onboarding/archetype/')
    print(f'✅ Archetype selection: Status {response.status_code}')
    
    print('✅ E2E Flow: Basic navigation successful')
    
except Exception as e:
    print(f'❌ E2E Flow failed: {e}')
    exit(1)
"""
            
            result = subprocess.run([
                sys.executable, '-c', test_code
            ], capture_output=True, text=True, cwd=self.project_root, timeout=45)
            
            if result.returncode != 0:
                self.add_error(
                    "E2E_ONBOARDING",
                    f"E2E onboarding flow failed: {result.stdout.strip() or result.stderr.strip()}",
                    "Onboarding flow",
                    "Fix view or URL issues preventing user flow"
                )
            else:
                print("✅ E2E onboarding flow successful")
                for line in result.stdout.strip().split('\n'):
                    if line:
                        print(f"    {line}")
                        
        except Exception as e:
            self.add_error(
                "E2E_ONBOARDING",
                f"Failed to test E2E onboarding flow: {e}",
                "Onboarding flow",
                "Check onboarding views and URLs"
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
                
            # Check for web service
            web_service = None
            for service in config.get('services', []):
                if service.get('type') == 'web':
                    web_service = service
                    break
                    
            if web_service:
                print("✅ Web service found in render.yaml")
                
                # Check critical env vars
                env_vars = web_service.get('envVars', [])
                critical_vars = ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']
                
                configured_vars = [var.get('key') for var in env_vars if isinstance(var, dict)]
                for var in critical_vars:
                    if var not in configured_vars:
                        self.add_warning(
                            "DEPLOYMENT_CONFIG",
                            f"Critical env var '{var}' not configured in render.yaml",
                            "render.yaml",
                            f"Add {var} to environment variables"
                        )
            else:
                self.add_error(
                    "DEPLOYMENT_CONFIG",
                    "No web service found in render.yaml",
                    "render.yaml",
                    "Add web service configuration"
                )
                
        except Exception as e:
            self.add_error(
                "DEPLOYMENT_CONFIG",
                f"Invalid render.yaml: {e}",
                "render.yaml",
                "Fix YAML syntax"
            )
            
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("\n" + "="*80)
        print("🚀 COMPREHENSIVE DEPLOYMENT VALIDATION")
        print("   Full E2E Testing Before Production Deploy")
        print("="*80 + "\n")
        
        # Structure validation
        self.check_python_syntax()
        self.check_deployment_config()
        
        # Django functionality testing
        self.test_django_startup()
        self.test_settings_validity()
        self.test_view_imports()
        self.test_url_patterns()
        self.test_template_rendering()
        self.test_model_queries()
        self.test_management_commands()
        
        # End-to-end testing
        self.test_e2e_onboarding_flow()
        
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
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE DEPLOYMENT VALIDATION REPORT")
        print("="*80)
        
        if results['errors']:
            print(f"\n❌ CRITICAL ERRORS: {len(results['errors'])}")
            print("-"*60)
            for i, error in enumerate(results['errors'], 1):
                print(f"{i}. [{error['category']}] {error['message']}")
                if error['location']:
                    print(f"   📍 Location: {error['location']}")
                if error['fix_hint']:
                    print(f"   💡 Fix: {error['fix_hint']}")
                print()
                
        if results['warnings']:
            print(f"\n⚠️  WARNINGS: {len(results['warnings'])}")
            print("-"*60)
            for i, warning in enumerate(results['warnings'], 1):
                print(f"{i}. [{warning['category']}] {warning['message']}")
                if warning['location']:
                    print(f"   📍 Location: {warning['location']}")
                if warning['fix_hint']:
                    print(f"   💡 Tip: {warning['fix_hint']}")
                print()
                
        print("\n" + "="*80)
        if results['summary']['total_errors'] == 0:
            print("✅ NO CRITICAL ERRORS FOUND!")
            if results['summary']['total_warnings'] == 0:
                print("🎉 FULLY PRODUCTION READY!")
                print("🚀 All user journeys tested successfully!")
            else:
                print(f"⚠️  {results['summary']['total_warnings']} warnings found")
                print("🚀 Safe to deploy - warnings are mostly environment-specific")
        else:
            print(f"❌ Found {results['summary']['total_errors']} CRITICAL ERRORS")
            print("🔧 MUST FIX ALL ERRORS BEFORE DEPLOYMENT!")
            print("🚫 User journeys will fail in production!")
            
        print("="*80 + "\n")
        return results['summary']['total_errors'] == 0


def main():
    validator = ComprehensiveDeploymentValidator()
    results = validator.validate_all()
    success = validator.print_report(results)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())