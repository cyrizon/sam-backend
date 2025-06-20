"""
geographic_utils.py
-------------------

Utilitaires géographiques pour les calculs de distance et positionnement.
"""

import math
from typing import List


def calculate_distance_km(coord1: List[float], coord2: List[float]) -> float:
    """
    Calcule la distance entre deux coordonnées en kilomètres.
    
    Args:
        coord1: [lon, lat] première coordonnée
        coord2: [lon, lat] deuxième coordonnée
        
    Returns:
        float: Distance en kilomètres
    """
    # Conversion en radians
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    
    # Formule haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en km
    R = 6371
    return R * c


def find_route_position(point: List[float], route_coords: List[List[float]]) -> float:
    """
    Trouve la position d'un point le long d'une route en kilomètres depuis le début.
    
    Args:
        point: Coordonnées [lon, lat] du point
        route_coords: Liste des coordonnées de la route
        
    Returns:
        float: Position en kilomètres depuis le début de la route
    """
    if not route_coords or len(route_coords) < 2:
        return 0.0
    
    min_distance = float('inf')
    best_position = 0.0
    cumulative_distance = 0.0
    
    for i in range(len(route_coords) - 1):
        segment_start = route_coords[i]
        segment_end = route_coords[i + 1]
        
        # Distance du point au segment
        distance_to_segment = _distance_point_to_segment(point, segment_start, segment_end)
        
        if distance_to_segment < min_distance:
            min_distance = distance_to_segment
            # Position approximative sur ce segment
            segment_length = calculate_distance_km(segment_start, segment_end)
            best_position = cumulative_distance + segment_length * 0.5  # Milieu du segment
        
        cumulative_distance += calculate_distance_km(segment_start, segment_end)
    
    return best_position


def _distance_point_to_segment(point: List[float], seg_start: List[float], seg_end: List[float]) -> float:
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
