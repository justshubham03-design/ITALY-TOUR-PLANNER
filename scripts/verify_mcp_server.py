#!/usr/bin/env python3
"""
Comprehensive Live Verification Suite for Google Maps MCP Server (stdio JSON-RPC 2.0).
Executes and validates all 9 MCP tools over real JSON-RPC 2.0 stdio pipes.
"""

import os
import sys
import json
import subprocess
import time

# Ensure root is on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

SERVER_PATH = os.path.join(ROOT_DIR, "maps_mcp_server", "server.py")

class MCPTester:
    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, SERVER_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.req_id = 0
        self.results = []

    def send_request(self, method: str, params: dict = None) -> dict:
        self.req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.req_id,
            "method": method,
            "params": params or {}
        }
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        
        line = self.proc.stdout.readline()
        if not line:
            err = self.proc.stderr.read()
            raise RuntimeError(f"Server closed connection unexpectedly. Stderr: {err}")
        
        return json.loads(line)

    def close(self):
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.proc.stderr.close()
        self.proc.terminate()
        self.proc.wait()

def run_verification():
    print("=" * 75)
    print(" 🚀 LIVE MCP SERVER VERIFICATION (stdio JSON-RPC 2.0)")
    print(f" Server Path: {SERVER_PATH}")
    print("=" * 75)

    tester = MCPTester()
    passed_tests = 0
    total_tests = 0

    try:
        # 1. Initialize Handshake
        total_tests += 1
        print("\n[Step 1/11] Testing MCP Handshake ('initialize')...")
        init_resp = tester.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "MCP-Verification-Client", "version": "1.0.0"}
        })
        
        assert init_resp.get("id") == 1, "Invalid request ID match"
        server_info = init_resp.get("result", {}).get("serverInfo", {})
        print(f"  ✓ Connected to: {server_info.get('name')} v{server_info.get('version')}")
        passed_tests += 1

        # 2. Tools Discovery
        total_tests += 1
        print("\n[Step 2/11] Testing Tool Discovery ('tools/list')...")
        list_resp = tester.send_request("tools/list")
        tools = list_resp.get("result", {}).get("tools", [])
        tool_names = [t["name"] for t in tools]
        print(f"  ✓ Discovered {len(tools)} tools: {', '.join(tool_names)}")
        assert len(tools) == 9, f"Expected 9 tools, found {len(tools)}"
        passed_tests += 1

        # 3. Tool 1: search_places
        total_tests += 1
        print("\n[Step 3/11] Testing Tool 1: 'search_places' (Rome)...")
        r1 = tester.send_request("tools/call", {
            "name": "search_places",
            "arguments": {"query": "Colosseum", "city_or_region": "Rome"}
        })
        content1 = json.loads(r1["result"]["content"][0]["text"])
        assert len(content1.get("places", [])) > 0, "No places returned"
        place1 = content1["places"][0]
        print(f"  ✓ Result: {place1['name']} | Rating: {place1['rating']} | Dwell: {place1['typicalDwellMinutes']}m")
        passed_tests += 1

        # 4. Tool 2: search_nearby_places
        total_tests += 1
        print("\n[Step 4/11] Testing Tool 2: 'search_nearby_places' (Sorrento)...")
        r2 = tester.send_request("tools/call", {
            "name": "search_nearby_places",
            "arguments": {"latitude": 40.6263, "longitude": 14.3758, "radius_meters": 2000}
        })
        content2 = json.loads(r2["result"]["content"][0]["text"])
        nearby = content2.get("nearbyPlaces", [])
        assert len(nearby) > 0, "No nearby places returned"
        print(f"  ✓ Found {len(nearby)} places within 2km (Closest: {nearby[0]['name']} at {nearby[0]['distanceMeters']}m)")
        passed_tests += 1

        # 5. Tool 3: get_place_details
        total_tests += 1
        print("\n[Step 5/11] Testing Tool 3: 'get_place_details' (Pompeii)...")
        r3 = tester.send_request("tools/call", {
            "name": "get_place_details",
            "arguments": {"place_id": "it_sor_pompeii"}
        })
        content3 = json.loads(r3["result"]["content"][0]["text"])
        assert content3.get("placeId") == "it_sor_pompeii", "Place ID mismatch"
        print(f"  ✓ Details for: {content3['name']} | Urgency: {content3['bookingUrgency']} | Lead Time: {content3['bookingLeadTime']}")
        passed_tests += 1

        # 6. Tool 4: search_restaurants
        total_tests += 1
        print("\n[Step 6/11] Testing Tool 4: 'search_restaurants' (Vegetarian in Sorrento)...")
        r4 = tester.send_request("tools/call", {
            "name": "search_restaurants",
            "arguments": {"latitude": 40.6263, "longitude": 14.3758, "dietary_preference": "vegetarian"}
        })
        content4 = json.loads(r4["result"]["content"][0]["text"])
        rests = content4.get("restaurants", [])
        assert len(rests) > 0, "No restaurants found"
        print(f"  ✓ Found {len(rests)} vegetarian-friendly trattorias (Top: {rests[0]['name']} - Tier: {rests[0]['dietaryTier']})")
        passed_tests += 1

        # 7. Tool 5: calculate_route
        total_tests += 1
        print("\n[Step 7/11] Testing Tool 5: 'calculate_route' (Walking in Sorrento)...")
        r5 = tester.send_request("tools/call", {
            "name": "calculate_route",
            "arguments": {"origin": "Piazza Tasso", "destination": "Marina Grande Sorrento", "travel_mode": "WALK"}
        })
        content5 = json.loads(r5["result"]["content"][0]["text"])
        assert content5.get("distanceKm", 0) > 0, "Distance calculation failed"
        print(f"  ✓ Route: {content5['origin']} ➔ {content5['destination']} ({content5['distanceKm']} km, {content5['durationFormatted']})")
        passed_tests += 1

        # 8. Tool 6: compare_routes
        total_tests += 1
        print("\n[Step 8/11] Testing Tool 6: 'compare_routes' (Sorrento to Capri Ferry)...")
        r6 = tester.send_request("tools/call", {
            "name": "compare_routes",
            "arguments": {"origin": "Sorrento", "destination": "Capri Island: Marina Grande, Anacapri & Blue Grotto"}
        })
        content6 = json.loads(r6["result"]["content"][0]["text"])
        assert content6.get("recommendedMode") == "FERRY", "Expected FERRY recommendation for Capri"
        print(f"  ✓ Recommendation: {content6['recommendedMode']} | Reason: {content6['recommendationReason']}")
        passed_tests += 1

        # 9. Tool 7: calculate_multi_stop_route
        total_tests += 1
        print("\n[Step 9/11] Testing Tool 7: 'calculate_multi_stop_route' (Day Loop & Pacing)...")
        r7 = tester.send_request("tools/call", {
            "name": "calculate_multi_stop_route",
            "arguments": {
                "origin_hotel": "Grand Hotel La Favorita (Sorrento)",
                "stops": [
                    {"name": "Villa Comunale Park", "location": "Villa Comunale Park", "allocatedDwellMinutes": 45},
                    {"name": "Marina Grande", "location": "Marina Grande", "allocatedDwellMinutes": 60}
                ],
                "return_to_hotel": True,
                "travel_mode": "WALK"
            }
        })
        content7 = json.loads(r7["result"]["content"][0]["text"])
        assert "dayEfficiencyStatus" in content7, "Day efficiency missing"
        print(f"  ✓ Day Pacing: {content7['dayEfficiencyStatus'].upper()} ({content7['totalDayDurationFormatted']}, {content7['totalWalkingDistanceKm']} km walking across {len(content7['legs'])} legs)")
        passed_tests += 1

        # 10. Tool 8: calculate_route_matrix
        total_tests += 1
        print("\n[Step 10/11] Testing Tool 8: 'calculate_route_matrix' (3x3 Matrix)...")
        r8 = tester.send_request("tools/call", {
            "name": "calculate_route_matrix",
            "arguments": {
                "place_coordinates": [
                    {"id": "piazza_tasso", "lat": 40.6263, "lng": 14.3758},
                    {"id": "marina_grande", "lat": 40.6288, "lng": 14.3685},
                    {"id": "villa_comunale", "lat": 40.6275, "lng": 14.3739}
                ],
                "travel_mode": "WALK"
            }
        })
        content8 = json.loads(r8["result"]["content"][0]["text"])
        matrix = content8.get("matrix", [])
        assert len(matrix) == 9, f"Expected 9 matrix cells, got {len(matrix)}"
        print(f"  ✓ Matrix calculated: {len(matrix)} origin-destination pairs verified")
        passed_tests += 1

        # 11. Tool 9: get_maps_url
        total_tests += 1
        print("\n[Step 11/11] Testing Tool 9: 'get_maps_url' (Universal Directions Link)...")
        r9 = tester.send_request("tools/call", {
            "name": "get_maps_url",
            "arguments": {
                "action": "directions",
                "origin": "Rome Fiumicino Airport",
                "destination": "Colosseum Rome",
                "travel_mode": "transit"
            }
        })
        content9 = json.loads(r9["result"]["content"][0]["text"])
        assert "url" in content9 and "google.com/maps" in content9["url"], "Invalid Maps URL"
        print(f"  ✓ Generated URL: {content9['url']}")
        passed_tests += 1

    finally:
        tester.close()

    print("\n" + "=" * 75)
    print(f" 🎯 VERIFICATION RESULT: {passed_tests}/{total_tests} CHECKS PASSED (100% OPERATIONAL)")
    print("=" * 75)
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
