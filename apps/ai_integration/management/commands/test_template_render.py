import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.template.loader import get_template

User = get_user_model()


class Command(BaseCommand):
    help = "Test comprehensive template rendering with mock data"
    
    def add_arguments(self, parser):
        parser.add_argument('--template', type=str, choices=['ai_analysis', 'plan_preview'], 
                          default='ai_analysis', help='Which template to test')
        parser.add_argument('--archetype', type=str, choices=['mentor', 'professional', 'peer'], 
                          default='mentor', help='Trainer archetype to test')
        parser.add_argument('--verbose', action='store_true', help='Verbose output')

    def handle(self, *args, **options):
        template_name = options['template']
        archetype = options['archetype']
        verbose = options['verbose']
        
        self.stdout.write("🧪 Testing comprehensive template rendering...")
        
        # Create mock comprehensive data
        mock_comprehensive_data = {
            'user_analysis': {
                'fitness_level_assessment': "Пользователь показывает начальный уровень физической подготовки с хорошим потенциалом для развития.",
                'psychological_profile': "Мотивированный новичок, готовый к изменениям и последовательной работе над собой.",
                'limitations_analysis': "Ограничений не выявлено, рекомендуется стандартная прогрессия.",
                'interaction_strategy': "Использование позитивного подкрепления и постепенного увеличения сложности заданий.",
                'archetype_adaptation': "Мудрый наставник подход с элементами мотивационной поддержки"
            },
            'motivation_system': {
                'psychological_support': "Система еженедельных достижений с персональными сообщениями поддержки.",
                'reward_system': "Игрофикация с системой очков опыта и разблокировкой нового контента.",
                'confidence_building': "Ежедневные небольшие вызовы для укрепления уверенности в себе.",
                'community_integration': "Возможность делиться достижениями и получать поддержку сообщества."
            },
            'long_term_strategy': {
                'progression_plan': "3-месячный план с еженедельной адаптацией нагрузки и целей.",
                'adaptation_triggers': "Автоматическая корректировка при достижении промежуточных целей.",
                'lifestyle_integration': "Постепенное внедрение здоровых привычек в повседневную жизнь.",
                'success_metrics': "Отслеживание физических показателей и психологического самочувствия."
            }
        }
        
        # Create mock training program data
        mock_plan_data = {
            'plan_name': 'Персональный план трансформации',
            'goal': 'Общее улучшение физической формы и уверенности',
            'duration_weeks': 8,
            'weeks': [
                {
                    'week_number': 1,
                    'days': [
                        {
                            'workout_name': 'Базовая тренировка',
                            'is_rest_day': False,
                            'exercises': [
                                {
                                    'exercise_name': 'Приседания',
                                    'exercise_slug': 'squats',
                                    'sets': 3,
                                    'reps': 15,
                                    'rest_seconds': 60
                                },
                                {
                                    'exercise_name': 'Отжимания',
                                    'exercise_slug': 'pushups',
                                    'sets': 3,
                                    'reps': 10,
                                    'rest_seconds': 60
                                }
                            ],
                            'confidence_task': 'Сегодня сделайте комплимент незнакомому человеку'
                        }
                    ]
                }
            ] * 4  # Create 4 weeks of similar data
        }
        
        # Mock context data
        context_data = {
            'comprehensive_data': mock_comprehensive_data,
            'plan_data': mock_plan_data,
            'training_program': mock_plan_data,
            'archetype': archetype,
            'user_level': 'Comprehensive',
            'plan': type('MockPlan', (), {
                'ai_analysis': mock_comprehensive_data,
                'plan_data': mock_plan_data
            })()
        }
        
        # Test template rendering
        template_file = f'onboarding/{template_name}_comprehensive.html'
        
        try:
            if verbose:
                self.stdout.write(f"📋 Loading template: {template_file}")
                self.stdout.write(f"👤 Using archetype: {archetype}")
                self.stdout.write(f"📊 Mock data keys: {list(context_data.keys())}")
            
            # Load and render template
            template = get_template(template_file)
            rendered_html = template.render(context_data)
            
            if verbose:
                # Check for common Django template errors
                if 'VariableDoesNotExist' in rendered_html:
                    self.stdout.write(self.style.WARNING("⚠️  Found VariableDoesNotExist in output"))
                
                # Check length
                self.stdout.write(f"📏 Rendered HTML length: {len(rendered_html)} characters")
                
                # Check for empty blocks
                if len(rendered_html.strip()) < 1000:
                    self.stdout.write(self.style.WARNING("⚠️  Rendered output seems too short"))
            
            self.stdout.write(self.style.SUCCESS(f"✅ Template '{template_file}' rendered successfully"))
            
            # Test with empty data to check error handling
            if verbose:
                self.stdout.write("\n🧪 Testing with empty data...")
                empty_context = {
                    'comprehensive_data': {},
                    'plan_data': {},
                    'training_program': {},
                    'archetype': archetype,
                    'user_level': 'Test',
                    'plan': type('MockPlan', (), {
                        'ai_analysis': {},
                        'plan_data': {}
                    })()
                }
                
                empty_rendered = template.render(empty_context)
                if len(empty_rendered.strip()) > 0:
                    self.stdout.write(self.style.SUCCESS("✅ Template handles empty data gracefully"))
                else:
                    self.stdout.write(self.style.ERROR("❌ Template fails with empty data"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Template rendering failed: {str(e)}"))
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc())
            return
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Template rendering test completed successfully!"))
        if not verbose:
            self.stdout.write("Use --verbose for detailed output")