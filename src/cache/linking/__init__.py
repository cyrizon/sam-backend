"""
Cache V2 Linking Package
-----------------------

Modules for linking motorway segments and detecting tolls.
"""

from .link_builder import LinkBuilder
from .toll_detector import TollDetector

__all__ = [
    'LinkBuilder',
    'TollDetector'
]
