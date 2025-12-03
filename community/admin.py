from django.contrib import admin
from .models import Post

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at', 'content_preview')
    search_fields = ('content', 'author__username')

    def content_preview(self, obj):
        return obj.content[:50]
