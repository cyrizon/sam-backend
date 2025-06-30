"""
Cache Package
---------------

New multi-source OSM cache system.

This package provides:
- Parsing from 4 separate GeoJSON files (toll_booths, entries, exits, indeterminate)
- Linking of motorway segments into complete links
- Toll detection and association with motorway links
- High-performance spatial operations
"""

from .models import LinkType, TollBoothStation, MotorwayLink, CompleteMotorwayLink
from .parsers import MultiSourceParser
from .linking import LinkBuilder, TollDetector
from .managers import OSMDataManager

__all__ = [
    # Models
    'LinkType',
    'TollBoothStation', 
    'MotorwayLink',
    'CompleteMotorwayLink',
    
    # Parsers
    'MultiSourceParser',
    
    # Linking
    'LinkBuilder',
    'TollDetector',
    
    # Managers
    'OSMDataManager'
]

__version__ = "1.0.0"
