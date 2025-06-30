"""
MotorwayJunction Model
---------------------

Represents a motorway junction (highway exit).
"""

from typing import List, Dict, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .motorway_link import MotorwayLink
    from .matched_toll import MatchedToll

from ..utils.geographic_utils import calculate_distance


@dataclass
class MotorwayJunction:
    """Représente une sortie d'autoroute (motorway_junction)."""
    node_id: str
    ref: Optional[str]  # Numéro de sortie (ex: "6.1")
    coordinates: List[float]  # [lon, lat]
    properties: Dict
    linked_motorway_links: List['MotorwayLink'] = field(default_factory=list)  # Chaîne de liens associés
    toll: bool = False  # Indique si la sortie possède un péage
    toll_station: Optional['MatchedToll'] = None  # Référence vers le péage s'il existe
    
    def distance_to(self, point: List[float]) -> float:
        """Calcule la distance à un point en km."""
        return calculate_distance(self.coordinates, point)
