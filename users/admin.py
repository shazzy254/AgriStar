from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, DeliveryAddress
from .review_models import FarmerReview, FarmerBadge

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )

@admin.register(FarmerReview)
class FarmerReviewAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'buyer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('farmer__username', 'buyer__username', 'review_text')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FarmerBadge)
class FarmerBadgeAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'badge_level', 'total_sales', 'average_rating', 'total_reviews')
    list_filter = ('badge_level',)
    search_fields = ('farmer__username',)
    readonly_fields = ('earned_date', 'updated_at')
    actions = ['update_badges']
    
    def update_badges(self, request, queryset):
        for badge in queryset:
            badge.update_badge_level()
        self.message_user(request, f"{queryset.count()} badges updated successfully!")
    update_badges.short_description = "Update badge levels"

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(DeliveryAddress)
