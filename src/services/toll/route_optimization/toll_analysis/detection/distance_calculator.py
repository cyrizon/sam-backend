"""
Distance Calculator Optimized
============================

Calculs de distances géographiques ultra-optimisés pour la détection de péages.
Responsabilité unique : calculs de distances rapides et précis.
"""

import math
from typing import List, Tuple, Optional, Dict


class OptimizedDistanceCalculator:
    """Calculateur de distances optimisé pour la détection de péages."""
    
    @staticmethod
    def fast_approximate_distance_meters(
        point: List[float], 
        segment_start: List[float], 
        segment_end: List[float]
    ) -> float:
        """
        Distance approximative ultra-rapide (Manhattan + correction).
        Utilisée pour le pré-filtrage avant calcul précis.
        
        Args:
            point: [longitude, latitude]
            segment_start: [longitude, latitude] début segment
            segment_end: [longitude, latitude] fin segment
            
        Returns:
            Distance approximative en mètres
        """
        if not all([point, segment_start, segment_end]):
            return float('inf')
        
        # Distance Manhattan au milieu du segment
        mid_x = (segment_start[0] + segment_end[0]) / 2
        mid_y = (segment_start[1] + segment_end[1]) / 2
        
        dx = abs(point[0] - mid_x)
        dy = abs(point[1] - mid_y)
        
        # Conversion approximative degrés → mètres
        # 1 degré ≈ 111000m, correction Manhattan → Euclidienne ≈ 0.7
        return (dx + dy) * 111000 * 0.7
    
    @staticmethod
    def precise_point_to_segment_meters(
        point: List[float], 
        segment_start: List[float], 
        segment_end: List[float]
    ) -> float:
        """
        Distance précise point-à-segment avec projection géodésique.
        
        Args:
            point: [longitude, latitude]
            segment_start: [longitude, latitude] début segment
            segment_end: [longitude, latitude] fin segment
            
        Returns:
            Distance précise en mètres
        """
        if not all([point, segment_start, segment_end]):
            return float('inf')
        
        # Conversion en coordonnées cartésiennes locales
        def to_cartesian(coord):
            lon_rad = math.radians(coord[0])
            lat_rad = math.radians(coord[1])
            return [lon_rad, lat_rad]
        
        p = to_cartesian(point)
        a = to_cartesian(segment_start)
        b = to_cartesian(segment_end)
        
        # Vecteurs
        ab = [b[0] - a[0], b[1] - a[1]]
        ap = [p[0] - a[0], p[1] - a[1]]
        
        # Produit scalaire et norme au carré
        ab_dot_ab = ab[0] * ab[0] + ab[1] * ab[1]
        
        if ab_dot_ab == 0:
            # Segment de longueur 0
            return OptimizedDistanceCalculator._haversine_distance(point, segment_start)
        
        # Paramètre de projection
        ap_dot_ab = ap[0] * ab[0] + ap[1] * ab[1]
        t = max(0, min(1, ap_dot_ab / ab_dot_ab))
        
        # Point projeté
        projection = [
            a[0] + t * ab[0],
            a[1] + t * ab[1]
        ]
        
        # Reconversion en degrés
        projection_deg = [math.degrees(projection[0]), math.degrees(projection[1])]
        
        # Distance Haversine au point projeté
        return OptimizedDistanceCalculator._haversine_distance(point, projection_deg)
    
    @staticmethod
    def optimized_point_to_polyline_meters(
        point: List[float], 
        polyline: List[List[float]]
    ) -> Tuple[float, int, int]:
        """
        Distance optimisée point-à-polyligne avec early optimizations.
        
        Args:
            point: [longitude, latitude]
            polyline: Liste des coordonnées de la polyligne
            
        Returns:
            Tuple (distance_minimale, index_segment_le_plus_proche, index_point_le_plus_proche)
        """
        if not point or not polyline or len(polyline) < 2:
            return float('inf'), -1, -1
        
        min_distance = float('inf')
        closest_segment_idx = -1
        closest_point_idx = -1
        
        # Échantillonnage adaptatif pour polylignes très longues
        step = max(1, len(polyline) // 500)  # Max 500 segments à vérifier
        
        for i in range(0, len(polyline) - 1, step):
            segment_start = polyline[i]
            segment_end = polyline[min(i + step, len(polyline) - 1)]
            
            # Pré-filtrage avec distance approximative
            approx_dist = OptimizedDistanceCalculator.fast_approximate_distance_meters(
                point, segment_start, segment_end
            )
            
            # Si approximation prometteuse, calcul précis
            if approx_dist < min_distance + 200:  # Marge 200m
                precise_dist = OptimizedDistanceCalculator.precise_point_to_segment_meters(
                    point, segment_start, segment_end
                )
                
                if precise_dist < min_distance:
                    min_distance = precise_dist
                    closest_segment_idx = i
                    closest_point_idx = i
                    
                    # Micro-optimisation : si très proche, inutile de chercher mieux
                    if precise_dist <= 0.5:  # 50cm
                        break
        
        return min_distance, closest_segment_idx, closest_point_idx
    
    @staticmethod
    def _haversine_distance(coord1: List[float], coord2: List[float]) -> float:
        """
        Distance Haversine précise entre deux points.
        
        Args:
            coord1: [longitude, latitude]
            coord2: [longitude, latitude]
            
        Returns:
            Distance en mètres
        """
        if not coord1 or not coord2 or len(coord1) < 2 or len(coord2) < 2:
            return float('inf')
        
        R = 6371000  # Rayon terrestre en mètres
        
        lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
        lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @staticmethod
    def batch_distance_calculation(
        candidates: List, 
        route_coordinates: List[List[float]]
    ) -> List[Dict]:
        """
        Calcul optimisé par lot pour tous les candidats.
        
        Args:
            candidates: Liste des péages candidats
            route_coordinates: Coordonnées de la route
            
        Returns:
            Liste des résultats avec distances calculées
        """
        results = []
        
        print(f"   📐 Calcul distances pour {len(candidates)} candidats...")
        
        for toll in candidates:
            if not toll.osm_coordinates:
                continue
            
            # Calcul distance optimisé
            min_dist, segment_idx, point_idx = \
                OptimizedDistanceCalculator.optimized_point_to_polyline_meters(
                    toll.osm_coordinates, route_coordinates
                )
            
            results.append({
                'toll': toll,
                'distance': min_dist,
                'closest_segment_idx': segment_idx,
                'closest_point_idx': point_idx
            })
        
        return results
