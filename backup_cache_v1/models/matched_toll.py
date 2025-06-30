"""
MatchedToll Model
----------------

Represents a toll that has been matched between OSM and CSV data.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class MatchedToll:
    """
    Péage matché avec ses données OSM et CSV.
    """
    # Données OSM
    osm_id: str
    osm_name: Optional[str]
    osm_coordinates: List[float]  # [lon, lat] WGS84
    
    # Données CSV matchées
    csv_id: Optional[str]
    csv_name: Optional[str]
    csv_role: Optional[str]  # 'O' pour ouvert, 'F' pour fermé
    csv_coordinates: Optional[List[float]]  # [lon, lat] WGS84
    
    # Métadonnées du matching
    distance_m: float  # Distance entre OSM et CSV en mètres
    confidence: float  # Confiance du matching (0-1)
    is_exit: bool = False  # True si ce péage est une sortie d'autoroute optimisée
    
    @property
    def is_open_system(self) -> bool:
        """Retourne True si c'est un péage à système ouvert."""
        return self.csv_role == 'O'
    
    @property
    def effective_name(self) -> str:
        """Retourne le nom le plus pertinent."""
        return self.csv_name or self.osm_name or f"Péage {self.osm_id}"
