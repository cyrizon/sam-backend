#!/usr/bin/env python3
"""
Test script for Step 3: Toll Detection & Analysis
Tests the 3-phase detection pipeline with real ORS routes and loaded cache.
"""

import os

from src.services.toll.route_optimization.toll_analysis.toll_identifier import TollIdentifier
from src.services.ors_service import ORSService
from src.cache.cached_osm_manager import CachedOSMDataManager

def load_cache_data():
    """Load cache data using the existing cache system."""
    print("🔄 Loading cache data...")
    
    try:
        # Import the global cache manager instance
        from src.cache.cached_osm_manager import cached_osm_data_manager
        
        # Configuration
        osm_file = "data/osm_export.geojson"
        
        if not os.path.exists(osm_file):
            print(f"⚠️ OSM file not found: {osm_file}, trying toll version...")
            osm_file = "data/osm_export_toll.geojson"
            
        if not os.path.exists(osm_file):
            print(f"❌ OSM file not found: {osm_file}")
            return False
            
        # Load data with the GLOBAL cache manager instance
        success = cached_osm_data_manager.load_osm_data_with_cache(osm_file, force_reload=False)
        
        if success and cached_osm_data_manager.osm_parser:
            parser = cached_osm_data_manager.osm_parser
            print(f"✅ Cache loaded successfully!")
            print(f"   📊 Toll stations: {len(parser.toll_stations)}")
            print(f"   🗂️ Junctions: {len(parser.motorway_junctions)}")
            print(f"   🔗 Links: {len(parser.motorway_links)}")
            if hasattr(parser, 'matched_tolls'):
                print(f"   📍 Matched tolls: {len(parser.matched_tolls)}")
            return True
        else:
            print("❌ Failed to load cache or no data available")
            return False
            
    except Exception as e:
        print(f"❌ Error loading cache: {str(e)}")
        return False

def test_route_toll_detection(route_name, start_coords, end_coords):
    """Test toll detection for a specific route using real ORS data."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING ROUTE: {route_name}")
    print(f"📍 From: {start_coords} to {end_coords}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Get real route from ORS
        print("📋 Step 1: Getting real route from ORS...")
        ors_service = ORSService()
        
        if not ors_service.test_all_set():
            print("   ❌ ORS service not configured")
            return {
                'route_name': route_name,
                'start': start_coords,
                'end': end_coords,
                'route_distance': 0,
                'route_points': 0,
                'tolls_count': 0,
                'tolls': [],
                'success': False,
                'error': 'ORS service not configured'
            }
        
        route_data = ors_service.get_base_route([start_coords, end_coords], include_tollways=True)
        
        if not route_data or 'features' not in route_data:
            print("   ❌ Failed to get route from ORS")
            return {
                'route_name': route_name,
                'start': start_coords,
                'end': end_coords,
                'route_distance': 0,
                'route_points': 0,
                'tolls_count': 0,
                'tolls': [],
                'success': False,
                'error': 'Failed to get route from ORS'
            }
        
        feature = route_data['features'][0]
        coordinates = feature['geometry']['coordinates']
        properties = feature['properties']
        summary = properties['summary']
        
        print(f"   ✅ Route retrieved with {len(coordinates)} points")
        print(f"   📊 Distance: {summary.get('distance', 0)/1000:.1f} km")
        print(f"   ⏱️ Duration: {summary.get('duration', 0)/60:.0f} min")
        
        # Step 2: Initialize toll identifier
        print("🎯 Step 2: Initializing toll identifier...")
        toll_identifier = TollIdentifier()
        print("   ✅ Toll identifier initialized")
        
        # Step 3: Run toll detection (3-phase pipeline)
        print("🎯 Step 3: Running toll detection (3-phase pipeline)...")
        print("   Phase 1: Spatial prefiltering...")
        print("   Phase 2: Distance calculation...")
        print("   Phase 3: Classification & mapping...")
        
        # Extract tollway segments from ORS data
        extras = properties.get('extras', {})
        tollways = extras.get('tollways', {})
        tollway_values = tollways.get('values', [])
        
        # Create tollway segments from the route coordinates and tollway information
        tollway_segments = []
        if tollway_values:
            print(f"   📊 Found {len(tollway_values)} tollway segments in ORS data")
            for segment in tollway_values:
                if len(segment) >= 3:  # [start_index, end_index, is_toll_value]
                    start_idx = segment[0]
                    end_idx = segment[1]
                    is_toll = segment[2] == 1  # 1 = toll road, 0 = free road
                    
                    # Extract coordinates for this segment
                    segment_coords = coordinates[start_idx:end_idx + 1]
                    if segment_coords:
                        tollway_segments.append({
                            'coordinates': segment_coords,
                            'start_waypoint': start_idx,
                            'end_waypoint': end_idx,
                            'is_toll': is_toll
                        })
                        print(f"      - Segment {len(tollway_segments)-1}: points {start_idx}-{end_idx}, {'toll' if is_toll else 'free'}")
        
        # If no tollway segments found, use full route (fallback)
        if not tollway_segments:
            print("   ⚠️  No specific tollway segments found, using full route")
            tollway_segments = [{'coordinates': coordinates, 'start_waypoint': 0, 'end_waypoint': len(coordinates)-1, 'is_toll': False}]
        else:
            print(f"   ✅ Created {len(tollway_segments)} tollway segments for analysis")
        
        result = toll_identifier.identify_tolls_on_route(coordinates, tollway_segments)
        detected_tolls = result.get('tolls_on_route', [])  # Correction: utiliser 'tolls_on_route'
        tolls_around = result.get('tolls_around', [])
        
        print(f"   ✅ Toll detection completed!")
        print(f"   📊 Results: {len(detected_tolls)} tolls on route, {len(tolls_around)} tolls around")
        
        # Step 4: Display results
        print("📋 Step 4: Analysis results:")
        if detected_tolls:
            for i, toll in enumerate(detected_tolls, 1):
                print(f"   🛣️  Toll {i}:")
                print(f"      OSM ID: {toll.osm_id}")
                print(f"      Name: {toll.effective_name}")
                print(f"      Coordinates: {toll.osm_coordinates}")
                print(f"      System: {'Open' if toll.is_open_system else 'Closed'}")
                print(f"      Confidence: {toll.confidence:.2f}")
        else:
            print("   ℹ️  No tolls detected for this route")
        
        return {
            'route_name': route_name,
            'start': start_coords,
            'end': end_coords,
            'route_distance': summary.get('distance', 0),
            'route_points': len(coordinates),
            'tolls_count': len(detected_tolls),
            'tolls': detected_tolls,
            'success': True
        }
        
    except Exception as e:
        print(f"   ❌ Error during toll detection: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'route_name': route_name,
            'start': start_coords,
            'end': end_coords,
            'route_distance': 0,
            'route_points': 0,
            'tolls_count': 0,
            'tolls': [],
            'success': False,
            'error': str(e)
        }

def main():
    """Main test function."""
    print("🚀 Starting Step 3 Toll Detection Tests with Real Data")
    print("=" * 80)
    
    # Step 0: Load cache data first
    print("📦 Step 0: Loading cache data...")
    cache_loaded = load_cache_data()
    if not cache_loaded:
        print("⚠️ Cache not loaded, continuing with empty cache")
    print()
    
    # Test routes from Strasbourg to various destinations
    test_routes = [
        {
            'name': 'Strasbourg → Dijon',
            'start': [7.448595, 48.262004],
            'end': [5.037793, 47.317743]
        },
        {
            'name': 'Strasbourg → Lyon',
            'start': [7.448595, 48.262004],
            'end': [4.840823, 45.752181]
        },
        {
            'name': 'Strasbourg → Clermont-Ferrand',
            'start': [7.448595, 48.262004],
            'end': [3.114432, 45.784832]
        }
    ]
    
    results = []
    
    # Run tests for each route
    for route in test_routes:
        result = test_route_toll_detection(
            route['name'],
            route['start'], 
            route['end']
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY OF ALL TESTS")
    print(f"{'='*80}")
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tolls = sum(r['tolls_count'] for r in results)
    total_distance = sum(r.get('route_distance', 0) for r in results)
    total_points = sum(r.get('route_points', 0) for r in results)
    
    print(f"✅ Successful tests: {successful_tests}/{len(results)}")
    print(f"🛣️  Total tolls detected: {total_tolls}")
    print(f"📏 Total distance tested: {total_distance/1000:.1f} km")
    print(f"📍 Total route points: {total_points}")
    print()
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        distance_km = result.get('route_distance', 0) / 1000
        points = result.get('route_points', 0)
        print(f"{status} {result['route_name']}: {result['tolls_count']} tolls ({distance_km:.1f} km, {points} points)")
        if not result['success']:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    print(f"\n{'='*80}")
    print("🏁 Step 3 Toll Detection Tests Complete!")
    print(f"{'='*80}")
    
    return results

if __name__ == "__main__":
    results = main()
