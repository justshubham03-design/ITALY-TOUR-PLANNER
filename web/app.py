#!/usr/bin/env python3
"""
Italy Local Travel Planner - Web Server & REST API.
Serves responsive SPA frontend and REST API endpoints connected to the Maps MCP service & Travel Agent.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, List, Any, Optional

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from maps_mcp_server.google_maps_service import GoogleMapsService
from agent.travel_agent import ItalyTravelAgent
from knowledge_base.italy_knowledge import DESTINATIONS, HOTELS, PLACES, RESTAURANTS, REGIONAL_SIGNATURE_DISHES, TRANSIT_KNOWLEDGE

maps_service = GoogleMapsService()
travel_agent = ItalyTravelAgent()

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

class TravelPlannerRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def _send_json(self, data: Any, status: int = 200):
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            print(f"Error sending JSON response: {e}")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            query_params = urllib.parse.parse_qs(parsed.query)

            if path == '/api/health':
                llm_stat = travel_agent.llm_router.get_status()
                self._send_json({
                    'status': 'healthy', 
                    'version': '2.0.0', 
                    'engine': 'Hybrid Groq + Gemini AI Travel Agent & Maps MCP',
                    'llm_provider': 'Groq + Gemini',
                    'groq_connected': llm_stat['groq_connected'],
                    'gemini_connected': llm_stat['gemini_connected'],
                    'llm_status': llm_stat,
                    'mcp_tools_count': 9
                })
            elif path == '/api/destinations':
                self._send_json({'destinations': list(DESTINATIONS.values())})
            elif path == '/api/hotels':
                self._send_json({'hotels': HOTELS})
            elif path == '/api/explore':
                city = query_params.get('city', [None])[0]
                category = query_params.get('category', [None])[0]
                q = query_params.get('query', [''])[0]
                limit = int(query_params.get('limit', [50])[0])
                res = maps_service.search_places(query=q, city_or_region=city, category=category, limit=limit)
                self._send_json(res)
            elif path == '/api/restaurants':
                city = query_params.get('city', ['sorrento'])[0]
                dietary = query_params.get('dietary', ['both'])[0]
                cuisine = query_params.get('cuisine', [None])[0]
                dest = DESTINATIONS.get(city.lower(), DESTINATIONS['sorrento'])
                res = maps_service.search_restaurants(
                    latitude=dest['center']['lat'],
                    longitude=dest['center']['lng'],
                    radius_meters=35000,
                    cuisine=cuisine,
                    dietary_preference=dietary,
                    min_rating=4.0,
                    limit=20
                )
                self._send_json(res)
            elif path == '/api/regional-guide':
                city = query_params.get('city', ['sorrento'])[0].lower()
                dishes = REGIONAL_SIGNATURE_DISHES.get(city, REGIONAL_SIGNATURE_DISHES.get('sorrento', []))
                dest = DESTINATIONS.get(city, DESTINATIONS['sorrento'])
                self._send_json({
                    'city': dest['name'],
                    'region': dest['region'],
                    'description': dest['description'],
                    'transitNotes': dest.get('transit_notes', ''),
                    'dishes': dishes,
                    'signature_dishes': dishes
                })
            else:
                # Fallback to serving static frontend files
                if path == '/' or path == '':
                    self.path = '/index.html'
                super().do_GET()
        except Exception as e:
            self._send_json({'error': f'GET handler error: {str(e)}'}, status=500)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body_bytes = self.rfile.read(content_length)
                body = json.loads(body_bytes.decode('utf-8')) if body_bytes else {}
            except Exception as e:
                self._send_json({'error': f'Invalid JSON payload: {str(e)}'}, status=400)
                return

            if path == '/api/trips/generate':
                dest_id = body.get('destination') or body.get('destination_id') or 'sorrento'
                days = int(body.get('days') or body.get('duration_days') or 3)
                interests = body.get('interests', ['historical', 'viewpoints', 'beaches', 'food'])
                dietary = body.get('dietaryPreference') or body.get('dietary_preference') or 'vegetarian'
                pace = body.get('pace', 'balanced')
                hotel = body.get('hotel') or body.get('hotel_name')
                start_date = body.get('startDate') or body.get('start_date')
                llm_prov = body.get('llm_provider', 'auto')

                trip = travel_agent.generate_itinerary(
                    destination_id=dest_id,
                    days=days,
                    interests=interests,
                    dietary_preference=dietary,
                    pace=pace,
                    start_date=start_date,
                    hotel_name=hotel,
                    llm_provider=llm_prov
                )
                self._send_json({'trip': trip, **trip})

            elif path == '/api/trips/mutate':
                current_trip = body.get('currentTrip') or body.get('trip')
                instruction = body.get('instruction') or body.get('mutation_prompt') or ''
                llm_prov = body.get('llm_provider', 'auto')
                if not current_trip or not instruction:
                    self._send_json({'error': 'currentTrip and instruction are required.'}, status=400)
                    return

                updated_trip = travel_agent.mutate_itinerary(current_trip, instruction, llm_provider=llm_prov)
                self._send_json({
                    'trip': updated_trip,
                    'mutation_summary': updated_trip.get('lastMutationSummary', 'Itinerary updated.'),
                    **updated_trip
                })

            elif path == '/api/mcp/call':
                tool_name = body.get('tool')
                tool_args = body.get('arguments', {})
                try:
                    from maps_mcp_server.server import handle_call_tool
                    result = handle_call_tool(tool_name, tool_args)
                    self._send_json({'success': True, 'tool': tool_name, 'result': result})
                except Exception as e:
                    self._send_json({'success': False, 'tool': tool_name, 'error': str(e)}, status=500)
            else:
                self._send_json({'error': f'Endpoint {path} not found'}, status=404)
        except Exception as e:
            self._send_json({'error': f'POST handler error: {str(e)}', 'detail': str(e)}, status=500)


def run_server(port: int = 8080):
    server_address = ('0.0.0.0', port)
    httpd = ThreadedHTTPServer(server_address, TravelPlannerRequestHandler)
    print(f"Viaggio Italia Server running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    port_env = os.environ.get('PORT')
    if port_env:
        port = int(port_env)
    elif len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8080
    run_server(port)
