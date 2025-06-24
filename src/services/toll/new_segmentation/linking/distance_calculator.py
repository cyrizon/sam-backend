"""
distance_calculator.py
---------------------

Module pour calculer les distances entre points géographiques.

Responsabilité : calculs de distance précis en mètres.
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
    lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
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
