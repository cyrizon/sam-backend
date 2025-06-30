"""
Motorway Link Model
------------------

Represents a single motorway link segment.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .link_types import LinkType


@dataclass
class MotorwayLink:
    """Segment de motorway_link individuel."""
    way_id: str
    link_type: LinkType
    coordinates: List[List[float]]  # Liste de points [lon, lat]
    properties: Dict
    destination: Optional[str] = None
    
    # Points de départ et fin (calculés automatiquement)
    start_point: List[float] = field(init=False)
    end_point: List[float] = field(init=False)
    
    def __post_init__(self):
        """Calcule les points de départ et fin."""
        if self.coordinates:
            self.start_point = self.coordinates[0]
            self.end_point = self.coordinates[-1]
        else:
            self.start_point = [0.0, 0.0]
            self.end_point = [0.0, 0.0]
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début [lon, lat]."""
        return self.start_point
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin [lon, lat]."""
        return self.end_point
    
    def get_all_coordinates(self) -> List[List[float]]:
        """Retourne toutes les coordonnées du segment."""
        return self.coordinates
