"""
Distance Calculator
==================

Utilitaires pour les calculs de distances géographiques.
Fournit des méthodes optimisées pour les calculs point-à-point et point-à-segment.
"""

import math
from typing import List, Tuple


class DistanceCalculator:
    """Calculateur de distances géographiques optimisé."""
    
    @staticmethod
    def calculate_distance_meters(coord1: List[float], coord2: List[float]) -> float:
        """
        Calcule la distance en mètres entre deux coordonnées.
        
        Args:
            coord1: [longitude, latitude] du premier point
            coord2: [longitude, latitude] du second point
            
        Returns:
            Distance en mètres
        """
        if not coord1 or not coord2 or len(coord1) < 2 or len(coord2) < 2:
            return float('inf')
        
        lon1, lat1 = coord1[0], coord1[1]
        lon2, lat2 = coord2[0], coord2[1]
        
        # Formule de Haversine
        R = 6371000  # Rayon de la Terre en mètres
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def distance_point_to_segment_meters(
        point: List[float], 
        segment_start: List[float], 
        segment_end: List[float]
    ) -> float:
        """
        Calcule la distance minimale entre un point et un segment.
        
        Args:
            point: [longitude, latitude] du point
            segment_start: [longitude, latitude] du début du segment
            segment_end: [longitude, latitude] de la fin du segment
            
        Returns:
            Distance minimale en mètres
        """
        if not all([point, segment_start, segment_end]):
            return float('inf')
        
        # Projection du point sur le segment
        def dot_product(v1, v2):
            return v1[0] * v2[0] + v1[1] * v2[1]
        
        def vector_subtract(v1, v2):
            return [v1[0] - v2[0], v1[1] - v2[1]]
        
        def vector_add(v1, v2):
            return [v1[0] + v2[0], v1[1] + v2[1]]
        
        def vector_scale(v, scale):
            return [v[0] * scale, v[1] * scale]
        
        # Vecteurs
        segment_vec = vector_subtract(segment_end, segment_start)
        point_vec = vector_subtract(point, segment_start)
        
        # Longueur au carré du segment
        segment_length_sq = dot_product(segment_vec, segment_vec)
        
        if segment_length_sq == 0:
            # Segment de longueur 0, distance au point
            return DistanceCalculator.calculate_distance_meters(point, segment_start)
        
        # Paramètre t de projection
        t = max(0, min(1, dot_product(point_vec, segment_vec) / segment_length_sq))
        
        # Point projeté
        projection = vector_add(segment_start, vector_scale(segment_vec, t))
        
        # Distance du point à sa projection
        return DistanceCalculator.calculate_distance_meters(point, projection)
    
    @staticmethod
    def min_distance_to_polyline_meters(
        point: List[float], 
        polyline: List[List[float]]
    ) -> float:
        """
        Calcule la distance minimale entre un point et une polyligne.
        
        Args:
            point: [longitude, latitude] du point
            polyline: Liste de coordonnées formant la polyligne
            
        Returns:
            Distance minimale en mètres
        """
        if not point or not polyline or len(polyline) < 2:
            return float('inf')
        
        min_distance = float('inf')
        
        for i in range(len(polyline) - 1):
            segment_start = polyline[i]
            segment_end = polyline[i + 1]
            
            distance = DistanceCalculator.distance_point_to_segment_meters(
                point, segment_start, segment_end
            )
            
            min_distance = min(min_distance, distance)
        
        return min_distance
