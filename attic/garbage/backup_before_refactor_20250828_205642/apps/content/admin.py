from django.contrib import admin
from .models import MediaAsset, TrainerPersona, LandingContent


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("id", "file_name", "asset_type", "category", "exercise", "is_active", "uploaded_at")
    list_filter = ("asset_type", "category", "is_active", "cdn_status", "archetype")
    search_fields = ("file_name", "file_url", "tags")
    autocomplete_fields = ("exercise", "uploaded_by")
    readonly_fields = ("uploaded_at",)


@admin.register(TrainerPersona)
class TrainerPersonaAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "archetype", "title", "is_active", "display_order", "created_at")
    list_filter = ("is_active", "archetype")
    search_fields = ("slug", "title")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LandingContent)
class LandingContentAdmin(admin.ModelAdmin):
    list_display = ("id", "version", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("version",)
    readonly_fields = ("created_at", "updated_at")