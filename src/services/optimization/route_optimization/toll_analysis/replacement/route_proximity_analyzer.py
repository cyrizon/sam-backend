"""
Route Proximity Analyzer
========================

Analyse la proximité entre les péages et la route pour optimiser les remplacements.
Calcule les distances et positions relatives sur la polyline.
"""

from typing import List, Tuple, Optional
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

from src.cache.models.complete_motorway_link import CompleteMotorwayLink
from src.cache.models.toll_booth_station import TollBoothStation


class RouteProximityAnalyzer:
    """
    Responsabilité : Analyser la proximité entre péages et route.
    Calcule distances, positions relatives et scores de pertinence.
    """
    
    def calculate_toll_position_on_route(
        self, 
        toll_coordinates: List[float], 
        route_coordinates: List[List[float]]
    ) -> Optional[float]:
        """
        Calcule la position d'un péage projeté sur la route (0.0 à 1.0).
        
        Args:
            toll_coordinates: Coordonnées du péage [lon, lat]
            route_coordinates: Coordonnées de la route
            
        Returns:
            Position normalisée sur la route (0=début, 1=fin) ou None
        """
        if not route_coordinates or len(route_coordinates) < 2:
            return None
        
        try:
            route_line = LineString([(coord[0], coord[1]) for coord in route_coordinates])
            toll_point = Point(toll_coordinates[0], toll_coordinates[1])
            
            # Position du péage projeté sur la route
            position_on_route = route_line.project(toll_point)
            
            # Normaliser par la longueur totale de la route
            total_route_length = route_line.length
            if total_route_length > 0:
                return position_on_route / total_route_length
            
            return 0.0
            
        except Exception as e:
            print(f"❌ Erreur calcul position péage: {e}")
            return None
    
    def calculate_distance_to_route(
        self, 
        coordinates: List[float], 
        route_coordinates: List[List[float]]
    ) -> Optional[float]:
        """
        Calcule la distance perpendiculaire d'un point à la route.
        
        Args:
            coordinates: Coordonnées du point [lon, lat]
            route_coordinates: Coordonnées de la route
            
        Returns:
            Distance en mètres ou None
        """
        if not route_coordinates or len(route_coordinates) < 2:
            return None
        
        try:
            route_line = LineString([(coord[0], coord[1]) for coord in route_coordinates])
            point = Point(coordinates[0], coordinates[1])
            
            distance_degrees = route_line.distance(point)
            # Conversion approximative en mètres (1 degré ≈ 111320m)
            distance_meters = distance_degrees * 111320
            
            return distance_meters
            
        except Exception as e:
            print(f"❌ Erreur calcul distance: {e}")
            return None
    
    def score_entry_for_replacement(
        self, 
        entry: CompleteMotorwayLink,
        target_toll_position: float,
        route_coordinates: List[List[float]]
    ) -> float:
        """
        Calcule un score de pertinence pour une entrée comme remplacement.
        
        Args:
            entry: Entrée d'autoroute candidate
            target_toll_position: Position du péage à remplacer (0.0-1.0)
            route_coordinates: Coordonnées de la route
            
        Returns:
            Score de pertinence (plus élevé = meilleur)
        """
        if not entry.has_toll():
            return 0.0
        
        # Position de l'entrée sur la route
        entry_position = self.calculate_toll_position_on_route(
            entry.get_start_point(), route_coordinates
        )
        
        if entry_position is None:
            return 0.0
        
        # Distance à la route
        distance_to_route = self.calculate_distance_to_route(
            entry.get_start_point(), route_coordinates
        )
        
        if distance_to_route is None:
            return 0.0
        
        # Calcul du score composite
        return self._calculate_composite_score(
            entry_position, target_toll_position, distance_to_route
        )
    
    def find_best_replacement_entry(
        self, 
        candidate_entries: List[CompleteMotorwayLink],
        target_toll_coordinates: List[float],
        route_coordinates: List[List[float]]
    ) -> Optional[Tuple[CompleteMotorwayLink, float]]:
        """
        Trouve la meilleure entrée pour remplacer un péage fermé.
        
        Args:
            candidate_entries: Entrées candidates
            target_toll_coordinates: Coordonnées du péage à remplacer
            route_coordinates: Coordonnées de la route
            
        Returns:
            Tuple (meilleure_entrée, score) ou None
        """
        if not candidate_entries:
            return None
        
        # Position du péage cible sur la route
        target_position = self.calculate_toll_position_on_route(
            target_toll_coordinates, route_coordinates
        )
        
        if target_position is None:
            return None
        
        best_entry = None
        best_score = 0.0
        
        for entry in candidate_entries:
            score = self.score_entry_for_replacement(
                entry, target_position, route_coordinates
            )
            
            if score > best_score:
                best_score = score
                best_entry = entry
        
        return (best_entry, best_score) if best_entry else None
    
    def _calculate_composite_score(
        self, 
        entry_position: float, 
        target_position: float, 
        distance_to_route: float
    ) -> float:
        """
        Calcule un score composite basé sur position et distance.
        
        Args:
            entry_position: Position de l'entrée (0.0-1.0)
            target_position: Position du péage cible (0.0-1.0)
            distance_to_route: Distance à la route en mètres
            
        Returns:
            Score composite (0.0-1.0)
        """
        # Critère 1: L'entrée doit être après le péage cible
        if entry_position <= target_position:
            return 0.0  # Entrée avant le péage = invalide
        
        # Critère 2: Distance optimale (plus proche = mieux)
        max_distance = 200.0  # Buffer maximum en mètres
        distance_score = max(0.0, (max_distance - distance_to_route) / max_distance)
        
        # Critère 3: Position relative (pas trop loin après le péage)
        position_diff = entry_position - target_position
        max_position_diff = 0.3  # Maximum 30% de la route après le péage
        position_score = max(0.0, (max_position_diff - position_diff) / max_position_diff)
        
        # Score composite : pondération distance (70%) + position (30%)
        composite_score = (distance_score * 0.7) + (position_score * 0.3)
        
        return min(1.0, max(0.0, composite_score))
