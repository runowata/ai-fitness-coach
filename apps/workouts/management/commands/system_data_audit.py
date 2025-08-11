from django.core.management.base import BaseCommand
from django.db import connection
from apps.workouts.models import CSVExercise, VideoClip, DailyWorkout, WorkoutPlan
from apps.workouts.constants import VideoKind, Archetype
from apps.users.models import User
import json


class Command(BaseCommand):
    help = "Audit system data: exercises, videos, users, plans"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', help='Verbose output')
        parser.add_argument('--check-r2', action='store_true', help='Check R2 storage connectivity')

    def handle(self, *args, **options):
        verbose = options['verbose']
        check_r2 = options['check_r2']
        
        self.stdout.write("🔍 СИСТЕМА ДАННЫХ - ПОЛНЫЙ АУДИТ")
        self.stdout.write("=" * 50)
        
        # 1. Проверка упражнений
        self.audit_exercises(verbose)
        
        # 2. Проверка видео клипов
        self.audit_video_clips(verbose)
        
        # 3. Проверка пользователей и планов
        self.audit_users_and_plans(verbose)
        
        # 4. Проверка связи с R2
        if check_r2:
            self.audit_r2_storage(verbose)
        
        # 5. Итоговый отчет
        self.generate_summary()

    def audit_exercises(self, verbose):
        """Проверка упражнений в базе данных"""
        self.stdout.write("\n📚 УПРАЖНЕНИЯ")
        self.stdout.write("-" * 20)
        
        total_exercises = CSVExercise.objects.count()
        active_exercises = CSVExercise.objects.filter(is_active=True).count()
        
        self.stdout.write(f"📊 Всего упражнений: {total_exercises}")
        self.stdout.write(f"📊 Активных упражнений: {active_exercises}")
        
        if total_exercises == 0:
            self.stdout.write(self.style.ERROR("❌ КРИТИЧНО: Нет упражнений в базе данных!"))
            self.stdout.write("   💡 Нужно запустить: python manage.py import_exercises_v2")
            return
        
        # Проверка категорий упражнений
        if verbose:
            self.stdout.write("\n📋 Категории упражнений:")
            categories = CSVExercise.objects.values('category').distinct()
            for cat in categories:
                count = CSVExercise.objects.filter(category=cat['category']).count()
                self.stdout.write(f"   • {cat['category']}: {count} упражнений")
        
        # Примеры упражнений
        sample_exercises = CSVExercise.objects.all()[:5]
        if sample_exercises:
            self.stdout.write("\n📝 Примеры упражнений:")
            for ex in sample_exercises:
                self.stdout.write(f"   • {ex.id}: {ex.name}")

    def audit_video_clips(self, verbose):
        """Проверка видео клипов"""
        self.stdout.write("\n🎬 ВИДЕО КЛИПЫ")
        self.stdout.write("-" * 20)
        
        total_clips = VideoClip.objects.count()
        active_clips = VideoClip.objects.filter(is_active=True).count()
        placeholder_clips = VideoClip.objects.filter(is_placeholder=True).count()
        
        self.stdout.write(f"📊 Всего видео клипов: {total_clips}")
        self.stdout.write(f"📊 Активных клипов: {active_clips}")
        self.stdout.write(f"📊 Placeholder клипов: {placeholder_clips}")
        
        if total_clips == 0:
            self.stdout.write(self.style.ERROR("❌ КРИТИЧНО: Нет видео клипов в базе данных!"))
            self.stdout.write("   💡 Нужно запустить bootstrap команды для загрузки видео")
            return
        
        # Статистика по типам видео
        self.stdout.write("\n📊 Распределение по типам видео:")
        video_kinds = [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION, VideoKind.MISTAKE, 
                      VideoKind.INTRO, VideoKind.CLOSING, VideoKind.WEEKLY]
        
        for kind in video_kinds:
            count = VideoClip.objects.filter(r2_kind=kind).count()
            self.stdout.write(f"   • {kind}: {count} клипов")
        
        # Статистика по архетипам
        self.stdout.write("\n👤 Распределение по архетипам:")
        archetypes = ['mentor', 'professional', 'peer', 'bro', 'sergeant', 'intellectual']
        
        for archetype in archetypes:
            count = VideoClip.objects.filter(r2_archetype=archetype).count()
            if count > 0:
                self.stdout.write(f"   • {archetype}: {count} клипов")
        
        # Проверка покрытия упражнений видео
        exercises_with_video = VideoClip.objects.filter(
            exercise__isnull=False
        ).values('exercise').distinct().count()
        
        total_exercises = CSVExercise.objects.count()
        if total_exercises > 0:
            coverage_percent = (exercises_with_video / total_exercises) * 100
            self.stdout.write(f"\n🎯 Покрытие упражнений видео: {exercises_with_video}/{total_exercises} ({coverage_percent:.1f}%)")
        
        if verbose and VideoClip.objects.exists():
            # Примеры видео
            self.stdout.write("\n📝 Примеры видео клипов:")
            sample_clips = VideoClip.objects.all()[:5]
            for clip in sample_clips:
                exercise_name = clip.exercise.name if clip.exercise else "Глобальное видео"
                self.stdout.write(f"   • {clip.id}: {exercise_name} - {clip.r2_kind} ({clip.r2_archetype})")

    def audit_users_and_plans(self, verbose):
        """Проверка пользователей и планов тренировок"""
        self.stdout.write("\n👥 ПОЛЬЗОВАТЕЛИ И ПЛАНЫ")
        self.stdout.write("-" * 25)
        
        total_users = User.objects.count()
        users_with_plans = User.objects.filter(workout_plans__isnull=False).distinct().count()
        total_plans = WorkoutPlan.objects.count()
        active_plans = WorkoutPlan.objects.filter(is_active=True).count()
        total_workouts = DailyWorkout.objects.count()
        completed_workouts = DailyWorkout.objects.filter(completed_at__isnull=False).count()
        
        self.stdout.write(f"📊 Всего пользователей: {total_users}")
        self.stdout.write(f"📊 Пользователей с планами: {users_with_plans}")
        self.stdout.write(f"📊 Всего планов тренировок: {total_plans}")
        self.stdout.write(f"📊 Активных планов: {active_plans}")
        self.stdout.write(f"📊 Всего тренировок: {total_workouts}")
        self.stdout.write(f"📊 Завершенных тренировок: {completed_workouts}")
        
        if verbose and total_plans > 0:
            # Статистика по архетипам планов
            self.stdout.write("\n👤 Планы по архетипам:")
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT up.archetype, COUNT(*) 
                    FROM workouts_workoutplan wp
                    JOIN users_userprofile up ON wp.user_id = up.user_id
                    WHERE up.archetype IS NOT NULL
                    GROUP BY up.archetype
                """)
                for row in cursor.fetchall():
                    self.stdout.write(f"   • {row[0]}: {row[1]} планов")

    def audit_r2_storage(self, verbose):
        """Проверка подключения к R2 хранилищу"""
        self.stdout.write("\n☁️  CLOUDFLARE R2 ХРАНИЛИЩЕ")
        self.stdout.write("-" * 30)
        
        try:
            from apps.workouts.video_storage import R2Adapter
            from django.conf import settings
            
            # Проверка настроек R2
            r2_settings = [
                'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 
                'R2_BUCKET_NAME', 'R2_ENDPOINT_URL', 'R2_PUBLIC_URL'
            ]
            
            missing_settings = []
            for setting in r2_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing_settings.append(setting)
            
            if missing_settings:
                self.stdout.write(self.style.ERROR(f"❌ Отсутствуют настройки R2: {', '.join(missing_settings)}"))
            else:
                self.stdout.write("✅ Настройки R2 присутствуют")
                
                if verbose:
                    self.stdout.write(f"   📦 Bucket: {settings.R2_BUCKET_NAME}")
                    self.stdout.write(f"   🌐 Public URL: {settings.R2_PUBLIC_URL}")
            
            # Попробовать создать R2 адаптер
            try:
                r2_adapter = R2Adapter()
                self.stdout.write("✅ R2 адаптер создан успешно")
                
                # Проверить доступность бакета (если есть тестовый клип)
                test_clip = VideoClip.objects.filter(r2_file__isnull=False).first()
                if test_clip:
                    try:
                        exists = r2_adapter.exists(test_clip)
                        if exists:
                            self.stdout.write("✅ Тестовый файл найден в R2")
                        else:
                            self.stdout.write("⚠️  Тестовый файл не найден в R2")
                    except Exception as e:
                        self.stdout.write(f"❌ Ошибка проверки файла в R2: {str(e)}")
                
            except Exception as e:
                self.stdout.write(f"❌ Ошибка создания R2 адаптера: {str(e)}")
                
        except ImportError as e:
            self.stdout.write(f"❌ Ошибка импорта R2 модулей: {str(e)}")

    def generate_summary(self):
        """Генерация итогового отчета"""
        self.stdout.write("\n🎯 ИТОГОВЫЙ ОТЧЕТ")
        self.stdout.write("=" * 20)
        
        # Сбор ключевых метрик
        exercises_count = CSVExercise.objects.count()
        videos_count = VideoClip.objects.count()
        users_count = User.objects.count()
        plans_count = WorkoutPlan.objects.count()
        
        # Определение состояния системы
        system_status = "🟢 ГОТОВА"  # Зеленый
        issues = []
        
        if exercises_count == 0:
            system_status = "🔴 НЕ ГОТОВА"  # Красный
            issues.append("Нет упражнений в базе")
            
        if videos_count == 0:
            system_status = "🔴 НЕ ГОТОВА"
            issues.append("Нет видео клипов в базе")
            
        if exercises_count > 0 and videos_count == 0:
            system_status = "🟡 ЧАСТИЧНО"  # Желтый
            issues.append("Видео плейлисты будут пустыми")
        
        self.stdout.write(f"\n🏗️  Состояние системы: {system_status}")
        
        if issues:
            self.stdout.write("\n⚠️  Обнаруженные проблемы:")
            for issue in issues:
                self.stdout.write(f"   • {issue}")
                
        self.stdout.write(f"\n📊 Ключевые метрики:")
        self.stdout.write(f"   • Упражнения: {exercises_count}")
        self.stdout.write(f"   • Видео клипы: {videos_count}")
        self.stdout.write(f"   • Пользователи: {users_count}")
        self.stdout.write(f"   • Планы тренировок: {plans_count}")
        
        # Рекомендации
        if system_status != "🟢 ГОТОВА":
            self.stdout.write(f"\n💡 Рекомендации для запуска:")
            if exercises_count == 0:
                self.stdout.write("   1. python manage.py import_exercises_v2 --data-dir ./data/raw")
            if videos_count == 0:
                self.stdout.write("   2. python manage.py bootstrap_v2_min")
                self.stdout.write("   3. python manage.py setup_v2_production")
        else:
            self.stdout.write("\n🚀 Система готова к генерации видео плейлистов!")