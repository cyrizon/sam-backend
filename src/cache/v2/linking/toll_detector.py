"""
Toll Detector
------------

Detects and associates tolls with complete motorway links.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass

from ..models.complete_motorway_link import CompleteMotorwayLink
from ..models.toll_booth_station import TollBoothStation
from ...utils.geographic_utils import calculate_distance, distance_point_to_polyline_meters


@dataclass
class TollAssociation:
    """Association entre un péage et un lien complet."""
    toll: TollBoothStation
    complete_link: CompleteMotorwayLink
    distance_meters: float
    association_type: str  # 'point_to_point' ou 'point_to_line'


@dataclass
class TollDetectionResult:
    """Résultat de la détection de péages."""
    associations: List[TollAssociation]
    unassociated_tolls: List[TollBoothStation]
    links_with_tolls: List[CompleteMotorwayLink]
    links_without_tolls: List[CompleteMotorwayLink]
    
    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques de détection."""
        return {
            'total_associations': len(self.associations),
            'unassociated_tolls': len(self.unassociated_tolls),
            'links_with_tolls': len(self.links_with_tolls),
            'links_without_tolls': len(self.links_without_tolls)
        }


class TollDetector:
    """Détecteur de péages sur les liens motorway complets."""
    
    def __init__(self, max_distance_meters: float = 500.0):
        """
        Initialise le détecteur de péages.
        
        Args:
            max_distance_meters: Distance maximale péage-lien (mètres)
        """
        self.max_distance_meters = max_distance_meters
    
    def detect_tolls_on_links(
        self,
        complete_links: List[CompleteMotorwayLink],
        toll_booths: List[TollBoothStation]
    ) -> TollDetectionResult:
        """
        Détecte les péages associés aux liens complets.
        
        Args:
            complete_links: Liens motorway complets
            toll_booths: Stations de péage
            
        Returns:
            TollDetectionResult: Résultat de la détection
        """
        print("🏪 Détection des péages sur les liens...")
        
        associations = []
        used_toll_ids = set()
        
        for complete_link in complete_links:
            # Chercher le péage le plus proche pour ce lien
            closest_toll, distance = self._find_closest_toll(complete_link, toll_booths)
            
            if closest_toll and distance <= self.max_distance_meters:
                # Éviter les doublons
                if closest_toll.osm_id not in used_toll_ids:
                    # Créer l'association
                    association = TollAssociation(
                        toll=closest_toll,
                        complete_link=complete_link,
                        distance_meters=distance,
                        association_type='point_to_line'
                    )
                    associations.append(association)
                    used_toll_ids.add(closest_toll.osm_id)
                    
                    # Associer le péage au lien
                    complete_link.associated_toll = closest_toll
                    complete_link.toll_distance_meters = distance
        
        # Classer les résultats
        links_with_tolls = [link for link in complete_links if link.has_toll()]
        links_without_tolls = [link for link in complete_links if not link.has_toll()]
        unassociated_tolls = [
            toll for toll in toll_booths 
            if toll.osm_id not in used_toll_ids
        ]
        
        result = TollDetectionResult(
            associations=associations,
            unassociated_tolls=unassociated_tolls,
            links_with_tolls=links_with_tolls,
            links_without_tolls=links_without_tolls
        )
        
        self._print_detection_summary(result)
        return result
    
    def _find_closest_toll(
        self, 
        complete_link: CompleteMotorwayLink, 
        toll_booths: List[TollBoothStation]
    ) -> Tuple[TollBoothStation, float]:
        """
        Trouve le péage le plus proche d'un lien complet.
        
        Returns:
            Tuple[TollBoothStation, float]: (péage le plus proche, distance en mètres)
        """
        if not toll_booths:
            return None, float('inf')
        
        # Obtenir toutes les coordonnées du lien complet
        link_coordinates = complete_link.get_all_coordinates()
        
        closest_toll = None
        min_distance = float('inf')
        
        for toll in toll_booths:
            # Calculer la distance du péage à la polyligne du lien
            distance = distance_point_to_polyline_meters(
                toll.get_coordinates(), 
                link_coordinates
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_toll = toll
        
        return closest_toll, min_distance
    
    def _print_detection_summary(self, result: TollDetectionResult):
        """Affiche un résumé de la détection."""
        stats = result.get_stats()
        print(f"📊 Résumé de la détection de péages:")
        print(f"   • Associations péage-lien: {stats['total_associations']}")
        print(f"   • Liens avec péages: {stats['links_with_tolls']}")
        print(f"   • Liens sans péages: {stats['links_without_tolls']}")
        print(f"   • Péages non associés: {stats['unassociated_tolls']}")
        print("✅ Détection des péages terminée!\n")
