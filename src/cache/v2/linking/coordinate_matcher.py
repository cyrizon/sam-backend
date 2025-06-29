"""
Coordinate Matcher
-----------------

Utilities for comparing coordinates between motorway segments.
"""

import math
from typing import List, Tuple


def are_coordinates_equal(point1: List[float], point2: List[float], precision: int = 7) -> bool:
    """
    Vérifie si deux coordonnées sont exactement égales (avec précision).
    
    Args:
        point1: [longitude, latitude]
        point2: [longitude, latitude]
        precision: Nombre de décimales pour la comparaison
        
    Returns:
        bool: True si les coordonnées sont identiques
    """
    if not point1 or not point2 or len(point1) < 2 or len(point2) < 2:
        return False
    
    return (round(point1[0], precision) == round(point2[0], precision) and 
            round(point1[1], precision) == round(point2[1], precision))


def calculate_distance_meters(point1: List[float], point2: List[float]) -> float:
    """
    Calcule la distance entre deux points en mètres (formule de Haversine).
    
    Args:
        point1: [longitude, latitude]
        point2: [longitude, latitude]
        
    Returns:
        float: Distance en mètres
    """
    if not point1 or not point2 or len(point1) < 2 or len(point2) < 2:
        return float('inf')
    
    # Rayon de la Terre en mètres
    R = 6371000
    
    lat1, lon1 = math.radians(point1[1]), math.radians(point1[0])
    lat2, lon2 = math.radians(point2[1]), math.radians(point2[0])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = (math.sin(dlat/2)**2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def are_segments_linkable(
    end_point: List[float], 
    start_point: List[float], 
    max_distance_m: float = 2.0
) -> Tuple[bool, str]:
    """
    Détermine si deux segments peuvent être liés (uniquement coordonnées exactes).
    
    Args:
        end_point: Point de fin du premier segment [lon, lat]
        start_point: Point de début du second segment [lon, lat]
        max_distance_m: Paramètre ignoré (compatibilité)
        
    Returns:
        Tuple[bool, str]: (peut_être_lié, raison)
    """
    # Vérification égalité exacte uniquement
    if are_coordinates_equal(end_point, start_point):
        return True, "Coordonnées exactement égales"
    
    return False, "Coordonnées différentes"


class SegmentConnectionAnalyzer:
    """Analyseur de connexions entre segments."""
    
    def __init__(self, max_distance_m: float = 2.0):
        """
        Initialise l'analyseur.
        
        Args:
            max_distance_m: Distance maximale pour lier deux segments
        """
        self.max_distance_m = max_distance_m
    
    def can_connect_segments(
        self, 
        segment1_end: List[float], 
        segment2_start: List[float]
    ) -> Tuple[bool, str]:
        """
        Vérifie si segment1 peut se connecter à segment2 (coordonnées exactes uniquement).
        
        Args:
            segment1_end: Point de fin du segment 1
            segment2_start: Point de début du segment 2
            
        Returns:
            Tuple[bool, str]: (connexion_possible, raison)
        """
        return are_segments_linkable(segment1_end, segment2_start, 0)
    
    def find_connection_type(
        self, 
        seg1_start: List[float], 
        seg1_end: List[float],
        seg2_start: List[float], 
        seg2_end: List[float]
    ) -> Tuple[bool, str, str]:
        """
        Trouve le type de connexion possible entre deux segments (coordonnées exactes uniquement).
        
        Args:
            seg1_start, seg1_end: Points du segment 1
            seg2_start, seg2_end: Points du segment 2
            
        Returns:
            Tuple[bool, str, str]: (connexion_trouvée, type_connexion, raison)
        """
        # Test 1: fin_seg1 → début_seg2 (ordre naturel)
        if are_coordinates_equal(seg1_end, seg2_start):
            return True, "end_to_start", "Fin segment 1 = Début segment 2"
        
        # Test 2: fin_seg1 → fin_seg2 (seg2 inversé)
        if are_coordinates_equal(seg1_end, seg2_end):
            return True, "end_to_end", "Fin segment 1 = Fin segment 2"
        
        # Test 3: début_seg1 → début_seg2 (seg1 inversé)
        if are_coordinates_equal(seg1_start, seg2_start):
            return True, "start_to_start", "Début segment 1 = Début segment 2"
        
        # Test 4: début_seg1 → fin_seg2 (ordre inverse)
        if are_coordinates_equal(seg1_start, seg2_end):
            return True, "start_to_end", "Début segment 1 = Fin segment 2"
        
        return False, "no_connection", "Aucune coordonnée commune"
