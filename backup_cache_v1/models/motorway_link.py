"""
MotorwayLink Model
-----------------

Represents a motorway link (exit road connection).
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MotorwayLink:
    """Représente un lien de sortie (motorway_link)."""
    way_id: str
    destination: Optional[str]
    coordinates: List[List[float]]  # Liste de points [lon, lat]
    properties: Dict
    next_link: Optional['MotorwayLink'] = None  # Lien suivant dans la chaîne
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début du lien."""
        return self.coordinates[0] if self.coordinates else [0, 0]
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin du lien."""
        return self.coordinates[-1] if self.coordinates else [0, 0]
