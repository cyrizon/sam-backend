"""
Serialization module for OSM cache data.

This module provides efficient serialization and deserialization of OSM data
to avoid re-parsing large geojson files on every application startup.
"""

from .cache_serializer import CacheSerializer
from .cache_metadata import CacheMetadata
from .compression_utils import CompressionUtils

__all__ = [
    'CacheSerializer',
    'CacheMetadata', 
    'CompressionUtils'
]
