"""
Toll Booth Station Model
-----------------------

Represents a toll booth from OSM data.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TollBoothStation:
    """Station de péage OSM."""
    osm_id: str
    name: Optional[str]
    operator: Optional[str] 
    operator_ref: Optional[str]
    highway_ref: Optional[str]  # Ex: "A 6"
    coordinates: List[float]    # [lon, lat]
    properties: Dict
    type: str = "F"  # "O" pour ouvert, "F" pour fermé (défaut)
    
    @property
    def is_open_toll(self) -> bool:
        """Retourne True si c'est un péage ouvert."""
        return self.type == "O"
    
    @property
    def is_closed_toll(self) -> bool:
        """Retourne True si c'est un péage fermé."""
        return self.type == "F"
    
    @property
    def display_name(self) -> str:
        """Retourne le nom d'affichage du péage."""
        if self.name:
            return self.name
        elif self.operator_ref:
            return f"Péage {self.operator_ref}"
        else:
            return f"Péage {self.osm_id}"
    
    def get_coordinates(self) -> List[float]:
        """Retourne les coordonnées [lon, lat]."""
        return self.coordinates
