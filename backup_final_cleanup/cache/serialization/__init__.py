"""
Cache V2 Serialization Package
------------------------------

Serialization system for the multi-source OSM cache V2.
"""

from .cache_metadata_v2 import CacheMetadataV2
from .cache_serializer_v2 import CacheSerializerV2

__all__ = [
    'CacheMetadataV2',
    'CacheSerializerV2'
]
