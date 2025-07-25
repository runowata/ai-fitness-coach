from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    path('start/', views.start_onboarding, name='start'),
    path('question/<int:question_id>/', views.question_view, name='question'),
    path('answer/<int:question_id>/', views.save_answer, name='save_answer'),
    path('archetype/', views.select_archetype, name='select_archetype'),
    path('generate/', views.generate_plan, name='generate_plan'),
    path('generate-ajax/', views.generate_plan_ajax, name='generate_plan_ajax'),
    path('plan-confirmation/', views.plan_confirmation, name='plan_confirmation'),
    path('preview/', views.plan_preview, name='plan_preview'),
]