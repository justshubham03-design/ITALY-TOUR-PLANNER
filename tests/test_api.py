"""
Test Suite for REST API Request Handler (Mock Socket in-memory testing).
"""

import unittest
import json
import io
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import TravelPlannerRequestHandler


class MockSocket:
    def __init__(self, input_bytes: bytes):
        self._rfile = io.BytesIO(input_bytes)
        self._wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if 'r' in mode:
            return self._rfile
        elif 'w' in mode:
            return self._wfile
        return self._wfile

    def sendall(self, data):
        self._wfile.write(data)

    def get_output(self) -> bytes:
        return self._wfile.getvalue()


class MockServer:
    def __init__(self):
        pass


def execute_request(method: str, path: str, body: dict = None) -> tuple:
    """Simulates an HTTP request against TravelPlannerRequestHandler."""
    body_bytes = json.dumps(body).encode('utf-8') if body is not None else b''
    headers_str = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\n"
    if body_bytes:
        headers_str += f"Content-Type: application/json\r\nContent-Length: {len(body_bytes)}\r\n"
    headers_str += "\r\n"
    
    raw_input = headers_str.encode('utf-8') + body_bytes
    sock = MockSocket(raw_input)
    
    handler = TravelPlannerRequestHandler(sock, ('127.0.0.1', 8080), MockServer())
    raw_output = sock.get_output()
    
    # Parse status and response body
    header_part, _, body_part = raw_output.partition(b'\r\n\r\n')
    first_line = header_part.split(b'\r\n')[0].decode('utf-8')
    status_code = int(first_line.split(' ')[1])
    
    try:
        json_data = json.loads(body_part.decode('utf-8'))
    except Exception:
        json_data = body_part.decode('utf-8', errors='ignore')
        
    return status_code, json_data


class TestRESTAPI(unittest.TestCase):

    def test_health_endpoint(self):
        status, data = execute_request('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('Groq', data['llm_provider'])
        self.assertTrue(data['groq_connected'])
        self.assertTrue(data['gemini_connected'])
        self.assertEqual(data['mcp_tools_count'], 9)

    def test_destinations_endpoint(self):
        status, data = execute_request('GET', '/api/destinations')
        self.assertEqual(status, 200)
        self.assertIn('destinations', data)
        self.assertGreaterEqual(len(data['destinations']), 6)

    def test_explore_endpoint(self):
        status, data = execute_request('GET', '/api/explore?city=sorrento')
        self.assertEqual(status, 200)
        self.assertIn('places', data)
        self.assertGreater(len(data['places']), 0)

    def test_restaurants_endpoint(self):
        status, data = execute_request('GET', '/api/restaurants?city=sorrento&dietary=vegetarian')
        self.assertEqual(status, 200)
        self.assertIn('restaurants', data)
        self.assertGreater(len(data['restaurants']), 0)

    def test_regional_guide_endpoint(self):
        status, data = execute_request('GET', '/api/regional-guide?city=sorrento')
        self.assertEqual(status, 200)
        self.assertIn('region', data)
        self.assertIn('dishes', data)
        self.assertGreater(len(data['dishes']), 0)

    def test_trips_generate_endpoint(self):
        payload = {
            "destination": "sorrento",
            "duration_days": 3,
            "pace": "balanced",
            "dietary_preference": "vegetarian",
            "interests": ["historical", "museums", "beaches", "viewpoints", "food"]
        }
        status, data = execute_request('POST', '/api/trips/generate', payload)
        self.assertEqual(status, 200)
        trip = data.get('trip', data)
        self.assertEqual(trip['destination'], 'sorrento')
        self.assertEqual(len(trip['days']), 3)

    def test_trips_mutate_endpoint(self):
        # 1. Generate trip first
        payload = {
            "destination": "sorrento",
            "duration_days": 3,
            "pace": "balanced",
            "dietary_preference": "vegetarian"
        }
        _, gen_data = execute_request('POST', '/api/trips/generate', payload)
        trip = gen_data.get('trip', gen_data)

        # 2. Mutate trip
        mutate_payload = {
            "trip": trip,
            "mutation_prompt": "Swap Day 1 and Day 2"
        }
        status, mut_data = execute_request('POST', '/api/trips/mutate', mutate_payload)
        self.assertEqual(status, 200)
        self.assertIn('mutation_summary', mut_data)

    def test_mcp_call_endpoint(self):
        mcp_payload = {
            "tool": "calculate_route",
            "arguments": {
                "origin": "Piazza Tasso",
                "destination": "Marina Grande",
                "travel_mode": "WALK"
            }
        }
        status, data = execute_request('POST', '/api/mcp/call', mcp_payload)
        self.assertEqual(status, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['tool'], 'calculate_route')
        self.assertIn('distanceKm', data['result'])


if __name__ == "__main__":
    unittest.main()
