"""
Cache module for SAM Backend
---------------------------

Centralizes all caching functionality including:
- OSM data parsing and caching with serialization
- Toll data management
- Geographic matching utilities
- Element linking (junctions, links, tolls)
- High-performance cache serialization
"""

from .managers.toll_data_manager import TollDataManager
from .managers.osm_data_manager import OSMDataManager
from .cached_osm_manager import CachedOSMDataManager, cached_osm_data_manager

# Global cache instances
print("🚀 Initialisation du cache global des péages...")
toll_data_cache = TollDataManager()

print("🚦 Initialisation du cache global OSM avec sérialisation...")
# Use the new cached manager for better performance
osm_data_cache = cached_osm_data_manager

__all__ = [
    'toll_data_cache',
    'osm_data_cache',
    'TollDataManager',
    'OSMDataManager',
    'CachedOSMDataManager',
    'cached_osm_data_manager'
]
