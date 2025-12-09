from django.contrib import admin
from .models import FarmerSchedule, JournalEntry

@admin.register(FarmerSchedule)
class FarmerScheduleAdmin(admin.ModelAdmin):
    list_display = ('title', 'farmer', 'event_type', 'start_time', 'status', 'created_at')
    list_filter = ('event_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'farmer__username')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'farmer', 'date', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('title', 'content', 'farmer__username')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
