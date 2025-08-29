from django.contrib import admin
from .models import LandingContent

# УДАЛЕНО: MediaAssetAdmin - заменено на R2VideoAdmin/R2ImageAdmin в workouts.admin
# УДАЛЕНО: TrainerPersonaAdmin - функциональность перенесена в архетипы R2Video/R2Image

@admin.register(LandingContent)
class LandingContentAdmin(admin.ModelAdmin):
    list_display = ("id", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("version",)
    readonly_fields = ("created_at", "updated_at")
    
    fieldsets = (
        ('Version Info', {
            'fields': ('version', 'is_active', 'created_at', 'updated_at')
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_cta_primary', 'hero_cta_secondary')
        }),
        ('Content Sections', {
            'fields': ('for_whom', 'how_it_works', 'safety', 'personalization')
        }),
        ('Dynamic Content', {
            'fields': ('cases', 'features'),
            'classes': ('collapse',)
        }),
        ('Footer', {
            'fields': ('footer_text',),
            'classes': ('collapse',)
        })
    )