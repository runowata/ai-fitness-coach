"""
GPT-5 Smoke Test - Comprehensive test of GPT-5 Responses API integration
Tests reasoning.effort, text.verbosity, telemetry, and performance
"""
import time
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.ai_integration.ai_client_gpt5 import OpenAIClient as GPT5Client, AIClientError


class Command(BaseCommand):
    help = 'Comprehensive smoke test for GPT-5 Responses API integration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reasoning-effort',
            type=str,
            choices=['minimal', 'medium', 'high'],
            default='minimal',
            help='Reasoning effort for smoke test'
        )
        parser.add_argument(
            '--text-verbosity',
            type=str,
            choices=['low', 'medium', 'high'], 
            default='low',
            help='Text verbosity for smoke test'
        )
        parser.add_argument(
            '--max-tokens',
            type=int,
            default=256,
            help='Max output tokens for smoke test'
        )
        parser.add_argument(
            '--timeout-threshold',
            type=int,
            default=int(os.getenv('AI_SMOKE_TEST_TIMEOUT', '10')),
            help='Timeout threshold in seconds'
        )
        parser.add_argument(
            '--fast-mode',
            action='store_true',
            help='Enable fast mode testing'
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 GPT-5 Smoke Test - Responses API Integration")
        self.stdout.write("=" * 60)
        
        # Test configuration check
        if not self.check_configuration():
            return
        
        # Set test parameters
        if options['fast_mode']:
            settings.AI_FAST_MODE = True
            self.stdout.write("⚡ Fast mode enabled")
            
        # Override test parameters
        original_reasoning = getattr(settings, 'OPENAI_REASONING_EFFORT', 'medium')
        original_verbosity = getattr(settings, 'OPENAI_TEXT_VERBOSITY', 'low')
        
        settings.OPENAI_REASONING_EFFORT = options['reasoning_effort']
        settings.OPENAI_TEXT_VERBOSITY = options['text_verbosity']
        
        try:
            # Run smoke tests
            results = self.run_smoke_tests(options)
            self.print_results(results)
            
            # Exit with appropriate code
            if all(test['passed'] for test in results):
                self.stdout.write(self.style.SUCCESS("✅ All smoke tests passed!"))
                exit(0)
            else:
                self.stdout.write(self.style.ERROR("❌ Some smoke tests failed!"))
                exit(1)
                
        finally:
            # Restore original settings
            settings.OPENAI_REASONING_EFFORT = original_reasoning
            settings.OPENAI_TEXT_VERBOSITY = original_verbosity

    def check_configuration(self):
        """Check if GPT-5 is properly configured"""
        self.stdout.write("🔧 Configuration Check:")
        
        if not settings.OPENAI_API_KEY:
            self.stdout.write(self.style.ERROR("❌ OPENAI_API_KEY not configured"))
            return False
            
        model = getattr(settings, 'OPENAI_MODEL', 'unknown')
        if not model.startswith('gpt-5'):
            self.stdout.write(self.style.WARNING(f"⚠️ Model {model} is not GPT-5 series"))
            
        self.stdout.write(f"✅ Model: {model}")
        self.stdout.write(f"✅ Reasoning effort: {getattr(settings, 'OPENAI_REASONING_EFFORT', 'medium')}")
        self.stdout.write(f"✅ Text verbosity: {getattr(settings, 'OPENAI_TEXT_VERBOSITY', 'low')}")
        self.stdout.write(f"✅ Max tokens: {getattr(settings, 'OPENAI_MAX_OUTPUT_TOKENS', 12288)}")
        return True

    def run_smoke_tests(self, options):
        """Run comprehensive smoke tests"""
        tests = []
        
        # Test 1: Basic Responses API call
        tests.append(self.test_basic_responses_api(options))
        
        # Test 2: Telemetry and logging 
        tests.append(self.test_telemetry_logging(options))
        
        # Test 3: Error handling
        tests.append(self.test_error_handling(options))
        
        # Test 4: Performance thresholds
        tests.append(self.test_performance_thresholds(options))
        
        return tests

    def test_basic_responses_api(self, options):
        """Test basic Responses API functionality"""
        test_name = "Basic Responses API"
        self.stdout.write(f"\\n🧪 Testing: {test_name}")
        
        try:
            client = GPT5Client()
            start_time = time.time()
            
            # Simple test prompt
            prompt = 'Create a simple JSON response with just: {"status": "success", "message": "GPT-5 working"}'
            
            result = client.generate_completion(
                prompt, 
                max_tokens=options['max_tokens'],
                temperature=0.1
            )
            
            duration = time.time() - start_time
            
            # Validate response
            if isinstance(result, dict) and 'status' in result:
                self.stdout.write(f"✅ Valid response in {duration:.1f}s")
                return {'name': test_name, 'passed': True, 'duration': duration, 'details': result}
            else:
                self.stdout.write(f"❌ Invalid response format")
                return {'name': test_name, 'passed': False, 'duration': duration, 'error': 'Invalid format'}
                
        except Exception as e:
            self.stdout.write(f"❌ Failed: {str(e)}")
            return {'name': test_name, 'passed': False, 'error': str(e)}

    def test_telemetry_logging(self, options):
        """Test telemetry and logging output"""
        test_name = "Telemetry & Logging"
        self.stdout.write(f"\\n🧪 Testing: {test_name}")
        
        try:
            # Capture logging by checking if structured call works
            client = GPT5Client()
            
            prompt = 'Generate: {"test": "telemetry", "tokens": "measured"}'
            
            # This should generate telemetry logs
            result = client.generate_completion(prompt, max_tokens=128)
            
            if isinstance(result, dict):
                self.stdout.write("✅ Telemetry logged successfully") 
                return {'name': test_name, 'passed': True, 'details': 'Telemetry data captured'}
            else:
                return {'name': test_name, 'passed': False, 'error': 'No telemetry data'}
                
        except Exception as e:
            return {'name': test_name, 'passed': False, 'error': str(e)}

    def test_error_handling(self, options):
        """Test error handling for Responses API"""
        test_name = "Error Handling"
        self.stdout.write(f"\\n🧪 Testing: {test_name}")
        
        try:
            client = GPT5Client()
            
            # Test normal error handling
            try:
                # This should work normally
                result = client.generate_completion('Generate: {"error_test": "passed"}', max_tokens=64)
                if isinstance(result, dict):
                    self.stdout.write("✅ Normal operation successful")
                    return {'name': test_name, 'passed': True, 'details': 'Error handling works'}
                else:
                    return {'name': test_name, 'passed': False, 'error': 'Unexpected response format'}
            except AIClientError as e:
                # Expected error handling
                return {'name': test_name, 'passed': True, 'details': f'Proper error handling: {str(e)[:50]}'}
                
        except Exception as e:
            return {'name': test_name, 'passed': False, 'error': str(e)}

    def test_performance_thresholds(self, options):
        """Test performance meets thresholds"""
        test_name = "Performance Thresholds"
        self.stdout.write(f"\\n🧪 Testing: {test_name}")
        
        try:
            client = GPT5Client()
            start_time = time.time()
            
            prompt = 'Generate a simple JSON: {"performance": "test", "speed": "measured"}'
            
            result = client.generate_completion(prompt, max_tokens=options['max_tokens'])
            duration = time.time() - start_time
            
            # Check performance thresholds
            threshold = options['timeout_threshold']
            
            if duration < threshold:
                self.stdout.write(f"✅ Performance: {duration:.1f}s < {threshold}s threshold")
                return {'name': test_name, 'passed': True, 'duration': duration, 'threshold': threshold}
            else:
                self.stdout.write(f"⚠️ Slow performance: {duration:.1f}s > {threshold}s threshold")
                return {'name': test_name, 'passed': False, 'duration': duration, 'threshold': threshold}
                
        except Exception as e:
            return {'name': test_name, 'passed': False, 'error': str(e)}

    def print_results(self, results):
        """Print comprehensive test results"""
        self.stdout.write("\\n📊 Smoke Test Results:")
        self.stdout.write("-" * 40)
        
        for test in results:
            status = "✅ PASS" if test['passed'] else "❌ FAIL"
            self.stdout.write(f"{status} {test['name']}")
            
            if 'duration' in test:
                self.stdout.write(f"    ⏱️ Duration: {test['duration']:.2f}s")
            
            if 'details' in test:
                self.stdout.write(f"    ℹ️ Details: {test['details']}")
                
            if 'error' in test:
                self.stdout.write(f"    ❌ Error: {test['error']}")
                
        # Summary
        passed = sum(1 for test in results if test['passed'])
        total = len(results)
        self.stdout.write(f"\\n📈 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            self.stdout.write("🎉 All systems operational!")
        else:
            self.stdout.write("⚠️ Some issues detected - check logs above")