"""
segment_route_calculator.py
--------------------------

Module pour calculer les routes des segments.
Responsabilité : calculer chaque segment (normal ou sans péage).
"""

from typing import List, Dict, Optional
from .intelligent_segmentation_helpers import RouteUtils


class SegmentRouteCalculator:
    """
    Calcule les routes pour chaque segment défini.
    """
    
    def __init__(self, ors_service):
        """
        Initialise avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """
        self.ors = ors_service
    
    def calculate_segment_route(self, segment: Dict) -> Optional[Dict]:
        """
        Calcule la route pour un segment donné.
        
        Args:
            segment: Définition du segment
            
        Returns:
            Dict: Route calculée ou None si échec
        """
        segment_type = segment['type']
        coordinates = [segment['start'], segment['end']]
        description = segment['description']
        
        print(f"🔄 Calcul segment : {description}")
        print(f"   📍 Départ: {coordinates[0]}")
        print(f"   📍 Arrivée: {coordinates[1]}")
        
        if segment_type == 'avoid_tolls':
            return self._calculate_toll_free_route(coordinates, description)
        else:  # segment_type == 'normal'
            return self._calculate_normal_route(coordinates, description)
    
    def _calculate_toll_free_route(self, coordinates: List[List[float]], description: str) -> Optional[Dict]:
        """
        Calcule une route sans péage.
        
        Args:
            coordinates: [start, end]
            description: Description du segment
            
        Returns:
            Dict: Route sans péage ou None
        """
        try:
            print(f"   🚫 Calcul route sans péage : {description}")
            route = self.ors.get_route_avoid_tollways(coordinates)
            
            if route:
                print(f"   ✅ Route sans péage calculée")
                return route
            else:
                print(f"   ❌ Impossible de calculer une route sans péage")
                # Fallback vers route normale
                return self._calculate_normal_route(coordinates, description)                
        except Exception as e:
            print(f"   ❌ Erreur calcul route sans péage : {e}")
            return self._calculate_normal_route(coordinates, description)
    
    def _calculate_normal_route(self, coordinates: List[List[float]], description: str) -> Optional[Dict]:
        """
        Calcule une route normale.
        
        Args:
            coordinates: [start, end]
            description: Description du segment
            
        Returns:
            Dict: Route normale ou None
        """
        try:
            print(f"   🛣️ Calcul route normale : {description}")
            start_coord = coordinates[0]
            end_coord = coordinates[1]
            route = self.ors.get_route(start_coord, end_coord)
            
            if route:
                print(f"   ✅ Route normale calculée")
                return route
            else:
                print(f"   ❌ Impossible de calculer la route normale")
                return None
                
        except Exception as e:
            print(f"   ❌ Erreur calcul route normale : {e}")
            return None
    
    def calculate_all_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Calcule toutes les routes des segments.
        
        Args:
            segments: Liste des segments à calculer
            
        Returns:
            List[Dict]: Routes calculées
        """
        calculated_routes = []
        
        print(f"🔢 Calcul de {len(segments)} segments...")
        
        for i, segment in enumerate(segments, 1):
            print(f"\n📍 Segment {i}/{len(segments)}")
            route = self.calculate_segment_route(segment)
            
            if route:
                calculated_routes.append(route)
            else:
                print(f"❌ Échec du calcul du segment {i}")
                return []  # Échec si un segment ne peut pas être calculé
        
        print(f"✅ {len(calculated_routes)} segments calculés avec succès")
        return calculated_routes
