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
    active_riders = RiderProfile.objects.filter(is_available=True).select_related('user')
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
