import math
from decimal import Decimal
from users.models import User, RiderProfile

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def get_nearby_riders(latitude, longitude, radius_km=10):
    """
    Find active riders within a certain radius.
    Returns a list of tuples: (rider_user, distance_km)
    Sorted by distance.
    """
    active_riders = RiderProfile.objects.filter(is_available=True, verification_status='VERIFIED').select_related('user')
    nearby_riders = []

    for rider_profile in active_riders:
        if rider_profile.current_latitude and rider_profile.current_longitude:
            dist = haversine_distance(
                latitude, 
                longitude, 
                rider_profile.current_latitude, 
                rider_profile.current_longitude
            )
            if dist <= radius_km:
                nearby_riders.append((rider_profile.user, round(dist, 2)))
    
    # Sort by distance
    nearby_riders.sort(key=lambda x: x[1])
    return nearby_riders

def generate_order_qr(order):
    """
    Generate a QR code containing order details.
    Returns a base64 string of the PNG image.
    """
    import qrcode
    import io
    import base64
    
    # Construct data string
    farmer = order.product.seller
    buyer = order.buyer
    
    farmer_phone = farmer.profile.phone_number if hasattr(farmer, 'profile') else "N/A"
    buyer_phone = buyer.profile.phone_number if hasattr(buyer, 'profile') else "N/A"
    
    # Get coordinates if available
    delivery_coords = ""
    if hasattr(buyer, 'delivery_addresses') and buyer.delivery_addresses.filter(is_default=True).exists():
        addr = buyer.delivery_addresses.filter(is_default=True).first()
        if addr.gps_coordinates:
            delivery_coords = f"Loc: {addr.gps_coordinates}"
            
    data = f"""Order #{order.id}
Item: {order.product.name} (x{order.quantity})
-- PICKUP --
Farmer: {farmer.get_full_name() or farmer.username}
Phone: {farmer_phone}
Loc: {farmer.profile.location or 'N/A'}
-- DROP OFF --
Buyer: {buyer.get_full_name() or buyer.username}
Phone: {buyer_phone}
{delivery_coords}
"""
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    return qr_base64
