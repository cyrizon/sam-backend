"""
Complete Motorway Link Model
---------------------------

Represents a complete motorway link composed of multiple segments.
"""

from typing import List, Optional
from dataclasses import dataclass, field

from .link_types import LinkType
from .motorway_link import MotorwayLink
from .toll_booth_station import TollBoothStation


@dataclass
class CompleteMotorwayLink:
    """
    Lien motorway complet composé de plusieurs segments.
    
    Représente une bretelle complète d'entrée ou de sortie, 
    obtenue en liant les segments entry/exit avec les segments indéterminés.
    """
    link_id: str  # Identifiant unique généré
    link_type: LinkType  # ENTRY ou EXIT (pas INDETERMINATE)
    segments: List[MotorwayLink]  # Segments qui composent le lien complet
    
    # Coordonnées de départ et fin de la bretelle complète
    start_coordinates: List[float] = field(init=False)
    end_coordinates: List[float] = field(init=False)
    
    # Péage associé (si détecté)
    associated_toll: Optional[TollBoothStation] = None
    toll_distance_meters: Optional[float] = None
    
    # Métadonnées
    destination: Optional[str] = None
    total_length_km: Optional[float] = None
    
    def __post_init__(self):
        """Calcule les coordonnées de début et fin de la bretelle complète."""
        if self.segments:
            # Le début de la bretelle = début du premier segment
            self.start_coordinates = self.segments[0].get_start_point()
            # La fin de la bretelle = fin du dernier segment
            self.end_coordinates = self.segments[-1].get_end_point()
        else:
            self.start_coordinates = [0.0, 0.0]
            self.end_coordinates = [0.0, 0.0]
    
    def get_start_point(self) -> List[float]:
        """Retourne le point de début de la bretelle [lon, lat]."""
        return self.start_coordinates
    
    def get_end_point(self) -> List[float]:
        """Retourne le point de fin de la bretelle [lon, lat]."""
        return self.end_coordinates
    
    def get_all_coordinates(self) -> List[List[float]]:
        """Retourne toutes les coordonnées de la bretelle complète."""
        all_coords = []
        for segment in self.segments:
            all_coords.extend(segment.get_all_coordinates())
        return all_coords
    
    def has_toll(self) -> bool:
        """Retourne True si un péage est associé à cette bretelle."""
        return self.associated_toll is not None
    
    def add_segment(self, segment: MotorwayLink):
        """Ajoute un segment à la bretelle."""
        self.segments.append(segment)
        # Recalculer les coordonnées de fin
        self.__post_init__()
    
    def get_segment_count(self) -> int:
        """Retourne le nombre de segments dans cette bretelle."""
        return len(self.segments)
