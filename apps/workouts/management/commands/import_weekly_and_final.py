import yaml
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.workouts.models import WeeklyLesson, FinalVideo


class Command(BaseCommand):
    help = "Импортирует weekly-lessons и финальные видео из YAML файлов"

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-yaml',
            type=str,
            default='content',
            help='Путь к директории с YAML файлами (по умолчанию: content)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет импортировано без создания записей'
        )

    def handle(self, *args, **options):
        content_dir = Path(options['from_yaml'])
        dry_run = options['dry_run']
        
        if not content_dir.exists():
            raise CommandError(f"Директория {content_dir} не существует")
        
        weekly_dir = content_dir / 'weekly'
        final_dir = content_dir / 'final'
        
        created_weekly = 0
        updated_weekly = 0
        created_final = 0
        updated_final = 0
        
        # Import weekly lessons
        if weekly_dir.exists():
            weekly_files = sorted(weekly_dir.glob('week*.yaml'))
            self.stdout.write(f"Найдено {len(weekly_files)} weekly файлов")
            
            for yaml_file in weekly_files:
                self.stdout.write(f"Обрабатываем {yaml_file.name}...")
                
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    week_num = data['week']
                    week_title = data['title']
                    
                    for lesson in data['lessons']:
                        archetype = lesson['archetype']
                        locale = lesson['locale']
                        script = lesson['script'].strip()
                        
                        if dry_run:
                            self.stdout.write(
                                f"  [DRY RUN] Week {week_num}, Archetype {archetype}: {len(script)} chars"
                            )
                            continue
                        
                        obj, created = WeeklyLesson.objects.update_or_create(
                            week=week_num,
                            archetype=archetype,
                            locale=locale,
                            defaults={
                                'title': f"{week_title}",
                                'script': script
                            }
                        )
                        
                        if created:
                            created_weekly += 1
                            self.stdout.write(
                                f"  ✓ Created Week {week_num} - {archetype}"
                            )
                        else:
                            updated_weekly += 1
                            self.stdout.write(
                                f"  ↻ Updated Week {week_num} - {archetype}"
                            )
                            
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Ошибка в {yaml_file.name}: {e}")
                    )
        
        # Import final videos
        if final_dir.exists():
            final_files = list(final_dir.glob('*.yaml'))
            self.stdout.write(f"Найдено {len(final_files)} final файлов")
            
            for yaml_file in final_files:
                self.stdout.write(f"Обрабатываем {yaml_file.name}...")
                
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    archetype = data['archetype']
                    locale = data['locale']
                    script = data['script'].strip()
                    
                    if dry_run:
                        self.stdout.write(
                            f"  [DRY RUN] Final {archetype}: {len(script)} chars"
                        )
                        continue
                    
                    obj, created = FinalVideo.objects.update_or_create(
                        arch=archetype,
                        locale=locale,
                        defaults={'script': script}
                    )
                    
                    if created:
                        created_final += 1
                        self.stdout.write(f"  ✓ Created Final {archetype}")
                    else:
                        updated_final += 1
                        self.stdout.write(f"  ↻ Updated Final {archetype}")
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Ошибка в {yaml_file.name}: {e}")
                    )
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nИмпорт завершен!\n"
                    f"Weekly: Created {created_weekly}, Updated {updated_weekly}\n"
                    f"Final: Created {created_final}, Updated {updated_final}"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("\n[DRY RUN] Никакие данные не были изменены"))