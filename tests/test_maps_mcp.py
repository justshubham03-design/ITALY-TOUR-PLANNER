"""
Test Suite for Google Maps MCP Server (9 Tools) and JSON-RPC stdio Protocol.
"""

import unittest
import json
import subprocess
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maps_mcp_server.google_maps_service import GoogleMapsService


class TestGoogleMapsMCPService(unittest.TestCase):
    def setUp(self):
        self.service = GoogleMapsService()

    def test_tool_1_search_places(self):
        result = self.service.search_places(query="Centro Storico", city_or_region="sorrento")
        self.assertIn("places", result)
        self.assertGreater(len(result["places"]), 0)
        names = [p["name"] for p in result["places"]]
        self.assertTrue(any("Centro Storico" in name for name in names))

    def test_tool_2_search_nearby_places(self):
        # Sorrento center coordinates
        result = self.service.search_nearby_places(latitude=40.6263, longitude=14.3758, radius_meters=1500)
        self.assertIn("nearbyPlaces", result)
        self.assertGreater(len(result["nearbyPlaces"]), 0)

    def test_tool_3_get_place_details(self):
        result = self.service.get_place_details(place_id="it_sor_pompeii")
        self.assertIn("placeId", result)
        self.assertEqual(result["placeId"], "it_sor_pompeii")
        self.assertEqual(result["bookingUrgency"], "urgent")
        self.assertTrue(result["officialBookingUrl"].startswith("http"))

    def test_tool_4_search_restaurants(self):
        # Sorrento coordinates
        result = self.service.search_restaurants(
            latitude=40.6263, 
            longitude=14.3758, 
            radius_meters=10000, 
            dietary_preference="vegetarian"
        )
        self.assertIn("restaurants", result)
        self.assertGreater(len(result["restaurants"]), 0)
        for r in result["restaurants"]:
            self.assertTrue(r["vegetarianFriendly"])
            self.assertIn(r["dietaryTier"], ["naturally_vegetarian", "easily_modified", "vegetarian_friendly"])

    def test_tool_5_calculate_route(self):
        route = self.service.calculate_route(
            origin="Piazza Tasso", 
            destination="Marina Grande Sorrento", 
            travel_mode="WALK"
        )
        self.assertIn("distanceKm", route)
        self.assertIn("durationFormatted", route)
        self.assertGreater(route["durationSeconds"], 0)
        self.assertTrue(route["googleMapsNavigationUrl"].startswith("https://www.google.com/maps/dir/"))

    def test_tool_6_compare_routes(self):
        comparison = self.service.compare_routes(
            origin="Sorrento", 
            destination="Pompeii Archaeological Park"
        )
        self.assertIn("modes", comparison)
        self.assertIn("recommendedMode", comparison)
        self.assertIn("transit", comparison["modes"])
        self.assertIn("driving", comparison["modes"])

    def test_tool_7_calculate_multi_stop_route(self):
        stops = [
            {"name": "Villa Comunale Park", "location": "Villa Comunale Park", "allocatedDwellMinutes": 45},
            {"name": "Marina Grande", "location": "Marina Grande", "allocatedDwellMinutes": 60}
        ]
        multi = self.service.calculate_multi_stop_route(
            origin_hotel="Piazza Tasso", 
            stops=stops, 
            return_to_hotel=True, 
            travel_mode="WALK"
        )
        self.assertIn("totalWalkingDistanceKm", multi)
        self.assertIn("totalTravelDurationMinutes", multi)
        self.assertIn("dayEfficiencyStatus", multi)
        self.assertEqual(len(multi["legs"]), 3)

    def test_tool_8_calculate_route_matrix(self):
        place_coords = [
            {"id": "piazza_tasso", "lat": 40.6263, "lng": 14.3758},
            {"id": "marina_grande", "lat": 40.6288, "lng": 14.3685},
            {"id": "villa_comunale", "lat": 40.6275, "lng": 14.3739}
        ]
        matrix = self.service.calculate_route_matrix(
            place_coordinates=place_coords, 
            travel_mode="WALK"
        )
        self.assertIn("matrix", matrix)
        self.assertEqual(len(matrix["matrix"]), 9)  # 3 x 3

    def test_tool_9_get_maps_url(self):
        res = self.service.get_maps_url(action="search", query_or_place_name="Piazza Tasso Sorrento")
        self.assertIn("url", res)
        self.assertTrue(res["url"].startswith("https://www.google.com/maps/search/?api=1"))


class TestMCPStdioServer(unittest.TestCase):
    """Test stdio JSON-RPC 2.0 communication with maps_mcp_server/server.py"""

    def test_mcp_stdio_initialize_and_call(self):
        server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "maps_mcp_server", "server.py")
        
        proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            # 1. Initialize
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"clientInfo": {"name": "test_client", "version": "1.0"}}
            }
            proc.stdin.write(json.dumps(init_req) + "\n")
            proc.stdin.flush()
            init_resp = json.loads(proc.stdout.readline())
            self.assertEqual(init_resp["id"], 1)
            self.assertIn("serverInfo", init_resp["result"])
            self.assertEqual(init_resp["result"]["serverInfo"]["name"], "italy-travel-maps-mcp")

            # 2. List tools
            tools_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            proc.stdin.write(json.dumps(tools_req) + "\n")
            proc.stdin.flush()
            tools_resp = json.loads(proc.stdout.readline())
            self.assertEqual(tools_resp["id"], 2)
            tools = tools_resp["result"]["tools"]
            self.assertEqual(len(tools), 9)
            tool_names = [t["name"] for t in tools]
            self.assertIn("search_places", tool_names)
            self.assertIn("get_maps_url", tool_names)

            # 3. Call tool: calculate_route
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "calculate_route",
                    "arguments": {
                        "origin": "Piazza Tasso",
                        "destination": "Marina Grande",
                        "travel_mode": "WALK"
                    }
                }
            }
            proc.stdin.write(json.dumps(call_req) + "\n")
            proc.stdin.flush()
            call_resp = json.loads(proc.stdout.readline())
            self.assertEqual(call_resp["id"], 3)
            content_text = call_resp["result"]["content"][0]["text"]
            route_data = json.loads(content_text)
            self.assertIn("distanceKm", route_data)
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.stderr.close()
            proc.terminate()
            proc.wait()


if __name__ == "__main__":
    unittest.main()
