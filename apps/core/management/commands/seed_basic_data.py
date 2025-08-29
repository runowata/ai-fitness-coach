from django.core.management.base import BaseCommand
from apps.content.models import LandingContent
# УДАЛЕНО: TrainerPersona - заменен на архетипы в R2Video/R2Image


class Command(BaseCommand):
    help = 'Seed basic data to make UI alive'

    def handle(self, *args, **options):
        self.stdout.write("Starting basic data seed...")
        
        # 1) Seed Trainer Personas
        personas = [
            {
                "slug": "peer",
                "archetype": "peer",
                "title": "Лучший друг",
                "description": "Теплый, поддерживающий стиль. Помогает начать и не бросить.",
                "tone_guidelines": "Дружелюбно, кратко, без жаргона.",
                "motivational_style": "Небольшие победы, регулярная похвала."
            },
            {
                "slug": "professional",
                "archetype": "professional", 
                "title": "Профессионал",
                "description": "Четкий, структурированный подход. Фокус на результате.",
                "tone_guidelines": "Деловой стиль, конкретные инструкции, мотивация через цели.",
                "motivational_style": "Достижение целей, прогресс по метрикам."
            },
            {
                "slug": "mentor",
                "archetype": "mentor",
                "title": "Мудрый наставник",
                "description": "Глубокий, философский подход. Развитие через понимание.",
                "tone_guidelines": "Спокойный, вдумчивый, с метафорами и примерами.",
                "motivational_style": "Внутренняя мотивация, долгосрочные изменения."
            }
        ]
        
        # УДАЛЕНО: TrainerPersona - функциональность перенесена в архетипы R2Video/R2Image
        # TODO: Создать R2Image для аватаров архетипов
        self.stdout.write("  TrainerPersona seeding skipped - using R2Image avatars")
        
        # 2) Seed Landing Content
        landing, created = LandingContent.objects.update_or_create(
            version="2.0",
            defaults={
                "hero_title": "Твой AI-тренер",
                "hero_subtitle": "Персональные тренировки под твои цели",
                "hero_cta_primary": "Начать",
                "hero_cta_secondary": "Узнать больше",
                "for_whom": "Новички и продолжающие, домашние тренировки и зал.",
                "how_it_works": "Ответь на вопросы — мы соберём план и видео-плейлист.",
                "safety": "Безопасная техника, напоминания о разогреве и заминке.",
                "personalization": "Учитываем инвентарь, опыт, график и предпочтения.",
                "cases": [],
                "features": [],
                "footer_text": "© AI Fitness Coach",
                "is_active": True
            }
        )
        action = "Created" if created else "Updated"
        self.stdout.write(f"  {action} landing content v2.0")
        
        # 3) Verify counts
        landing_count = LandingContent.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f"""
✅ Basic seed completed!
  - Landing content: {landing_count}
  - Trainer personas: Using R2Image avatars
        
Now the UI should show:
  - Homepage with hero section
  - Trainer selection screen with 3 personas
"""))