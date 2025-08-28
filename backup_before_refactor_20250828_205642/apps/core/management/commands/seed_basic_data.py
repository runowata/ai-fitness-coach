from django.core.management.base import BaseCommand
from apps.content.models import TrainerPersona, LandingContent


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
        
        for i, persona_data in enumerate(personas):
            persona, created = TrainerPersona.objects.update_or_create(
                slug=persona_data["slug"],
                defaults={
                    "archetype": persona_data["archetype"],
                    "title": persona_data["title"],
                    "description": persona_data["description"],
                    "tone_guidelines": persona_data["tone_guidelines"],
                    "motivational_style": persona_data["motivational_style"],
                    "display_order": i,
                    "is_active": True
                }
            )
            action = "Created" if created else "Updated"
            self.stdout.write(f"  {action} persona: {persona.title}")
        
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
        persona_count = TrainerPersona.objects.count()
        landing_count = LandingContent.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f"""
✅ Basic seed completed!
  - Trainer personas: {persona_count}
  - Landing content: {landing_count}
        
Now the UI should show:
  - Homepage with hero section
  - Trainer selection screen with 3 personas
"""))