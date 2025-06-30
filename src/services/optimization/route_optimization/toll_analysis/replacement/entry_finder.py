"""
Entry Finder
============

Recherche d'entrées d'autoroute proches d'une route donnée.
Utilise le cache V2 pour récupérer efficacement les entrées avec péages.
"""

from typing import List, Tuple
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

from ...utils.cache_accessor import CacheAccessor
from src.cache.models.complete_motorway_link import CompleteMotorwayLink


class EntryFinder:
    """
    Responsabilité : Trouver les entrées d'autoroute proches d'une route.
    Utilise un buffer de 200m et filtre les entrées avec péages.
    """
    
    PROXIMITY_BUFFER_METERS = 200  # Buffer de proximité en mètres
    
    def find_entries_near_route(self, route_coordinates: List[List[float]]) -> List[CompleteMotorwayLink]:
        """
        Trouve toutes les entrées d'autoroute proches de la route donnée.
        
        Args:
            route_coordinates: Coordonnées de la route [[lon, lat], ...]
            
        Returns:
            Liste des entrées proches avec péages
        """
        if not route_coordinates or len(route_coordinates) < 2:
            return []
        
        # Récupérer toutes les entrées avec péages du cache V2
        all_entries = CacheAccessor.get_entry_links()
        entries_with_tolls = [entry for entry in all_entries if entry.has_toll()]
        
        if not entries_with_tolls:
            return []
        
        # Créer la geometrie de la route
        route_line = LineString([(coord[0], coord[1]) for coord in route_coordinates])
        
        # Filtrer les entrées proches
        nearby_entries = []
        for entry in entries_with_tolls:
            if self._is_entry_near_route(entry, route_line):
                nearby_entries.append(entry)
        
        return nearby_entries
    
    def find_entries_after_position(
        self, 
        route_coordinates: List[List[float]], 
        reference_position: List[float]
    ) -> List[Tuple[CompleteMotorwayLink, float]]:
        """
        Trouve les entrées situées après une position de référence sur la route.
        
        Args:
            route_coordinates: Coordonnées de la route
            reference_position: Position de référence [lon, lat]
            
        Returns:
            Liste de tuples (entrée, distance_depuis_référence)
        """
        nearby_entries = self.find_entries_near_route(route_coordinates)
        if not nearby_entries:
            return []
        
        route_line = LineString([(coord[0], coord[1]) for coord in route_coordinates])
        reference_point = Point(reference_position[0], reference_position[1])
        
        # Calculer la position de référence sur la route
        ref_position_on_route = route_line.project(reference_point)
        
        entries_after_ref = []
        for entry in nearby_entries:
            entry_point = Point(entry.get_start_point()[0], entry.get_start_point()[1])
            entry_position_on_route = route_line.project(entry_point)
            
            # Vérifier si l'entrée est après la position de référence
            if entry_position_on_route > ref_position_on_route:
                distance_from_ref = entry_position_on_route - ref_position_on_route
                entries_after_ref.append((entry, distance_from_ref))
        
        # Trier par distance depuis la référence
        entries_after_ref.sort(key=lambda x: x[1])
        return entries_after_ref
    
    def _is_entry_near_route(self, entry: CompleteMotorwayLink, route_line: LineString) -> bool:
        """
        Vérifie si une entrée est proche de la route (buffer de 200m).
        
        Args:
            entry: Entrée d'autoroute à vérifier
            route_line: Geometrie de la route
            
        Returns:
            True si l'entrée est dans le buffer
        """
        # Point de départ de l'entrée (coordonnées réelles)
        entry_point = Point(entry.get_start_point()[0], entry.get_start_point()[1])
        
        # Calculer la distance à la route
        distance_to_route = route_line.distance(entry_point)
        
        # Convertir en mètres approximatifs (1 degré ≈ 111320m)
        distance_meters = distance_to_route * 111320
        
        return distance_meters <= self.PROXIMITY_BUFFER_METERS
    
    def get_entry_statistics(self, route_coordinates: List[List[float]]) -> dict:
        """
        Statistiques sur les entrées trouvées près de la route.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            Dictionnaire avec les statistiques
        """
        nearby_entries = self.find_entries_near_route(route_coordinates)
        
        operators = {}
        for entry in nearby_entries:
            operator = entry.associated_toll.operator if entry.associated_toll else "Unknown"
            operators[operator] = operators.get(operator, 0) + 1
        
        return {
            'total_entries_found': len(nearby_entries),
            'entries_with_tolls': len([e for e in nearby_entries if e.has_toll()]),
            'operators': operators,
            'buffer_used_meters': self.PROXIMITY_BUFFER_METERS
        }
