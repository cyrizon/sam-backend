#!/usr/bin/env python3
"""
Diagnostic du cache et de l'index spatial
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.toll.route_optimization.utils.cache_accessor import CacheAccessor
from src.services.toll.route_optimization.toll_analysis.spatial.spatial_index import SpatialIndexManager
from src.cache.cached_osm_manager import CachedOSMDataManager

def diagnostic_cache():
    """Diagnostic complet du cache."""
    print("🔍 DIAGNOSTIC DU CACHE ET INDEX SPATIAL")
    print("=" * 60)
    
    # 1. Charger le cache
    print("📦 1. Chargement du cache...")
    osm_file = "data/osm_export.geojson"
    cache_manager = CachedOSMDataManager('osm_cache')
    success = cache_manager.load_osm_data_with_cache(osm_file, force_reload=False)
    
    if not success:
        print("❌ Échec chargement cache")
        return
    
    print(f"✅ Cache chargé avec succès")
    
    # 2. Test CacheAccessor
    print("\n🔧 2. Test CacheAccessor...")
    
    print(f"   is_cache_available(): {CacheAccessor.is_cache_available()}")
    
    cache_stats = CacheAccessor.get_cache_stats()
    print(f"   Cache stats: {cache_stats}")
    
    toll_stations = CacheAccessor.get_toll_stations()
    print(f"   Toll stations: {len(toll_stations)}")
    
    if len(toll_stations) > 0:
        print(f"   Premier péage: {toll_stations[0]}")
        print(f"   Type: {type(toll_stations[0])}")
        if hasattr(toll_stations[0], 'coordinates'):
            print(f"   Coordonnées: {toll_stations[0].coordinates}")
    
    matched_tolls = CacheAccessor.get_matched_tolls()
    print(f"   Matched tolls: {len(matched_tolls)}")
    
    if len(matched_tolls) > 0:
        print(f"   Premier matched toll: {matched_tolls[0]}")
        print(f"   Type: {type(matched_tolls[0])}")
    
    # 3. Test SpatialIndexManager
    print("\n🗂️ 3. Test SpatialIndexManager...")
    
    spatial_manager = SpatialIndexManager()
    print(f"   Index créé: {spatial_manager.index is not None}")
    
    # Tester directement l'accès aux péages
    print("\n🔍 4. Test direct accès cache...")
    from src.cache.cached_osm_manager import cached_osm_data_manager
    
    print(f"   cached_osm_data_manager.is_loaded: {cached_osm_data_manager.is_loaded}")
    print(f"   cached_osm_data_manager.osm_parser: {cached_osm_data_manager.osm_parser is not None}")
    
    if cached_osm_data_manager.osm_parser:
        parser = cached_osm_data_manager.osm_parser
        print(f"   parser.toll_stations: {len(parser.toll_stations) if hasattr(parser, 'toll_stations') else 'N/A'}")
        
        if hasattr(parser, 'toll_stations') and len(parser.toll_stations) > 0:
            toll = parser.toll_stations[0]
            print(f"   Premier toll_station:")
            print(f"     - Type: {type(toll)}")
            print(f"     - Attributs: {dir(toll)}")
            if hasattr(toll, 'coordinates'):
                print(f"     - Coordonnées: {toll.coordinates}")
            if hasattr(toll, 'feature_id'):
                print(f"     - ID: {toll.feature_id}")
            if hasattr(toll, 'name'):
                print(f"     - Nom: {toll.name}")

if __name__ == "__main__":
    diagnostic_cache()
