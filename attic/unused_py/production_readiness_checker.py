#!/usr/bin/env python3
"""
PRODUCTION READINESS CHECKER
Simplified validator that focuses only on deployment-critical issues
"""

import os
import sys
import ast
import yaml
import subprocess
from pathlib import Path
from typing import List, Dict, Any


class ProductionReadinessChecker:
    """Production-focused validator that checks only deployment-critical items"""
    
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
            
    def check_critical_files(self):
        """Check for essential files and structure"""
        print("🔍 Checking critical files...")
        
        critical_files = [
            'manage.py',
            'config/settings.py',
            'config/wsgi.py',
            'apps/onboarding/urls.py',
            'apps/onboarding/views.py',
            'templates/workouts/no_plan.html'
        ]
        
        for file_path in critical_files:
            file = self.project_root / file_path
            if not file.exists():
                self.add_error(
                    "CRITICAL_FILES",
                    f"Critical file missing: {file_path}",
                    file_path,
                    f"Create or restore {file_path}"
                )
                
    def check_url_pattern_consistency(self):
        """Check template-URL consistency without Django import"""
        print("🔍 Checking URL pattern consistency...")
        
        # Check template references
        template_file = self.project_root / 'templates/workouts/no_plan.html'
        if template_file.exists():
            try:
                with open(template_file, 'r') as f:
                    content = f.read()
                    
                if 'start_onboarding' in content:
                    # Check if URL is defined
                    urls_file = self.project_root / 'apps/onboarding/urls.py'
                    if urls_file.exists():
                        with open(urls_file, 'r') as f:
                            url_content = f.read()
                            
                        if 'start_onboarding' not in url_content:
                            self.add_error(
                                "URL_CONSISTENCY",
                                "Template references 'start_onboarding' but URL not defined",
                                "apps/onboarding/urls.py",
                                "Add name='start_onboarding' to URL pattern"
                            )
                        else:
                            print("✅ URL pattern 'start_onboarding' found in urls.py")
                            
            except Exception as e:
                self.add_warning(
                    "URL_CONSISTENCY",
                    f"Could not check template-URL consistency: {e}",
                    "Template/URL consistency",
                    "Manual check required"
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
                
    def check_render_environment_vars(self):
        """Check for critical environment variables in render.yaml"""
        print("🔍 Checking environment variables configuration...")
        
        render_file = self.project_root / 'render.yaml'
        if not render_file.exists():
            return
            
        try:
            with open(render_file, 'r') as f:
                config = yaml.safe_load(f)
                
            critical_vars = [
                'SECRET_KEY',
                'DATABASE_URL',
                'REDIS_URL', 
                'OPENAI_API_KEY',
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY',
                'AWS_STORAGE_BUCKET_NAME',
                'AWS_S3_ENDPOINT_URL'
            ]
            
            # Find web service env vars
            web_service = None
            for service in config.get('services', []):
                if service.get('type') == 'web':
                    web_service = service
                    break
                    
            if web_service and 'envVars' in web_service:
                configured_vars = [var.get('key') for var in web_service['envVars'] 
                                 if isinstance(var, dict) and 'key' in var]
                
                for var in critical_vars:
                    if var not in configured_vars:
                        self.add_warning(
                            "ENVIRONMENT_CONFIG",
                            f"Critical environment variable '{var}' not configured in render.yaml",
                            "render.yaml envVars",
                            f"Add {var} to web service environment variables"
                        )
            else:
                self.add_warning(
                    "ENVIRONMENT_CONFIG",
                    "No environment variables configured in render.yaml web service",
                    "render.yaml envVars",
                    "Configure environment variables for web service"
                )
                
        except Exception as e:
            self.add_warning(
                "ENVIRONMENT_CONFIG",
                f"Could not validate environment variables: {e}",
                "render.yaml",
                "Check render.yaml structure"
            )
            
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("\n" + "="*70)
        print("🚀 PRODUCTION READINESS CHECK")
        print("="*70 + "\n")
        
        # Production-focused validation checks
        self.check_python_syntax()
        self.check_deployment_config()
        self.check_requirements()
        self.check_critical_files()
        self.check_url_pattern_consistency()
        self.check_data_directory()
        self.check_render_environment_vars()
        
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
        print("📊 PRODUCTION READINESS REPORT")
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
                print("🎉 PRODUCTION READY!")
            else:
                print(f"⚠️  {results['summary']['total_warnings']} warnings found - review before deployment")
        else:
            print(f"❌ Found {results['summary']['total_errors']} CRITICAL ERRORS")
            print("🔧 MUST FIX ALL ERRORS BEFORE DEPLOYMENT!")
            
        print("="*70 + "\n")
        return results['summary']['total_errors'] == 0
        

def main():
    checker = ProductionReadinessChecker()
    results = checker.validate_all()
    success = checker.print_report(results)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())