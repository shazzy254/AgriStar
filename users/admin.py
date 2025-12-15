from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, DeliveryAddress, RiderProfile, VehicleChangeRequest
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
    list_display = ('farmer', 'badge_level', 'total_sales', 'average_rating', 'total_reviews', 'is_manual_override')
    list_filter = ('badge_level', 'is_manual_override')
    search_fields = ('farmer__username',)
    readonly_fields = ('earned_date', 'updated_at')
    actions = ['update_badges']
    
    def update_badges(self, request, queryset):
        for badge in queryset:
            badge.update_badge_level()
        self.message_user(request, f"{queryset.count()} badges updated successfully!")
    update_badges.short_description = "Update badge levels"

@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'vehicle_plate_number', 'verification_status', 'is_available')
    list_filter = ('verification_status', 'vehicle_type', 'is_available')
    search_fields = ('user__username', 'vehicle_plate_number', 'id_number', 'license_number')
    readonly_fields = ('total_deliveries', 'completed_deliveries', 'wallet_balance', 'delivery_success_rate')
    
    actions = ['approve_verification', 'reject_verification']
    
    def approve_verification(self, request, queryset):
        queryset.update(verification_status='VERIFIED')
        self.message_user(request, f"{queryset.count()} riders marked as VERIFIED.")
    approve_verification.short_description = "Mark selected riders as Verified"
    
    def reject_verification(self, request, queryset):
        queryset.update(verification_status='PENDING')
        self.message_user(request, f"{queryset.count()} riders verification rejected/reset to Pending.")
    reject_verification.short_description = "Reject verification (Reset to Pending)"

    fieldsets = (
        ('Rider Info', {
            'fields': ('user', 'id_number', 'license_number', 'passport_photo', 'verification_status', 'is_available')
        }),
        ('Vehicle Details', {
            'fields': ('vehicle_type', 'vehicle_plate_number')
        }),
        ('Verification Documents', {
            'fields': ('verification_id_front', 'verification_id_back', 'verification_selfie', 'verification_license', 'verification_good_conduct')
        }),
        ('Statistics', {
            'fields': ('total_deliveries', 'completed_deliveries', 'delivery_success_rate', 'wallet_balance')
        }),
        ('Location', {
            'fields': ('current_latitude', 'current_longitude')
        })
    )

@admin.register(VehicleChangeRequest)
class VehicleChangeRequestAdmin(admin.ModelAdmin):
    list_display = ('rider', 'old_vehicle_type', 'new_vehicle_type', 'status', 'requested_at', 'reviewed_by')
    list_filter = ('status', 'requested_at')
    search_fields = ('rider__username', 'reason', 'admin_notes')
    readonly_fields = ('requested_at', 'reviewed_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('rider', 'status', 'reason')
        }),
        ('Old Vehicle Details', {
            'fields': ('old_vehicle_type', 'old_vehicle_plate', 'old_license_number')
        }),
        ('New Vehicle Details', {
            'fields': ('new_vehicle_type', 'new_vehicle_plate', 'new_license_number')
        }),
        ('Admin Review', {
            'fields': ('admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('requested_at',)
        })
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        """Approve selected vehicle change requests"""
        count = 0
        for change_request in queryset.filter(status='PENDING'):
            change_request.approve(request.user, "Approved via admin action")
            count += 1
        self.message_user(request, f"{count} vehicle change request(s) approved successfully!")
    approve_requests.short_description = "Approve selected requests"
    
    def reject_requests(self, request, queryset):
        """Reject selected vehicle change requests"""
        count = 0
        for change_request in queryset.filter(status='PENDING'):
            change_request.reject(request.user, "Rejected via admin action")
            count += 1
        self.message_user(request, f"{count} vehicle change request(s) rejected.")
    reject_requests.short_description = "Reject selected requests"

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(DeliveryAddress)
