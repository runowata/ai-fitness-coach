from apps.workouts.models import CSVExercise, VideoClip, WeeklyLesson, FinalVideo, DailyWorkout
from apps.ai_integration.models import WorkoutPlan
print('CSVExercise:', CSVExercise.objects.count())
print('VideoClip:', VideoClip.objects.count())
print('WeeklyLesson:', WeeklyLesson.objects.count())
print('FinalVideo:', FinalVideo.objects.count())
print('WorkoutPlan:', WorkoutPlan.objects.count())
print('DailyWorkout:', DailyWorkout.objects.count())