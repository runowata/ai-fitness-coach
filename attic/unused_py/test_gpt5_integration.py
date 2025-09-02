# DISABLED AI: GPT-5 integration test command commented out
# """
# Smoke test for GPT-5 integration to verify proper model usage and API endpoints
# """
# import time
# from django.core.management.base import BaseCommand
# from django.conf import settings
# from apps.ai_integration.ai_client_gpt5 import GPT5Client, AIClientError

# DISABLED AI: GPT-5 test command implementation commented out
\"\"\"


class Command(BaseCommand):
    help = 'Test GPT-5 integration with responses API and telemetry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model', 
            type=str, 
            default='gpt-5-mini',
            help='GPT-5 model to test (gpt-5, gpt-5-mini, gpt-5-nano)'
        )
        parser.add_argument(
            '--test-all',
            action='store_true',
            help='Test all available GPT-5 models'
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 GPT-5 Integration Smoke Test")
        self.stdout.write("=" * 50)
        
        # Test configuration
        if not settings.OPENAI_API_KEY:
            self.stdout.write(self.style.ERROR("❌ OPENAI_API_KEY not configured"))
            return
        
        self.stdout.write(f"🔧 Current model setting: {settings.OPENAI_MODEL}")
        self.stdout.write(f"🎛️ Max tokens setting: {settings.OPENAI_MAX_TOKENS}")
        
        models_to_test = ['gpt-5', 'gpt-5-mini', 'gpt-5-nano'] if options['test_all'] else [options['model']]
        
        for model in models_to_test:
            self.test_model(model)
        
        self.stdout.write("\n✅ GPT-5 Integration Test Complete")

    def test_model(self, model_name):
        """Test specific GPT-5 model"""
        self.stdout.write(f"\n🧪 Testing {model_name}")
        self.stdout.write("-" * 30)
        
        try:
            # Override model setting temporarily
            original_model = settings.OPENAI_MODEL
            settings.OPENAI_MODEL = model_name
            
            # Initialize client
            client = GPT5Client()
            self.stdout.write(f"✅ Client initialized with {model_name}")
            
            # Test 1: Simple completion
            self.test_simple_completion(client)
            
            # Test 2: Workout plan generation
            self.test_workout_plan(client)
            
            # Test 3: API endpoint verification
            self.verify_api_endpoint(client, model_name)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Model {model_name} failed: {str(e)}"))
        finally:
            # Restore original model
            settings.OPENAI_MODEL = original_model

    def test_simple_completion(self, client):
        """Test basic completion functionality"""
        try:
            start_time = time.time()
            prompt = "Create a simple JSON response with a greeting message. Include only: {\"message\": \"Hello from GPT-5!\"}"
            
            result = client.generate_completion(prompt, max_tokens=100)
            duration = time.time() - start_time
            
            if isinstance(result, dict) and 'message' in result:
                self.stdout.write(f"✅ Simple completion: {duration:.1f}s")
                self.stdout.write(f"📝 Response: {result.get('message', 'No message')}")
            else:
                self.stdout.write(self.style.WARNING("⚠️ Simple completion: unexpected format"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Simple completion failed: {str(e)}"))

    def test_workout_plan(self, client):
        """Test workout plan generation"""
        try:
            start_time = time.time()
            prompt = """
            Create a minimal 1-week workout plan for a beginner.
            User: 25 years old, male, beginner fitness level
            Equipment: bodyweight only
            Goal: general fitness
            """
            
            result = client.generate_workout_plan(prompt, max_tokens=2000)
            duration = time.time() - start_time
            
            if hasattr(result, 'plan_name') and hasattr(result, 'weeks'):
                weeks_count = len(result.weeks)
                self.stdout.write(f"✅ Workout plan: {duration:.1f}s")
                self.stdout.write(f"📋 Plan: '{result.plan_name}' with {weeks_count} week(s)")
            else:
                self.stdout.write(self.style.WARNING("⚠️ Workout plan: unexpected format"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Workout plan failed: {str(e)}"))

    def verify_api_endpoint(self, client, model_name):
        """Verify correct API endpoint usage"""
        try:
            expected_api = "Responses API" if model_name.startswith('gpt-5') else "Chat Completions API"
            
            # This would be logged during actual API calls
            self.stdout.write(f"🔧 Expected API: {expected_api}")
            
            if model_name.startswith('gpt-5'):
                if hasattr(client.client, 'responses'):
                    self.stdout.write("✅ Responses API available")
                else:
                    self.stdout.write(self.style.WARNING("⚠️ Responses API not found"))
            
            # Test model validation
            gpt5_models = {'gpt-5', 'gpt-5-mini', 'gpt-5-nano'}
            if model_name in gpt5_models:
                self.stdout.write(f"✅ Model {model_name} is GPT-5 series")
            else:
                self.stdout.write(self.style.WARNING(f"⚠️ Model {model_name} is not GPT-5 series"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ API verification failed: {str(e)}"))

    def show_recommendations(self):
        """Show optimization recommendations"""
        self.stdout.write("\n💡 Optimization Recommendations:")
        self.stdout.write("-" * 40)
        
        current_model = settings.OPENAI_MODEL
        if not current_model.startswith('gpt-5'):
            self.stdout.write("📈 Consider upgrading to gpt-5-mini for better performance")
        
        if settings.OPENAI_MAX_TOKENS > 5000:
            self.stdout.write("⚡ Consider reducing OPENAI_MAX_TOKENS for faster responses")
        
        self.stdout.write("🔍 Monitor logs for token usage and generation time")
        self.stdout.write("📊 Use telemetry data to optimize max_tokens per use case")
\"\"\"

# DISABLED AI: End of GPT-5 test command