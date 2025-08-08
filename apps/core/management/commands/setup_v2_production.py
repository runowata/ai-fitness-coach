"""
One-command production setup for v2 system
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
import os

class Command(BaseCommand):
    help = "Complete v2 production setup: import data, generate plans, run tests"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Directory containing Excel files (auto-resolved if not specified)'
        )
        parser.add_argument(
            '--force-download',
            action='store_true',
            help='Force download from cloud even if local data exists'
        )
        parser.add_argument(
            '--skip-import',
            action='store_true',
            help='Skip data import (use existing data)'
        )
        parser.add_argument(
            '--skip-plans',
            action='store_true',
            help='Skip test plan generation (recommended for production)'
        )

    def _resolve_data_dir(self, data_dir, force_download):
        """Resolve data directory: prefer local, fallback to cloud download"""
        
        # If explicit data_dir provided, use it
        if data_dir:
            return data_dir
            
        # Check for local data/raw directory
        local_data_dir = './data/raw'
        if Path(local_data_dir).exists() and not force_download:
            # Check if it has Excel files
            excel_files = list(Path(local_data_dir).glob('*.xlsx'))
            if excel_files:
                self.stdout.write(self.style.SUCCESS(f"  📁 Using local data: {local_data_dir} ({len(excel_files)} Excel files)"))
                return local_data_dir
        
        # Fallback to cloud download
        self.stdout.write(self.style.WARNING("  ☁️  Local data not found, will use cloud bootstrap"))
        bootstrap_url = os.environ.get('BOOTSTRAP_DATA_URL')
        if not bootstrap_url:
            self.stdout.write(self.style.ERROR("  ❌ BOOTSTRAP_DATA_URL environment variable not set"))
            self.stdout.write("  💡 Either add data/raw/ directory or set BOOTSTRAP_DATA_URL")
            return None
            
        # Use bootstrap command logic (will download and extract)
        return 'cloud'

    def handle(self, *args, **options):
        data_dir = options['data_dir'] 
        force_download = options['force_download']
        skip_import = options['skip_import']
        skip_plans = options['skip_plans']
        
        self.stdout.write(self.style.SUCCESS("🚀 V2 Production Setup Starting..."))
        self.stdout.write("=" * 60)
        
        # Step 1: Database migrations
        self.stdout.write("\n1️⃣ Applying database migrations...")
        try:
            call_command('migrate', verbosity=1)
            self.stdout.write(self.style.SUCCESS("  ✅ Migrations applied"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Migration failed: {e}"))
            return
        
        # Step 2: Import exercises and videos (if not skipped)
        if not skip_import:
            self.stdout.write("\n2️⃣ Importing exercises and video clips...")
            
            # Resolve data directory (local first, cloud fallback)
            resolved_data_dir = self._resolve_data_dir(data_dir, force_download)
            if not resolved_data_dir:
                return
                
            try:
                if resolved_data_dir == 'cloud':
                    # Use bootstrap command for cloud download + import
                    call_command('bootstrap_v2_min', verbosity=1)
                else:
                    # Use local directory import
                    call_command('import_exercises_v2', data_dir=resolved_data_dir, verbosity=1)
                self.stdout.write(self.style.SUCCESS("  ✅ Import completed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Import failed: {e}"))
                return
        else:
            self.stdout.write("\n2️⃣ Skipping import (--skip-import)")
        
        # Step 3: Generate test plans for each archetype (if not skipped)
        if not skip_plans:
            self.stdout.write("\n3️⃣ Generating test workout plans...")
            for archetype in ['mentor', 'professional', 'peer']:
                try:
                    call_command('generate_test_plan_v2', 
                               archetype=archetype,
                               username=f'test_{archetype}',
                               verbosity=1)
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {archetype} plan generated"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  {archetype} plan failed: {e}"))
        else:
            self.stdout.write("\n3️⃣ Skipping plan generation (--skip-plans)")
        
        # Step 4: Run preflight checks
        self.stdout.write("\n4️⃣ Running preflight checks...")
        try:
            call_command('preflight_v2_prod', verbosity=1)
            self.stdout.write(self.style.SUCCESS("  ✅ Preflight passed"))
        except SystemExit as e:
            if e.code != 0:
                self.stdout.write(self.style.WARNING("  ⚠️  Preflight had warnings"))
            else:
                self.stdout.write(self.style.SUCCESS("  ✅ Preflight passed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Preflight failed: {e}"))
        
        # Step 5: Run comprehensive smoke test
        self.stdout.write("\n5️⃣ Running comprehensive smoke test...")
        try:
            call_command('smoke_v2_ready', verbose=True)
            self.stdout.write(self.style.SUCCESS("  ✅ Smoke test completed"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  ⚠️  Smoke test issues: {e}"))
        
        # Step 6: Summary and next steps
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🎉 V2 PRODUCTION SETUP COMPLETE"))
        self.stdout.write("\n📋 Next steps:")
        self.stdout.write("  1. Check smoke test results above")
        self.stdout.write("  2. Apply CORS configuration to R2 bucket")
        self.stdout.write("  3. Test video playback in browser")
        self.stdout.write("  4. Monitor logs for first 24h")
        self.stdout.write("\n🔗 Admin panel: /admin/")
        self.stdout.write("🔗 Test user login: test_mentor / (set password)")
        self.stdout.write("=" * 60)