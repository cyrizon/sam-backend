#!/usr/bin/env python3
"""
Cache Loader for Tests
======================

Utility to load cache with real toll data for testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_cache_data():
    """Force load cache data from CSV files."""
    print("🔄 Loading cache data...")
    
    try:
        # Import cache modules
        from src.cache.cached_osm_manager import CachedOSMDataManager
        from src.cache.serialization.cache_serializer import CacheSerializer
        
        # Initialize cache serializer
        cache_serializer = CacheSerializer('osm_cache')
        
        # Initialize OSM manager
        osm_manager = CachedOSMDataManager('osm_cache')
        
        # Force load data from CSV files
        print("📊 Loading toll stations from CSV...")
        osm_manager._load_toll_stations_from_csv()
        
        print("🗂️ Loading junctions from CSV...")
        osm_manager._load_junctions_from_csv()
        
        print("🔗 Loading links from CSV...")
        osm_manager._load_links_from_csv()
        
        print("📍 Loading matched tolls from JSON...")
        osm_manager._load_matched_tolls_from_json()
        
        # Get statistics
        stats = osm_manager.get_cache_statistics()
        print(f"✅ Cache loaded successfully!")
        print(f"   📊 Toll stations: {stats.get('toll_stations', 0)}")
        print(f"   🗂️ Junctions: {stats.get('motorway_junctions', 0)}")
        print(f"   🔗 Links: {stats.get('motorway_links', 0)}")
        print(f"   📍 Matched tolls: {stats.get('matched_tolls', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading cache: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    load_cache_data()
