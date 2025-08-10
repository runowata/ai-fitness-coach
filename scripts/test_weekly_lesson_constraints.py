#!/usr/bin/env python
"""
Test script to verify WeeklyLesson table constraints after migration fix
Run: python scripts/test_weekly_lesson_constraints.py
"""

import os
import sys
import django
from django.db import connection, IntegrityError

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.workouts.models import WeeklyLesson


def test_table_exists():
    """Check if weekly_lessons table exists"""
    print("🔍 Testing table existence...")
    
    with connection.cursor() as cursor:
        db_vendor = connection.vendor
        
        if db_vendor == 'postgresql':
            cursor.execute("SELECT to_regclass('public.weekly_lessons');")
            result = cursor.fetchone()[0]
            
            if result:
                print(f"  ✅ Table exists: {result}")
                return True
            else:
                print("  ❌ Table weekly_lessons does not exist")
                return False
        else:
            # For SQLite, check if we can query the table
            try:
                cursor.execute("SELECT COUNT(*) FROM weekly_lessons;")
                count = cursor.fetchone()[0]
                print(f"  ✅ Table exists (SQLite): weekly_lessons with {count} records")
                return True
            except Exception as e:
                print(f"  ❌ Table weekly_lessons does not exist (SQLite): {e}")
                return False


def test_unique_constraints():
    """Check unique constraints on weekly_lessons table"""
    print("🔍 Testing unique constraints...")
    
    with connection.cursor() as cursor:
        db_vendor = connection.vendor
        
        if db_vendor == 'postgresql':
            cursor.execute("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'weekly_lessons'::regclass AND contype = 'u';
            """)
            
            constraints = cursor.fetchall()
            if constraints:
                print(f"  ✅ Found {len(constraints)} unique constraints:")
                for name, definition in constraints:
                    print(f"    - {name}: {definition}")
                return True
            else:
                print("  ⚠️  No unique constraints found")
                return False
        else:
            # For SQLite, check index information
            try:
                cursor.execute("PRAGMA index_list(weekly_lessons);")
                indexes = cursor.fetchall()
                unique_indexes = [idx for idx in indexes if idx[2] == 1]  # unique=1
                
                if unique_indexes:
                    print(f"  ✅ Found {len(unique_indexes)} unique indexes (SQLite):")
                    for idx in unique_indexes:
                        print(f"    - {idx[1]} (unique)")
                    return True
                else:
                    print("  ⚠️  No unique constraints found (SQLite)")
                    return False
            except Exception as e:
                print(f"  ❌ Error checking constraints (SQLite): {e}")
                return False


def test_django_model_uniqueness():
    """Test Django model unique constraint enforcement"""
    print("🔍 Testing Django model uniqueness...")
    
    # Clean up any existing test data
    WeeklyLesson.objects.filter(week=999, archetype="111").delete()
    
    try:
        # Create first record
        wl1 = WeeklyLesson.objects.create(
            week=999, 
            archetype="111", 
            locale="ru", 
            title="Test 1", 
            script="Test script 1"
        )
        print("  ✅ First record created successfully")
        
        # Try to create duplicate - should fail
        try:
            wl2 = WeeklyLesson.objects.create(
                week=999, 
                archetype="111", 
                locale="ru", 
                title="Test 2", 
                script="Test script 2"
            )
            print("  ❌ Uniqueness constraint failed - duplicate was allowed!")
            wl2.delete()
            return False
        except IntegrityError as e:
            print(f"  ✅ Uniqueness constraint working: {e}")
            return True
        finally:
            # Clean up
            wl1.delete()
            
    except Exception as e:
        print(f"  ❌ Error testing model uniqueness: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 WeeklyLesson Constraint Tests")
    print("=" * 50)
    
    tests = [
        ("Table Existence", test_table_exists),
        ("Unique Constraints", test_unique_constraints), 
        ("Django Model Uniqueness", test_django_model_uniqueness),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
            print()
        except Exception as e:
            print(f"  ❌ {name} test failed with error: {e}")
            results.append(False)
            print()
    
    # Summary
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    for i, (name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! WeeklyLesson constraints are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed - review database setup")
        return 1


if __name__ == "__main__":
    sys.exit(main())