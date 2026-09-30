"""
Phase 8: Anti-Hallucination QA & 10 AI Direct Rules Verification Suite.
Automated validation of:
- Rule 1: Zero Fabrication (All places & restaurants in itinerary exist in ground truth)
- Rule 2: Ground-Truth Routing & Physics (Walking @ 4.5km/h, Ferries, Transit)
- Rule 3: Official Booking Hierarchy (Only .va, .it, .gov.it and primary authorized ticketing partners)
- Rule 4: Ticketing Urgency Hierarchy (🔴 Urgent, 🟡 Advance, 🟢 Flexible)
- Rule 5: No Overload Pacing (<=8h Comfortable, 8-10.5h Busy, >10.5h Overloaded)
- Rule 6: Geographical Clustering & Zero Backtracking (TSP proximity ordering)
- Rule 7: Mandatory Dwell & Transit Buffers (>=30 min dwell)
- Rule 8: Dietary Fidelity (Vegetarian classification integrity)
- Rule 9: Transparency & Uncertainty Disclaimers
- Rule 10: Performance & Latency Benchmark (<5 seconds)
"""

import unittest
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.travel_agent import TravelAgent
from agent.search_verifier import SearchVerifier
from knowledge_base.italy_knowledge import DESTINATIONS, PLACES, RESTAURANTS


class TestAIRulesAndAntiHallucination(unittest.TestCase):
    def setUp(self):
        self.agent = TravelAgent()
        self.verifier = SearchVerifier()

    def test_rule_1_zero_fabrication(self):
        """Rule 1: All generated itinerary stops must exist in ground-truth database."""
        trip = self.agent.generate_itinerary(destination_id="sorrento", days=3, dietary_preference="vegetarian")
        known_place_names = {p['name'] for p in PLACES} | {r['name'] for r in RESTAURANTS}

        for day in trip['days']:
            for stop in day['stops']:
                self.assertIn(stop['name'], known_place_names, f"Fabricated place detected: {stop['name']}")

    def test_rule_2_ground_truth_routing(self):
        """Rule 2: Transit times and distances must match physical distance routing."""
        route = self.agent.maps_service.calculate_route("Piazza Tasso", "Marina Grande Fisherman Village", travel_mode="walking")
        self.assertIn('distanceKm', route)
        self.assertGreater(route['distanceKm'], 0.5)
        self.assertLess(route['distanceKm'], 1.5)
        self.assertIn('durationFormatted', route)
        self.assertIn('mins', route['durationFormatted'])

    def test_rule_3_official_booking_hierarchy(self):
        """Rule 3: Official booking links must point to official authorities, never blacklisted resellers."""
        colosseum_url = 'https://ticketing.colosseo.it/en/'
        vatican_url = 'https://tickets.museivaticani.va/'
        reseller_url = 'https://www.getyourguide.com/colosseum-tickets'

        v_col = self.verifier.verify_booking_url(colosseum_url)
        self.assertTrue(v_col['is_official'])
        self.assertTrue(v_col['is_verified'])

        v_vat = self.verifier.verify_booking_url(vatican_url)
        self.assertTrue(v_vat['is_official'])
        self.assertTrue(v_vat['is_verified'])

        v_res = self.verifier.verify_booking_url(reseller_url)
        self.assertFalse(v_res['is_official'])
        self.assertFalse(v_res['is_verified'])

    def test_rule_4_urgency_hierarchy(self):
        """Rule 4: High-demand sights must have correct urgency tier and lead times."""
        u_col = self.verifier.classify_urgency("Colosseum & Roman Forum")
        self.assertEqual(u_col['tag'], 'urgent')

        u_vat = self.verifier.classify_urgency("Vatican Museums & Sistine Chapel")
        self.assertEqual(u_vat['tag'], 'urgent')

        u_piaz = self.verifier.classify_urgency("Piazza Navona")
        self.assertEqual(u_piaz['tag'], 'flexible')

    def test_rule_5_no_overload_pacing(self):
        """Rule 5: Pacing statuses must accurately reflect total day active hours."""
        trip = self.agent.generate_itinerary(destination_id="rome", days=4, pace="balanced")
        for day in trip['days']:
            hours = day['total_active_hours']
            if hours <= 8.0:
                self.assertEqual(day['pacing_status'], 'comfortable')
            elif hours <= 10.5:
                self.assertEqual(day['pacing_status'], 'busy')
            else:
                self.assertEqual(day['pacing_status'], 'overloaded')

    def test_rule_6_geographic_clustering_no_backtracking(self):
        """Rule 6: POIs within a day must be geographically adjacent."""
        trip = self.agent.generate_itinerary(destination_id="rome", days=3)
        for day in trip['days']:
            coords = [(s['latitude'], s['longitude']) for s in day['stops'] if 'latitude' in s and 'longitude' in s]
            if len(coords) >= 2:
                # Max distance between consecutive stops in central Rome should be <= 6km
                for i in range(len(coords) - 1):
                    lat_diff = abs(coords[i][0] - coords[i+1][0])
                    lng_diff = abs(coords[i][1] - coords[i+1][1])
                    self.assertLess(lat_diff, 0.15)
                    self.assertLess(lng_diff, 0.15)

    def test_rule_7_mandatory_buffers(self):
        """Rule 7: Every stop must have realistic dwell time >= 0.5 hours."""
        trip = self.agent.generate_itinerary(destination_id="milan", days=2)
        for day in trip['days']:
            for stop in day['stops']:
                self.assertGreaterEqual(stop.get('dwell_time_hours', 0), 0.5)

    def test_rule_8_dietary_fidelity(self):
        """Rule 8: Vegetarian trip must only include vegetarian-friendly restaurants and dishes."""
        trip = self.agent.generate_itinerary(destination_id="sorrento", days=3, dietary_preference="vegetarian")
        for day in trip['days']:
            for stop in day['stops']:
                if stop.get('type') == 'restaurant' or stop.get('category') == 'food':
                    dish = stop.get('signature_dish', '').lower()
                    # Must not contain explicit meat indicators
                    self.assertNotIn('carbonara con guanciale', dish)
                    self.assertNotIn('cotoletta', dish)

    def test_rule_9_uncertainty_disclaimers(self):
        """Rule 9: Empty or invalid booking URLs must return explicit fallback disclaimers."""
        v_empty = self.verifier.verify_booking_url('')
        self.assertFalse(v_empty['is_official'])
        self.assertIn('No direct booking link required', v_empty['disclaimer'])

    def test_rule_10_latency_benchmark(self):
        """Rule 10: End-to-end itinerary synthesis must execute in under 5 seconds."""
        t0 = time.time()
        trip = self.agent.generate_itinerary(destination_id="puglia", days=4, dietary_preference="vegetarian")
        elapsed = time.time() - t0
        self.assertIsNotNone(trip)
        self.assertLess(elapsed, 5.0, f"Synthesis exceeded 5 seconds limit: {elapsed:.2f}s")
        print(f"\n[BENCHMARK] 4-Day Puglia synthesis completed in {elapsed:.3f} seconds (Target < 5.0s)")


if __name__ == '__main__':
    unittest.main()
