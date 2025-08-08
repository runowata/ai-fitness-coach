"""
One-command production setup for v2 system
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from pathlib import Path
import os
import tempfile
import tarfile
import hashlib
import requests

class Command(BaseCommand):
    help = "Complete v2 production setup: import data, generate plans, run tests"
    
    def _resolve_data_dir(self, local_path="./data/raw", force_download=False):
        """
        Resolve data directory - use local if exists, otherwise download from cloud
        
        Args:
            local_path: Preferred local path
            force_download: Force download even if local path exists
            
        Returns:
            Path to data directory (local or extracted from archive)
        """
        if not force_download and os.path.isdir(local_path):
            self.stdout.write(f"📁 Using local data dir: {local_path}")
            return local_path

        # Try to get bootstrap data from environment
        bootstrap_url = getattr(settings, "BOOTSTRAP_DATA_URL", None) or os.getenv("BOOTSTRAP_DATA_URL")
        bootstrap_sha = getattr(settings, "BOOTSTRAP_DATA_SHA256", None) or os.getenv("BOOTSTRAP_DATA_SHA256")
        bootstrap_version = getattr(settings, "BOOTSTRAP_DATA_VERSION", None) or os.getenv("BOOTSTRAP_DATA_VERSION", "unknown")
        
        if not bootstrap_url:
            if not os.path.isdir(local_path):
                raise RuntimeError(
                    f"❌ No data directory '{local_path}' found and BOOTSTRAP_DATA_URL is not set. "
                    f"Set BOOTSTRAP_DATA_URL environment variable or create local data directory."
                )
            return local_path

        self.stdout.write(f"🌐 Downloading bootstrap data from cloud...")
        self.stdout.write(f"  📦 Version: {bootstrap_version}")
        self.stdout.write(f"  🔗 URL: {bootstrap_url}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="bootstrap_v2_")
        archive_path = os.path.join(temp_dir, "bootstrap.tar.gz")
        
        try:
            # Download archive
            self.stdout.write(f"  ⬇️  Downloading...")
            response = requests.get(bootstrap_url, timeout=120)
            response.raise_for_status()
            
            with open(archive_path, "wb") as f:
                f.write(response.content)
                
            self.stdout.write(f"  ✅ Downloaded {len(response.content):,} bytes")
            
            # Verify SHA256 hash if provided
            if bootstrap_sha:
                with open(archive_path, "rb") as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                
                if actual_hash != bootstrap_sha:
                    raise RuntimeError(
                        f"❌ SHA256 mismatch!\n"
                        f"  Expected: {bootstrap_sha}\n"
                        f"  Actual:   {actual_hash}"
                    )
                self.stdout.write(f"  🔐 SHA256 verified")
            
            # Extract archive
            self.stdout.write(f"  📦 Extracting archive...")
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(temp_dir)
            
            # Find extracted data directory
            extracted_data_dir = os.path.join(temp_dir, "data", "raw")
            if not os.path.isdir(extracted_data_dir):
                # Try alternative structure
                extracted_data_dir = os.path.join(temp_dir, "raw")
                if not os.path.isdir(extracted_data_dir):
                    raise RuntimeError(f"❌ Archive doesn't contain expected data/raw directory")
            
            self.stdout.write(f"  ✅ Using extracted data: {extracted_data_dir}")
            return extracted_data_dir
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"❌ Failed to download bootstrap data: {e}")
        except Exception as e:
            raise RuntimeError(f"❌ Error processing bootstrap data: {e}")
        finally:
            # Clean up archive file (but keep extracted data)
            if os.path.exists(archive_path):
                os.unlink(archive_path)
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='./data/raw',
            help='Directory containing Excel files'
        )
        parser.add_argument(
            '--skip-import',
            action='store_true',
            help='Skip data import (use existing data)'
        )
        parser.add_argument(
            '--skip-plans',
            action='store_true',
            help='Skip test plan generation'
        )
        parser.add_argument(
            '--force-download',
            action='store_true',
            help='Force download of bootstrap data even if local dir exists'
        )

    def handle(self, *args, **options):
        data_dir = options['data_dir']
        skip_import = options['skip_import']
        skip_plans = options['skip_plans']
        force_download = options['force_download']
        
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
        
        # Step 2: Resolve data directory and import exercises (if not skipped)
        if not skip_import:
            self.stdout.write("\n2️⃣ Resolving data directory and importing exercises...")
            try:
                resolved_data_dir = self._resolve_data_dir(data_dir, force_download)
                self.stdout.write(f"📦 Using data dir: {resolved_data_dir}")
                
                call_command('import_exercises_v2', data_dir=resolved_data_dir, verbosity=1)
                self.stdout.write(self.style.SUCCESS("  ✅ Import completed"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Import failed: {e}"))
                if "No data directory" in str(e) or "BOOTSTRAP_DATA_URL" in str(e):
                    self.stdout.write(self.style.WARNING(
                        "  💡 Set BOOTSTRAP_DATA_URL environment variable for automatic data download"
                    ))
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