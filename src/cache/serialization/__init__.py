"""
Cache V2 Serialization Package
------------------------------

Serialization system for the multi-source OSM cache V2.
"""

from .cache_metadata import CacheMetadata
from .cache_serializer import CacheSerializer

__all__ = [
    'CacheMetadata',
    'CacheSerializer'
]
