"""
junction_finder.py
------------------

Module pour trouver les motorway_junctions sur une route.
"""

from typing import List, Dict
from src.cache.parsers.osm_parser import OSMParser
from ..polyline_intersection import point_to_polyline_distance
from .geographic_utils import calculate_distance_km


class JunctionFinder:
    """
    Classe pour trouver les motorway_junctions qui sont sur une route donnée.
    """
    
    def __init__(self, osm_parser: OSMParser):
        """
        Initialise le finder avec les données OSM.
        
        Args:
            osm_parser: Parser contenant les données OSM
        """
        self.osm_parser = osm_parser

    def find_junctions_on_route(self, route_coords: List[List[float]]) -> List[Dict]:        
        """
        Trouve toutes les motorway_junctions sur la route.
        
        Args:
            route_coords: Coordonnées de la route
        Returns:
            List[Dict]: Junctions qui sont sur la route
        """
        junctions_on_route = []
        all_junctions = self.osm_parser.motorway_junctions
        
        if not all_junctions:
            return []
        
        for junction in all_junctions:
            # Récupérer les coordonnées de la junction
            junction_coords = junction.coordinates if hasattr(junction, 'coordinates') else []
            if not junction_coords or len(junction_coords) != 2:
                continue
            
            # Calculer la distance à la route
            distance_result = point_to_polyline_distance(junction_coords, route_coords)
            min_distance_m = distance_result[0] * 1000  # Conversion km -> m (prendre seulement la distance)              
            
            # Garder seulement les junctions très proches de la route (1m max)
            if min_distance_m <= 1:  # Très strict pour éviter de prendre le mauvais côté du péage
                junction_data = {
                    'id': junction.node_id if hasattr(junction, 'node_id') else '',
                    'name': junction.properties.get('name', 'Sortie inconnue') if hasattr(junction, 'properties') else 'Sortie inconnue',
                    'ref': junction.ref if hasattr(junction, 'ref') else '',
                    'coordinates': junction_coords,
                    'distance_to_route': min_distance_m
                }
                
                # Filtrer les aires de repos et services
                if self._is_real_exit(junction_data):
                    junctions_on_route.append(junction_data)
        
        return junctions_on_route

    def order_junctions_by_route_position(
        self, 
        junctions: List[Dict], 
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Ordonne les junctions selon leur position sur la route.
        
        Args:
            junctions: Liste des junctions
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions ordonnées selon leur position sur la route
        """
        for junction in junctions:
            junction_position = self._calculate_position_on_route(
                junction['coordinates'], route_coords
            )
            junction['position_on_route_km'] = junction_position
        
        # Trier par position sur la route
        junctions.sort(key=lambda j: j['position_on_route_km'])
        
        return junctions

    def _calculate_position_on_route(
        self, 
        point_coords: List[float], 
        route_coords: List[List[float]]
    ) -> float:
        """
        Calcule la position d'un point sur la route en kilomètres depuis le début.
        
        Args:
            point_coords: Coordonnées du point [lon, lat]
            route_coords: Coordonnées de la route
            
        Returns:
            float: Position en kilomètres depuis le début de la route
        """
        if not route_coords or len(route_coords) < 2:
            return 0.0
        
        # Trouver le segment de route le plus proche du point
        min_distance = float('inf')
        closest_segment_index = 0
        
        for i in range(len(route_coords) - 1):
            segment_start = route_coords[i]
            segment_end = route_coords[i + 1]
            
            # Distance du point au segment
            distance = self._point_to_segment_distance(
                point_coords, segment_start, segment_end
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_segment_index = i
        
        # Calculer la distance cumulée jusqu'au segment le plus proche
        cumulative_distance = 0.0
        for i in range(closest_segment_index):
            distance = calculate_distance_km(route_coords[i], route_coords[i + 1])
            cumulative_distance += distance
        
        # Ajouter la moitié du segment le plus proche (approximation)
        if closest_segment_index < len(route_coords) - 1:
            segment_distance = calculate_distance_km(
                route_coords[closest_segment_index], 
                route_coords[closest_segment_index + 1]
            )
            cumulative_distance += segment_distance / 2
        
        return cumulative_distance

    def _point_to_segment_distance(
        self, 
        point: List[float], 
        seg_start: List[float], 
        seg_end: List[float]
    ) -> float:
        """
        Calcule la distance d'un point à un segment de ligne.
        
        Args:
            point: Point [lon, lat]
            seg_start: Début du segment [lon, lat]
            seg_end: Fin du segment [lon, lat]
            
        Returns:
            float: Distance minimale en kilomètres
        """
        # Distance aux extrémités du segment
        dist_to_start = calculate_distance_km(point, seg_start)
        dist_to_end = calculate_distance_km(point, seg_end)
        
        # Retourner la distance minimale (approximation simple)
        return min(dist_to_start, dist_to_end)

    def _is_real_exit(self, junction_data: Dict) -> bool:
        """
        Vérifie si une junction est une vraie sortie d'autoroute.
        
        Args:
            junction_data: Données de la junction
            
        Returns:
            bool: True si c'est une vraie sortie
        """
        name = junction_data.get('name', '').lower()
        ref = junction_data.get('ref', '')
        
        # Exclure les aires de repos et services
        excluded_terms = [
            'aire de repos', 'aire de service', 'rest area', 'service area',
            'parking', 'wc', 'toilettes', 'station service'
        ]
        
        for term in excluded_terms:
            if term in name:
                return False
        # NOUVEAU : Filtrage strict - excluer les sorties sans référence
        if not ref or ref.strip() == '':
            # Log seulement en mode debug pour éviter le spam
            return False
        
        # Log seulement les inclusions importantes
        return True
