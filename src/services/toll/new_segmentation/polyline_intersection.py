"""
polyline_intersection.py
-----------------------

Module pour détecter l'intersection stricte entre des péages et une polyline de route.
Calcule si un péage est vraiment "SUR" la route (intersection géométrique stricte).

Responsabilité : 
- Calculer l'intersection géométrique stricte entre points de péage et segments de polyline
- Distinguer les péages "sur la route" (intersection stricte) des péages "près de la route"
- Fournir des méthodes de détection fine pour améliorer la précision
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PolylineSegment:
    """Segment de polyline entre deux points consécutifs."""
    start: List[float]  # [lon, lat]
    end: List[float]    # [lon, lat]
    
    def length_km(self) -> float:
        """Calcule la longueur du segment en km."""
        return calculate_distance(self.start, self.end)


def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    Calcule la distance entre deux points géographiques en km.
    
    Args:
        point1: [longitude, latitude]
        point2: [longitude, latitude]
        
    Returns:
        float: Distance en kilomètres
    """
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en km
    return 6371 * c


def point_to_segment_distance(point: List[float], segment: PolylineSegment) -> Tuple[float, List[float]]:
    """
    Calcule la distance minimale d'un point à un segment de ligne.
    
    Args:
        point: Point [lon, lat]
        segment: Segment de polyline
        
    Returns:
        Tuple[float, List[float]]: (distance_km, point_projection_sur_segment)
    """
    # Convertir en coordonnées planes locales pour le calcul
    x1, y1 = segment.start[0], segment.start[1]
    x2, y2 = segment.end[0], segment.end[1]
    px, py = point[0], point[1]
    
    # Vecteur du segment
    dx = x2 - x1
    dy = y2 - y1
    
    # Si le segment est un point (longueur nulle)
    if dx == 0 and dy == 0:
        return calculate_distance(point, segment.start), segment.start
    
    # Paramètre t pour la projection
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    
    # Point de projection sur le segment
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    projection = [proj_x, proj_y]
    
    # Distance du point à la projection
    distance = calculate_distance(point, projection)
    
    return distance, projection


def point_to_polyline_distance(point: List[float], polyline: List[List[float]]) -> Tuple[float, int, List[float]]:
    """
    Calcule la distance minimale d'un point à une polyline complète.
    
    Args:
        point: Point [lon, lat]
        polyline: Liste de points constituant la polyline [[lon, lat], ...]
        
    Returns:
        Tuple[float, int, List[float]]: (distance_minimale_km, index_segment_le_plus_proche, point_projection)
    """
    if len(polyline) < 2:
        return float('inf'), -1, [0, 0]
    
    min_distance = float('inf')
    closest_segment_index = -1
    closest_projection = [0, 0]
    
    # Tester chaque segment de la polyline
    for i in range(len(polyline) - 1):
        segment = PolylineSegment(polyline[i], polyline[i + 1])
        distance, projection = point_to_segment_distance(point, segment)
        
        if distance < min_distance:
            min_distance = distance
            closest_segment_index = i
            closest_projection = projection
    
    return min_distance, closest_segment_index, closest_projection


def is_toll_on_route_strict(
    toll_coordinates: List[float], 
    route_polyline: List[List[float]], 
    max_distance_m: float = 200
) -> Tuple[bool, float, Optional[List[float]]]:
    """
    Détermine si un péage est strictement SUR la route.
    
    Cette fonction calcule l'intersection géométrique stricte entre le point de péage
    et la polyline de la route. Un péage est considéré "sur la route" si sa distance
    perpendiculaire à la polyline est inférieure au seuil donné.
    
    Args:
        toll_coordinates: Coordonnées du péage [lon, lat]
        route_polyline: Points de la route [[lon, lat], ...]
        max_distance_m: Distance maximale en mètres pour considérer le péage "sur la route"
        
    Returns:
        Tuple[bool, float, Optional[List[float]]]: 
            (est_sur_route, distance_minimale_m, point_projection_sur_route)
    """
    if not route_polyline or len(route_polyline) < 2:
        return False, float('inf'), None
    
    # Calculer la distance minimale à la polyline
    distance_km, segment_index, projection = point_to_polyline_distance(toll_coordinates, route_polyline)
    distance_m = distance_km * 1000  # Convertir en mètres
    
    # Vérifier si c'est dans le seuil
    is_on_route = distance_m <= max_distance_m
    
    return is_on_route, distance_m, projection if is_on_route else None


def filter_tolls_on_route_strict(
    tolls: List, 
    route_polyline: List[List[float]], 
    max_distance_m: float = 200,
    coordinate_attr: str = 'coordinates'
) -> List[Tuple[object, float, List[float]]]:
    """
    Filtre les péages qui sont strictement SUR la route avec intersection géométrique.
    
    Args:
        tolls: Liste des péages (objets avec attribut coordinates ou dictionnaires)
        route_polyline: Points de la route [[lon, lat], ...]
        max_distance_m: Distance maximale en mètres pour considérer un péage "sur la route"
        coordinate_attr: Nom de l'attribut contenant les coordonnées
        
    Returns:
        List[Tuple[object, float, List[float]]]: 
            Liste de (péage, distance_m, point_projection) pour les péages sur la route
    """
    if not route_polyline or len(route_polyline) < 2:
        return []
    
    tolls_on_route = []
    
    print(f"🎯 Détection stricte : péages à moins de {max_distance_m}m de la polyline")
    
    for toll in tolls:
        # Extraire les coordonnées selon le type d'objet
        if hasattr(toll, coordinate_attr):
            coords = getattr(toll, coordinate_attr)
        elif isinstance(toll, dict):
            coords = toll.get(coordinate_attr, [])
        else:
            continue
        
        if not coords or len(coords) != 2:
            continue
        
        # Tester l'intersection stricte
        is_on_route, distance_m, projection = is_toll_on_route_strict(
            coords, route_polyline, max_distance_m
        )
        
        if is_on_route:
            tolls_on_route.append((toll, distance_m, projection))
            
            # Log pour debug
            toll_name = getattr(toll, 'name', None) or getattr(toll, 'effective_name', 'Péage inconnu')
            if callable(toll_name):
                toll_name = toll_name()
            elif hasattr(toll, 'osm_name'):
                toll_name = toll.osm_name or 'Péage sans nom'
            
            print(f"   ✅ {toll_name} : {distance_m:.1f}m de la route")
        else:
            # Log pour debug (péages proches mais pas assez)
            toll_name = getattr(toll, 'name', None) or getattr(toll, 'effective_name', 'Péage inconnu')
            if callable(toll_name):
                toll_name = toll_name()
            elif hasattr(toll, 'osm_name'):
                toll_name = toll.osm_name or 'Péage sans nom'
            
            print(f"   ❌ {toll_name} : {distance_m:.1f}m de la route (trop loin)")
    
    print(f"📍 Détection stricte terminée : {len(tolls_on_route)} péages vraiment sur la route")
    return tolls_on_route


def get_toll_position_on_route(
    toll_coordinates: List[float], 
    route_polyline: List[List[float]]
) -> Optional[float]:
    """
    Calcule la position relative d'un péage sur la route (0.0 = début, 1.0 = fin).
    
    Args:
        toll_coordinates: Coordonnées du péage [lon, lat]
        route_polyline: Points de la route [[lon, lat], ...]
        
    Returns:
        Optional[float]: Position relative sur la route (0.0 à 1.0) ou None si erreur
    """
    if not route_polyline or len(route_polyline) < 2:
        return None
    
    # Trouver le segment le plus proche
    distance_km, segment_index, projection = point_to_polyline_distance(toll_coordinates, route_polyline)
    
    if segment_index < 0:
        return None
    
    # Calculer la distance cumulée jusqu'au début du segment
    cumulative_distance = 0.0
    for i in range(segment_index):
        cumulative_distance += calculate_distance(route_polyline[i], route_polyline[i + 1])
    
    # Ajouter la distance dans le segment jusqu'à la projection
    segment_start = route_polyline[segment_index]
    distance_in_segment = calculate_distance(segment_start, projection)
    cumulative_distance += distance_in_segment
    
    # Calculer la distance totale de la route
    total_distance = 0.0
    for i in range(len(route_polyline) - 1):
        total_distance += calculate_distance(route_polyline[i], route_polyline[i + 1])
    
    # Position relative
    if total_distance > 0:
        return cumulative_distance / total_distance
    else:
        return 0.0
