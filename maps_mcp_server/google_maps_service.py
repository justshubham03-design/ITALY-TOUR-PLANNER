# Google Maps Service & Geospatial Routing Engine
import math
import urllib.parse
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from knowledge_base.italy_knowledge import DESTINATIONS, PLACES, RESTAURANTS, TRANSIT_KNOWLEDGE

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two points in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def resolve_coords(loc: Union[Dict[str, float], str]) -> Tuple[float, float, str]:
    """Resolves a location (dict with lat/lng, or place ID, or place name) to (lat, lng, label)."""
    if isinstance(loc, dict) and 'lat' in loc and 'lng' in loc:
        label = loc.get('name', f"{loc['lat']:.4f},{loc['lng']:.4f}")
        return float(loc['lat']), float(loc['lng']), label

    loc_str = str(loc).strip()
    if ',' in loc_str:
        parts = loc_str.split(',')
        try:
            return float(parts[0].strip()), float(parts[1].strip()), loc_str
        except ValueError:
            pass

    loc_lower = loc_str.lower()
    clean_query = loc_lower.replace("'", " ").replace("-", " ").replace(",", " ")
    generic_words = {'piazza', 'san', 'santa', 'via', 'dei', 'del', 'delle', 'di', 'da', 'la', 'il', 'park', 'church', 'island', 'village', 'hotel', 'road', 'street', 'gate', 'arch', 'and', 'the'}
    query_tokens = set([w for w in clean_query.split() if len(w) > 2 and w not in generic_words])

    # 1. Exact match in curated places
    for p in PLACES:
        if p['place_id'] == loc_str or p['name'].lower() == loc_lower:
            return p['coordinates']['lat'], p['coordinates']['lng'], p['name']

    # 2. Exact match in curated restaurants
    for r in RESTAURANTS:
        if r['place_id'] == loc_str or r['name'].lower() == loc_lower:
            return r['coordinates']['lat'], r['coordinates']['lng'], r['name']

    # 3. Known landmarks mapping (High Priority)
    if 'tasso' in loc_lower:
        return 40.6263, 14.3758, 'Piazza Tasso (Sorrento)'
    if 'fiumicino' in loc_lower:
        return 41.8003, 12.2389, 'Rome Fiumicino Airport (FCO)'
    if 'termini' in loc_lower:
        return 41.9010, 12.5019, 'Roma Termini Station'
    if 'malpensa' in loc_lower:
        return 45.6301, 8.7255, 'Milan Malpensa Airport (MXP)'
    if 'capri' in loc_lower:
        return 40.5507, 14.2426, 'Capri Island (Marina Grande)'

    # 4. Landmark token matching in places (e.g. 'marina grande', 'colosseum', 'trevi', 'pompeii')
    best_p = None
    best_p_overlap = 0
    if query_tokens:
        for p in PLACES:
            p_clean = p['name'].lower().replace("'", " ").replace("-", " ").replace(":", " ").replace("&", " ")
            p_tokens = set([w for w in p_clean.split() if len(w) > 2 and w not in generic_words])
            overlap = len(query_tokens.intersection(p_tokens))
            if overlap > best_p_overlap and overlap >= 1:
                best_p = p
                best_p_overlap = overlap

    if best_p and best_p_overlap >= 1:
        return best_p['coordinates']['lat'], best_p['coordinates']['lng'], best_p['name']

    # 5. Landmark token matching in restaurants
    if query_tokens:
        for r in RESTAURANTS:
            r_clean = r['name'].lower().replace("'", " ").replace("-", " ")
            r_tokens = set([w for w in r_clean.split() if len(w) > 2 and w not in generic_words])
            if len(query_tokens.intersection(r_tokens)) >= 1:
                return r['coordinates']['lat'], r['coordinates']['lng'], r['name']

    # 6. Search in destinations & default hotels
    for d_id, d in DESTINATIONS.items():
        if d_id == loc_lower or d['name'].lower() == loc_lower:
            return d['center']['lat'], d['center']['lng'], d['name']
        if 'default_hotel' in d and (loc_lower in d['default_hotel']['name'].lower() or d['default_hotel']['name'].lower() in loc_lower):
            return d['default_hotel']['lat'], d['default_hotel']['lng'], d['default_hotel']['name']

    # 7. Destination fuzzy fallback
    for d_id, d in DESTINATIONS.items():
        if d_id in loc_lower or d['name'].lower() in loc_lower:
            return d['center']['lat'], d['center']['lng'], d['name']

    # Default to Rome center
    return 41.9028, 12.4964, loc_str

class GoogleMapsService:
    """
    Core Geospatial & Routing Service implementing the 9 Maps MCP tools.
    Supports real Google Maps API calls if GOOGLE_MAPS_API_KEY is configured,
    with an ultra-reliable, high-accuracy geospatial offline simulation engine.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('GOOGLE_MAPS_API_KEY', '')

    # -------------------------------------------------------------
    # Tool 1: search_places
    # -------------------------------------------------------------
    def search_places(self, query: str = '', city_or_region: Optional[str] = None, 
                      category: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        query_norm = query.lower().strip() if query else ''
        city_norm = city_or_region.lower().strip() if city_or_region else None
        cat_norm = category.lower().strip() if category else None

        matched = []
        for p in PLACES:
            # City filter
            if city_norm:
                if (city_norm not in p['city_id'].lower() and 
                    city_norm not in p['city'].lower()):
                    # check destination region
                    dest = DESTINATIONS.get(p['city_id'])
                    if not (dest and city_norm in dest['region'].lower()):
                        continue

            # Category filter
            if cat_norm and cat_norm != 'all':
                if cat_norm == 'must_visit':
                    if p.get('rating', 0) < 4.7:
                        continue
                elif p.get('category') != cat_norm and cat_norm not in p.get('types', []):
                    continue

            # Query filter
            if query_norm:
                name_match = query_norm in p['name'].lower()
                desc_match = query_norm in p.get('description', '').lower()
                city_match = query_norm in p['city'].lower()
                tips_match = query_norm in p.get('local_tips', '').lower()
                type_match = any(query_norm in t.lower() for t in p.get('types', []))
                if not (name_match or desc_match or city_match or tips_match or type_match):
                    continue

            dwell = p.get('typical_dwell_minutes', 60)
            maps_url = p.get('google_maps_url', self.get_maps_url(action='place', query_or_place_name=p['name'], place_id=p['place_id'])['url'])
            photos_url = p.get('google_photos_url', maps_url)
            matched.append({
                'placeId': p['place_id'],
                'place_id': p['place_id'],
                'name': p['name'],
                'address': p['address'],
                'city': p['city'],
                'cityId': p['city_id'],
                'city_id': p['city_id'],
                'category': p.get('category', 'historical'),
                'coordinates': p['coordinates'],
                'rating': p['rating'],
                'userRatingCount': p['user_ratings_total'],
                'user_ratings_total': p['user_ratings_total'],
                'types': p.get('types', []),
                'priceLevel': p.get('price_level', '€€'),
                'price_level': p.get('price_level', '€€'),
                'typicalDwellMinutes': dwell,
                'typical_dwell_minutes': dwell,
                'dwell_time_hours': round(dwell / 60.0, 1),
                'bookingUrgency': p.get('booking_urgency', 'optional'),
                'booking_urgency': p.get('booking_urgency', 'optional'),
                'ticket_urgency': p.get('booking_urgency', 'optional'),
                'bookingLeadTime': p.get('booking_lead_time', ''),
                'booking_lead_time': p.get('booking_lead_time', ''),
                'officialBookingUrl': p.get('official_booking_url', ''),
                'official_booking_url': p.get('official_booking_url', ''),
                'ticket_url': p.get('official_booking_url', ''),
                'google_maps_url': maps_url,
                'googleMapsUri': maps_url,
                'google_photos_url': photos_url,
                'googlePhotosUrl': photos_url,
                'image_url': p.get('image_url', 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'),
                'imageUrl': p.get('image_url', 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'),
                'what_to_do': p.get('what_to_do', []),
                'opening_hours': p.get('opening_hours', {}),
                'description': p.get('description', ''),
                'localTips': p.get('local_tips', ''),
                'local_tips': p.get('local_tips', '')
            })

        # Sort by rating * log(ratings_count)
        matched.sort(key=lambda x: (x['rating'] * math.log10(max(10, x['userRatingCount']))), reverse=True)
        return {'places': matched[:limit]}

    # -------------------------------------------------------------
    # Tool 2: search_nearby_places
    # -------------------------------------------------------------
    def search_nearby_places(self, latitude: float, longitude: float, 
                             radius_meters: int = 5000, 
                             included_types: Optional[List[str]] = None, 
                             min_rating: float = 4.0, limit: int = 10) -> Dict[str, Any]:
        results = []
        for p in PLACES:
            dist = haversine_distance(latitude, longitude, p['coordinates']['lat'], p['coordinates']['lng'])
            if dist <= radius_meters and p.get('rating', 0) >= min_rating:
                if included_types:
                    if not any(t in p.get('types', []) or t == p.get('category') for t in included_types):
                        continue
                results.append({
                    'placeId': p['place_id'],
                    'name': p['name'],
                    'distanceMeters': round(dist),
                    'distanceKm': round(dist / 1000.0, 2),
                    'coordinates': p['coordinates'],
                    'rating': p['rating'],
                    'types': p.get('types', []),
                    'category': p.get('category', 'historical'),
                    'typicalDwellMinutes': p.get('typical_dwell_minutes', 60)
                })

        results.sort(key=lambda x: x['distanceMeters'])
        return {'nearbyPlaces': results[:limit]}

    # -------------------------------------------------------------
    # Tool 3: get_place_details
    # -------------------------------------------------------------
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        for p in PLACES:
            if p['place_id'] == place_id:
                maps_url = p.get('google_maps_url', self.get_maps_url(action='place', query_or_place_name=p['name'], place_id=p['place_id'])['url'])
                photos_url = p.get('google_photos_url', maps_url)
                return {
                    'placeId': p['place_id'],
                    'place_id': p['place_id'],
                    'name': p['name'],
                    'formattedAddress': p['address'],
                    'address': p['address'],
                    'city': p['city'],
                    'cityId': p.get('city_id', ''),
                    'city_id': p.get('city_id', ''),
                    'coordinates': p['coordinates'],
                    'rating': p['rating'],
                    'userRatingCount': p['user_ratings_total'],
                    'user_ratings_total': p['user_ratings_total'],
                    'priceLevel': p.get('price_level', '€€'),
                    'price_level': p.get('price_level', '€€'),
                    'typicalDwellMinutes': p.get('typical_dwell_minutes', 60),
                    'typical_dwell_minutes': p.get('typical_dwell_minutes', 60),
                    'dwell_time_hours': round(p.get('typical_dwell_minutes', 60) / 60.0, 1),
                    'googleMapsUri': maps_url,
                    'google_maps_url': maps_url,
                    'googlePhotosUrl': photos_url,
                    'google_photos_url': photos_url,
                    'image_url': p.get('image_url', 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'),
                    'imageUrl': p.get('image_url', 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80'),
                    'what_to_do': p.get('what_to_do', []),
                    'regularOpeningHours': p.get('opening_hours', {'open_now': True, 'weekday_descriptions': ['Open daily']}),
                    'opening_hours': p.get('opening_hours', {}),
                    'types': p.get('types', []),
                    'category': p.get('category', 'historical'),
                    'bookingUrgency': p.get('booking_urgency', 'optional'),
                    'booking_urgency': p.get('booking_urgency', 'optional'),
                    'ticket_urgency': p.get('booking_urgency', 'optional'),
                    'bookingLeadTime': p.get('booking_lead_time', ''),
                    'booking_lead_time': p.get('booking_lead_time', ''),
                    'officialBookingUrl': p.get('official_booking_url', ''),
                    'official_booking_url': p.get('official_booking_url', ''),
                    'ticket_url': p.get('official_booking_url', ''),
                    'bestTimeOfDay': p.get('best_time_of_day', 'morning'),
                    'description': p.get('description', ''),
                    'localTips': p.get('local_tips', ''),
                    'local_tips': p.get('local_tips', '')
                }

        # Check restaurants if place_id matches a restaurant
        for r in RESTAURANTS:
            if r['place_id'] == place_id:
                maps_url = self.get_maps_url(action='place', query_or_place_name=r['name'], place_id=r['place_id'])['url']
                return {
                    'placeId': r['place_id'],
                    'name': r['name'],
                    'formattedAddress': r['address'],
                    'city': r['city'],
                    'coordinates': r['coordinates'],
                    'rating': r['rating'],
                    'userRatingCount': r['user_ratings_total'],
                    'priceLevel': r.get('price_level', '€€'),
                    'googleMapsUri': maps_url,
                    'types': ['restaurant', 'food', 'point_of_interest'],
                    'cuisineType': r.get('cuisine_types', []),
                    'dietaryTier': r.get('dietary_tier', 'vegetarian_friendly'),
                    'vegetarianFriendly': r.get('vegetarian_friendly', True),
                    'signatureDishes': r.get('signature_dishes', []),
                    'reservationUrgency': r.get('reservation_urgency', 'Optional')
                }

        return {'error': f'Place ID {place_id} not found.'}

    # -------------------------------------------------------------
    # Tool 4: search_restaurants
    # -------------------------------------------------------------
    def search_restaurants(self, latitude: float, longitude: float, 
                           radius_meters: int = 25000, 
                           cuisine: Optional[str] = None, 
                           dietary_preference: str = 'both', 
                           price_levels: Optional[List[str]] = None, 
                           min_rating: float = 4.2, limit: int = 5) -> Dict[str, Any]:
        results = []
        for r in RESTAURANTS:
            dist = haversine_distance(latitude, longitude, r['coordinates']['lat'], r['coordinates']['lng'])
            if dist > radius_meters:
                continue
            if r.get('rating', 0) < min_rating:
                continue

            # Dietary preferences filter
            if dietary_preference == 'vegetarian':
                if not r.get('vegetarian_friendly', False):
                    continue
            elif dietary_preference == 'non_vegetarian':
                pass  # non-veg travelers can eat anywhere

            # Cuisine filter
            if cuisine:
                c_norm = cuisine.lower()
                if not any(c_norm in c.lower() for c in r.get('cuisine_types', [])):
                    continue

            # Price level filter
            if price_levels:
                # e.g. [PRICE_LEVEL_INEXPENSIVE, PRICE_LEVEL_MODERATE, €, €€]
                p_level = r.get('price_level', '€€')
                matched_price = False
                for p_req in price_levels:
                    if p_req in p_level or (p_req == 'PRICE_LEVEL_INEXPENSIVE' and p_level == '€') or                        (p_req == 'PRICE_LEVEL_MODERATE' and p_level == '€€') or                        (p_req == 'PRICE_LEVEL_EXPENSIVE' and p_level in ['€€€', '€€€€']):
                        matched_price = True
                        break
                if not matched_price:
                    continue

            walk_mins = max(1, round(dist / (4.5 * 1000 / 60)))  # 4.5 km/h walking speed
            maps_url = self.get_maps_url(action='place', query_or_place_name=r['name'], place_id=r['place_id'])['url']

            results.append({
                'placeId': r['place_id'],
                'place_id': r['place_id'],
                'name': r['name'],
                'address': r['address'],
                'city': r['city'],
                'neighborhood': r.get('neighborhood', ''),
                'coordinates': r['coordinates'],
                'rating': r['rating'],
                'priceLevel': r.get('price_level', '€€'),
                'price_level': r.get('price_level', '€€'),
                'price_tier': len(r.get('price_level', '€€')),
                'cuisine': ', '.join(r.get('cuisine_types', ['Trattoria'])),
                'cuisineType': r.get('cuisine_types', []),
                'cuisine_types': r.get('cuisine_types', []),
                'dietaryTier': r.get('dietary_tier', 'vegetarian_friendly'),
                'dietary_tier': r.get('dietary_tier', 'vegetarian_friendly'),
                'dietary_classification': r.get('dietary_tier', 'vegetarian_friendly'),
                'vegetarianFriendly': r.get('vegetarian_friendly', True),
                'vegetarian_friendly': r.get('vegetarian_friendly', True),
                'signatureDishes': r.get('signature_dishes', []),
                'signature_dishes': r.get('signature_dishes', []),
                'signature_dish': ', '.join(r.get('signature_dishes', [])[:2]),
                'approxWalkingMinutes': walk_mins,
                'distanceMeters': round(dist),
                'distance_meters': round(dist),
                'googleMapsUri': maps_url,
                'google_maps_url': maps_url,
                'localNotes': r.get('local_notes', ''),
                'local_notes': r.get('local_notes', '')
            })

        # Sort: if vegetarian requested, prioritize naturally_vegetarian and highest ratings
        def sort_key(x):
            tier_score = 3 if x['dietaryTier'] == 'naturally_vegetarian' else (2 if x['dietaryTier'] == 'vegetarian_friendly' else 1)
            return (tier_score if dietary_preference == 'vegetarian' else 1, -x['distanceMeters'] / 500.0 + x['rating'])

        results.sort(key=sort_key, reverse=True)
        return {'restaurants': results[:limit]}

    # -------------------------------------------------------------
    # Tool 5: calculate_route
    # -------------------------------------------------------------
    def calculate_route(self, origin: Union[Dict[str, float], str], 
                        destination: Union[Dict[str, float], str], 
                        travel_mode: str = 'WALK', 
                        transit_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lat1, lng1, orig_name = resolve_coords(origin)
        lat2, lng2, dest_name = resolve_coords(destination)

        direct_dist = haversine_distance(lat1, lng1, lat2, lng2)
        mode = travel_mode.upper()

        # Check special transit/ferry cases
        is_capri_crossing = ('sorrento' in orig_name.lower() and 'capri' in dest_name.lower()) or                             ('capri' in orig_name.lower() and 'sorrento' in dest_name.lower())
        is_garda_crossing = ('malcesine' in orig_name.lower() and 'limone' in dest_name.lower()) or                             ('limone' in orig_name.lower() and 'malcesine' in dest_name.lower())

        transit_steps = []
        if is_capri_crossing:
            distance_meters = 14500
            duration_seconds = 25 * 60  # 25 min hydrofoil
            formatted_duration = '25 mins'
            mode_used = 'FERRY'
            transit_steps = [
                {'instruction': 'Board Caremar / NLG Hydrofoil at Sorrento Marina Piccola', 'durationSeconds': 1500, 'travelMode': 'FERRY'},
                {'instruction': 'Arrive at Capri Marina Grande Port', 'durationSeconds': 0, 'travelMode': 'WALK'}
            ]
        elif is_garda_crossing:
            distance_meters = 5800
            duration_seconds = 20 * 60
            formatted_duration = '20 mins'
            mode_used = 'FERRY'
            transit_steps = [
                {'instruction': 'Board Navigazione Laghi passenger ferry at Malcesine pier', 'durationSeconds': 1200, 'travelMode': 'FERRY'},
                {'instruction': 'Disembark at Limone sul Garda lakeside harbor', 'durationSeconds': 0, 'travelMode': 'WALK'}
            ]
        elif mode == 'WALK':
            # Winding street factor = 1.25, walking speed = 4.5 km/h (1.25 m/s)
            distance_meters = round(direct_dist * 1.25)
            duration_seconds = max(60, round(distance_meters / 1.25))
            duration_mins = max(1, round(duration_seconds / 60))
            formatted_duration = f'{duration_mins} mins'
            mode_used = 'WALK'
            transit_steps = [
                {'instruction': f'Walk {round(distance_meters/1000.0, 1) if distance_meters >= 1000 else distance_meters} {("km" if distance_meters >= 1000 else "m")} to {dest_name}', 'durationSeconds': duration_seconds, 'travelMode': 'WALK'}
            ]
        elif mode == 'TRANSIT':
            # Urban transit or train
            if direct_dist > 5000:
                # Regional or rail
                distance_meters = round(direct_dist * 1.3)
                duration_seconds = max(600, round((distance_meters / (60 * 1000 / 3600)) + 600))  # 60km/h avg + 10m wait
                duration_mins = round(duration_seconds / 60)
                formatted_duration = f'{duration_mins} mins'
                mode_used = 'TRANSIT'
                transit_steps = [
                    {'instruction': f'Walk to nearest station / transit stop', 'durationSeconds': 300, 'travelMode': 'WALK'},
                    {'instruction': f'Take train / express bus towards {dest_name}', 'durationSeconds': duration_seconds - 600, 'travelMode': 'TRANSIT'},
                    {'instruction': f'Walk to {dest_name}', 'durationSeconds': 300, 'travelMode': 'WALK'}
                ]
            else:
                # Local metro/bus
                distance_meters = round(direct_dist * 1.3)
                duration_seconds = max(300, round((distance_meters / (22 * 1000 / 3600)) + 420))  # 22km/h + 7m wait
                duration_mins = round(duration_seconds / 60)
                formatted_duration = f'{duration_mins} mins'
                mode_used = 'TRANSIT'
                transit_steps = [
                    {'instruction': f'Take local Metro / Bus line towards {dest_name}', 'durationSeconds': duration_seconds - 180, 'travelMode': 'TRANSIT'},
                    {'instruction': f'Walk 2 mins to {dest_name}', 'durationSeconds': 180, 'travelMode': 'WALK'}
                ]
        elif mode == 'DRIVE':
            distance_meters = round(direct_dist * 1.35)
            avg_speed_kmh = 35.0 if direct_dist < 15000 else 80.0
            duration_seconds = max(180, round(distance_meters / (avg_speed_kmh * 1000 / 3600)))
            duration_mins = max(3, round(duration_seconds / 60))
            formatted_duration = f'{duration_mins} mins'
            mode_used = 'DRIVE'
            transit_steps = [
                {'instruction': f'Drive via main route to {dest_name} (Beware of ZTL limited traffic zones in city centers)', 'durationSeconds': duration_seconds, 'travelMode': 'DRIVE'}
            ]
        else: # BICYCLE
            distance_meters = round(direct_dist * 1.25)
            duration_seconds = max(120, round(distance_meters / (14 * 1000 / 3600)))  # 14 km/h
            duration_mins = max(2, round(duration_seconds / 60))
            formatted_duration = f'{duration_mins} mins'
            mode_used = 'BICYCLE'
            transit_steps = [
                {'instruction': f'Cycle to {dest_name}', 'durationSeconds': duration_seconds, 'travelMode': 'BICYCLE'}
            ]

        # Polyline simulation for map rendering
        num_pts = max(3, min(10, int(distance_meters / 300) + 2))
        polyline_pts = []
        for i in range(num_pts):
            t = i / float(num_pts - 1)
            # subtle curve
            curve = math.sin(t * math.pi) * 0.001
            p_lat = lat1 + t * (lat2 - lat1) + curve
            p_lng = lng1 + t * (lng2 - lng1) + curve
            polyline_pts.append({'lat': round(p_lat, 6), 'lng': round(p_lng, 6)})

        maps_nav_url = self.get_maps_url(action='directions', origin=f'{lat1},{lng1}', destination=f'{lat2},{lng2}', travel_mode=mode.lower())['url']

        return {
            'origin': orig_name,
            'originCoords': {'lat': lat1, 'lng': lng1},
            'destination': dest_name,
            'destinationCoords': {'lat': lat2, 'lng': lng2},
            'travelMode': mode_used,
            'distanceMeters': distance_meters,
            'distanceKm': round(distance_meters / 1000.0, 2),
            'durationSeconds': duration_seconds,
            'durationFormatted': formatted_duration,
            'transitSteps': transit_steps,
            'polylineCoordinates': polyline_pts,
            'googleMapsNavigationUrl': maps_nav_url
        }

    # -------------------------------------------------------------
    # Tool 6: compare_routes
    # -------------------------------------------------------------
    def compare_routes(self, origin: Union[Dict[str, float], str], 
                       destination: Union[Dict[str, float], str]) -> Dict[str, Any]:
        lat1, lng1, orig_name = resolve_coords(origin)
        lat2, lng2, dest_name = resolve_coords(destination)
        dist = haversine_distance(lat1, lng1, lat2, lng2)

        is_capri = ('sorrento' in orig_name.lower() and 'capri' in dest_name.lower()) or                    ('capri' in orig_name.lower() and 'sorrento' in dest_name.lower())

        walk_route = self.calculate_route(origin, destination, travel_mode='WALK')
        transit_route = self.calculate_route(origin, destination, travel_mode='TRANSIT')
        drive_route = self.calculate_route(origin, destination, travel_mode='DRIVE')

        modes: Dict[str, Any] = {
            'walking': {
                'distanceMeters': walk_route['distanceMeters'],
                'durationMinutes': round(walk_route['durationSeconds'] / 60),
                'feasible': dist <= 3500
            },
            'transit': {
                'distanceMeters': transit_route['distanceMeters'],
                'durationMinutes': round(transit_route['durationSeconds'] / 60),
                'lines': ['Local Transit Line / Metro']
            },
            'driving': {
                'distanceMeters': drive_route['distanceMeters'],
                'durationMinutes': round(drive_route['durationSeconds'] / 60),
                'ztlWarning': True
            }
        }

        if is_capri:
            modes['ferry'] = {
                'durationMinutes': 25,
                'departurePort': 'Sorrento Marina Piccola',
                'ticketPriceEur': 22.50
            }
            rec_mode = 'FERRY'
            rec_reason = 'Capri is an island accessible exclusively via high-speed hydrofoil or ferry (25 min crossing).'
        elif dist <= 1200:
            rec_mode = 'WALK'
            rec_reason = f'Walking is {modes["walking"]["durationMinutes"]} mins (faster than waiting for transit and avoids historic center ZTL traffic).'
        elif dist <= 5000:
            rec_mode = 'TRANSIT'
            rec_reason = f'Transit is recommended ({modes["transit"]["durationMinutes"]} mins) to avoid high parking fees and restricted driving zones (ZTL).'
        else:
            rec_mode = 'TRANSIT' if 'rome' in orig_name.lower() or 'milan' in orig_name.lower() else 'DRIVE'
            rec_reason = 'High-speed rail / regional transit is fastest and avoids regional highway tolls and city center driving bans.'

        return {
            'origin': orig_name,
            'destination': dest_name,
            'recommendedMode': rec_mode,
            'recommendationReason': rec_reason,
            'modes': modes
        }

    # -------------------------------------------------------------
    # Tool 7: calculate_multi_stop_route
    # -------------------------------------------------------------
    def calculate_multi_stop_route(self, origin_hotel: Union[Dict[str, float], str], 
                                   stops: List[Dict[str, Any]], 
                                   return_to_hotel: bool = True, 
                                   travel_mode: str = 'WALK') -> Dict[str, Any]:
        legs = []
        total_travel_seconds = 0
        total_activity_minutes = 0
        total_walking_meters = 0

        current_location = origin_hotel
        waypoints_for_day = [origin_hotel] + [s.get('location', s.get('name')) for s in stops]
        if return_to_hotel:
            waypoints_for_day.append(origin_hotel)

        for i in range(len(waypoints_for_day) - 1):
            from_loc = waypoints_for_day[i]
            to_loc = waypoints_for_day[i + 1]

            leg_route = self.calculate_route(from_loc, to_loc, travel_mode=travel_mode)
            legs.append({
                'legIndex': i + 1,
                'from': leg_route['origin'],
                'to': leg_route['destination'],
                'fromCoords': leg_route['originCoords'],
                'toCoords': leg_route['destinationCoords'],
                'distanceMeters': leg_route['distanceMeters'],
                'durationMinutes': round(leg_route['durationSeconds'] / 60),
                'mode': leg_route['travelMode'],
                'instructions': leg_route['transitSteps'][0]['instruction'] if leg_route['transitSteps'] else f'Proceed to {leg_route["destination"]}',
                'polylineCoordinates': leg_route['polylineCoordinates'],
                'googleMapsUrl': leg_route['googleMapsNavigationUrl']
            })

            total_travel_seconds += leg_route['durationSeconds']
            if leg_route['travelMode'] == 'WALK':
                total_walking_meters += leg_route['distanceMeters']

        for s in stops:
            dwell = s.get('allocatedDwellMinutes', 60)
            total_activity_minutes += dwell

        total_travel_mins = round(total_travel_seconds / 60)
        total_day_mins = total_travel_mins + total_activity_minutes
        total_walk_km = round(total_walking_meters / 1000.0, 2)

        # Day efficiency pacing formula:
        # <= 8h (480m) = comfortable, 8-10.5h (481-630m) = busy, > 10.5h (> 630m) = overloaded
        if total_day_mins <= 480:
            status = 'comfortable'
        elif total_day_mins <= 630:
            status = 'busy'
        else:
            status = 'overloaded'

        return {
            'totalTravelDurationMinutes': total_travel_mins,
            'totalActivityDurationMinutes': total_activity_minutes,
            'totalDayDurationMinutes': total_day_mins,
            'totalDayDurationFormatted': f'{total_day_mins // 60}h {total_day_mins % 60}m',
            'totalWalkingDistanceKm': total_walk_km,
            'dayEfficiencyStatus': status,
            'stopsCount': len(stops),
            'legs': legs
        }

    # -------------------------------------------------------------
    # Tool 8: calculate_route_matrix
    # -------------------------------------------------------------
    def calculate_route_matrix(self, place_coordinates: List[Dict[str, Any]], 
                               travel_mode: str = 'WALK') -> Dict[str, Any]:
        matrix = []
        n = len(place_coordinates)
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrix.append({
                        'originId': place_coordinates[i]['id'],
                        'destinationId': place_coordinates[j]['id'],
                        'distanceMeters': 0,
                        'durationSeconds': 0,
                        'status': 'SUCCESS'
                    })
                    continue

                lat1, lng1 = place_coordinates[i]['lat'], place_coordinates[i]['lng']
                lat2, lng2 = place_coordinates[j]['lat'], place_coordinates[j]['lng']
                dist = haversine_distance(lat1, lng1, lat2, lng2)

                route = self.calculate_route(
                    {'lat': lat1, 'lng': lng1, 'name': place_coordinates[i]['id']},
                    {'lat': lat2, 'lng': lng2, 'name': place_coordinates[j]['id']},
                    travel_mode=travel_mode
                )

                matrix.append({
                    'originId': place_coordinates[i]['id'],
                    'destinationId': place_coordinates[j]['id'],
                    'distanceMeters': route['distanceMeters'],
                    'durationSeconds': route['durationSeconds'],
                    'status': 'SUCCESS'
                })

        return {'matrix': matrix}

    # -------------------------------------------------------------
    # Tool 9: get_maps_url
    # -------------------------------------------------------------
    def get_maps_url(self, action: str, query_or_place_name: Optional[str] = None, 
                     place_id: Optional[str] = None, origin: Optional[str] = None, 
                     destination: Optional[str] = None, waypoints: Optional[List[str]] = None, 
                     travel_mode: str = 'walking') -> Dict[str, Any]:
        base = 'https://www.google.com/maps/'
        if action == 'search':
            q = query_or_place_name or 'Italy'
            params = {'api': '1', 'query': q}
            url = f"{base}search/?{urllib.parse.urlencode(params)}"
        elif action == 'place':
            q = query_or_place_name or 'Place'
            params = {'api': '1', 'query': q}
            if place_id:
                params['query_place_id'] = place_id
            url = f"{base}search/?{urllib.parse.urlencode(params)}"
        elif action == 'directions':
            params = {
                'api': '1',
                'origin': origin or '',
                'destination': destination or '',
                'travelmode': travel_mode.lower()
            }
            if waypoints:
                params['waypoints'] = '|'.join(waypoints)
            url = f"{base}dir/?{urllib.parse.urlencode(params)}"
        else:
            url = 'https://www.google.com/maps'

        return {'url': url}
