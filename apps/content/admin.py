from django.contrib import admin
from django.utils.html import format_html
from .models import Story, StoryChapter, MediaAsset, UserStoryAccess


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


class StoryChapterInline(admin.TabularInline):
    model = StoryChapter
    extra = 1
    fields = ("order", "title", "video_url", "thumbnail_url", "is_published")
    ordering = ("order",)

@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "is_published", "created_at", "thumb")
    list_filter = ("is_published", "genre", "created_at")
    search_fields = ("title", "author", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "cover_preview")
    inlines = [StoryChapterInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "author", "description", "genre", "is_published")}),
        ("Обложка", {"fields": ("cover_image_url", "cover_preview")}),
        ("Служебные", {"fields": ("created_at", "updated_at")}),
    )
    def thumb(self, obj):
        if obj.cover_image_url:
            return format_html('<img src="{}" style="height:40px;border-radius:6px;" />', obj.cover_image_url)
        return "—"
    thumb.short_description = "Обложка"
    def cover_preview(self, obj):
        if obj.cover_image_url:
            return format_html('<img src="{}" style="height:140px;border-radius:10px;" />', obj.cover_image_url)
        return "—"


@admin.register(StoryChapter)
class StoryChapterAdmin(admin.ModelAdmin):
    list_display = ("story", "order", "title", "is_published", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "story__title")
    ordering = ("story", "order")
    readonly_fields = ("created_at", "updated_at")

@admin.register(UserStoryAccess)
class UserStoryAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter", "unlocked_at")
    search_fields = ("user__email", "chapter__story__title")
    readonly_fields = ("unlocked_at",)