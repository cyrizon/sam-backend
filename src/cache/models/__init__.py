"""
Cache Models Package
----------------------

New data models for the multi-source OSM cache system.
"""

from .link_types import LinkType
from .toll_booth_station import TollBoothStation
from .motorway_link import MotorwayLink
from .complete_motorway_link import CompleteMotorwayLink

__all__ = [
    'LinkType',
    'TollBoothStation', 
    'MotorwayLink',
    'CompleteMotorwayLink'
]
