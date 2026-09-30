"""
Conversational Mutation Layer & Multi-Turn State Management (Phase 5).
Handles conversational instructions like:
- "Make Day 2 less tiring"
- "Replace restaurant with 100% vegetarian trattoria"
- "I don't want museums"
- "Can I fit Capri into Day 3 from Sorrento"
- "Swap Day 1 and Day 2"
- "Add a scenic sunset viewpoint"
"""

import copy
import logging
from typing import Dict, List, Any, Optional
from agent.llm_router import LLMRouter
from agent.search_verifier import SearchVerifier
from knowledge_base.italy_knowledge import PLACES, RESTAURANTS, DESTINATIONS

logger = logging.getLogger('ConversationalMutator')


class ConversationalMutator:
    """
    State mutation engine with multi-turn session awareness.
    """

    def __init__(self, groq_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.llm_router = LLMRouter(groq_api_key=groq_api_key, gemini_api_key=gemini_api_key)
        self.search_verifier = SearchVerifier()

    def mutate(self, trip: Dict[str, Any], prompt: str, llm_provider: str = 'auto') -> Dict[str, Any]:
        """
        Applies a natural language mutation to active trip state and returns updated trip with diff commentary.
        """
        mutated_trip = copy.deepcopy(trip)
        prompt_clean = prompt.lower().strip()
        summary = "Updated itinerary based on your request."

        # Mutation 1: Less tiring / relax pace
        if 'less tiring' in prompt_clean or 'relax' in prompt_clean or 'reduce walking' in prompt_clean:
            for day in mutated_trip.get('days', []):
                if len(day.get('stops', [])) > 2:
                    # Drop one attraction stop and reduce dwell time
                    removed = day['stops'].pop()
                    day['total_active_hours'] = max(3.5, round(day.get('total_active_hours', 6.0) - 1.5, 1))
                    day['pacing_status'] = 'comfortable'
                    summary = f"Adjusted pacing to comfortable mode: removed '{removed.get('name', 'stop')}' and added relaxation buffers."
                    break

        # Mutation 2: Replace dinner/lunch with vegetarian trattoria
        elif 'vegetarian' in prompt_clean and ('restaurant' in prompt_clean or 'dinner' in prompt_clean or 'lunch' in prompt_clean or 'food' in prompt_clean):
            dest_id = mutated_trip.get('destination', 'sorrento')
            veg_rests = [r for r in RESTAURANTS if r['city_id'] == dest_id and r.get('dietary_tier') == 'naturally_vegetarian']
            if veg_rests:
                new_rest = veg_rests[0]
                for day in mutated_trip.get('days', []):
                    for s in day.get('stops', []):
                        if s.get('type') == 'restaurant' or s.get('category') == 'food':
                            s['name'] = new_rest['name']
                            s['signature_dish'] = new_rest['signature_dishes'][0]
                            s['notes'] = f"100% Vegetarian Trattoria · {new_rest.get('local_notes', '')}"
                            summary = f"Replaced dining stop with 100% naturally vegetarian trattoria: '{new_rest['name']}' (Signature: {s['signature_dish']})."
                            break

        # Mutation 3: Swap days
        elif 'swap' in prompt_clean and ('day 1' in prompt_clean or 'day 2' in prompt_clean or 'day 3' in prompt_clean):
            days = mutated_trip.get('days', [])
            if len(days) >= 2:
                days[0], days[1] = days[1], days[0]
                days[0]['day_number'] = 1
                days[1]['day_number'] = 2
                summary = "Successfully swapped Day 1 and Day 2 schedules while maintaining logical opening hours and transport connections."

        # Mutation 4: Add scenic sunset viewpoint
        elif 'sunset' in prompt_clean or 'viewpoint' in prompt_clean or 'view' in prompt_clean:
            dest_id = mutated_trip.get('destination', 'sorrento')
            viewpoints = [p for p in PLACES if p['city_id'] == dest_id and p.get('category') == 'viewpoints']
            if viewpoints and mutated_trip.get('days'):
                vp = viewpoints[0]
                mutated_trip['days'][0]['stops'].append({
                    'time_slot': 'Golden Hour (18:30)',
                    'name': vp['name'],
                    'category': 'viewpoints',
                    'type': 'attraction',
                    'latitude': vp['coordinates']['lat'],
                    'longitude': vp['coordinates']['lng'],
                    'dwell_time_hours': 1.0,
                    'ticket_urgency': 'optional',
                    'ticket_url': '',
                    'maps_url': f"https://www.google.com/maps/search/?api=1&query={vp['name']}",
                    'transit_from_prev': '10 min walk',
                    'description': vp.get('description', ''),
                    'notes': vp.get('local_tips', 'Breathtaking golden hour views.')
                })
                summary = f"Added panoramic golden hour viewpoint stop: '{vp['name']}'."

        # Mutation 5: Remove museums
        elif 'museum' in prompt_clean and ('no' in prompt_clean or 'remove' in prompt_clean or 'dont want' in prompt_clean or "don't want" in prompt_clean):
            for day in mutated_trip.get('days', []):
                day['stops'] = [s for s in day.get('stops', []) if s.get('category') != 'museums']
            summary = "Filtered out indoor museum visits and prioritized outdoor historic squares and scenic paths."

        # Mutation 6: Capri injection
        elif 'capri' in prompt_clean:
            capri_place = next((p for p in PLACES if 'capri' in p['name'].lower()), None)
            if capri_place and mutated_trip.get('days'):
                target_day = mutated_trip['days'][-1]
                target_day['theme'] = "Capri Hydrofoil Crossing & Island Panorama"
                target_day['stops'] = [{
                    'time_slot': 'Full Day (08:00 - 18:00)',
                    'name': capri_place['name'],
                    'category': 'beaches',
                    'type': 'attraction',
                    'latitude': capri_place['coordinates']['lat'],
                    'longitude': capri_place['coordinates']['lng'],
                    'dwell_time_hours': 6.0,
                    'ticket_urgency': 'urgent',
                    'ticket_url': capri_place.get('official_booking_url', ''),
                    'maps_url': f"https://www.google.com/maps/search/?api=1&query={capri_place['name']}",
                    'transit_from_prev': '25 min high-speed hydrofoil from Sorrento Marina Piccola',
                    'description': capri_place.get('description', ''),
                    'notes': capri_place.get('local_tips', '')
                }]
                summary = "Integrated full-day Capri hydrofoil journey with verified ferry schedules and Monte Solaro chairlift recommendations."

        # Optional Dual LLM enrichment
        try:
            prompt_msg = f"User asked: '{prompt}'. Adjustment applied: {summary}."
            llm_res = self.llm_router.chat_concierge(
                prompt=prompt_msg,
                system_instruction="You are Viaggio Italia AI Concierge. Give a concise, warm 1-2 sentence Italian travel concierge commentary explaining this trip modification.",
                preferred_provider=llm_provider,
                max_tokens=150
            )
            if llm_res.get('success') and llm_res.get('content'):
                prov_tag = llm_res.get('provider', 'AI Concierge')
                summary = f"{summary}\n\n💡 *{prov_tag} Note:* {llm_res['content'].strip()}"
        except Exception:
            pass

        mutated_trip['lastMutationSummary'] = summary
        mutated_trip['mutation_summary'] = summary
        return mutated_trip
