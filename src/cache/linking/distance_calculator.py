"""
Distance Calculator
------------------

Module for calculating distances between geographic points.
Moved from linking/distance_calculator.py
"""

import math
from typing import List


def calculate_distance_meters(point1: List[float], point2: List[float]) -> float:
    """
    Calcule la distance entre deux points géographiques en mètres.
    
    Args:
        point1: [longitude, latitude]
        point2: [longitude, latitude]
        
    Returns:
        float: Distance en mètres
    """
    try:
        # Conversion sécurisée en float si nécessaire
        if isinstance(point1[0], str):
            lon1, lat1 = float(point1[0]), float(point1[1])
        else:
            lon1, lat1 = point1[0], point1[1]
            
        if isinstance(point2[0], str):
            lon2, lat2 = float(point2[0]), float(point2[1])
        else:
            lon2, lat2 = point2[0], point2[1]
            
    except (ValueError, IndexError, TypeError) as e:
        print(f"❌ Erreur conversion coordonnées pour distance: {e}")
        return 0.0
    
    lon1_rad, lat1_rad = math.radians(lon1), math.radians(lat1)
    lon2_rad, lat2_rad = math.radians(lon2), math.radians(lat2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Rayon de la Terre en mètres
    return 6371000 * c


def is_within_distance(point1: List[float], point2: List[float], max_distance_m: float) -> bool:
    """
    Vérifie si deux points sont à une distance inférieure au seuil.
    
    Args:
        point1: Premier point [lon, lat]
        point2: Deuxième point [lon, lat]
        max_distance_m: Distance maximale en mètres
        
    Returns:
        bool: True si les points sont assez proches
    """
    return calculate_distance_meters(point1, point2) <= max_distance_m
