from django.urls import path

from . import views

app_name = 'onboarding'

urlpatterns = [
    path('start/', views.start_onboarding, name='start'),
    path('start/', views.start_onboarding, name='start_onboarding'),  # Alternative name for templates
    path('question/<int:question_id>/', views.question_view, name='question'),
    path('answer/<int:question_id>/', views.save_answer, name='save_answer'),
    path('archetype/', views.select_archetype, name='select_archetype'),
    path('generate/', views.generate_plan, name='generate_plan'),
    path('generate-ajax/', views.generate_plan_ajax, name='generate_plan_ajax'),
    path('plan-confirmation/', views.plan_confirmation, name='plan_confirmation'),
    path('plan-confirmation/<int:plan_id>/', views.plan_confirmation, name='plan_confirmation'),
    path('preview/', views.plan_preview, name='plan_preview'),
    
    # Comprehensive AI analysis routes
    path('ai-analysis/', views.ai_analysis, name='ai_analysis'),
    path('ai-analysis-comprehensive/', views.ai_analysis_comprehensive, name='ai_analysis_comprehensive'),
    path('plan-preview-comprehensive/', views.plan_preview_comprehensive, name='plan_preview_comprehensive'),
    
    # Diagnostic endpoints
    path('diag/sleep/<int:seconds>/', views.sleep_test, name='sleep_test'),
]