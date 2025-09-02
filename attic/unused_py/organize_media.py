#!/usr/bin/env python3
"""
Local media organization script.
Copies and organizes media files from source to local destination folder.
"""

import argparse
import csv
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import yaml

# File extensions
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg', '.wmv', '.flv'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.gi', '.bmp', '.tif', '.svg', '.webp', '.heic', '.raw'}

def load_categories(yaml_path: Path = Path("media_organizer/categories.yml")) -> Dict[str, str]:
    """Load category mappings from YAML file."""
    if not yaml_path.exists():
        print(f"Warning: {yaml_path} not found. Using default categories.")
        return {}
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        categories_data = yaml.safe_load(f)
    
    # Convert to lowercase for case-insensitive matching
    return {k.lower(): v for k, v in categories_data.items()}

def categorize_file(file_path: Path, categories: Dict[str, str]) -> str:
    """Determine category for a file based on its name."""
    filename_lower = file_path.stem.lower()
    
    for keyword, category in categories.items():
        if keyword in filename_lower:
            return category
    
    # Default categories
    if any(parent.name.lower() == name for parent in file_path.parents 
           for name in ['chest', 'legs', 'back', 'arms', 'shoulders', 'core', 'cardio']):
        return file_path.parent.name.lower()
    
    return 'uncategorized'

def load_rename_log(log_path: Path) -> Set[str]:
    """Load previously processed files from rename_log.csv."""
    if not log_path.exists():
        return set()
    
    logged_paths = set()
    with open(log_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'new_path' in row:
                # Store relative path like "videos/chest/chest_001.mp4"
                logged_paths.add(row['new_path'])
    
    return logged_paths

def scan_destination(dest_path: Path) -> Set[str]:
    """Scan destination folder for existing files."""
    dest_paths = set()
    
    if not dest_path.exists():
        return dest_paths
    
    for file_path in dest_path.rglob('*'):
        if file_path.is_file():
            # Store relative path from dest_path
            relative = file_path.relative_to(dest_path)
            dest_paths.add(str(relative))
    
    return dest_paths

def find_duplicates(dest_path: Path) -> List[Path]:
    """Find duplicate files in destination (same folder and name)."""
    file_map = defaultdict(list)
    
    if not dest_path.exists():
        return []
    
    for file_path in dest_path.rglob('*'):
        if file_path.is_file():
            key = (file_path.parent.relative_to(dest_path), file_path.name)
            file_map[key].append(file_path)
    
    duplicates_to_remove = []
    for key, paths in file_map.items():
        if len(paths) > 1:
            # Keep the oldest file (earliest mtime)
            paths.sort(key=lambda p: p.stat().st_mtime)
            duplicates_to_remove.extend(paths[1:])  # Remove all but the oldest
    
    return duplicates_to_remove

def get_next_counter(dest_path: Path, media_type: str, category: str) -> int:
    """Get the next available counter for a category."""
    category_path = dest_path / media_type / category
    
    if not category_path.exists():
        return 1
    
    max_num = 0
    for file_path in category_path.glob(f"{category}_*.*"):
        try:
            # Extract number from filename like "chest_014.mp4"
            parts = file_path.stem.split('_')
            if len(parts) >= 2 and parts[-1].isdigit():
                num = int(parts[-1])
                max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue
    
    return max_num + 1

def copy_file(source: Path, dest: Path, dry_run: bool = False) -> bool:
    """Copy file from source to destination."""
    if dry_run:
        print(f"  [DRY-RUN] Would copy: {source.name} → {dest}")
        return True
    
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        print(f"  Copied: {source.name} → {dest.relative_to(dest.parent.parent.parent)}")
        return True
    except Exception as e:
        print(f"  ERROR copying {source}: {e}")
        return False

def write_log_entry(log_path: Path, source_path: str, new_path: str, append: bool = True):
    """Write an entry to rename_log.csv."""
    mode = 'a' if append and log_path.exists() else 'w'
    write_header = not log_path.exists() or mode == 'w'
    
    with open(log_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['original_path', 'new_path'])
        if write_header:
            writer.writeheader()
        writer.writerow({
            'original_path': source_path,
            'new_path': new_path
        })

def main():
    parser = argparse.ArgumentParser(description='Organize media files locally')
    parser.add_argument('--source', default='/Volumes/fitnes ai/', 
                        help='Source directory path')
    parser.add_argument('--dest', default='./organized_media',
                        help='Destination directory path')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from previous run, skip already copied files')
    parser.add_argument('--dedup', action='store_true',
                        help='Remove duplicates in destination before copying')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview actions without copying/deleting files')
    
    args = parser.parse_args()
    
    # Convert paths
    source_path = Path(args.source)
    dest_path = Path(args.dest)
    log_path = Path('media_organizer/rename_log.csv')
    
    # Ensure media_organizer directory exists for log
    log_path.parent.mkdir(exist_ok=True)
    
    # Check source exists
    if not source_path.exists():
        print(f"ERROR: Source path does not exist: {source_path}")
        return 1
    
    print(f"Source: {source_path}")
    print(f"Destination: {dest_path}")
    print(f"Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")
    print("-" * 50)
    
    # Load categories
    categories = load_categories()
    print(f"Loaded {len(categories)} category mappings")
    
    # Track already processed files if resuming
    already_present = set()
    if args.resume:
        logged_paths = load_rename_log(log_path)
        dest_paths = scan_destination(dest_path)
        already_present = logged_paths | dest_paths
        print(f"Resume mode: Found {len(already_present)} existing files")
    
    # Handle deduplication
    duplicates_removed = 0
    if args.dedup:
        duplicates = find_duplicates(dest_path)
        duplicates_removed = len(duplicates)
        if duplicates:
            print(f"\nFound {duplicates_removed} duplicate files to remove")
            for dup_path in duplicates:
                if not args.dry_run:
                    dup_path.unlink()
                    print(f"  Removed duplicate: {dup_path.relative_to(dest_path)}")
                else:
                    print(f"  [DRY-RUN] Would remove: {dup_path.relative_to(dest_path)}")
    
    # Scan source for media files
    print("\nScanning source directory...")
    all_files = []
    for ext in VIDEO_EXTS | PHOTO_EXTS:
        all_files.extend(source_path.rglob(f'*{ext}'))
        all_files.extend(source_path.rglob(f'*{ext.upper()}'))
    
    print(f"Found {len(all_files)} media files in source")
    
    # Process files
    skipped = 0
    videos_copied = 0
    photos_copied = 0
    counters = defaultdict(lambda: defaultdict(int))  # counters[media_type][category]
    
    # Pre-populate counters for existing files
    if dest_path.exists():
        for media_type in ['videos', 'photos']:
            type_path = dest_path / media_type
            if type_path.exists():
                for category_path in type_path.iterdir():
                    if category_path.is_dir():
                        category = category_path.name
                        counters[media_type][category] = get_next_counter(
                            dest_path, media_type, category
                        )
    
    print("\nProcessing files...")
    for file_path in sorted(all_files):
        # Determine media type
        ext = file_path.suffix.lower()
        if ext in VIDEO_EXTS:
            media_type = 'videos'
        elif ext in PHOTO_EXTS:
            media_type = 'photos'
        else:
            continue
        
        # Categorize
        category = categorize_file(file_path, categories)
        
        # Get counter for this category
        if category not in counters[media_type]:
            counters[media_type][category] = get_next_counter(dest_path, media_type, category)
        
        counter = counters[media_type][category]
        
        # Generate new filename
        new_name = f"{category}_{counter:03d}{ext}"
        relative_path = f"{media_type}/{category}/{new_name}"
        
        # Check if already processed
        if relative_path in already_present:
            skipped += 1
            continue
        
        # Copy file
        dest_file = dest_path / media_type / category / new_name
        if copy_file(file_path, dest_file, args.dry_run):
            if not args.dry_run:
                write_log_entry(log_path, str(file_path), relative_path, args.resume)
            
            if media_type == 'videos':
                videos_copied += 1
            else:
                photos_copied += 1
            
            counters[media_type][category] += 1
    
    # Final count of files in destination
    final_videos = 0
    final_photos = 0
    if dest_path.exists():
        videos_path = dest_path / 'videos'
        if videos_path.exists():
            final_videos = sum(1 for _ in videos_path.rglob('*') if _.is_file())
        
        photos_path = dest_path / 'photos'
        if photos_path.exists():
            final_photos = sum(1 for _ in photos_path.rglob('*') if _.is_file())
    
    # Report
    print("\n" + "=" * 50)
    print("ORGANIZATION COMPLETE")
    print("-" * 50)
    print(f"Files skipped (already exist):  {skipped:>5}")
    print(f"Duplicates removed (--dedup):   {duplicates_removed:>5}")
    print(f"New videos copied:              {videos_copied:>5}")
    print(f"New photos copied:              {photos_copied:>5}")
    print(f"Total files in destination:     {final_videos:>5} videos / {final_photos} photos")
    print("=" * 50)
    
    if args.dry_run:
        print("\n⚠️  DRY-RUN MODE - No files were actually copied or deleted")
    
    return 0

if __name__ == '__main__':
    exit(main())