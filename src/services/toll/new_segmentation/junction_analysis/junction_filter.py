"""
junction_filter.py
------------------

Module pour filtrer les junctions selon leur position par rapport aux péages.
"""

from typing import List, Dict
from ..toll_matcher import MatchedToll
from .geographic_utils import find_route_position


class JunctionFilter:
    """
    Classe pour filtrer les junctions selon différents critères de position.
    """
    
    def filter_junctions_before_toll(
        self, 
        junctions: List[Dict], 
        toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont AVANT le péage cible.
        
        Args:
            junctions: Junctions ordonnées
            toll_position_km: Position du péage en km
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions avant le péage (ordonnées de la plus proche à la plus lointaine du péage)
        """
        junctions_before = []
        
        for junction in junctions:
            if junction['position_on_route_km'] < toll_position_km:
                junctions_before.append(junction)
        
        # Trier par position décroissante (plus proche du péage en premier)
        junctions_before.sort(key=lambda j: j['position_on_route_km'], reverse=True)
        
        print(f"📍 {len(junctions_before)} junctions trouvées avant le péage cible")
        return junctions_before
    
    def filter_junctions_between_tolls(
        self, 
        junctions: List[Dict], 
        start_toll_position_km: float,
        end_toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont ENTRE deux péages.
        
        Args:
            junctions: Junctions ordonnées
            start_toll_position_km: Position du péage de début (utilisé)
            end_toll_position_km: Position du péage de fin (à éviter)
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions entre les deux péages (ordonnées de la plus proche du début)
        """
        junctions_between = []
        
        for junction in junctions:
            position = junction['position_on_route_km']
            if start_toll_position_km < position < end_toll_position_km:
                junctions_between.append(junction)
        
        # Trier par position décroissante (plus proche du péage de destination en premier)
        junctions_between.sort(key=lambda j: j['position_on_route_km'], reverse=True)
        
        print(f"📍 {len(junctions_between)} junctions trouvées entre les péages ({start_toll_position_km:.1f} km - {end_toll_position_km:.1f} km)")
        return junctions_between
    
    def filter_junctions_after_toll(
        self, 
        junctions: List[Dict], 
        toll_position_km: float,
        route_coords: List[List[float]]
    ) -> List[Dict]:
        """
        Filtre les junctions qui sont APRÈS le péage.
        
        Args:
            junctions: Junctions ordonnées
            toll_position_km: Position du péage en km
            route_coords: Coordonnées de la route
            
        Returns:
            List[Dict]: Junctions après le péage (ordonnées par position croissante)
        """
        junctions_after = []
        
        for junction in junctions:
            if junction['position_on_route_km'] > toll_position_km:
                junctions_after.append(junction)
        
        # Trier par position croissante (plus proche du péage en premier)
        junctions_after.sort(key=lambda j: j['position_on_route_km'])
        
        print(f"📍 {len(junctions_after)} junctions trouvées après le péage ({toll_position_km:.1f} km)")
        return junctions_after

    def find_toll_position_on_route(self, toll: MatchedToll, route_coords: List[List[float]]) -> float:
        """
        Trouve la position d'un péage sur la route.
        
        Args:
            toll: Péage à localiser
            route_coords: Coordonnées de la route
            
        Returns:
            float: Position en kilomètres depuis le début de la route
        """
        toll_coords = toll.osm_coordinates
        return find_route_position(toll_coords, route_coords)
