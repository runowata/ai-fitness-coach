#!/usr/bin/env python3
"""
Diagnostic script to understand migration loading issues
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db import migrations
from django.db.migrations.loader import MigrationLoader
import importlib

def diagnose_migrations():
    print("=== MIGRATION DIAGNOSTICS ===")
    
    # 1. Check workouts app configuration
    try:
        workouts_app = apps.get_app_config('workouts')
        print(f"✅ Workouts app found: {workouts_app.name}")
        print(f"   Path: {workouts_app.path}")
        print(f"   Label: {workouts_app.label}")
    except Exception as e:
        print(f"❌ Workouts app error: {e}")
        return
    
    # 2. Check migrations directory
    migrations_dir = Path(workouts_app.path) / 'migrations'
    print(f"\n📁 Migrations directory: {migrations_dir}")
    if migrations_dir.exists():
        migration_files = sorted([f.name for f in migrations_dir.glob('*.py') if not f.name.startswith('__')])
        print(f"   Files found: {len(migration_files)}")
        for f in migration_files:
            print(f"   - {f}")
    else:
        print("   ❌ Directory not found!")
        return
    
    # 3. Try to import 0013_v2_schema specifically
    print(f"\n🔍 Testing 0013_v2_schema import:")
    try:
        mod = importlib.import_module('apps.workouts.migrations.0013_v2_schema')
        migration_class = getattr(mod, 'Migration', None)
        if migration_class:
            print(f"   ✅ Module imported successfully")
            print(f"   Dependencies: {getattr(migration_class, 'dependencies', 'None')}")
            print(f"   Replaces: {getattr(migration_class, 'replaces', 'None')}")
        else:
            print(f"   ❌ No Migration class found")
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
    
    # 4. Check Django migration loader
    print(f"\n🔄 Django MigrationLoader analysis:")
    try:
        loader = MigrationLoader(None)
        workouts_migrations = loader.graph.nodes.get(('workouts',), {})
        
        print(f"   Loaded migrations for workouts: {len(workouts_migrations)}")
        for migration_name in sorted(workouts_migrations.keys()):
            print(f"   - {migration_name}")
        
        # Check for leaf nodes
        leaf_nodes = loader.graph.leaf_nodes()
        workouts_leaves = [node for node in leaf_nodes if node[0] == 'workouts']
        print(f"\n   Leaf nodes in workouts: {workouts_leaves}")
        
        # Check if 0013_v2_schema is in the graph
        if ('workouts', '0013_v2_schema') in workouts_migrations:
            print(f"   ✅ 0013_v2_schema found in migration graph")
            node = loader.graph.nodes[('workouts', '0013_v2_schema')]
            print(f"   Dependencies: {node.dependencies}")
        else:
            print(f"   ❌ 0013_v2_schema NOT found in migration graph")
    
    except Exception as e:
        print(f"   ❌ MigrationLoader error: {e}")
    
    print(f"\n=== DIAGNOSTICS COMPLETE ===")

if __name__ == "__main__":
    diagnose_migrations()