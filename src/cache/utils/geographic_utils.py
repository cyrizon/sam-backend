"""
Geographic Utilities
-------------------

Utility functions for geographic calculations.
"""

import math
from typing import List


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


def distance_point_to_polyline_meters(point: List[float], polyline: List[List[float]]) -> float:
    """
    Calcule la distance minimale (en mètres) entre un point et une polyligne.
    
    Args:
        point: Point [lon, lat]
        polyline: Liste de points [[lon, lat], ...]
        
    Returns:
        float: Distance minimale en mètres
    """
    min_dist = float('inf')
    
    for i in range(len(polyline) - 1):
        seg_a = polyline[i]
        seg_b = polyline[i + 1]
        
        # Calcul de distance point-segment adapté
        lon1, lat1 = math.radians(seg_a[0]), math.radians(seg_a[1])
        lon2, lat2 = math.radians(seg_b[0]), math.radians(seg_b[1])
        lonp, latp = math.radians(point[0]), math.radians(point[1])
        
        R = 6371000.0  # Rayon de la Terre en mètres
        x1, y1 = R * lon1 * math.cos((lat1+lat2)/2), R * lat1
        x2, y2 = R * lon2 * math.cos((lat1+lat2)/2), R * lat2
        xp, yp = R * lonp * math.cos((lat1+lat2)/2), R * latp
        
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            dist = math.hypot(xp - x1, yp - y1)
        else:
            t = ((xp - x1) * dx + (yp - y1) * dy) / (dx*dx + dy*dy)
            t = max(0, min(1, t))
            x_proj, y_proj = x1 + t * dx, y1 + t * dy
            dist = math.hypot(xp - x_proj, yp - y_proj)
        
        if dist < min_dist:
            min_dist = dist
    
    return min_dist
