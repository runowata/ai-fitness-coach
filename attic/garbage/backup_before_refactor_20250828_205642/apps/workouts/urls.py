from django.urls import path

from . import views

app_name = 'workouts'

urlpatterns = [
    path('daily/<int:workout_id>/', views.daily_workout_view, name='daily_workout'),
    path('complete/<int:workout_id>/', views.complete_workout_view, name='complete_workout'),
    path('substitute/<int:workout_id>/', views.substitute_exercise_view, name='substitute_exercise'),
    path('history/', views.workout_history_view, name='history'),
    path('plan/', views.plan_overview_view, name='plan_overview'),
    
    # Demo plan views (Phase 4.2)
    path('my-plan/', views.my_plan, name='my_plan'),
    path('day/<int:day_id>/', views.workout_day, name='workout_day'),
]