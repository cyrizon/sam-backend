"""
exit_toll_detector.py
--------------------

Module spécialisé pour détecter les nouveaux péages sur les routes calculées par ORS.

Responsabilité unique :
- Analyser une route ORS pour identifier les péages
- Détecter les nouveaux péages créés par l'utilisation d'une sortie
- Associer les péages détectés aux coordonnées de sortie
- Fournir les informations nécessaires pour la comptabilisation

Cas d'usage :
Quand on utilise une sortie d'autoroute au lieu d'un péage d'entrée,
ORS calcule une nouvelle route qui peut passer par des péages de sortie.
Ce module détecte ces nouveaux péages pour les comptabiliser correctement.
"""

from typing import List, Optional, Dict, Any, Tuple
from src.cache.models.matched_toll import MatchedToll
from src.cache.parsers.toll_matcher import TollMatcher
from src.cache.parsers.osm_parser import OSMParser


class ExitTollDetector:
    """
    Détecte les péages sur les nouvelles routes calculées après utilisation d'une sortie.
    """
    
    def __init__(self, osm_data_parser: OSMParser, toll_matcher: TollMatcher):
        """
        Initialise le détecteur.
        
        Args:
            osm_data_parser: Parser pour accéder aux données OSM
            toll_matcher: Matcher pour identifier les péages
        """
        self.osm_parser = osm_data_parser
        self.toll_matcher = toll_matcher
    
    def detect_tolls_on_exit_route(
        self, 
        route_coordinates: List[List[float]], 
        exit_coordinates: List[float]
    ) -> Optional[MatchedToll]:
        """
        Détecte les péages sur une route qui utilise une sortie d'autoroute.
        
        Args:
            route_coordinates: Coordonnées de la route calculée par ORS
            exit_coordinates: Coordonnées de la sortie utilisée
            
        Returns:
            Optional[MatchedToll]: Le péage de sortie détecté, ou None
        """
        print(f"   🔍 Détection de péages sur route de sortie...")
        
        # 1. Chercher les péages proches de la route
        nearby_tolls = self._find_tolls_near_route(route_coordinates)
        
        if not nearby_tolls:
            print(f"   ⚠️ Aucun péage détecté sur la route de sortie")
            return None
        
        # 2. Identifier le péage le plus proche de la sortie
        exit_toll = self._find_toll_closest_to_exit(nearby_tolls, exit_coordinates)
        
        if exit_toll:
            print(f"   ✅ Péage de sortie détecté : {exit_toll.effective_name}")
        
        return exit_toll
    
    def _find_tolls_near_route(self, route_coordinates: List[List[float]]) -> List[MatchedToll]:
        """
        Trouve les péages proches de la route.
        
        Args:
            route_coordinates: Coordonnées de la route
            
        Returns:
            List[MatchedToll]: Péages trouvés près de la route
        """
        # Utiliser la même logique que dans l'identification de péages principale
        osm_tolls = self.osm_parser.find_tolls_near_route(route_coordinates, max_distance_km=0.5)
        
        # Convertir et matcher avec les données CSV
        osm_tolls_formatted = self._convert_osm_tolls_to_matched_format(osm_tolls)
        matched_tolls = self.toll_matcher.match_osm_tolls_with_csv(
            osm_tolls_formatted, 
            max_distance_km=2.0
        )
        
        return matched_tolls
    
    def _find_toll_closest_to_exit(
        self, 
        tolls: List[MatchedToll], 
        exit_coordinates: List[float]
    ) -> Optional[MatchedToll]:
        """
        Trouve le péage le plus proche des coordonnées de sortie.
        
        Args:
            tolls: Liste des péages candidats
            exit_coordinates: Coordonnées de la sortie [lon, lat]
            
        Returns:
            Optional[MatchedToll]: Le péage le plus proche
        """
        if not tolls:
            return None
        
        closest_toll = None
        min_distance = float('inf')
        
        for toll in tolls:
            toll_coords = self._get_toll_coordinates(toll)
            if toll_coords:
                distance = self._calculate_distance(exit_coordinates, toll_coords)
                if distance < min_distance:
                    min_distance = distance
                    closest_toll = toll
        
        return closest_toll
    
    def _get_toll_coordinates(self, toll: MatchedToll) -> Optional[List[float]]:
        """
        Récupère les coordonnées d'un péage (priorité OSM puis CSV).
        
        Args:
            toll: Le péage dont récupérer les coordonnées
            
        Returns:
            Optional[List[float]]: [longitude, latitude] ou None
        """
        if toll.osm_coordinates and len(toll.osm_coordinates) == 2:
            return toll.osm_coordinates
        elif toll.csv_coordinates and len(toll.csv_coordinates) == 2:
            return toll.csv_coordinates
        else:
            return None
    
    def _calculate_distance(self, point1: List[float], point2: List[float]) -> float:
        """
        Calcule la distance entre deux points en km.
        
        Args:
            point1: [longitude, latitude]
            point2: [longitude, latitude]
            
        Returns:
            float: Distance en kilomètres
        """
        import math
        
        lon1, lat1 = math.radians(point1[0]), math.radians(point1[1])
        lon2, lat2 = math.radians(point2[0]), math.radians(point2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return c * 6371  # Rayon de la Terre en km
    
    def _convert_osm_tolls_to_matched_format(self, osm_tolls: List) -> List:
        """
        Convertit les péages OSM au format attendu par le matcher.
        
        Args:
            osm_tolls: Péages OSM bruts
            
        Returns:
            List: Péages au format MatchedToll
        """
        # Utiliser la fonction existante du module toll_matcher
        from src.cache.parsers.toll_matcher import convert_osm_tolls_to_matched_format
        return convert_osm_tolls_to_matched_format(osm_tolls)
    
    def validate_exit_toll_replacement(
        self, 
        original_toll: MatchedToll, 
        exit_toll: MatchedToll
    ) -> bool:
        """
        Valide qu'un remplacement de péage par un péage de sortie est pertinent.
        
        Args:
            original_toll: Le péage original qu'on voulait remplacer
            exit_toll: Le péage de sortie proposé
            
        Returns:
            bool: True si le remplacement est valide
        """
        # Vérifications de base
        if not original_toll or not exit_toll:
            return False
        
        # Vérifier que les péages sont différents
        if original_toll.effective_name == exit_toll.effective_name:
            return False
        
        # Vérifier que le péage de sortie est dans une zone proche
        original_coords = self._get_toll_coordinates(original_toll)
        exit_coords = self._get_toll_coordinates(exit_toll)
        
        if not original_coords or not exit_coords:
            return False
        
        distance_km = self._calculate_distance(original_coords, exit_coords)
        
        # Accepter seulement si les péages sont dans un rayon raisonnable (5km max)
        if distance_km > 5.0:
            print(f"   ⚠️ Péages trop éloignés : {distance_km:.1f}km > 5km")
            return False
        
        print(f"   ✅ Remplacement validé : {original_toll.effective_name} → {exit_toll.effective_name} ({distance_km:.1f}km)")
        return True
