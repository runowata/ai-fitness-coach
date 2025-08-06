import os
import yaml
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.workouts.models import WeeklyLesson


class Command(BaseCommand):
    help = 'Load weekly lessons from YAML files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--content-path',
            type=str,
            default='content/weekly',
            help='Path to weekly content YAML files (default: content/weekly)'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing lessons with same week/archetype/locale'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be loaded without actually loading'
        )

    def handle(self, *args, **options):
        content_path = options['content_path']
        overwrite = options['overwrite']
        dry_run = options['dry_run']
        
        # Build full path
        if not os.path.isabs(content_path):
            content_path = os.path.join(settings.BASE_DIR, content_path)
        
        if not os.path.exists(content_path):
            raise CommandError(f'Content directory does not exist: {content_path}')
        
        loaded_count = 0
        skipped_count = 0
        updated_count = 0
        
        # Find all YAML files in content path
        yaml_files = []
        for filename in os.listdir(content_path):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                yaml_files.append(os.path.join(content_path, filename))
        
        yaml_files.sort()  # Process in order
        
        if not yaml_files:
            self.stdout.write(
                self.style.WARNING(f'No YAML files found in {content_path}')
            )
            return
        
        for yaml_file in yaml_files:
            self.stdout.write(f'Processing {yaml_file}...')
            
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                week_number = data.get('week')
                title = data.get('title', f'Week {week_number}')
                lessons = data.get('lessons', [])
                
                if not week_number:
                    self.stdout.write(
                        self.style.ERROR(f'No week number found in {yaml_file}')
                    )
                    continue
                
                if not lessons:
                    self.stdout.write(
                        self.style.WARNING(f'No lessons found in {yaml_file}')
                    )
                    continue
                
                for lesson_data in lessons:
                    archetype = lesson_data.get('archetype')
                    locale = lesson_data.get('locale', 'ru')
                    script = lesson_data.get('script', '').strip()
                    
                    if not archetype or not script:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Missing archetype or script in {yaml_file}'
                            )
                        )
                        continue
                    
                    if dry_run:
                        self.stdout.write(
                            f'  Would create/update: Week {week_number}, '
                            f'Archetype {archetype}, Locale {locale}'
                        )
                        loaded_count += 1
                        continue
                    
                    # Check if lesson already exists
                    existing = WeeklyLesson.objects.filter(
                        week=week_number,
                        archetype=archetype,
                        locale=locale
                    ).first()
                    
                    if existing:
                        if overwrite:
                            existing.title = title
                            existing.script = script
                            existing.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  Updated: Week {week_number}, '
                                    f'Archetype {archetype}, Locale {locale}'
                                )
                            )
                            updated_count += 1
                        else:
                            self.stdout.write(
                                f'  Skipped (exists): Week {week_number}, '
                                f'Archetype {archetype}, Locale {locale}'
                            )
                            skipped_count += 1
                    else:
                        # Create new lesson
                        WeeklyLesson.objects.create(
                            week=week_number,
                            archetype=archetype,
                            locale=locale,
                            title=title,
                            script=script
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  Created: Week {week_number}, '
                                f'Archetype {archetype}, Locale {locale}'
                            )
                        )
                        loaded_count += 1
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {yaml_file}: {e}')
                )
                continue
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would load {loaded_count} lessons'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Loaded {loaded_count} lessons, updated {updated_count}, '
                    f'skipped {skipped_count}'
                )
            )