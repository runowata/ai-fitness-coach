
from django.core.management.base import BaseCommand

from apps.workouts.constants import ARCHETYPE_FALLBACK_ORDER, PLAYLIST_MISTAKE_PROB, VideoKind


class Command(BaseCommand):
    help = "Detailed analysis of video playlist generation mechanism"

    def add_arguments(self, parser):
        parser.add_argument('--verbose', action='store_true', help='Verbose output')

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        self.stdout.write("🎬 МЕХАНИЗМ РАБОТЫ ВИДЕО ПЛЕЙЛИСТОВ")
        self.stdout.write("=" * 50)
        
        # 1. Структура плейлиста
        self.analyze_playlist_structure(verbose)
        
        # 2. Типы видео и их появление
        self.analyze_video_types(verbose)
        
        # 3. Система контроля повторений
        self.analyze_deduplication_system(verbose)
        
        # 4. Архетипы и fallback
        self.analyze_archetype_system(verbose)
        
        # 5. Cloudflare R2 структура
        self.analyze_r2_structure(verbose)

    def analyze_playlist_structure(self, verbose):
        """Анализ структуры плейлиста"""
        self.stdout.write("\n📋 СТРУКТУРА ПЛЕЙЛИСТА")
        self.stdout.write("-" * 25)
        
        playlist_flow = [
            "1. 🎬 INTRO видео (приветствие тренера)",
            "2. 💪 УПРАЖНЕНИЯ:",
            "   • TECHNIQUE видео (техника выполнения)",
            "   • INSTRUCTION видео (мотивация от архетипа)", 
            "   • MISTAKE видео (30% вероятность)",
            "3. 🏆 WEEKLY видео (только в день 7 недели)",
            "4. 🎯 REST DAY видео (только в дни отдыха)"
        ]
        
        for step in playlist_flow:
            self.stdout.write(f"   {step}")
            
        if verbose:
            self.stdout.write("\n🎯 Детали генерации:")
            self.stdout.write(f"   • Mistake видео: {PLAYLIST_MISTAKE_PROB * 100}% вероятность")
            self.stdout.write("   • Deterministic selection: Основан на workout_id + week + day + archetype")
            self.stdout.write("   • Storage validation: Проверка существования файла в R2")

    def analyze_video_types(self, verbose):
        """Анализ типов видео"""
        self.stdout.write("\n🎥 ТИПЫ ВИДЕО И ИХ РОЛЬ")
        self.stdout.write("-" * 25)
        
        video_types = {
            VideoKind.INTRO: {
                "name": "Приветствие тренера",
                "when": "В начале каждой тренировки",
                "content": "Общее приветствие и настройка на тренировку",
                "archetype_specific": True,
                "required": False
            },
            VideoKind.TECHNIQUE: {
                "name": "Техника выполнения",
                "when": "Для каждого упражнения",
                "content": "Демонстрация правильной техники",
                "archetype_specific": False,
                "required": True
            },
            VideoKind.INSTRUCTION: {
                "name": "Инструкция и мотивация",
                "when": "Для каждого упражнения",
                "content": "Персональные инструкции от архетипа",
                "archetype_specific": True,
                "required": True
            },
            VideoKind.MISTAKE: {
                "name": "Частые ошибки", 
                "when": "30% вероятность для упражнения",
                "content": "Разбор типичных ошибок",
                "archetype_specific": True,
                "required": False
            },
            VideoKind.WEEKLY: {
                "name": "Еженедельная мотивация",
                "when": "7-й день недели или день отдыха",
                "content": "Поздравления с завершением недели",
                "archetype_specific": True,
                "required": False
            },
            VideoKind.CLOSING: {
                "name": "Завершение недели",
                "when": "В конце недели",
                "content": "Подведение итогов недели",
                "archetype_specific": True,
                "required": False
            }
        }
        
        for kind, info in video_types.items():
            status = "✅ ОБЯЗАТЕЛЬНО" if info["required"] else "🔍 ОПЦИОНАЛЬНО"
            archetype_note = "🎭 По архетипам" if info["archetype_specific"] else "🔄 Универсально"
            
            self.stdout.write(f"\n📹 {kind.upper()} ({info['name']})")
            self.stdout.write(f"   {status} | {archetype_note}")
            self.stdout.write(f"   📅 Когда: {info['when']}")
            self.stdout.write(f"   📝 Контент: {info['content']}")

    def analyze_deduplication_system(self, verbose):
        """Анализ системы контроля повторений"""
        self.stdout.write("\n🔄 СИСТЕМА КОНТРОЛЯ ПОВТОРЕНИЙ")
        self.stdout.write("-" * 35)
        
        self.stdout.write("🎯 Deterministic Selection:")
        self.stdout.write("   • Seed: MD5(workout_id + week_number + day_number + archetype)")
        self.stdout.write("   • Один и тот же workout всегда даст одинаковый плейлист")
        self.stdout.write("   • Разные пользователи с одинаковыми параметрами = разные видео")
        
        self.stdout.write("\n🔍 Multi-Level Fallback:")
        self.stdout.write("   Level 1: Точное совпадение (exercise + kind + archetype)")
        self.stdout.write("   Level 2: Fallback по архетипу")
        self.stdout.write("   Level 3: Пропуск опциональных видео")
        
        self.stdout.write("\n⚡ Storage Retry Mechanism:")
        self.stdout.write("   • Проверка существования файла в R2")
        self.stdout.write("   • До 2 попыток выбора альтернативного клипа")
        self.stdout.write("   • Исключение недоступных файлов из candidates")
        
        self.stdout.write("\n🎲 Randomization Control:")
        self.stdout.write("   • RNG.choice() с фиксированным seed")
        self.stdout.write("   • Воспроизводимые результаты")
        self.stdout.write("   • Исключение exclude_id для избежания повторов")

    def analyze_archetype_system(self, verbose):
        """Анализ системы архетипов"""
        self.stdout.write("\n👤 СИСТЕМА АРХЕТИПОВ И FALLBACK")
        self.stdout.write("-" * 35)
        
        self.stdout.write("🎭 Архетипы тренеров:")
        archetype_descriptions = {
            "mentor": "Мудрый наставник - поддержка и мудрость",
            "professional": "Успешный профессионал - эффективность и результат", 
            "peer": "Близкий по духу ровесник - дружба и понимание"
        }
        
        for archetype, description in archetype_descriptions.items():
            self.stdout.write(f"   • {archetype}: {description}")
        
        self.stdout.write("\n🔄 Fallback Order:")
        for primary, fallbacks in ARCHETYPE_FALLBACK_ORDER.items():
            fallback_chain = " → ".join(fallbacks)
            self.stdout.write(f"   • {primary}: {fallback_chain}")
        
        self.stdout.write("\n📊 Принцип работы:")
        self.stdout.write("   1. Ищем видео для основного архетипа")
        self.stdout.write("   2. Если не найдено → пробуем fallback архетипы")
        self.stdout.write("   3. Если REQUIRED видео не найдено → логируем ERROR")
        self.stdout.write("   4. Если OPTIONAL видео не найдено → пропускаем")

    def analyze_r2_structure(self, verbose):
        """Анализ структуры Cloudflare R2"""
        self.stdout.write("\n☁️  СТРУКТУРА CLOUDFLARE R2")
        self.stdout.write("-" * 30)
        
        r2_structure = {
            "Упражнения": {
                "technique": "/videos/exercises/{slug}_technique_{model}.mp4",
                "mistake": "/videos/exercises/{slug}_mistake_{model}.mp4"
            },
            "Инструкции": {
                "instruction": "/videos/instructions/{slug}_instruction_{archetype}_{model}.mp4"
            },
            "Напоминания": {
                "reminder": "/videos/reminders/{slug}_reminder_{archetype}_{number}.mp4"
            },
            "Глобальные": {
                "intro": "/videos/intro/{archetype}_intro_{model}.mp4",
                "weekly": "/videos/motivation/weekly_{archetype}_week{number}.mp4",
                "closing": "/videos/closing/{archetype}_closing_{model}.mp4"
            },
            "Мотивационные карточки": {
                "images": "/images/cards/card_{category}_{number}.jpg"
            },
            "Аватары": {
                "avatars": "/images/avatars/{archetype}_avatar_{number}.jpg"
            }
        }
        
        for category, paths in r2_structure.items():
            self.stdout.write(f"\n📁 {category}:")
            for kind, path in paths.items():
                self.stdout.write(f"   {kind}: {path}")
        
        self.stdout.write("\n🔧 Плейсхолдеры:")
        placeholders = [
            "{slug} - ID упражнения (например: push_ups)",
            "{archetype} - mentor/professional/peer", 
            "{model} - версия видео (v1, v2, etc)",
            "{category} - категория карточки",
            "{number} - порядковый номер"
        ]
        
        for placeholder in placeholders:
            self.stdout.write(f"   • {placeholder}")
        
        self.stdout.write("\n🌐 URL Generation:")
        self.stdout.write("   • Base URL: R2_PUBLIC_URL из настроек")
        self.stdout.write("   • Dynamic path: Подставляется на основе VideoClip.r2_file")
        self.stdout.write("   • CDN caching: Автоматически через Cloudflare")
        
        # Итоговая сводка
        self.stdout.write("\n📋 ИТОГО:")
        self.stdout.write("   🎬 Система плейлистов работает детерминистически")
        self.stdout.write("   👤 3 архетипа с fallback цепочками")
        self.stdout.write("   🔄 Контроль повторений через seeded RNG")
        self.stdout.write("   ☁️  Все видео хранятся в Cloudflare R2")
        self.stdout.write("   ⚡ Storage validation предотвращает битые ссылки")