"""
TollStation Model
----------------

Represents a toll station/booth.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from ..utils.geographic_utils import calculate_distance


@dataclass
class TollStation:
    """Représente une station de péage."""
    feature_id: str
    name: Optional[str]
    coordinates: List[float]  # [lon, lat]
    toll_type: str  # "open" ou "closed"
    properties: Dict
    csv_match: Optional[Dict] = None  # NOUVEAU : Données CSV pré-matchées
    
    def distance_to(self, point: List[float]) -> float:
        """Calcule la distance à un point en km."""
        return calculate_distance(self.coordinates, point)
