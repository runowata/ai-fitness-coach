from django.contrib import admin
from django.utils.html import format_html

from .models import MediaAsset, Story, StoryChapter


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'asset_type', 'category', 'exercise', 'archetype', 'cdn_status', 'preview')
    list_filter = ('asset_type', 'category', 'archetype', 'cdn_status', 'is_active')
    search_fields = ('file_name', 'tags', 'exercise__name')
    readonly_fields = ('uploaded_at', 'file_size_mb', 'preview_large')
    
    fieldsets = (
        ('File Information', {
            'fields': ('file_name', 'file_url', 'asset_type', 'file_size_mb', 'preview_large')
        }),
        ('Categorization', {
            'fields': ('category', 'exercise', 'archetype', 'tags')
        }),
        ('Media Details', {
            'fields': ('duration_seconds', 'width', 'height')
        }),
        ('CDN', {
            'fields': ('cdn_url', 'cdn_status')
        }),
        ('Management', {
            'fields': ('is_active', 'uploaded_by', 'uploaded_at')
        })
    )
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024 / 1024:.2f} MB"
        return "-"
    file_size_mb.short_description = "File Size"
    
    def preview(self, obj):
        if obj.asset_type == 'image':
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;"/>',
                obj.get_serving_url()
            )
        elif obj.asset_type == 'video':
            return format_html(
                '<video width="100" height="50" controls><source src="{}" type="video/mp4"></video>',
                obj.get_serving_url()
            )
        return "-"
    preview.short_description = "Preview"
    
    def preview_large(self, obj):
        if obj.asset_type == 'image':
            return format_html(
                '<img src="{}" style="max-height: 300px; max-width: 500px;"/>',
                obj.get_serving_url()
            )
        elif obj.asset_type == 'video':
            return format_html(
                '<video width="500" height="300" controls><source src="{}" type="video/mp4"></video>',
                obj.get_serving_url()
            )
        return "-"
    preview_large.short_description = "Preview"


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'total_chapters', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'author', 'description')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Media', {
            'fields': ('cover_image_url',)
        }),
        ('Publishing', {
            'fields': ('total_chapters', 'is_published')
        })
    )


@admin.register(StoryChapter)
class StoryChapterAdmin(admin.ModelAdmin):
    list_display = ('story', 'chapter_number', 'title', 'estimated_reading_time', 'is_published')
    list_filter = ('story', 'is_published')
    search_fields = ('title', 'content')
    ordering = ('story', 'chapter_number')
    
    fieldsets = (
        ('Chapter Information', {
            'fields': ('story', 'chapter_number', 'title')
        }),
        ('Content', {
            'fields': ('content', 'estimated_reading_time')
        }),
        ('Media', {
            'fields': ('image_url',)
        }),
        ('Publishing', {
            'fields': ('is_published',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('story')