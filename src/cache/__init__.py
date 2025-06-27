"""
Cache module for SAM Backend
---------------------------

Centralizes all caching functionality including:
- OSM data parsing and caching
- Toll data management
- Geographic matching utilities
- Element linking (junctions, links, tolls)
"""

from .managers.toll_data_manager import TollDataManager
from .managers.osm_data_manager import OSMDataManager

# Global cache instances
toll_data_cache = TollDataManager()
osm_data_cache = OSMDataManager()

__all__ = [
    'toll_data_cache',
    'osm_data_cache',
    'TollDataManager',
    'OSMDataManager'
]
