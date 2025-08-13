"""
Management command to test the new comprehensive AI system
"""
import json
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.ai_integration.ai_client import AIClientFactory
from apps.ai_integration.comprehensive_validator import ComprehensiveReportValidator
from apps.ai_integration.prompt_manager_v2 import PromptManagerV2
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.onboarding.services import OnboardingDataProcessor

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test comprehensive AI report generation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archetype',
            type=str,
            choices=['mentor', 'professional', 'peer'],
            default='mentor',
            help='Trainer archetype to test'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only validate prompts and schemas, do not call AI'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to generate plan for (uses test data if not provided)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        archetype = options['archetype']
        dry_run = options['dry_run']
        user_id = options['user_id']
        verbose = options['verbose']

        if verbose:
            logger.setLevel(logging.DEBUG)

        self.stdout.write(f"🧪 Тестирование системы comprehensive AI для архетипа: {archetype}")
        
        try:
            # 1. Test prompt system
            self.test_prompt_system(archetype, verbose)
            
            # 2. Test schemas and validation
            self.test_schemas_validation(verbose)
            
            if not dry_run:
                # 3. Test AI generation
                user_data = self.get_test_user_data(user_id, verbose)
                self.test_ai_generation(user_data, archetype, verbose)
            
            self.stdout.write(self.style.SUCCESS('✅ Все тесты пройдены успешно!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка тестирования: {str(e)}'))
            raise CommandError(f'Test failed: {str(e)}')

    def test_prompt_system(self, archetype: str, verbose: bool):
        """Test comprehensive prompt system"""
        self.stdout.write("🔍 Тестирование системы промптов...")
        
        prompt_manager = PromptManagerV2()
        
        # Test prompt loading
        try:
            system_prompt, user_prompt = prompt_manager.get_prompt_pair(
                'comprehensive', 
                archetype, 
                with_intro=True
            )
            
            if not system_prompt:
                raise ValueError(f"System prompt not found for archetype {archetype}")
            if not user_prompt:
                raise ValueError(f"User prompt not found for archetype {archetype}")
                
            if verbose:
                self.stdout.write(f"📝 System prompt length: {len(system_prompt)} chars")
                self.stdout.write(f"📝 User prompt length: {len(user_prompt)} chars")
                
            # Test placeholder detection
            placeholders = prompt_manager.find_placeholders(user_prompt)
            if verbose:
                self.stdout.write(f"🏷️  Found placeholders: {list(placeholders)}")
            
            self.stdout.write(self.style.SUCCESS("✅ Система промптов работает"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка системы промптов: {str(e)}"))
            raise

    def test_schemas_validation(self, verbose: bool):
        """Test schemas and validation system"""
        self.stdout.write("🔍 Тестирование схем и валидации...")
        
        try:
            # Test schema loading
            prompt_manager = PromptManagerV2()
            try:
                schema = prompt_manager.load_schema('comprehensive_ai_report')
                if verbose:
                    self.stdout.write(f"📋 Schema loaded with {len(schema.get('properties', {}))} top-level properties")
            except FileNotFoundError:
                self.stdout.write(self.style.WARNING("⚠️ comprehensive_ai_report schema not found, using fallback"))
            
            # Test validator initialization
            validator = ComprehensiveReportValidator()
            if verbose:
                self.stdout.write("🛠️ ComprehensiveReportValidator initialized")
            
            # Test validation with mock data
            mock_report = {
                'meta': {'version': 'test', 'archetype': 'mentor'},
                'user_analysis': {},
                'training_program': {'plan_name': 'Test', 'duration_weeks': 4, 'goal': 'Test', 'weeks': []},
                'motivation_system': {},
                'long_term_strategy': {}
            }
            
            dry_validation = validator.dry_run_validation(mock_report)
            if verbose:
                self.stdout.write(f"🧪 Dry run validation: {dry_validation.get('fixes_applied', 0)} fixes needed")
            
            self.stdout.write(self.style.SUCCESS("✅ Схемы и валидация работают"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка схем/валидации: {str(e)}"))
            raise

    def get_test_user_data(self, user_id: int = None, verbose: bool = False) -> dict:
        """Get test user data"""
        self.stdout.write("👤 Получение данных пользователя...")
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user_data = OnboardingDataProcessor.collect_user_data(user)
                if verbose:
                    safe_data = {k: v for k, v in user_data.items() if 'password' not in k.lower()}
                    self.stdout.write(f"📊 Real user data keys: {list(safe_data.keys())}")
                return user_data
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ User {user_id} not found, using test data"))
        
        # Test data
        test_data = {
            'user_id': 'test_user',
            'age': 28,
            'height': 175,
            'weight': 75,
            'primary_goal': 'build_muscle',
            'injuries': 'Нет серьезных травм',
            'equipment_list': 'Домашние тренировки, гантели, коврик',
            'duration_weeks': 6,
            'archetype': 'mentor',
            'onboarding_payload_json': json.dumps({
                'fitness_level': 'beginner',
                'experience': 'no_experience',
                'time_availability': '3-4_per_week',
                'motivation': 'health_and_confidence'
            })
        }
        
        if verbose:
            self.stdout.write(f"🧪 Using test data for user")
        
        return test_data

    def test_ai_generation(self, user_data: dict, archetype: str, verbose: bool):
        """Test AI generation with comprehensive system"""
        self.stdout.write("🤖 Тестирование генерации ИИ...")
        
        try:
            # Test AI client
            ai_client = AIClientFactory.create_client()
            if not hasattr(ai_client, 'generate_comprehensive_report'):
                raise ValueError("AI client does not support comprehensive report generation")
            
            # Test workout plan generator
            generator = WorkoutPlanGenerator()
            
            # Generate comprehensive plan
            self.stdout.write("⏳ Генерация comprehensive плана (может занять несколько минут)...")
            
            plan_data = generator.generate_plan(user_data, use_comprehensive=True)
            
            # Validate results
            if not isinstance(plan_data, dict):
                raise ValueError(f"Expected dict, got {type(plan_data)}")
            
            is_comprehensive = plan_data.get('comprehensive', False)
            has_analysis = 'analysis' in plan_data
            weeks_count = len(plan_data.get('weeks', []))
            
            if verbose:
                self.stdout.write(f"📊 Plan results:")
                self.stdout.write(f"   - Comprehensive: {is_comprehensive}")
                self.stdout.write(f"   - Has analysis: {has_analysis}")
                self.stdout.write(f"   - Weeks: {weeks_count}")
                self.stdout.write(f"   - Plan name: {plan_data.get('plan_name', 'N/A')}")
                
                if has_analysis:
                    analysis = plan_data.get('analysis', {})
                    self.stdout.write(f"   - Analysis blocks: {list(analysis.keys())}")
            
            if is_comprehensive and has_analysis:
                self.stdout.write(self.style.SUCCESS("✅ Comprehensive план сгенерирован успешно"))
            else:
                self.stdout.write(self.style.WARNING("⚠️ План сгенерирован, но не comprehensive"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка генерации ИИ: {str(e)}"))
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc())
            raise