import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test video playlist generation from comprehensive AI plans"
    
    def add_arguments(self, parser):
        parser.add_argument('--archetype', type=str, choices=['mentor', 'professional', 'peer'], 
                          default='mentor', help='Trainer archetype to test')
        parser.add_argument('--verbose', action='store_true', help='Verbose output')
        parser.add_argument('--test-type', type=str, choices=['legacy', 'comprehensive', 'both'], 
                          default='both', help='Which plan type to test')

    def handle(self, *args, **options):
        archetype = options['archetype']
        verbose = options['verbose']
        test_type = options['test_type']
        
        self.stdout.write("🎬 Testing video playlist generation...")
        
        if test_type in ['legacy', 'both']:
            self.test_legacy_playlist(archetype, verbose)
            
        if test_type in ['comprehensive', 'both']:
            self.test_comprehensive_playlist(archetype, verbose)
    
    def test_legacy_playlist(self, archetype: str, verbose: bool):
        """Test legacy plan structure"""
        self.stdout.write(f"\n📹 Testing LEGACY playlist for {archetype}...")
        
        # Create mock legacy workout plan structure
        legacy_plan_data = {
            'plan_name': 'Legacy Test Plan',
            'duration_weeks': 4,
            'weeks': [
                {
                    'week_number': 1,
                    'days': [
                        {
                            'day_number': 1,
                            'workout_name': 'Full Body Workout',
                            'is_rest_day': False,
                            'exercises': [
                                {
                                    'exercise_slug': 'push_ups',
                                    'exercise_name': 'Push Ups',
                                    'sets': 3,
                                    'reps': '10-15',
                                    'rest_seconds': 60
                                },
                                {
                                    'exercise_slug': 'squats',
                                    'exercise_name': 'Squats',
                                    'sets': 3,
                                    'reps': '15-20',
                                    'rest_seconds': 90
                                }
                            ],
                            'confidence_task': 'Complete your first workout with confidence!'
                        },
                        {
                            'day_number': 2,
                            'workout_name': 'Rest Day',
                            'is_rest_day': True,
                            'exercises': []
                        }
                    ]
                }
            ]
        }
        
        success = self._test_playlist_generation(legacy_plan_data, archetype, verbose, 'legacy')
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Legacy playlist generation works"))
        else:
            self.stdout.write(self.style.ERROR("❌ Legacy playlist generation failed"))
    
    def test_comprehensive_playlist(self, archetype: str, verbose: bool):
        """Test comprehensive plan structure"""
        self.stdout.write(f"\n📹 Testing COMPREHENSIVE playlist for {archetype}...")
        
        # Create mock comprehensive report structure
        # The training_program part should be identical to legacy WorkoutPlan
        training_program_data = {
            'plan_name': 'Comprehensive Test Plan',
            'duration_weeks': 4,
            'goal': 'Comprehensive fitness improvement',
            'weeks': [
                {
                    'week_number': 1,
                    'days': [
                        {
                            'day_number': 1,
                            'workout_name': 'Strength Foundation',
                            'is_rest_day': False,
                            'exercises': [
                                {
                                    'exercise_slug': 'mountain_climbers',
                                    'exercise_name': 'Mountain Climbers',
                                    'sets': 3,
                                    'reps': '30 seconds',
                                    'rest_seconds': 45
                                },
                                {
                                    'exercise_slug': 'plank',
                                    'exercise_name': 'Plank Hold',
                                    'sets': 3,
                                    'reps': '30 seconds',
                                    'rest_seconds': 60
                                }
                            ],
                            'confidence_task': 'Take a selfie after your workout!'
                        }
                    ]
                }
            ]
        }
        
        comprehensive_data = {
            'meta': {
                'version': '1.0',
                'archetype': archetype,
                'generated_at': '2025-01-01T00:00:00Z'
            },
            'user_analysis': {
                'fitness_level_assessment': "User shows beginner level fitness with good potential for development.",
                'psychological_profile': "Motivated beginner ready for change and consistent work.",
                'limitations_analysis': "No limitations identified, standard progression recommended.",
                'interaction_strategy': "Positive reinforcement and gradual complexity increase.",
                'archetype_adaptation': "Wise mentor approach with motivational support elements"
            },
            'training_program': training_program_data,  # This is the key part
            'motivation_system': {
                'psychological_support': "Weekly achievement system with personalized support messages.",
                'reward_system': "Gamification with XP points and content unlocking.",
                'confidence_building': "Daily small challenges to build self-confidence.",
                'community_integration': "Ability to share achievements and get community support."
            },
            'long_term_strategy': {
                'progression_plan': "3-month plan with weekly load and goal adaptation.",
                'adaptation_triggers': "Automatic adjustment when reaching intermediate goals.",
                'lifestyle_integration': "Gradual integration of healthy habits into daily life.",
                'success_metrics': "Tracking physical indicators and psychological well-being."
            }
        }
        
        # Test the training_program part specifically
        success = self._test_playlist_generation(training_program_data, archetype, verbose, 'comprehensive')
        if success:
            self.stdout.write(self.style.SUCCESS("✅ Comprehensive playlist generation works"))
        else:
            self.stdout.write(self.style.ERROR("❌ Comprehensive playlist generation failed"))
    
    def _test_playlist_generation(self, plan_data: dict, archetype: str, verbose: bool, plan_type: str):
        """Test actual playlist generation"""
        try:
            # Create mock DailyWorkout objects from plan data
            first_week = plan_data.get('weeks', [{}])[0]
            first_day = first_week.get('days', [{}])[0]
            
            if verbose:
                self.stdout.write(f"📊 Plan type: {plan_type}")
                self.stdout.write(f"📊 Archetype: {archetype}")
                self.stdout.write(f"📊 First day exercises: {len(first_day.get('exercises', []))}")
                self.stdout.write(f"📊 Is rest day: {first_day.get('is_rest_day', False)}")
            
            # Create mock DailyWorkout object
            mock_workout = type('MockWorkout', (), {
                'id': 1,
                'week_number': first_week.get('week_number', 1),
                'day_number': first_day.get('day_number', 1),
                'exercises': first_day.get('exercises', []),
                'is_rest_day': first_day.get('is_rest_day', False),
                'name': first_day.get('workout_name', 'Test Workout')
            })()
            
            # Import the real VideoPlaylistBuilder class directly
            import importlib.util
            import os
            services_path = os.path.join(os.path.dirname(__file__), '../../services.py')
            spec = importlib.util.spec_from_file_location("services", services_path)
            services_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(services_module)
            VideoPlaylistBuilder = services_module.VideoPlaylistBuilder
            
            # Create VideoPlaylistBuilder
            playlist_builder = VideoPlaylistBuilder(archetype, locale="ru")
            
            if verbose:
                self.stdout.write("🔧 Creating playlist builder...")
            
            # Generate playlist
            playlist = playlist_builder.build_workout_playlist(mock_workout, archetype)
            
            if verbose:
                self.stdout.write(f"📝 Generated playlist with {len(playlist)} items:")
                for i, item in enumerate(playlist, 1):
                    self.stdout.write(f"  {i}. {item.get('type', 'unknown')} - {item.get('title', 'No title')}")
                    if 'exercise_slug' in item:
                        self.stdout.write(f"     Exercise: {item['exercise_slug']}")
                    if 'url' in item:
                        self.stdout.write(f"     URL: {item['url'][:50]}...")
            
            # Validate playlist structure
            if not playlist:
                if first_day.get('is_rest_day', False):
                    self.stdout.write("✅ Empty playlist for rest day is correct")
                    return True
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Empty playlist for workout day"))
                    return False
            
            # Check that each exercise has corresponding videos
            exercise_slugs = {ex.get('exercise_slug') for ex in first_day.get('exercises', [])}
            playlist_exercises = {item.get('exercise_slug') for item in playlist if item.get('exercise_slug')}
            
            if verbose:
                self.stdout.write(f"📋 Expected exercises: {exercise_slugs}")
                self.stdout.write(f"📋 Playlist exercises: {playlist_exercises}")
            
            # Check coverage
            missing_exercises = exercise_slugs - playlist_exercises
            if missing_exercises:
                self.stdout.write(self.style.WARNING(f"⚠️  Missing exercises in playlist: {missing_exercises}"))
            
            # Check video types
            video_types = [item.get('type') for item in playlist]
            expected_types = ['intro', 'technique', 'instruction']  # Common types
            
            if any(vt in video_types for vt in expected_types):
                self.stdout.write("✅ Found expected video types in playlist")
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Expected video types not found. Got: {video_types}"))
            
            return len(playlist) > 0
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Playlist generation failed: {str(e)}"))
            if verbose:
                import traceback
                self.stdout.write(traceback.format_exc())
            return False