"""
Cache Serialization Package
------------------------------

Serialization system for the multi-source OSM cache.
"""

from .cache_metadata import CacheMetadata
from .cache_serializer import CacheSerializer

__all__ = [
    'CacheMetadata',
    'CacheSerializer'
]
