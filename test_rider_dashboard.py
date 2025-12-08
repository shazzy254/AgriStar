"""
Quick test to verify rider dashboard changes
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AgriStar.settings')
django.setup()

from users.models import User, RiderProfile

print("=" * 60)
print("RIDER DASHBOARD VERIFICATION")
print("=" * 60)

# Check if there are any riders
riders = User.objects.filter(role='RIDER')
print(f"\n✓ Total Riders in system: {riders.count()}")

if riders.exists():
    rider = riders.first()
    print(f"\n📋 Sample Rider: {rider.username}")
    print(f"   Email: {rider.email}")
    
    if hasattr(rider, 'rider_profile'):
        profile = rider.rider_profile
        print(f"\n🚴 Rider Profile Details:")
        print(f"   Verification: {profile.verification_status}")
        print(f"   Available: {profile.is_available}")
        print(f"   Vehicle: {profile.get_vehicle_type_display()}")
        print(f"   Location: {profile.get_full_location()}")
        print(f"   Wallet Balance: KSH {profile.wallet_balance}")
        print(f"   Total Earnings: KSH {profile.total_earnings}")
        print(f"   Completed Deliveries: {profile.completed_deliveries}")
        print(f"   Success Rate: {profile.delivery_success_rate}%")
        print(f"   Max Weight: {profile.max_weight_kg} kg")
        
        print(f"\n✅ All new fields are accessible!")
    else:
        print(f"\n⚠️  Rider profile not found for {rider.username}")
else:
    print("\n⚠️  No riders found in the system")
    print("   You can create a test rider to see the new dashboard")

print("\n" + "=" * 60)
print("DASHBOARD FILES CHECK")
print("=" * 60)

# Check if dashboard file exists
dashboard_file = "templates/users/dashboard_rider.html"
if os.path.exists(dashboard_file):
    print(f"\n✓ Rider dashboard template exists")
    with open(dashboard_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Check for key features
    features = {
        "Purple gradient": "linear-gradient(135deg, #667eea" in content,
        "Wallet balance": "wallet-balance" in content or "Wallet Balance" in content,
        "Withdrawal modal": "withdrawModal" in content,
        "Performance ring": "performance-ring" in content,
        "Verification alert": "verification-alert" in content,
        "Availability toggle": "toggle_rider_availability" in content,
    }
    
    print("\n📊 Dashboard Features:")
    for feature, exists in features.items():
        status = "✓" if exists else "✗"
        print(f"   {status} {feature}")
else:
    print(f"\n✗ Dashboard template not found!")

print("\n" + "=" * 60)
print("URLS CHECK")
print("=" * 60)

# Check if withdrawal URL exists
from users import urls as user_urls
url_patterns = [str(pattern.pattern) for pattern in user_urls.urlpatterns]
withdrawal_exists = any('withdraw' in pattern for pattern in url_patterns)

print(f"\n{'✓' if withdrawal_exists else '✗'} Withdrawal URL configured")

print("\n" + "=" * 60)
print("\nTo test the dashboard:")
print("1. Login as a rider user")
print("2. Navigate to: http://localhost:8000/users/dashboard/")
print("3. You should see:")
print("   - Purple gradient background")
print("   - Wallet balance card")
print("   - Availability toggle")
print("   - Performance metrics")
print("   - Withdrawal button")
print("=" * 60)
