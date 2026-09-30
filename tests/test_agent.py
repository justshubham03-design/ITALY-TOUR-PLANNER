"""
Test Suite for Travel Agent (12-factor scoring, itinerary generation, pacing, and mutations).
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.travel_agent import TravelAgent


class TestTravelAgent(unittest.TestCase):
    def setUp(self):
        self.agent = TravelAgent()

    def test_groq_client_initialization(self):
        self.assertIsNotNone(self.agent.groq_client)
        self.assertTrue(self.agent.groq_client.is_available())
        self.assertEqual(self.agent.groq_client.api_key[:4], 'gsk_')

    def test_gemini_client_initialization(self):
        self.assertIsNotNone(self.agent.gemini_client)
        self.assertTrue(self.agent.gemini_client.is_available())
        self.assertEqual(self.agent.gemini_client.api_key[:3], 'AQ.')

    def test_llm_router_status(self):
        self.assertIsNotNone(self.agent.llm_router)
        status = self.agent.llm_router.get_status()
        self.assertTrue(status['groq_connected'])
        self.assertTrue(status['gemini_connected'])
        self.assertEqual(status['active_engine'], 'Hybrid (Groq + Gemini)')

    def test_llm_router_routing_auto(self):
        # Test routing in auto/groq/gemini mode (gracefully returns fallback or successful content)
        res = self.agent.llm_router.chat_concierge("Hello from Sorrento!", preferred_provider="auto")
        self.assertIn("success", res)
        if res["success"]:
            self.assertTrue(bool(res.get("content")))
            self.assertIn(res.get("provider"), ["Groq", "Gemini", "Groq (Fallback)", "Gemini (Fallback)"])

    def test_sorrento_3day_generation(self):
        trip = self.agent.generate_itinerary(
            destination="sorrento",
            duration_days=3,
            pace="balanced",
            dietary_preference="vegetarian",
            interests=["historical", "museums", "beaches", "viewpoints", "food"]
        )

        self.assertIsNotNone(trip)
        self.assertEqual(trip["destination"], "sorrento")
        self.assertEqual(len(trip["days"]), 3)

        # Check that each day has stops and valid pacing status
        for day in trip["days"]:
            self.assertIn(day["pacing_status"], ["comfortable", "busy", "overloaded"])
            self.assertGreater(len(day["stops"]), 0)
            self.assertGreater(day["total_active_hours"], 0)
            self.assertGreaterEqual(day["total_walking_km"], 0)

        # Check reservation checklist
        checklist = trip["reservation_checklist"]
        self.assertIn("urgent", checklist)
        self.assertIn("advance", checklist)
        self.assertIn("flexible", checklist)
        self.assertGreater(len(checklist["urgent"]) + len(checklist["advance"]) + len(checklist["flexible"]), 0)

    def test_rome_4day_generation(self):
        trip = self.agent.generate_itinerary(
            destination="rome",
            duration_days=4,
            pace="balanced",
            dietary_preference="vegetarian"
        )
        self.assertEqual(trip["destination"], "rome")
        self.assertEqual(len(trip["days"]), 4)

    def test_mutation_make_day_less_tiring(self):
        trip = self.agent.generate_itinerary(
            destination="sorrento",
            duration_days=3,
            pace="intense",
            dietary_preference="vegetarian"
        )
        original_hours = trip["days"][1]["total_active_hours"]

        result = self.agent.mutate_itinerary(trip, "Make Day 2 less tiring and remove afternoon sights")
        self.assertIn("mutation_summary", result)
        mutated_trip = result.get("trip", result)
        mutated_day2 = mutated_trip["days"][1]
        self.assertLessEqual(mutated_day2["total_active_hours"], original_hours)

    def test_mutation_replace_dinner_vegetarian(self):
        trip = self.agent.generate_itinerary(
            destination="sorrento",
            duration_days=3,
            pace="balanced",
            dietary_preference="non_vegetarian"
        )
        result = self.agent.mutate_itinerary(trip, "Replace dinner with 100% vegetarian trattoria")
        self.assertIn("mutation_summary", result)
        self.assertIn("vegetarian", result["mutation_summary"].lower())

    def test_mutation_swap_days(self):
        trip = self.agent.generate_itinerary(
            destination="sorrento",
            duration_days=3,
            pace="balanced",
            dietary_preference="vegetarian"
        )
        theme_day1 = trip["days"][0]["theme"]
        theme_day2 = trip["days"][1]["theme"]

        result = self.agent.mutate_itinerary(trip, "Swap Day 1 and Day 2")
        mutated_trip = result.get("trip", result)
        self.assertEqual(mutated_trip["days"][0]["theme"], theme_day2)
        self.assertEqual(mutated_trip["days"][1]["theme"], theme_day1)

    def test_mutation_add_sunset_viewpoint(self):
        trip = self.agent.generate_itinerary(
            destination="sorrento",
            duration_days=3,
            pace="balanced",
            dietary_preference="vegetarian"
        )
        result = self.agent.mutate_itinerary(trip, "Add a scenic sunset viewpoint to Day 1")
        self.assertIn("mutation_summary", result)
        mutated_trip = result.get("trip", result)
        day1_stop_names = [s["name"] for s in mutated_trip["days"][0]["stops"]]
        self.assertTrue(any("Sunset" in n or "Villa Comunale" in n or "Viewpoint" in n or "Bagni" in n for n in day1_stop_names))


if __name__ == "__main__":
    unittest.main()
