"""
Cache manager with serialization support.

Integrates cache serialization into the existing OSM data management system.
"""

import os
from typing import List, Optional, Tuple

from .serialization.cache_serializer import CacheSerializer
from .serialization.compression_utils import CompressionType
from .managers.osm_data_manager import OSMDataManager
from .managers.toll_data_manager import TollDataManager
from .parsers.osm_parser import OSMParser
from .parsers.toll_matcher import TollMatcher


class CachedOSMDataManager:
    """
    OSM Data Manager with cache serialization support.
    
    Automatically handles cache loading/saving to speed up application startup.
    """
    
    def __init__(self, cache_dir: str = "osm_cache"):
        """
        Initialize the cached OSM data manager.
        
        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_serializer = CacheSerializer(cache_dir)
        self.osm_data_manager = OSMDataManager()
        self.toll_data_manager = TollDataManager()
        
        # Track if data is loaded
        self._data_loaded = False
        self._osm_parser = None
        
        print(f"🗄️ Gestionnaire de cache OSM initialisé")
    
    def load_osm_data_with_cache(
        self, 
        osm_file_path: str,
        force_reload: bool = False,
        compression_type: Optional[CompressionType] = None
    ) -> bool:
        """
        Load OSM data with automatic cache management.
        
        Args:
            osm_file_path: Path to the OSM GeoJSON file
            force_reload: Force reload from source even if cache exists
            compression_type: Compression type for cache (auto-detect if None)
            
        Returns:
            bool: True if data loaded successfully
        """
        print(f"\n🚀 Chargement des données OSM avec cache...")
        print(f"   📁 Fichier source: {osm_file_path}")
        print(f"   🔄 Force reload: {force_reload}")
        
        # Try to load from cache first (unless force reload)
        if not force_reload and self.cache_serializer.is_cache_available(osm_file_path):
            cache_result = self.cache_serializer.load_cache(osm_file_path)
            
            if cache_result is not None:
                toll_stations, motorway_junctions, motorway_links, matched_tolls = cache_result
                
                # Create OSM parser with cached data
                self._osm_parser = OSMParser(osm_file_path)
                self._osm_parser.toll_stations = toll_stations
                self._osm_parser.motorway_junctions = motorway_junctions
                self._osm_parser.motorway_links = motorway_links
                self._osm_parser.matched_tolls = matched_tolls  # Assigner les matched tolls
                
                # Set the parsed data in the OSM data manager
                self.osm_data_manager._osm_parser = self._osm_parser
                
                self._data_loaded = True
                
                print(f"✅ Données chargées depuis le cache:")
                print(f"   - Péages: {len(toll_stations)}")
                print(f"   - Junctions: {len(motorway_junctions)}")
                print(f"   - Links: {len(motorway_links)}")
                print(f"   - Matchés: {len(matched_tolls)}")
                
                return True
        
        # Load from source file and create cache
        print("📂 Chargement depuis le fichier source...")
        
        # Initialize toll data manager first for OSM/CSV matching
        self.toll_data_manager.initialize()
        
        # Initialize global toll cache as well (for OSM parser dependency)
        from . import toll_data_cache
        if not toll_data_cache._initialized:
            toll_data_cache.initialize()
        
        self.osm_data_manager.initialize(osm_file_path)
        if not self.osm_data_manager._initialized:
            print("❌ Échec chargement depuis le fichier source")
            return False
        
        self._osm_parser = self.osm_data_manager._osm_parser
        self._data_loaded = True
        
        # Save to cache for next time
        print("💾 Sauvegarde en cache...")
        
        # Get matched tolls (if available)
        matched_tolls = []
        if hasattr(self._osm_parser, 'matched_tolls'):
            matched_tolls = self._osm_parser.matched_tolls
        
        cache_success = self.cache_serializer.save_cache(
            toll_stations=self._osm_parser.toll_stations,
            motorway_junctions=self._osm_parser.motorway_junctions,
            motorway_links=self._osm_parser.motorway_links,
            matched_tolls=matched_tolls,
            source_file=osm_file_path,
            compression_type=compression_type
        )
        
        if cache_success:
            print("✅ Cache créé avec succès")
        else:
            print("⚠️ Échec sauvegarde cache, mais données chargées")
        
        return True
    
    @property
    def osm_parser(self) -> Optional[OSMParser]:
        """Get the OSM parser instance."""
        return self._osm_parser
    
    @property
    def is_loaded(self) -> bool:
        """Check if OSM data is loaded."""
        return self._data_loaded
    
    def get_cache_info(self):
        """Get cache information."""
        return self.cache_serializer.get_cache_info()
    
    def clear_cache(self) -> bool:
        """Clear the cache."""
        return self.cache_serializer.clear_cache()
    
    def benchmark_cache(self, osm_file_path: str):
        """
        Run cache performance benchmark.
        
        Args:
            osm_file_path: Path to OSM file for benchmarking
        """
        if not self._data_loaded:
            print("⚠️ Données non chargées, chargement d'abord...")
            if not self.load_osm_data_with_cache(osm_file_path, force_reload=True):
                print("❌ Impossible de charger les données pour le benchmark")
                return
        
        # Get matched tolls
        matched_tolls = []
        if hasattr(self._osm_parser, 'matched_tolls'):
            matched_tolls = self._osm_parser.matched_tolls
        
        results = self.cache_serializer.benchmark_cache_performance(
            toll_stations=self._osm_parser.toll_stations,
            motorway_junctions=self._osm_parser.motorway_junctions,
            motorway_links=self._osm_parser.motorway_links,
            matched_tolls=matched_tolls,
            source_file=osm_file_path
        )
        
        # Print summary
        print(f"\n📊 Résumé du benchmark:")
        print(f"   📈 Données testées:")
        for key, value in results['data_summary'].items():
            print(f"      - {key}: {value}")
        
        print(f"\n   🏆 Performances par méthode:")
        for method, perf in results.get('performance_results', {}).items():
            if 'error' not in perf:
                print(f"      - {method.upper()}: "
                      f"Save {perf['save_time_s']:.2f}s, "
                      f"Load {perf['load_time_s']:.2f}s, "
                      f"{perf['cache_size_mb']:.1f} MB")
        
        return results


# Create a global cached instance to replace the existing osm_data_cache
cached_osm_data_manager = CachedOSMDataManager()
