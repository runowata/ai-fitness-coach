"""
Полная настройка системы под реальное Cloudflare R2 хранилище
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Setup complete system based on real Cloudflare R2 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-load',
            action='store_true',
            help='Skip data loading from R2',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*70)
        self.stdout.write("🚀 НАСТРОЙКА СИСТЕМЫ ПОД РЕАЛЬНОЕ R2 ХРАНИЛИЩЕ")
        self.stdout.write("="*70)
        
        self.stdout.write("\n📋 ПЛАН РАБОТЫ:")
        self.stdout.write("1. Исследование структуры R2")
        self.stdout.write("2. Загрузка данных из R2") 
        self.stdout.write("3. Тестирование видео системы")
        self.stdout.write("4. Тестирование изображений")
        self.stdout.write("5. Тестирование плейлистов")
        self.stdout.write("6. Тестирование мотивационных карточек")
        self.stdout.write("7. Итоговый отчет")
        
        try:
            # Шаг 1: Исследование R2
            self.stdout.write("\n🔍 STEP 1: Исследование структуры R2...")
            call_command('explore_r2_structure')
            self.stdout.write("✅ R2 structure analyzed")
            
            # Шаг 2: Загрузка данных
            if not options.get('skip_load'):
                self.stdout.write("\n📥 STEP 2: Загрузка данных из R2...")
                call_command('load_r2_data', '--clear')
                self.stdout.write("✅ Data loaded from R2")
            else:
                self.stdout.write("\n⏭️ STEP 2: Skipped data loading")
            
            # Шаг 3-6: Тестирование всех компонентов
            self.stdout.write("\n🧪 STEP 3-6: Комплексное тестирование...")
            call_command('test_r2_system', '--full-test')
            self.stdout.write("✅ All systems tested")
            
            # Шаг 7: Итоговый отчет
            self.stdout.write("\n📊 STEP 7: Итоговый отчет...")
            self._generate_final_report()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Setup failed: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🎉 СИСТЕМА УСПЕШНО НАСТРОЕНА ПОД РЕАЛЬНОЕ R2!")
        self.stdout.write("="*70)
        
        self.stdout.write("\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        self.stdout.write("1. Создать migration для новых моделей")
        self.stdout.write("2. Обновить views для использования R2Video и R2Image")  
        self.stdout.write("3. Обновить шаблоны для мотивационных карточек")
        self.stdout.write("4. Протестировать фронтенд")
        self.stdout.write("5. Запустить E2E тесты")
        self.stdout.write("6. Деплой в продакшн")
    
    def _generate_final_report(self):
        """Генерирует итоговый отчет о системе"""
        from apps.workouts.models import R2Video, R2Image
        
        self.stdout.write("📊 ИТОГОВАЯ СТАТИСТИКА:")
        self.stdout.write("-" * 40)
        
        # Видео статистика
        total_videos = R2Video.objects.count()
        self.stdout.write(f"🎬 Всего видео: {total_videos}")
        
        video_categories = R2Video.objects.values_list('category', flat=True).distinct()
        for category in video_categories:
            count = R2Video.objects.filter(category=category).count()
            self.stdout.write(f"  - {category}: {count}")
        
        # Изображения статистика
        total_images = R2Image.objects.count()
        self.stdout.write(f"\n🖼️ Всего изображений: {total_images}")
        
        image_categories = R2Image.objects.values_list('category', flat=True).distinct()
        for category in image_categories:
            count = R2Image.objects.filter(category=category).count()
            self.stdout.write(f"  - {category}: {count}")
        
        # Готовность системы
        self.stdout.write(f"\n✅ ГОТОВНОСТЬ СИСТЕМЫ:")
        
        exercises_ready = R2Video.objects.filter(category='exercises').count() >= 250
        self.stdout.write(f"  - Упражнения: {'✅' if exercises_ready else '❌'}")
        
        motivation_ready = R2Video.objects.filter(category='motivation').count() >= 300
        self.stdout.write(f"  - Мотивация: {'✅' if motivation_ready else '❌'}")
        
        cards_ready = R2Image.objects.filter(category='quotes').count() >= 500
        self.stdout.write(f"  - Карточки: {'✅' if cards_ready else '❌'}")
        
        avatars_ready = R2Image.objects.filter(category='avatars').count() >= 5
        self.stdout.write(f"  - Аватары: {'✅' if avatars_ready else '❌'}")
        
        if exercises_ready and motivation_ready and cards_ready and avatars_ready:
            self.stdout.write(f"\n🎉 ВСЁ ГОТОВО ДЛЯ ПРОДАКШНА!")
        else:
            self.stdout.write(f"\n⚠️ Требуется дополнительная настройка")
            
        self.stdout.write(f"\n🔗 ТЕСТОВЫЕ URL:")
        
        # Примеры URL для тестирования
        exercise_video = R2Video.objects.filter(category='exercises').first()
        if exercise_video:
            self.stdout.write(f"  Упражнение: {exercise_video.r2_url}")
        
        quote_image = R2Image.objects.filter(category='quotes').first()
        if quote_image:
            self.stdout.write(f"  Карточка: {quote_image.r2_url}")
        
        avatar_image = R2Image.objects.filter(category='avatars').first()
        if avatar_image:
            self.stdout.write(f"  Аватар: {avatar_image.r2_url}")