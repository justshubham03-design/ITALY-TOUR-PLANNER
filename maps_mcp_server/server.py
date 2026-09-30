import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Standard Server for Google Maps Tools.
Provides strictly the 9 tools specified in architectureplan.md over stdio JSON-RPC 2.0.
"""

import sys
import json
import logging
import traceback
from typing import Dict, Any, List
from maps_mcp_server.google_maps_service import GoogleMapsService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger('MapsMCPServer')

maps_service = GoogleMapsService()

TOOLS_METADATA = [
    {
        "name": "search_places",
        "description": "Search attractions, beaches, museums, historical monuments, shopping, and viewpoints in Italy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query e.g. 'historical landmarks in Rome'"},
                "city_or_region": {"type": "string", "description": "City or region name e.g. 'Rome', 'Sorrento', 'Puglia'"},
                "category": {"type": "string", "description": "Category filter e.g. 'historical', 'museums', 'beaches', 'viewpoints', 'churches', 'shopping'"},
                "limit": {"type": "integer", "description": "Maximum results to return", "default": 10}
            },
            "required": []
        }
    },
    {
        "name": "search_nearby_places",
        "description": "Find places and attractions surrounding a specific coordinate within a defined radius.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Center latitude"},
                "longitude": {"type": "number", "description": "Center longitude"},
                "radius_meters": {"type": "integer", "description": "Search radius in meters", "default": 5000},
                "included_types": {"type": "array", "items": {"type": "string"}, "description": "Optional place types"},
                "min_rating": {"type": "number", "description": "Minimum place rating (1-5)", "default": 4.0},
                "limit": {"type": "integer", "description": "Max results", "default": 10}
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "get_place_details",
        "description": "Retrieve verified metadata, hours, ratings, booking requirements, and Google Maps URL for a place ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "place_id": {"type": "string", "description": "Place ID string e.g. 'it_rom_colosseum'"}
            },
            "required": ["place_id"]
        }
    },
    {
        "name": "search_restaurants",
        "description": "Search authentic local Italian restaurants with strict vegetarian/non-veg criteria, price level, and ratings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Search center latitude"},
                "longitude": {"type": "number", "description": "Search center longitude"},
                "radius_meters": {"type": "integer", "description": "Radius in meters", "default": 25000},
                "cuisine": {"type": "string", "description": "Cuisine filter e.g. 'Roman', 'Pugliese', 'Pizza'"},
                "dietary_preference": {"type": "string", "enum": ["vegetarian", "non_vegetarian", "both"], "default": "both"},
                "price_levels": {"type": "array", "items": {"type": "string"}, "description": "Allowed price levels"},
                "min_rating": {"type": "number", "description": "Minimum rating", "default": 4.2},
                "limit": {"type": "integer", "description": "Max results", "default": 5}
            },
            "required": ["latitude", "longitude"]
        }
    },
    {
        "name": "calculate_route",
        "description": "Calculate precise turn-by-turn route, distance, travel time, and navigation URL between two points.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"description": "Origin coordinates or place name/ID"},
                "destination": {"description": "Destination coordinates or place name/ID"},
                "travel_mode": {"type": "string", "enum": ["WALK", "DRIVE", "TRANSIT", "BICYCLE"], "default": "WALK"},
                "transit_preferences": {"type": "object", "description": "Optional transit preferences"}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "compare_routes",
        "description": "Compare available travel modes (walking vs transit vs driving vs ferry) to select optimal mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"description": "Origin location"},
                "destination": {"description": "Destination location"}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "calculate_multi_stop_route",
        "description": "Calculate day load, sequence of legs, total distance, and fatigue metrics for an entire multi-stop itinerary day.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin_hotel": {"description": "Starting hotel / base accommodation"},
                "stops": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "location": {"description": "Place ID or coords"},
                            "allocatedDwellMinutes": {"type": "integer", "default": 60}
                        },
                        "required": ["name"]
                    }
                },
                "return_to_hotel": {"type": "boolean", "default": True},
                "travel_mode": {"type": "string", "default": "WALK"}
            },
            "required": ["origin_hotel", "stops"]
        }
    },
    {
        "name": "calculate_route_matrix",
        "description": "Compute pairwise distance & duration matrix for places to optimize clustering and solve TSP without backtracking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "place_coordinates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "lat": {"type": "number"},
                            "lng": {"type": "number"}
                        },
                        "required": ["id", "lat", "lng"]
                    }
                },
                "travel_mode": {"type": "string", "default": "WALK"}
            },
            "required": ["place_coordinates"]
        }
    },
    {
        "name": "get_maps_url",
        "description": "Generate official Google Maps Universal URLs for places, searches, and turn-by-turn navigation deep-links.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["search", "place", "directions"]},
                "query_or_place_name": {"type": "string"},
                "place_id": {"type": "string"},
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "waypoints": {"type": "array", "items": {"type": "string"}},
                "travel_mode": {"type": "string", "enum": ["walking", "transit", "driving", "bicycling"], "default": "walking"}
            },
            "required": ["action"]
        }
    }
]

def handle_call_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    if tool_name == 'search_places':
        return maps_service.search_places(
            query=args.get('query', ''),
            city_or_region=args.get('city_or_region'),
            category=args.get('category'),
            limit=args.get('limit', 10)
        )
    elif tool_name == 'search_nearby_places':
        return maps_service.search_nearby_places(
            latitude=float(args['latitude']),
            longitude=float(args['longitude']),
            radius_meters=args.get('radius_meters', 5000),
            included_types=args.get('included_types'),
            min_rating=args.get('min_rating', 4.0),
            limit=args.get('limit', 10)
        )
    elif tool_name == 'get_place_details':
        return maps_service.get_place_details(place_id=args['place_id'])
    elif tool_name == 'search_restaurants':
        return maps_service.search_restaurants(
            latitude=float(args['latitude']),
            longitude=float(args['longitude']),
            radius_meters=args.get('radius_meters', 25000),
            cuisine=args.get('cuisine'),
            dietary_preference=args.get('dietary_preference', 'both'),
            price_levels=args.get('price_levels'),
            min_rating=args.get('min_rating', 4.2),
            limit=args.get('limit', 5)
        )
    elif tool_name == 'calculate_route':
        return maps_service.calculate_route(
            origin=args['origin'],
            destination=args['destination'],
            travel_mode=args.get('travel_mode', 'WALK'),
            transit_preferences=args.get('transit_preferences')
        )
    elif tool_name == 'compare_routes':
        return maps_service.compare_routes(
            origin=args['origin'],
            destination=args['destination']
        )
    elif tool_name == 'calculate_multi_stop_route':
        return maps_service.calculate_multi_stop_route(
            origin_hotel=args['origin_hotel'],
            stops=args.get('stops', []),
            return_to_hotel=args.get('return_to_hotel', True),
            travel_mode=args.get('travel_mode', 'WALK')
        )
    elif tool_name == 'calculate_route_matrix':
        return maps_service.calculate_route_matrix(
            place_coordinates=args.get('place_coordinates', []),
            travel_mode=args.get('travel_mode', 'WALK')
        )
    elif tool_name == 'get_maps_url':
        return maps_service.get_maps_url(
            action=args['action'],
            query_or_place_name=args.get('query_or_place_name'),
            place_id=args.get('place_id'),
            origin=args.get('origin'),
            destination=args.get('destination'),
            waypoints=args.get('waypoints'),
            travel_mode=args.get('travel_mode', 'walking')
        )
    else:
        raise ValueError(f"Unknown tool: {tool_name}")

def run_stdio_server():
    logger.info("Starting Italy Travel Maps MCP Server on stdio...")
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue
        try:
            req = json.loads(line_str)
            req_id = req.get('id')
            method = req.get('method')
            params = req.get('params', {})

            if method == 'initialize':
                resp = {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {'tools': {}},
                        'serverInfo': {
                            'name': 'italy-travel-maps-mcp',
                            'version': '2.0.0'
                        }
                    }
                }
            elif method == 'notifications/initialized':
                continue
            elif method == 'ping':
                resp = {'jsonrpc': '2.0', 'id': req_id, 'result': {}}
            elif method == 'tools/list':
                resp = {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'result': {
                        'tools': TOOLS_METADATA
                    }
                }
            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})
                try:
                    tool_result = handle_call_tool(tool_name, tool_args)
                    resp = {
                        'jsonrpc': '2.0',
                        'id': req_id,
                        'result': {
                            'content': [
                                {
                                    'type': 'text',
                                    'text': json.dumps(tool_result, indent=2, ensure_ascii=False)
                                }
                            ],
                            'isError': False
                        }
                    }
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    resp = {
                        'jsonrpc': '2.0',
                        'id': req_id,
                        'result': {
                            'content': [
                                {
                                    'type': 'text',
                                    'text': f"Error executing tool {tool_name}: {str(e)}"
                                }
                            ],
                            'isError': True
                        }
                    }
            else:
                resp = {
                    'jsonrpc': '2.0',
                    'id': req_id,
                    'error': {
                        'code': -32601,
                        'message': f"Method {method} not found"
                    }
                }

            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        except Exception as e:
            logger.error(f"Error processing JSON-RPC message: {e} - {traceback.format_exc()}")
            err_resp = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {'code': -32700, 'message': f"Parse error or unhandled exception: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == '__main__':
    run_stdio_server()
