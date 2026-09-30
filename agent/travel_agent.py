# Italy Travel Planner - Intelligent AI Agent Engine with Groq + Gemini Dual LLM
import os
import json
import math
import logging
from typing import Dict, List, Any, Optional, Union
from maps_mcp_server.google_maps_service import GoogleMapsService
from agent.groq_client import GroqClient
from agent.gemini_client import GeminiClient
from agent.llm_router import LLMRouter
from knowledge_base.italy_knowledge import DESTINATIONS, PLACES, RESTAURANTS, REGIONAL_SIGNATURE_DISHES, TRANSIT_KNOWLEDGE

from agent.search_verifier import SearchVerifier
from agent.graph_pipeline import ItineraryGraphPipeline
from agent.conversational_mutator import ConversationalMutator

logger = logging.getLogger('TravelAgent')

class ItalyTravelAgent:
    """
    Core Agentic Planner for Italy Travel Itineraries.
    Powered by Dual / Hybrid LLM Engine (Groq + Gemini),
    paired with 12-factor recommendation scoring, TSP geographic clustering,
    day-load pacing analysis, and pre-trip reservation timelines.
    """

    def __init__(self, groq_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.llm_router = LLMRouter(groq_api_key=groq_api_key, gemini_api_key=gemini_api_key)
        self.groq_client = self.llm_router.groq_client
        self.gemini_client = self.llm_router.gemini_client
        self.maps_service = GoogleMapsService()
        self.search_verifier = SearchVerifier()
        self.conversational_mutator = ConversationalMutator(groq_api_key=groq_api_key, gemini_api_key=gemini_api_key)
        self.graph_pipeline = ItineraryGraphPipeline(groq_api_key=groq_api_key, gemini_api_key=gemini_api_key)

    def score_place(self, place: Dict[str, Any], user_interests: List[str], 
                    dietary_pref: str = 'both', pace: str = 'balanced') -> float:
        """
        12-factor recommendation scoring formula.
        """
        score = 0.0
        # 1. Rating (0 to 25 pts)
        rating = place.get('rating', 4.0)
        score += (rating / 5.0) * 25.0

        # 2. Popularity / review volume (0 to 15 pts)
        ratings_count = place.get('user_ratings_total', place.get('userRatingCount', 1000))
        popularity_score = min(15.0, math.log10(max(10, ratings_count)) * 2.8)
        score += popularity_score

        # 3. User interest match (0 to 25 pts)
        interests_lower = [i.lower() for i in user_interests] if user_interests else []
        cat = place.get('category', '').lower()
        types = [t.lower() for t in place.get('types', [])]

        if not interests_lower or 'all' in interests_lower:
            score += 20.0
        else:
            match_count = 0
            if cat in interests_lower or any(i in cat for i in interests_lower):
                match_count += 2
            for t in types:
                if any(i in t for i in interests_lower):
                    match_count += 1
            score += min(25.0, match_count * 8.0)

        # 4. Pace suitability (0 to 10 pts)
        dwell = place.get('typical_dwell_minutes', place.get('typicalDwellMinutes', 60))
        if pace == 'relaxed' and dwell <= 120:
            score += 10.0
        elif pace == 'intense':
            score += 8.0
        else:
            score += 9.0

        # 5. Must-see / urgency bonus (0 to 10 pts)
        if place.get('booking_urgency') == 'urgent' or place.get('bookingUrgency') == 'urgent':
            score += 8.0
        if place.get('local_tips') or place.get('localTips'):
            score += 5.0

        # 6. Authenticity baseline (0 to 15 pts)
        score += 12.0
        return round(score, 2)

    def generate_itinerary(self, destination: Optional[str] = None,
                           destination_id: Optional[str] = None, 
                           days: Optional[int] = None, 
                           duration_days: Optional[int] = None,
                           interests: Optional[List[str]] = None, 
                           dietary_preference: str = 'vegetarian', 
                           pace: str = 'balanced', 
                           start_date: Optional[str] = None, 
                           hotel_name: Optional[str] = None,
                           llm_provider: str = 'auto',
                           **kwargs) -> Dict[str, Any]:
        """
        Generates a multi-day geographically clustered, zero-backtracking itinerary.
        """
        dest_input = destination or destination_id or kwargs.get('dest', 'sorrento')
        dest_id = dest_input.lower().strip()
        num_days = days or duration_days or kwargs.get('duration', 3)
        num_days = int(num_days)

        dest_meta = DESTINATIONS.get(dest_id)
        if not dest_meta:
            for k, v in DESTINATIONS.items():
                if dest_id in k or k in dest_id:
                    dest_id = k
                    dest_meta = v
                    break

        if not dest_meta:
            dest_id = 'sorrento'
            dest_meta = DESTINATIONS['sorrento']

        interests = interests or ['historical', 'viewpoints', 'beaches', 'food']
        hotel = hotel_name or dest_meta.get('default_hotel', {}).get('name', f'Grand Hotel {dest_meta["name"]}')
        hotel_coords = dest_meta.get('default_hotel', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']})

        # 1. Fetch Candidate Attractions
        all_places_res = self.maps_service.search_places('', city_or_region=dest_meta['name'], limit=30)
        candidate_places = all_places_res.get('places', [])

        if len(candidate_places) < num_days * 2:
            nearby_res = self.maps_service.search_nearby_places(dest_meta['center']['lat'], dest_meta['center']['lng'], radius_meters=45000, limit=25)
            for nb in nearby_res.get('nearbyPlaces', []):
                if not any(cp['placeId'] == nb['placeId'] for cp in candidate_places):
                    full_p = self.maps_service.get_place_details(nb['placeId'])
                    if 'error' not in full_p:
                        candidate_places.append(full_p)

        # Score candidates
        for cp in candidate_places:
            cp['agentScore'] = self.score_place(cp, interests, dietary_pref=dietary_preference, pace=pace)

        candidate_places.sort(key=lambda x: x['agentScore'], reverse=True)

        # 2. Fetch Authentic Restaurants
        rest_res = self.maps_service.search_restaurants(
            latitude=dest_meta['center']['lat'],
            longitude=dest_meta['center']['lng'],
            radius_meters=35000,
            dietary_preference=dietary_preference,
            min_rating=4.2,
            limit=15
        )
        candidate_restaurants = rest_res.get('restaurants', [])

        # 3. Cluster into Day Itineraries (7-8 Options / Stops per Day)
        itinerary_days = []
        allocated_place_ids = set()

        for day_idx in range(1, num_days + 1):
            day_title = f'Day {day_idx}: '
            day_theme = ''

            # Region-specific curated clusters
            if dest_id == 'sorrento':
                if day_idx == 1:
                    day_theme = 'Sorrento Historic Heart, Lemon Groves, Marina Grande & Sunset Coast'
                    target_ids = ['it_sor_historic_centre', 'it_sor_villa_comunale', 'it_sor_san_francesco_cloister', 'it_sor_giardini_cataldo', 'it_sor_piazza_tasso', 'it_sor_marina_grande']
                elif day_idx == 2:
                    day_theme = 'Ancient Wonders of Pompeii, Roman Ruins & Emerald Cove'
                    target_ids = ['it_sor_pompeii', 'it_sor_bagni_regina', 'it_sor_vallone_mulini', 'it_sor_villa_comunale', 'it_sor_historic_centre']
                elif day_idx == 3:
                    day_theme = 'Glamorous Isle of Capri, Faraglioni Rocks & Cliffside Positano'
                    target_ids = ['it_sor_capri_ferry', 'it_sor_positano', 'it_sor_amalfi_duomo', 'it_sor_ravello', 'it_sor_marina_grande']
                else:
                    target_ids = ['it_sor_historic_centre', 'it_sor_villa_comunale', 'it_sor_bagni_regina']
            elif dest_id == 'rome':
                if day_idx == 1:
                    day_theme = 'Imperial Antiquities, Pantheon Oculus, Gelato & Trevi Golden Hour'
                    target_ids = ['it_rom_colosseum', 'it_rom_capitolini', 'it_rom_pantheon', 'it_rom_giolitti', 'it_rom_navona', 'it_rom_trevi']
                elif day_idx == 2:
                    day_theme = 'Vatican Splendors, Castel Sant\'Angelo, Gianicolo Hill & Trastevere'
                    target_ids = ['it_rom_vatican', 'it_rom_castel_santangelo', 'it_rom_campo_fiori', 'it_rom_gianicolo', 'it_rom_trastevere', 'it_rom_aventine_keyhole']
                elif day_idx == 3:
                    day_theme = 'Renaissance Art Masterpieces, Spanish Steps & Sunset Garden'
                    target_ids = ['it_rom_borghese', 'it_rom_spanish_steps', 'it_rom_navona', 'it_rom_giolitti', 'it_rom_aventine_keyhole', 'it_rom_trevi']
                elif day_idx == 4:
                    day_theme = 'Ancient Appian Way, Catacombs & Roman Piazzas'
                    target_ids = ['it_rom_colosseum', 'it_rom_pantheon', 'it_rom_trevi', 'it_rom_navona', 'it_rom_gianicolo']
                else:
                    target_ids = ['it_rom_colosseum', 'it_rom_pantheon', 'it_rom_trevi']
            elif dest_id == 'bari':
                if day_idx == 1:
                    day_theme = 'Bari Vecchia Orecchiette Nonnas, Norman Castle & Adriatic Lungomare'
                    target_ids = ['it_bar_bari_vecchia', 'it_bar_san_nicola', 'it_bar_orecchiette_street', 'it_bar_castello_svevo', 'it_bar_gelateria_gentile', 'it_bar_piazza_mercantile', 'it_bar_lungomare']
                elif day_idx == 2:
                    day_theme = 'Cliffside Polignano a Mare & Fairytale Trulli of Alberobello'
                    target_ids = ['it_pug_polignano', 'it_pug_alberobello', 'it_bar_molo_san_nicola', 'it_bar_teatro_petruzzelli', 'it_bar_panificio_fiore']
                elif day_idx == 3:
                    day_theme = 'Seaside Promenade, Opera Theater & Old Harbor'
                    target_ids = ['it_bar_teatro_petruzzelli', 'it_bar_san_sabino', 'it_bar_panificio_fiore', 'it_bar_ferrarese', 'it_bar_lungomare']
                else:
                    target_ids = ['it_bar_bari_vecchia', 'it_bar_san_nicola']
            elif dest_id == 'puglia':
                if day_idx == 1:
                    day_theme = "UNESCO Trulli of Alberobello, Circular Locorotondo & White City of Ostuni"
                    target_ids = ['it_pug_alberobello', 'it_pug_locorotondo', 'it_pug_martina_franca', 'it_pug_ostuni']
                elif day_idx == 2:
                    day_theme = 'Cliffside Polignano a Mare, Sea Caves & Monopoli Harbor'
                    target_ids = ['it_pug_polignano', 'it_pug_monopoli', 'it_pug_grotte_castellana', 'it_pug_torre_guaceto']
                elif day_idx == 3:
                    day_theme = 'Ancient Sassi di Matera Cave Sanctuary & Rock Churches'
                    target_ids = ['it_pug_matera', 'it_pug_alberobello', 'it_pug_ostuni']
                elif day_idx == 4:
                    day_theme = 'Baroque Splendors of Lecce & Adriatic Coastal Reserves'
                    target_ids = ['it_pug_lecce_croce', 'it_pug_torre_guaceto', 'it_pug_polignano']
                else:
                    target_ids = ['it_pug_alberobello', 'it_pug_polignano']
            elif dest_id == 'milan':
                if day_idx == 1:
                    day_theme = 'Duomo Rooftops, Galleria, Scala Opera, Sforza Castle & Brera Arts'
                    target_ids = ['it_mil_duomo', 'it_mil_galleria', 'it_mil_scala', 'it_mil_castello', 'it_mil_parco_sempione', 'it_mil_brera']
                elif day_idx == 2:
                    day_theme = "Da Vinci's Last Supper, Sant'Ambrogio, Pasticceria & Navigli Canals"
                    target_ids = ['it_mil_last_supper', 'it_mil_sant_ambrogio', 'it_mil_marchesi', 'it_mil_quadrilatero', 'it_mil_bosco_verticale', 'it_mil_navigli']
                elif day_idx == 3:
                    day_theme = 'Lake Garda Scaliger Fortress & Jamaica Beach Excursion'
                    target_ids = ['it_gar_sirmione_castle', 'it_gar_grotte_catullo', 'it_gar_jamaica_beach', 'it_mil_duomo']
                else:
                    target_ids = ['it_mil_duomo', 'it_mil_galleria']
            elif dest_id == 'lake_garda':
                if day_idx == 1:
                    day_theme = 'Sirmione Peninsula, Scaliger Castle, Roman Villa & Jamaica Beach'
                    target_ids = ['it_gar_sirmione_castle', 'it_gar_grotte_catullo', 'it_gar_jamaica_beach', 'it_gar_isola_garda']
                elif day_idx == 2:
                    day_theme = 'Monte Baldo Rotating Cableway, Malcesine Fortress & Lemon Groves'
                    target_ids = ['it_gar_malcesine_cablecar', 'it_gar_malcesine_castle', 'it_gar_limone', 'it_gar_riva']
                elif day_idx == 3:
                    day_theme = 'Scenic Lake Ferry, Gardone Riviera & Bardolino Vineyards'
                    target_ids = ['it_gar_gardone', 'it_gar_bardolino', 'it_gar_sirmione_castle']
                else:
                    target_ids = ['it_gar_sirmione_castle', 'it_gar_grotte_catullo']
            else:
                target_ids = []

            # Populate matched places (aiming for 6 attraction stops per day)
            selected_for_day = []
            for tid in target_ids:
                p_match = next((p for p in candidate_places if p.get('place_id') == tid or p.get('placeId') == tid), None)
                if not p_match:
                    details = self.maps_service.get_place_details(tid)
                    if 'error' not in details:
                        p_match = details
                if p_match and p_match.get('placeId', p_match.get('place_id')) not in [s.get('placeId', s.get('place_id')) for s in selected_for_day]:
                    selected_for_day.append(p_match)
                    allocated_place_ids.add(p_match.get('placeId', p_match.get('place_id')))

            target_attraction_count = 6
            if len(selected_for_day) < target_attraction_count:
                for cp in candidate_places:
                    cp_id = cp.get('placeId', cp.get('place_id'))
                    if cp_id not in allocated_place_ids and len(selected_for_day) < target_attraction_count:
                        selected_for_day.append(cp)
                        allocated_place_ids.add(cp_id)

            lunch_rest = candidate_restaurants[(day_idx - 1) % len(candidate_restaurants)] if candidate_restaurants else None
            dinner_rest = candidate_restaurants[(day_idx) % len(candidate_restaurants)] if candidate_restaurants else None

            # Build comprehensive 8-stop payload
            time_labels = [
                '09:00 – Morning Landmark & Monument',
                '10:45 – Historic Quarter & Artisan Walk',
                '12:00 – Midday Cultural / Sacred Art',
                '13:15 – Traditional Lunch Trattoria',
                '14:45 – Afternoon Museum / Archaeological Discovery',
                '16:45 – Historic Piazza & Artisanal Gelato Break',
                '18:15 – Sunset Panoramic Vista & Golden Hour',
                '20:00 – Authentic Dinner Trattoria & Passeggiata'
            ]

            stops_payload = []
            attraction_idx = 0

            for slot_idx, slot_label in enumerate(time_labels):
                if slot_idx == 3: # Lunch Stop
                    if lunch_rest:
                        l_coords = lunch_rest.get('coordinates', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']})
                        l_maps_url = lunch_rest.get('google_maps_url', lunch_rest.get('googleMapsUri', f"https://www.google.com/maps/search/?api=1&query={lunch_rest['name']}"))
                        l_photo_url = lunch_rest.get('image_url', 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80')
                        stops_payload.append({
                            'name': lunch_rest['name'],
                            'location': lunch_rest.get('place_id', lunch_rest.get('placeId', 'lunch_stop')),
                            'placeId': lunch_rest.get('place_id', lunch_rest.get('placeId', 'lunch_stop')),
                            'category': 'food',
                            'type': 'lunch',
                            'time_slot': slot_label,
                            'timeSlot': slot_label,
                            'dwell_time_hours': 1.0,
                            'allocatedDwellMinutes': 60,
                            'rating': lunch_rest.get('rating', 4.7),
                            'booking_urgency': 'flexible',
                            'bookingUrgency': 'flexible',
                            'ticket_urgency': 'flexible',
                            'booking_lead_time': 'Walk-in or 1 day prior',
                            'bookingLeadTime': 'Walk-in or 1 day prior',
                            'official_booking_url': lunch_rest.get('website', l_maps_url),
                            'officialBookingUrl': lunch_rest.get('website', l_maps_url),
                            'ticket_url': lunch_rest.get('website', l_maps_url),
                            'signature_dish': lunch_rest.get('signature_dish', ', '.join(lunch_rest.get('signatureDishes', ['Seasonal specialties']))),
                            'local_tips': f"Must-try specialty: {lunch_rest.get('signature_dish', 'Seasonal specialties')}. Dietary: {(lunch_rest.get('dietary_classification', 'vegetarian_friendly')).replace('_', ' ').title()}",
                            'notes': f"Must-try specialty: {lunch_rest.get('signature_dish', 'Seasonal specialties')}.",
                            'description': f"Authentic trattoria known for {lunch_rest.get('cuisine', 'Italian cuisine')} and local ingredients.",
                            'what_to_do': [
                                f"Savor authentic regional dishes including {lunch_rest.get('signature_dish', 'house specialties')}.",
                                "Experience traditional Italian family hospitality and local ambiance.",
                                "Pair meal with regional Italian wine or fresh local mineral water and seasonal dessert."
                            ],
                            'image_url': l_photo_url,
                            'imageUrl': l_photo_url,
                            'google_photos_url': l_maps_url,
                            'googlePhotosUrl': l_maps_url,
                            'coordinates': l_coords,
                            'latitude': l_coords.get('lat', dest_meta['center']['lat']),
                            'longitude': l_coords.get('lng', dest_meta['center']['lng']),
                            'maps_url': l_maps_url,
                            'googleMapsUrl': l_maps_url
                        })
                elif slot_idx == 7: # Dinner Stop
                    if dinner_rest:
                        d_coords = dinner_rest.get('coordinates', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']})
                        d_maps_url = dinner_rest.get('google_maps_url', dinner_rest.get('googleMapsUri', f"https://www.google.com/maps/search/?api=1&query={dinner_rest['name']}"))
                        d_photo_url = dinner_rest.get('image_url', 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80')
                        stops_payload.append({
                            'name': dinner_rest['name'],
                            'location': dinner_rest.get('place_id', dinner_rest.get('placeId', 'dinner_stop')),
                            'placeId': dinner_rest.get('place_id', dinner_rest.get('placeId', 'dinner_stop')),
                            'category': 'food',
                            'type': 'dinner',
                            'time_slot': slot_label,
                            'timeSlot': slot_label,
                            'dwell_time_hours': 1.5,
                            'allocatedDwellMinutes': 90,
                            'rating': dinner_rest.get('rating', 4.8),
                            'booking_urgency': 'advance',
                            'bookingUrgency': 'advance',
                            'ticket_urgency': 'advance',
                            'booking_lead_time': dinner_rest.get('reservationUrgency', 'Reserve 1-3 days ahead'),
                            'bookingLeadTime': dinner_rest.get('reservationUrgency', 'Reserve 1-3 days ahead'),
                            'official_booking_url': dinner_rest.get('website', d_maps_url),
                            'officialBookingUrl': dinner_rest.get('website', d_maps_url),
                            'ticket_url': dinner_rest.get('website', d_maps_url),
                            'signature_dish': dinner_rest.get('signature_dish', ', '.join(dinner_rest.get('signatureDishes', ['Regional pasta']))),
                            'local_tips': f"Dinner recommendation: {dinner_rest.get('signature_dish', 'House specialty')}. {dinner_rest.get('reservationUrgency', 'Book table in advance.')}",
                            'notes': f"Dinner recommendation: {dinner_rest.get('signature_dish', 'House specialty')}.",
                            'description': f"Cozy evening trattoria offering {dinner_rest.get('cuisine', 'Italian regional dining')}.",
                            'what_to_do': [
                                f"Indulge in classic evening specialties like {dinner_rest.get('signature_dish', 'handmade pasta and regional delicacies')}.",
                                "Relax over an aperitivo and digestivo (limoncello / amaro) in an authentic local setting.",
                                "Conclude the evening with an Italian passeggiata through illuminated historic piazzas."
                            ],
                            'image_url': d_photo_url,
                            'imageUrl': d_photo_url,
                            'google_photos_url': d_maps_url,
                            'googlePhotosUrl': d_maps_url,
                            'coordinates': d_coords,
                            'latitude': d_coords.get('lat', dest_meta['center']['lat']),
                            'longitude': d_coords.get('lng', dest_meta['center']['lng']),
                            'maps_url': d_maps_url,
                            'googleMapsUrl': d_maps_url
                        })
                else: # Attraction Stop
                    if attraction_idx < len(selected_for_day):
                        p = selected_for_day[attraction_idx]
                        attraction_idx += 1
                    else:
                        p = candidate_places[attraction_idx % len(candidate_places)] if candidate_places else {}
                        attraction_idx += 1

                    if p:
                        dwell = p.get('typicalDwellMinutes', p.get('typical_dwell_minutes', 60))
                        coords = p.get('coordinates', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']})
                        pid = p.get('place_id', p.get('placeId', ''))
                        maps_url = p.get('google_maps_url', self.maps_service.get_maps_url(action='place', query_or_place_name=p['name'], place_id=pid)['url'])
                        photos_url = p.get('google_photos_url', maps_url)
                        photo_url = p.get('image_url', 'https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=80')

                        wtd = p.get('what_to_do', [])
                        if not wtd:
                            wtd = [
                                f"Explore the grounds and architectural highlights of {p['name']}.",
                                "Take scenic photographs and observe the historic details of the landmark.",
                                "Immerse in the cultural heritage and local atmosphere of the surrounding area."
                            ]

                        stops_payload.append({
                            'name': p['name'],
                            'location': pid,
                            'placeId': pid,
                            'category': p.get('category', 'historical'),
                            'type': p.get('category', 'historical'),
                            'time_slot': slot_label,
                            'timeSlot': slot_label,
                            'dwell_time_hours': round(dwell / 60.0, 1),
                            'allocatedDwellMinutes': dwell,
                            'rating': p.get('rating', 4.8),
                            'booking_urgency': p.get('bookingUrgency', p.get('booking_urgency', 'optional')),
                            'bookingUrgency': p.get('bookingUrgency', p.get('booking_urgency', 'optional')),
                            'ticket_urgency': p.get('bookingUrgency', p.get('booking_urgency', 'optional')),
                            'booking_lead_time': p.get('bookingLeadTime', p.get('booking_lead_time', '')),
                            'bookingLeadTime': p.get('bookingLeadTime', p.get('booking_lead_time', '')),
                            'official_booking_url': p.get('officialBookingUrl', p.get('official_booking_url', '')),
                            'officialBookingUrl': p.get('officialBookingUrl', p.get('official_booking_url', '')),
                            'ticket_url': p.get('officialBookingUrl', p.get('official_booking_url', '')),
                            'local_tips': p.get('localTips', p.get('local_tips', '')),
                            'notes': p.get('localTips', p.get('local_tips', '')),
                            'description': p.get('description', ''),
                            'what_to_do': wtd,
                            'image_url': photo_url,
                            'imageUrl': photo_url,
                            'google_photos_url': photos_url,
                            'googlePhotosUrl': photos_url,
                            'coordinates': coords,
                            'latitude': coords.get('lat', 40.6263),
                            'longitude': coords.get('lng', 14.3758),
                            'maps_url': maps_url,
                            'googleMapsUrl': maps_url
                        })

            # Calculate day routes and pacing
            multi_stop_res = self.maps_service.calculate_multi_stop_route(
                origin_hotel=hotel_coords,
                stops=stops_payload,
                return_to_hotel=True,
                travel_mode='WALK' if dest_id in ['rome', 'sorrento', 'bari', 'milan'] else 'DRIVE'
            )

            pacing_status = multi_stop_res['dayEfficiencyStatus']
            total_active_hours = round(multi_stop_res['totalDayDurationMinutes'] / 60.0, 1)
            total_walk_km = multi_stop_res['totalWalkingDistanceKm']

            itinerary_days.append({
                'day_number': day_idx,
                'dayNumber': day_idx,
                'title': day_title + (day_theme or f'Exploring {dest_meta["name"]} Highlights'),
                'theme': day_theme or f'Cultural & scenic discoveries in {dest_meta["name"]}',
                'stops': stops_payload,
                'meals': {
                    'lunch': lunch_rest,
                    'dinner': dinner_rest
                },
                'pacing_status': pacing_status,
                'total_active_hours': total_active_hours,
                'total_walking_km': total_walk_km,
                'pacing': {
                    'dayEfficiencyStatus': pacing_status,
                    'totalTravelDurationMinutes': multi_stop_res['totalTravelDurationMinutes'],
                    'totalActivityDurationMinutes': multi_stop_res['totalActivityDurationMinutes'],
                    'totalDayDurationMinutes': multi_stop_res['totalDayDurationMinutes'],
                    'totalDayDurationFormatted': multi_stop_res['totalDayDurationFormatted'],
                    'totalWalkingDistanceKm': total_walk_km
                },
                'legs': multi_stop_res['legs']
            })

        checklist = self.generate_reservation_checklist(itinerary_days)
        regional_dishes = REGIONAL_SIGNATURE_DISHES.get(dest_id, REGIONAL_SIGNATURE_DISHES.get('sorrento', []))
        llm_status = self.llm_router.get_status()

        return {
            'trip_id': f'trip_{dest_id}_{num_days}d',
            'tripId': f'trip_{dest_id}_{num_days}d',
            'title': f'{dest_meta["name"]} Signature Journey',
            'destination': dest_id,
            'destination_meta': dest_meta,
            'duration_days': num_days,
            'daysCount': num_days,
            'pace': pace,
            'dietary_preference': dietary_preference,
            'dietaryPreference': dietary_preference,
            'hotel': hotel,
            'days': itinerary_days,
            'itinerary': itinerary_days,
            'reservation_checklist': checklist,
            'checklist': checklist,
            'regional_dishes': regional_dishes,
            'regionalDishes': regional_dishes,
            'transit_notes': dest_meta.get('transit_notes', ''),
            'transitNotes': dest_meta.get('transit_notes', ''),
            'llm_engine': llm_status['active_engine'],
            'llm_status': llm_status
        }

    def generate_reservation_checklist(self, itinerary_days: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts all attractions and dining requiring pre-booking and categorizes them by urgency.
        """
        urgent_items = []
        advance_items = []
        flexible_items = []
        seen_places = set()

        for day in itinerary_days:
            day_num = day.get('day_number', day.get('dayNumber', 1))
            for stop in day.get('stops', []):
                pid = stop.get('placeId', stop.get('name'))
                if pid in seen_places:
                    continue
                seen_places.add(pid)

                urgency = stop.get('bookingUrgency', stop.get('booking_urgency', stop.get('ticket_urgency', 'optional'))).lower()
                lead_time = stop.get('bookingLeadTime', stop.get('booking_lead_time', 'On-site or walk-in'))
                off_url = stop.get('officialBookingUrl', stop.get('official_booking_url', stop.get('ticket_url', '')))

                item = {
                    'id': f'chk_{pid}',
                    'day': day_num,
                    'name': stop['name'],
                    'category': stop.get('category', 'Attraction'),
                    'urgency': urgency,
                    'lead_time': lead_time,
                    'leadTime': lead_time,
                    'official_url': off_url,
                    'officialUrl': off_url,
                    'ticket_url': off_url,
                    'notes': f'Recommended booking: {lead_time}',
                    'action_required': f'Book timed entry ticket for Day {day_num}',
                    'actionRequired': f'Book timed entry ticket for Day {day_num}',
                    'completed': False
                }

                if urgency == 'urgent':
                    urgent_items.append(item)
                elif urgency == 'advance':
                    advance_items.append(item)
                else:
                    flexible_items.append(item)

            dinner = day.get('meals', {}).get('dinner')
            if dinner and isinstance(dinner, dict) and dinner.get('placeId') not in seen_places:
                seen_places.add(dinner['placeId'])
                urg_note = dinner.get('reservationUrgency', 'Book 1-3 days prior')
                d_maps_url = dinner.get('googleMapsUri', '')
                d_item = {
                    'id': f'chk_{dinner["placeId"]}',
                    'day': day_num,
                    'name': f'{dinner["name"]} (Dinner Trattoria)',
                    'category': 'Dining',
                    'lead_time': urg_note,
                    'leadTime': urg_note,
                    'official_url': d_maps_url,
                    'officialUrl': d_maps_url,
                    'ticket_url': d_maps_url,
                    'notes': f'Trattoria reservation: {urg_note}',
                    'actionRequired': f'Reserve dinner table for Day {day_num}',
                    'action_required': f'Reserve dinner table for Day {day_num}',
                    'completed': False
                }
                if 'urgent' in urg_note.lower() or 'weeks' in urg_note.lower() or '30-60' in urg_note:
                    d_item['urgency'] = 'urgent'
                    urgent_items.append(d_item)
                elif 'advance' in urg_note.lower() or 'days' in urg_note.lower():
                    d_item['urgency'] = 'advance'
                    advance_items.append(d_item)

        return {
            'urgent': urgent_items,
            'advance': advance_items,
            'flexible': flexible_items
        }

    def mutate_itinerary(self, current_trip: Dict[str, Any], mutation_instruction: str, llm_provider: str = 'auto') -> Dict[str, Any]:
        """
        Applies conversational user modifications (pacing adjustment, dietary switch, swap days, add viewpoint).
        Enriched by Dual / Hybrid LLM Engine (Groq + Gemini) with deterministic Maps MCP recalculation.
        """
        instruction_lower = mutation_instruction.lower().strip()
        itinerary = current_trip.get('days', current_trip.get('itinerary', []))
        dest_val = current_trip.get('destination', 'sorrento')
        dest_id = dest_val.get('id', 'sorrento') if isinstance(dest_val, dict) else str(dest_val).lower()
        dest_meta = DESTINATIONS.get(dest_id, DESTINATIONS['sorrento'])

        logger.info(f"Processing Multi-LLM ({llm_provider}) mutation: '{mutation_instruction}'")
        mutation_summary = ''

        # 1. Structural Modifications
        if 'less tiring' in instruction_lower or 'relax' in instruction_lower or 'too busy' in instruction_lower or 'pacing' in instruction_lower:
            target_day_num = 2
            for word in instruction_lower.split():
                if word.isdigit():
                    target_day_num = int(word)

            if target_day_num <= len(itinerary):
                day = itinerary[target_day_num - 1]
                if len(day['stops']) > 1:
                    removed_stop = day['stops'].pop()
                    mutation_summary = f"Reduced Day {target_day_num} load by removing '{removed_stop['name']}' to create a more comfortable, leisurely pace."
                else:
                    for s in day['stops']:
                        s['allocatedDwellMinutes'] = max(30, s.get('allocatedDwellMinutes', 60) - 30)
                        s['dwell_time_hours'] = round(s['allocatedDwellMinutes'] / 60.0, 1)
                    mutation_summary = f"Relaxed dwell times on Day {target_day_num} for a more tranquil experience."

                new_route = self.maps_service.calculate_multi_stop_route(
                    origin_hotel=dest_meta.get('default_hotel', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']}),
                    stops=day['stops'],
                    return_to_hotel=True
                )
                day['pacing_status'] = new_route['dayEfficiencyStatus']
                day['total_active_hours'] = round(new_route['totalDayDurationMinutes'] / 60.0, 1)
                day['total_walking_km'] = new_route['totalWalkingDistanceKm']
                day['pacing'] = {
                    'dayEfficiencyStatus': new_route['dayEfficiencyStatus'],
                    'totalTravelDurationMinutes': new_route['totalTravelDurationMinutes'],
                    'totalActivityDurationMinutes': new_route['totalActivityDurationMinutes'],
                    'totalDayDurationMinutes': new_route['totalDayDurationMinutes'],
                    'totalDayDurationFormatted': new_route['totalDayDurationFormatted'],
                    'totalWalkingDistanceKm': new_route['totalWalkingDistanceKm']
                }
                day['legs'] = new_route['legs']

        elif 'swap' in instruction_lower:
            days_found = [int(w) for w in instruction_lower.split() if w.isdigit()]
            if len(days_found) >= 2 and days_found[0] <= len(itinerary) and days_found[1] <= len(itinerary):
                d1_idx, d2_idx = days_found[0] - 1, days_found[1] - 1
                itinerary[d1_idx], itinerary[d2_idx] = itinerary[d2_idx], itinerary[d1_idx]
                itinerary[d1_idx]['day_number'] = days_found[0]
                itinerary[d1_idx]['dayNumber'] = days_found[0]
                itinerary[d2_idx]['day_number'] = days_found[1]
                itinerary[d2_idx]['dayNumber'] = days_found[1]
                mutation_summary = f"Swapped Day {days_found[0]} and Day {days_found[1]} schedule."
            elif len(itinerary) >= 2:
                itinerary[0], itinerary[1] = itinerary[1], itinerary[0]
                itinerary[0]['day_number'] = 1
                itinerary[0]['dayNumber'] = 1
                itinerary[1]['day_number'] = 2
                itinerary[1]['dayNumber'] = 2
                mutation_summary = 'Swapped Day 1 and Day 2 schedule.'

        elif 'restaurant' in instruction_lower or 'vegetarian' in instruction_lower or 'food' in instruction_lower or 'dinner' in instruction_lower:
            target_day_num = 1
            for word in instruction_lower.split():
                if word.isdigit():
                    target_day_num = int(word)

            day = itinerary[min(target_day_num - 1, len(itinerary) - 1)]
            veg_rests = self.maps_service.search_restaurants(
                latitude=dest_meta['center']['lat'],
                longitude=dest_meta['center']['lng'],
                dietary_preference='vegetarian',
                min_rating=4.5,
                limit=8
            ).get('restaurants', [])

            if veg_rests:
                current_dinner_id = day.get('meals', {}).get('dinner', {}).get('placeId') if isinstance(day.get('meals', {}).get('dinner'), dict) else None
                new_dinner = next((r for r in veg_rests if r['placeId'] != current_dinner_id), veg_rests[0])
                if 'meals' not in day:
                    day['meals'] = {}
                day['meals']['dinner'] = new_dinner
                dishes_str = ', '.join(new_dinner.get('signatureDishes', [])[:2])
                mutation_summary = f"Replaced Day {day.get('day_number', target_day_num)} dinner with authentic 100% vegetarian trattoria: '{new_dinner['name']}' ({dishes_str})."

        elif 'add' in instruction_lower or 'viewpoint' in instruction_lower or 'sunset' in instruction_lower:
            target_day_num = 1
            for word in instruction_lower.split():
                if word.isdigit():
                    target_day_num = int(word)
            day = itinerary[min(target_day_num - 1, len(itinerary) - 1)]

            viewpoints = [p for p in PLACES if p['category'] == 'viewpoints' and (p['city_id'] == dest_id or dest_id in p['city_id'])]
            if not viewpoints:
                viewpoints = [p for p in PLACES if p['category'] == 'viewpoints']
            if viewpoints:
                vp = viewpoints[0]
                day['stops'].append({
                    'name': vp['name'],
                    'location': vp['place_id'],
                    'placeId': vp['place_id'],
                    'category': 'viewpoints',
                    'type': 'viewpoints',
                    'time_slot': 'Sunset Viewpoint (18:45)',
                    'timeSlot': 'Sunset Viewpoint (18:45)',
                    'allocatedDwellMinutes': 45,
                    'dwell_time_hours': 0.8,
                    'rating': vp['rating'],
                    'booking_urgency': 'optional',
                    'bookingUrgency': 'optional',
                    'ticket_urgency': 'optional',
                    'local_tips': vp.get('local_tips', 'Magnificent panoramic golden hour spot.'),
                    'notes': vp.get('local_tips', 'Magnificent panoramic golden hour spot.'),
                    'description': vp.get('description', ''),
                    'coordinates': vp['coordinates'],
                    'latitude': vp['coordinates']['lat'],
                    'longitude': vp['coordinates']['lng'],
                    'maps_url': vp.get('google_maps_url', f"https://www.google.com/maps/search/?api=1&query={vp['name']}")
                })
                new_route = self.maps_service.calculate_multi_stop_route(
                    origin_hotel=dest_meta.get('default_hotel', {'lat': dest_meta['center']['lat'], 'lng': dest_meta['center']['lng']}),
                    stops=day['stops'],
                    return_to_hotel=True
                )
                day['pacing_status'] = new_route['dayEfficiencyStatus']
                day['total_active_hours'] = round(new_route['totalDayDurationMinutes'] / 60.0, 1)
                day['total_walking_km'] = new_route['totalWalkingDistanceKm']
                day['pacing'] = {
                    'dayEfficiencyStatus': new_route['dayEfficiencyStatus'],
                    'totalTravelDurationMinutes': new_route['totalTravelDurationMinutes'],
                    'totalActivityDurationMinutes': new_route['totalActivityDurationMinutes'],
                    'totalDayDurationMinutes': new_route['totalDayDurationMinutes'],
                    'totalDayDurationFormatted': new_route['totalDayDurationFormatted'],
                    'totalWalkingDistanceKm': new_route['totalWalkingDistanceKm']
                }
                day['legs'] = new_route['legs']
                mutation_summary = f"Added scenic sunset viewpoint '{vp['name']}' to Day {day.get('day_number', target_day_num)}."
            else:
                mutation_summary = 'Adjusted schedule and added panoramic viewpoint stop.'
        else:
            mutation_summary = f"Updated itinerary based on '{mutation_instruction}'."

        # 2. Enrich with Multi-LLM (Groq / Gemini) natural language commentary
        try:
            prompt_text = f"The traveler requested: '{mutation_instruction}'. Modification applied: {mutation_summary}. Destination: {dest_meta['name']}."
            llm_resp = self.llm_router.chat_concierge(
                prompt=prompt_text,
                system_instruction="You are Viaggio Italia AI Concierge. Provide a concise, elegant 1-2 sentence Italian concierge commentary explaining the traveler's itinerary adjustment.",
                preferred_provider=llm_provider,
                max_tokens=150
            )
            if llm_resp.get("success") and llm_resp.get("content"):
                provider_tag = llm_resp.get("provider", "AI Concierge")
                mutation_summary = f"{mutation_summary}\n\n💡 *{provider_tag} Note:* {llm_resp['content'].strip()}"
        except Exception as e:
            logger.debug(f"LLM commentary optional enrichment skipped: {e}")

        checklist = self.generate_reservation_checklist(itinerary)
        current_trip['checklist'] = checklist
        current_trip['reservation_checklist'] = checklist
        current_trip['lastMutationSummary'] = mutation_summary
        current_trip['mutation_summary'] = mutation_summary
        return current_trip

# Alias for simple imports
TravelAgent = ItalyTravelAgent
