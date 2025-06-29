#!/usr/bin/env python3
"""
Test script for Step 5: Toll Selection & Removal
Tests the selection/removal logic for different target counts using real ORS routes and loaded cache.
"""

import os
from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.toll.route_optimization.toll_analysis.toll_selector import TollSelector
from src.services.ors_service import ORSService

def load_cache_data():
    print("🔄 Loading cache data...")
    try:
        from src.cache.cached_osm_manager import cached_osm_data_manager
        osm_file = "data/osm_export.geojson"
        if not os.path.exists(osm_file):
            osm_file = "data/osm_export_toll.geojson"
        if not os.path.exists(osm_file):
            print(f"❌ OSM file not found: {osm_file}")
            return False
        success = cached_osm_data_manager.load_osm_data_with_cache(osm_file, force_reload=False)
        return success
    except Exception as e:
        print(f"❌ Error loading cache: {str(e)}")
        return False

def test_toll_selection(route_name, start_coords, end_coords, target_counts):
    print(f"\n{'='*60}")
    print(f"🧪 TESTING ROUTE: {route_name}")
    print(f"📍 From: {start_coords} to {end_coords}")
    print(f"{'='*60}")
    try:
        print("📋 Step 1: Getting real route from ORS...")
        ors_service = ORSService()
        if not ors_service.test_all_set():
            print("   ❌ ORS service not configured")
            return
        route_data = ors_service.get_base_route([start_coords, end_coords], include_tollways=True)
        if not route_data or 'features' not in route_data:
            print("   ❌ Failed to get route from ORS")
            return
        feature = route_data['features'][0]
        coordinates = feature['geometry']['coordinates']
        properties = feature['properties']
        extras = properties.get('extras', {})
        tollways = extras.get('tollways', {})
        tollway_values = tollways.get('values', [])
        tollway_segments = []
        if tollway_values:
            for segment in tollway_values:
                if len(segment) >= 3:
                    start_idx = segment[0]
                    end_idx = segment[1]
                    is_toll = segment[2] == 1
                    segment_coords = coordinates[start_idx:end_idx + 1]
                    if segment_coords:
                        tollway_segments.append({
                            'coordinates': segment_coords,
                            'start_waypoint': start_idx,
                            'end_waypoint': end_idx,
                            'is_toll': is_toll
                        })
        if not tollway_segments:
            tollway_segments = [{'coordinates': coordinates, 'start_waypoint': 0, 'end_waypoint': len(coordinates)-1, 'is_toll': False}]
        print(f"   ✅ Created {len(tollway_segments)} tollway segments for analysis")
        toll_identifier = TollIdentifier()
        result = toll_identifier.identify_tolls_on_route(coordinates, tollway_segments)
        
        # Ajouter les coordonnées de la route au résultat pour le remplacement géographique
        result['route_coordinates'] = coordinates
        
        detected_tolls = result.get('tolls_on_route', [])
        print(f"   ✅ Toll detection completed! {len(detected_tolls)} tolls on route")
        toll_selector = TollSelector()
        for target_count in target_counts:
            print(f"\n--- Selecting {target_count} toll(s) ---")
            selection = toll_selector.select_tolls_by_count(detected_tolls, target_count, result)
            selected = selection.get('selected_tolls', [])
            print(f"Selected {len(selected)} toll(s):")
            for i, toll in enumerate(selected, 1):
                print(f"   {i}. {getattr(toll, 'osm_name', getattr(toll, 'effective_name', 'Inconnu'))} | System: {'Open' if getattr(toll, 'is_open_system', False) else 'Closed'}")
            if not selected:
                print("   ℹ️  No tolls selected for this count.")
    except Exception as e:
        print(f"   ❌ Error during toll selection: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Starting Step 5 Toll Selection Tests with Real Data")
    print("=" * 80)
    print("📦 Step 0: Loading cache data...")
    cache_loaded = load_cache_data()
    if not cache_loaded:
        print("⚠️ Cache not loaded, continuing with empty cache")
    print()
    test_route = {
        'name': 'Strasbourg → Clermont-Ferrand',
        'start': [7.448595, 48.262004],
        'end': [3.114432, 45.784832]
    }
    # Tester pour différents target_count
    target_counts = [5, 4, 3, 2, 1]
    test_toll_selection(test_route['name'], test_route['start'], test_route['end'], target_counts)
    print("\n🏁 Step 5 Toll Selection Tests Complete!")

if __name__ == "__main__":
    main()
