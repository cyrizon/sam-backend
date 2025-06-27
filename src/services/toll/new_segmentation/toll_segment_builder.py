"""
toll_segment_builder.py
-----------------------

Module pour construire les segments de route intelligents.
Responsabilité : orchestrer la construction des segments en évitant les péages non-désirés.
"""

from typing import List, Dict, Optional
from src.cache.parsers.toll_matcher import MatchedToll
from .toll_entrance_exit_finder import TollEntranceExitFinder
from .motorway_junction_analyzer import MotorwayJunctionAnalyzer
from .segment_building import SegmentStrategy, SegmentBuilders


class TollSegmentBuilder:
    """
    Construit les segments de route pour éviter les péages non-désirés.
    Orchestre les différents modules spécialisés pour la construction des segments.
    """
    
    def __init__(self, ors_service):
        """
        Initialise avec le service ORS.
        
        Args:
            ors_service: Service ORS pour les calculs de routes
        """        
        self.ors = ors_service
        self.entrance_exit_finder = TollEntranceExitFinder(ors_service)
        self.junction_analyzer = None  # Sera initialisé avec le parser OSM
        
        # Modules spécialisés
        self.segment_strategy = None
        self.segment_builders = None
    
    def build_intelligent_segments(
        self, 
        start_coords: List[float], 
        end_coords: List[float],
        all_tolls_on_route: List[MatchedToll], 
        selected_tolls: List[MatchedToll],
        osm_parser = None,
        route_coords: List[List[float]] = None
    ) -> List[Dict]:
        """
        Construit les segments intelligents avec la nouvelle logique granulaire.
        
        Règles :
        - Segment vers péage seulement si nécessaire
        - Segment péage → sortie SEULEMENT si péages à éviter après
        - Segment sortie → entrée pour éviter des péages
        - Segment entrée → péage si nécessaire
        
        Args:
            start_coords: Coordonnées de départ
            end_coords: Coordonnées d'arrivée
            all_tolls_on_route: Tous les péages sur la route directe
            selected_tolls: Péages que l'on veut utiliser
            osm_parser: Parser OSM pour les junctions
            route_coords: Coordonnées de la route de base
            
        Returns:
            List[Dict]: Segments de route à calculer
        """
        print(f"🧩 Construction granulaire pour {len(selected_tolls)} péages sélectionnés...")
        
        # Initialiser l'analyzer de junctions avec les données OSM
        if osm_parser and route_coords:
            self.junction_analyzer = MotorwayJunctionAnalyzer(osm_parser)
            print("🔍 Analyse des motorway_junctions sur la route...")
        
        # Initialiser les modules spécialisés
        self.segment_strategy = SegmentStrategy(self.entrance_exit_finder, self.junction_analyzer)
        self.segment_builders = SegmentBuilders(self.entrance_exit_finder, self.junction_analyzer)
        
        # Cas spécial : aucun péage sélectionné
        if not selected_tolls:
            return []
            
        # Construire les segments selon la nouvelle logique
        segments = self.segment_strategy.build_granular_segments(
            start_coords, end_coords, all_tolls_on_route, selected_tolls, route_coords
        )
        
        return segments
