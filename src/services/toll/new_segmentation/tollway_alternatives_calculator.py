"""
tollway_alternatives_calculator.py
---------------------------------

Module responsable du calcul d'alternatives sans péages pour les segments de tollways.

Responsabilité unique : calculer des routes alternatives sans péages.
"""

from typing import List, Dict, Optional
from .tollway_extractor import TollwaySegment


class TollwayAlternativesCalculator:
    """
    Calculateur d'alternatives sans péages pour les segments de tollways.
    
    Responsabilité : pour chaque segment de péage trouvé, calculer une route alternative
    qui évite ce segment spécifique.
    """
    
    def __init__(self, ors_service):
        """
        Initialise le calculateur avec un service ORS.
        
        Args:
            ors_service: Instance du service ORS pour les appels API
        """
        self.ors = ors_service
    
    def calculate_alternatives(self, toll_segments: List[TollwaySegment]) -> List[Dict]:
        """
        Calcule des routes sans péage pour chaque segment de péage.
        
        Args:
            toll_segments: Liste des segments avec péages
            
        Returns:
            List[Dict]: Liste des alternatives calculées
        """
        print(f"🔄 Calcul de {len(toll_segments)} alternatives sans péage...")
        alternatives = []
        
        for i, segment in enumerate(toll_segments, 1):
            if self._has_valid_coordinates(segment):
                alternative = self._calculate_single_alternative(segment, i)
                if alternative:
                    alternatives.append(alternative)
            else:
                print(f"⚠️ Segment {i} : coordonnées invalides, pas d'alternative calculée")
        
        print(f"✅ {len(alternatives)} alternative(s) calculée(s)")
        return alternatives
    
    def _has_valid_coordinates(self, segment: TollwaySegment) -> bool:
        """
        Vérifie si un segment a des coordonnées valides.
        
        Args:
            segment: Segment à vérifier
            
        Returns:
            bool: True si les coordonnées sont valides
        """
        return (segment.coordinates and 
                len(segment.coordinates) >= 2 and
                all(len(coord) == 2 for coord in segment.coordinates[:2]))
    
    def _calculate_single_alternative(self, segment: TollwaySegment, segment_id: int) -> Optional[Dict]:
        """
        Calcule une alternative sans péage pour un segment donné.
        
        Args:
            segment: Segment de péage
            segment_id: ID du segment (pour les logs)
            
        Returns:
            Optional[Dict]: Route alternative ou None si échec
        """
        try:
            start_coord = segment.coordinates[0]    # [longitude, latitude]
            end_coord = segment.coordinates[-1]     # [longitude, latitude]
            
            print(f"  🧮 Alternative {segment_id} : calcul entre "
                  f"[{start_coord[0]:.6f}, {start_coord[1]:.6f}] et "
                  f"[{end_coord[0]:.6f}, {end_coord[1]:.6f}]")
            
            # Calculer route sans péage entre début et fin du segment
            alternative_route = self.ors.get_route_avoid_tollways([start_coord, end_coord])
            
            if alternative_route:
                distance = self._extract_distance(alternative_route)
                duration = self._extract_duration(alternative_route)
                
                print(f"    ✅ Alternative trouvée : {distance/1000:.1f} km, {duration/60:.1f} min")
                
                return {
                    'segment_id': segment_id,
                    'start_coordinates': start_coord,
                    'end_coordinates': end_coord,
                    'alternative_route': alternative_route,
                    'distance': distance,
                    'duration': duration
                }
            else:
                print(f"    ❌ Impossible de calculer une alternative pour le segment {segment_id}")
                return None
                
        except Exception as e:
            print(f"    ❌ Erreur calcul alternative segment {segment_id} : {e}")
            return None
    
    def _extract_distance(self, route: Dict) -> float:
        """
        Extrait la distance d'une route.
        
        Args:
            route: Réponse ORS
            
        Returns:
            float: Distance en mètres
        """
        try:
            return route['features'][0]['properties']['summary']['distance']
        except (KeyError, IndexError):
            return 0.0
    
    def _extract_duration(self, route: Dict) -> float:
        """
        Extrait la durée d'une route.
        
        Args:
            route: Réponse ORS
            
        Returns:
            float: Durée en secondes
        """
        try:
            return route['features'][0]['properties']['summary']['duration']
        except (KeyError, IndexError):
            return 0.0
