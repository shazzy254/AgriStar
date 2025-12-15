from django.contrib import admin
from .models import Post, PostImage, Comment, Follow, SavedPost, Report

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1
    max_num = 5

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'category', 'content_preview', 'created_at', 'likes_count', 'comments_count']
    list_filter = ['category', 'created_at']
    search_fields = ['content', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PostImageInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ['post', 'image', 'uploaded_at']
    list_filter = ['uploaded_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'author__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    list_filter = ['created_at']
    search_fields = ['follower__username', 'following__username']

@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'post__content']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'post', 'reason', 'status', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    search_fields = ['reporter__username', 'description']
    readonly_fields = ['created_at']
    
    actions = ['mark_as_reviewed', 'mark_as_resolved', 'mark_as_dismissed']
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='REVIEWED')
    mark_as_reviewed.short_description = 'Mark as Reviewed'
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='RESOLVED')
    mark_as_resolved.short_description = 'Mark as Resolved'
    
    def mark_as_dismissed(self, request, queryset):
        queryset.update(status='DISMISSED')
    mark_as_dismissed.short_description = 'Mark as Dismissed'
